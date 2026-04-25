import operator
from typing import Annotated, TypedDict, Union, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from crewai import Task, Crew
import asyncio
import random
import re
import json

from agents.intent_agent import IntentAgent
from agents.db_agent import DBAgent
from agents.schema_agent import SchemaAgent, SchemaTools
from agents.sql_agent import SQLAgent
from agents.validator_agent import ValidatorAgent
from agents.executor_agent import ExecutorAgent, ExecutionTools
from agents.explanation_agent import ExplanationAgent
from services.confidence_evaluator import ConfidenceEvaluator
from services.viz_engine import VisualizationEngine
from services.rbac_manager import RBACManager
from cache.caching import QueryCache
from memory.context_manager import ContextManager
from services.normalization import SchemaNormalizer

# Mechanical Intelligence Imports
from services.mechanical_reasoning_engine import MechanicalReasoningEngine
from services.failure_prediction_model import FailurePredictionModel
from services.maintenance_advisor import MaintenanceAdvisor
from services.auto_insights import AutoInsightGenerator

# Global semaphore to limit concurrent LLM calls
llm_semaphore = asyncio.Semaphore(2)

async def run_crew_with_retry(crew, max_retries=3):
    async with llm_semaphore:
        for i in range(max_retries):
            try:
                await asyncio.sleep(random.uniform(0.1, 0.5))
                return await crew.kickoff_async()
            except Exception as e:
                if "429" in str(e) and i < max_retries - 1:
                    await asyncio.sleep(5 * (i + 1))
                    continue
                raise e

class AgentState(TypedDict):
    user_query: str
    db_type: str
    db_name: str
    intent: str
    schema: str
    raw_schema: Dict[str, Any]
    sql: str
    explanation: str
    query_plan: str
    confidence_score: int
    confidence_level: str
    chart: dict
    result: Union[str, List[dict]]
    error: str
    retry_count: int
    role: str
    context_used: bool
    history: List[Dict[str, Any]]
    # Mechanical Copilot fields
    mode: str  # "data" or "mechanical"
    mechanical_analysis: Optional[Dict[str, Any]]
    prediction: Optional[Dict[str, Any]]
    recommendation: Optional[Dict[str, Any]]
    insights: Optional[List[Dict[str, Any]]]

# Initialize Agents
intent_agent = IntentAgent().get_agent()
db_agent = DBAgent().get_agent()
schema_agent_obj = SchemaAgent()
sql_agent_obj = SQLAgent()
validator_agent = ValidatorAgent()
explanation_agent = ExplanationAgent().get_agent()

# Nodes
async def classify_intent_node(state: AgentState):
    # Check for context first
    history_str = ContextManager.format_history(state.get("history", []))
    
    task = Task(
        description=f"Classify query: '{state['user_query']}'. Context:\n{history_str}\n"
                    f"Return ONLY one: LIST_DB, USE_DB, LIST_TABLES, SQL_QUERY, INSIGHTS.",
        agent=intent_agent,
        expected_output="One category name."
    )
    crew = Crew(agents=[intent_agent], tasks=[task])
    result = await run_crew_with_retry(crew)
    intent = str(result).strip().upper()
    intent = re.search(r'(LIST_DB|USE_DB|LIST_TABLES|SQL_QUERY|INSIGHTS)', intent, re.IGNORECASE)
    return {"intent": intent.group(1).upper() if intent else "SQL_QUERY"}

async def schema_node(state: AgentState):
    raw_schema = await SchemaTools.get_normalized_schema(state['db_type'], state['db_name'])
    formatted_schema = SchemaTools.format_for_llm(raw_schema)
    # Guard: if schema has no tables, set an error early
    if not raw_schema.get("tables"):
        return {
            "schema": formatted_schema,
            "raw_schema": raw_schema,
            "error": f"No tables found in database '{state['db_name']}' ({state['db_type']}). Please select a database that contains tables."
        }
    return {"schema": formatted_schema, "raw_schema": raw_schema}

