import operator
from typing import Annotated, TypedDict, Union, List, Dict, Any
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
    return {"schema": formatted_schema, "raw_schema": raw_schema}

async def sql_generation_node(state: AgentState):
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
    if state['sql'].startswith("-- ERROR"):
        return {"error": state['sql']}
    
    # Hallucination Guard
    is_valid, msg = validator_agent.validate_hallucination(state['sql'], state['raw_schema'])
    if not is_valid:
        return {"error": msg}
        
    # Security Guard
    is_safe, msg = validator_agent.is_safe(state['sql'], state.get('role', 'user'))
    if not is_safe:
        return {"error": msg}
        
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

# Router
def route_after_intent(state: AgentState):
    if state['intent'] == "SQL_QUERY": return "extract_schema"
    if state['intent'] == "INSIGHTS": return "extract_schema"
    return "db_ops" # Placeholder for other intents

def route_after_execution(state: AgentState):
    if state['error'] and state['retry_count'] < 2: return "generate_sql"
    if state['intent'] == "INSIGHTS": return "generate_insights"
    return "explain_and_visualize"

# Build Graph
workflow = StateGraph(AgentState)

workflow.add_node("classify_intent", classify_intent_node)
workflow.add_node("extract_schema", schema_node)
workflow.add_node("generate_sql", sql_generation_node)
workflow.add_node("validate_sql", validation_node)
workflow.add_node("execute_sql", execution_node)
workflow.add_node("explain_and_visualize", explain_node) # Combined for speed
workflow.add_node("visualize", visualization_node)
workflow.add_node("generate_insights", insights_node)

workflow.set_entry_point("classify_intent")

workflow.add_conditional_edges("classify_intent", route_after_intent, {
    "extract_schema": "extract_schema",
    "db_ops": END # Implementation for DB ops can be added later
})

workflow.add_edge("extract_schema", "generate_sql")
workflow.add_edge("generate_sql", "validate_sql")
workflow.add_edge("validate_sql", "execute_sql")

workflow.add_conditional_edges("execute_sql", route_after_execution, {
    "generate_sql": "generate_sql",
    "generate_insights": "generate_insights",
    "explain_and_visualize": "explain_and_visualize"
})

workflow.add_edge("explain_and_visualize", "visualize")
workflow.add_edge("visualize", END)
workflow.add_edge("generate_insights", END)

from langgraph.checkpoint.memory import MemorySaver
memory = MemorySaver()
app_graph = workflow.compile(checkpointer=memory)