async def sql_generation_node(state: AgentState):
    # 0. If schema is empty, short-circuit with a clear error
    if not state.get('raw_schema', {}).get('tables'):
        return {
            "sql": "",
            "error": f"No tables found in database '{state['db_name']}'. Cannot generate SQL without schema."
        }

    # 1. Caching Check
    schema_hash = SchemaNormalizer.get_schema_hash(state['raw_schema'])
    cached_sql = QueryCache.get_sql(state['user_query'], state['db_type'], schema_hash)
    if cached_sql:
        return {"sql": cached_sql, "context_used": True}

    # 2. Fast Path
    user_query = state['user_query'].lower().strip()
    table_match = re.search(r'(?:show|list|get|select|see)\s+(?:all\s+)?(?:rows\s+in\s+|data\s+in\s+|from\s+)?(?:the\s+)?([a-zA-Z0-9_]+)', user_query)
    if table_match:
        table_name = table_match.group(1)
        tables_in_schema = [t["name"].lower() for t in state['raw_schema'].get("tables", [])]
        if table_name in tables_in_schema:
            sql = f"SELECT * FROM {table_name} LIMIT 100;"
            return {"sql": sql}

    # 3. LLM Generation
    history_str = ContextManager.format_history(state.get("history", []))
    error_feedback = f"\n\nPREVIOUS ERROR: {state['error']}\nPlease correct the SQL." if state['error'] else ""
    
    agent = sql_agent_obj.get_agent(state['db_type'])
    task = Task(
        description=f"Schema:\n{state['schema']}\n\nContext:\n{history_str}\n\nUser Query: {state['user_query']}{error_feedback}",
        agent=agent,
        expected_output="Clean SQL query."
    )
    crew = Crew(agents=[agent], tasks=[task])
    result = await run_crew_with_retry(crew)
    sql = str(result).replace("```sql", "").replace("```", "").strip()
    
    # Cache the result
    QueryCache.set_sql(state['user_query'], state['db_type'], schema_hash, sql)
    return {"sql": sql}

async def validation_node(state: AgentState):
    # If there's already an error (e.g. from schema_node/sql_generation_node), pass it through
    if state.get('error') and not state.get('sql'):
        return {"error": state['error'], "retry_count": state['retry_count'] + 1}

    if state['sql'].startswith("-- ERROR"):
        return {"error": state['sql'], "retry_count": state['retry_count'] + 1}
    
    # Hallucination Guard
    is_valid, msg = validator_agent.validate_hallucination(state['sql'], state['raw_schema'])
    if not is_valid:
        return {"error": msg, "retry_count": state['retry_count'] + 1}
        
    # Security Guard
    is_safe, msg = validator_agent.is_safe(state['sql'], state.get('role', 'user'))
    if not is_safe:
        return {"error": msg, "retry_count": state['retry_count'] + 1}
        
    return {"error": ""}

async def execution_node(state: AgentState):
    if state['error']:
        return {"result": f"Execution Blocked: {state['error']}"}
        
    # Result Caching
    cached_result = QueryCache.get_result(state['sql'], state['db_name'])
    if cached_result:
        return {"result": cached_result, "context_used": True}

    result = await ExecutionTools.execute_sql(state['sql'], state['db_type'], state['db_name'])
    
    if "DATA_JSON:" in result:
        try:
            data = json.loads(result.split("DATA_JSON:")[1].strip())
            QueryCache.set_result(state['sql'], state['db_name'], data)
            return {"result": data, "error": ""}
        except:
            pass
            
    if "Error" in result:
        return {"error": result, "retry_count": state['retry_count'] + 1}
        
    return {"result": result, "error": ""}

async def explain_node(state: AgentState):
    if state['error'] or not state['sql']:
        return {"explanation": "", "query_plan": ""}
        
    # Get Query Plan
    plan = await ExecutionTools.get_explanation(state['sql'], state['db_type'], state['db_name'])
    
    # Get Human Explanation
    task = Task(
        description=f"Explain SQL: {state['sql']} for Query: {state['user_query']}. DB Type: {state['db_type']}",
        agent=explanation_agent,
        expected_output="Clear explanation."
    )
    crew = Crew(agents=[explanation_agent], tasks=[task])
    explanation = await run_crew_with_retry(crew)
    
    return {"explanation": str(explanation).strip(), "query_plan": plan}

async def visualization_node(state: AgentState):
    if state['error'] or not isinstance(state['result'], list):
        return {"chart": {}}
    
    chart_config = VisualizationEngine.detect_chart_type(state['result'], state['sql'])
    return {"chart": chart_config or {}}

async def insights_node(state: AgentState):
    # For "Why" queries
    task = Task(
        description=f"Analyze data for query: {state['user_query']}. Data: {state['result']}",
        agent=explanation_agent,
        expected_output="Strategic insights and anomalies."
    )
    crew = Crew(agents=[explanation_agent], tasks=[task])
    result = await run_crew_with_retry(crew)
    return {"explanation": str(result).strip()}

async def db_ops_node(state: AgentState):
    print(f"DEBUG: db_ops_node started. Intent: {state['intent']}")
    intent = state['intent']
    db_type = state['db_type']
    db_name = state['db_name']
    
    if intent == "LIST_DB":
        from agents.db_agent import DBTools
        dbs = await DBTools.list_databases(db_type)
        res = f"Available {db_type} databases: " + ", ".join(dbs)
        print(f"DEBUG: LIST_DB result: {res}")
        return {"result": res}
    
    if intent == "LIST_TABLES":
        from agents.db_agent import DBTools
        tables = await DBTools.list_tables(db_type, db_name)
        res = f"Tables in {db_name} ({db_type}): " + ", ".join(tables)
        print(f"DEBUG: LIST_TABLES result: {res}")
        return {"result": res}
    
    if intent == "USE_DB":
        res = f"Successfully switched to {db_name}. How can I help you with this database?"
        print(f"DEBUG: USE_DB result: {res}")
        return {"result": res}

    return {"result": "Operation completed."}

# ═══════════════════════════════════════════════
#  MECHANICAL INTELLIGENCE NODES (NEW)
# ═══════════════════════════════════════════════

async def mechanical_reasoning_node(state: AgentState):
    """Analyze SQL results through mechanical engineering lens."""
    result = state.get("result")
    if not isinstance(result, list) or not result:
        return {"mechanical_analysis": {"diagnoses": [], "health": {"status": "unknown"}}}
    
    try:
        diagnoses = MechanicalReasoningEngine.analyze_machine(result)
        health = MechanicalReasoningEngine.get_machine_health_status(result)
        
        # Generate auto-insights
        insights = AutoInsightGenerator.generate_from_data(result, state.get("user_query", ""))
        
        return {
            "mechanical_analysis": {
                "diagnoses": diagnoses,
                "health": health
            },
            "insights": insights
        }
    except Exception as e:
        print(f"Mechanical reasoning error: {e}")
        return {"mechanical_analysis": {"diagnoses": [], "health": {"status": "error", "error": str(e)}}}

async def prediction_node(state: AgentState):
    """Run ML failure prediction on sensor data."""
    result = state.get("result")
    if not isinstance(result, list) or not result:
        return {"prediction": {"failure_probability": 0, "risk_level": "unknown", "remaining_useful_life_hours": 999}}
    
    try:
        prediction = FailurePredictionModel.predict(result)
        return {"prediction": prediction}
    except Exception as e:
        print(f"Prediction error: {e}")
        return {"prediction": {"failure_probability": 0, "risk_level": "error", "remaining_useful_life_hours": 999, "error": str(e)}}

async def recommendation_node(state: AgentState):
    """Generate maintenance recommendations from analysis + prediction."""
    diagnoses = []
    prediction = state.get("prediction", {})
    
    analysis = state.get("mechanical_analysis", {})
    if analysis:
        diagnoses = analysis.get("diagnoses", [])
    
    try:
        recommendation = MaintenanceAdvisor.generate_recommendations(
            diagnoses=diagnoses,
            prediction=prediction,
            machine_name="Queried Machine"
        )
        return {"recommendation": recommendation}
    except Exception as e:
        print(f"Recommendation error: {e}")
        return {"recommendation": {"summary": "Unable to generate recommendations", "actions": [], "urgency": "unknown"}}

# ═══════════════════════════════════════════════
#  ROUTERS
# ═══════════════════════════════════════════════

def route_after_intent(state: AgentState):
    print(f"DEBUG: route_after_intent. Intent: {state['intent']}")
    if state['intent'] == "SQL_QUERY": return "extract_schema"
    if state['intent'] == "INSIGHTS": return "extract_schema"
    return "db_ops"

def route_after_execution(state: AgentState):
    # If there's an error but retries not exhausted, retry SQL generation
    if state['error'] and state['retry_count'] < 2:
        return "generate_sql"
    
    # If there's an error and retries are exhausted, stop — go to final output
    if state['error']:
        return "explain_and_visualize"
    
    if state['intent'] == "INSIGHTS": return "generate_insights"
    
    # Route to mechanical pipeline if in mechanical mode
    mode = state.get("mode", "data")
    if mode == "mechanical":
        return "mechanical_reasoning"
    
    return "explain_and_visualize"

def route_after_recommendation(state: AgentState):
    """After mechanical pipeline, go to explain+visualize for final formatting."""
    return END

# ═══════════════════════════════════════════════
#  BUILD GRAPH
# ═══════════════════════════════════════════════

workflow = StateGraph(AgentState)

# Existing nodes
workflow.add_node("classify_intent", classify_intent_node)
workflow.add_node("extract_schema", schema_node)
workflow.add_node("generate_sql", sql_generation_node)
workflow.add_node("validate_sql", validation_node)
workflow.add_node("execute_sql", execution_node)
workflow.add_node("explain_and_visualize", explain_node)
workflow.add_node("visualize", visualization_node)
workflow.add_node("generate_insights", insights_node)
workflow.add_node("db_ops", db_ops_node)

# New mechanical intelligence nodes
workflow.add_node("mechanical_reasoning", mechanical_reasoning_node)
workflow.add_node("failure_prediction", prediction_node)
workflow.add_node("maintenance_recommendation", recommendation_node)

workflow.set_entry_point("classify_intent")

workflow.add_conditional_edges("classify_intent", route_after_intent, {
    "extract_schema": "extract_schema",
    "db_ops": "db_ops"
})

workflow.add_edge("extract_schema", "generate_sql")
workflow.add_edge("generate_sql", "validate_sql")
workflow.add_edge("validate_sql", "execute_sql")
workflow.add_edge("db_ops", END)

workflow.add_conditional_edges("execute_sql", route_after_execution, {
    "generate_sql": "generate_sql",
    "generate_insights": "generate_insights",
    "explain_and_visualize": "explain_and_visualize",
    "mechanical_reasoning": "mechanical_reasoning"
})

# Mechanical pipeline chain
workflow.add_edge("mechanical_reasoning", "failure_prediction")
workflow.add_edge("failure_prediction", "maintenance_recommendation")
workflow.add_edge("maintenance_recommendation", END)

# Existing end edges
workflow.add_edge("explain_and_visualize", "visualize")
workflow.add_edge("visualize", END)
workflow.add_edge("generate_insights", END)

from langgraph.checkpoint.memory import MemorySaver
memory = MemorySaver()
app_graph = workflow.compile(checkpointer=memory)
app_graph.recursion_limit = 50  # Safety net to prevent infinite loops
