import time
import asyncio
from graph.workflow import app_graph
from db.factory import DatabaseFactory
from agents.db_agent import DBTools
from agents.schema_agent import SchemaTools
from config import settings
from crewai import Agent, Task, Crew
import json
import random

class BenchmarkRunner:
    @staticmethod
    async def run_benchmark(dummy_queries=None):
        """
        Dynamically discovers databases for both Postgres and MySQL, 
        generates schema-aware queries, and runs a comprehensive benchmark.
        """
        results = []
        db_types = ['postgres', 'mysql']
        
        # 1. Generate Queries for each DB Type
        generator_agent = Agent(
            role='Benchmark Architect',
            goal='Generate realistic business questions for a given database schema.',
            backstory='You are an expert data analyst who knows what users typically ask from databases.',
            llm=f"mistral/{settings.MISTRAL_MODEL_FAST}"
        )

        for db_type in db_types:
            try:
                dbs = await DBTools.list_databases(db_type)
                # Filter out system DBs
                system_dbs = ['postgres', 'template1', 'template0', 'information_schema', 'mysql', 'performance_schema', 'phpmyadmin', 'test']
                user_dbs = [db for db in dbs if db not in system_dbs]
                
                for db_name in user_dbs:
                    print(f"Generating benchmark queries for {db_type} database: {db_name}")
                    
                    # Extract schema
                    db = await DatabaseFactory.get_db(db_type, db_name)
                    raw_schema = await db.get_schema()
                    schema_text = json.dumps(raw_schema, indent=2)
                    
                    task = Task(
                        description=f"Based on this schema for {db_type} database '{db_name}':\n{schema_text}\n"
                                    f"Generate 2 diverse natural language questions. "
                                    f"One should be an aggregation (e.g. total, count) and one should be a filter. "
                                    f"Return ONLY a JSON list of strings. No markdown.",
                        agent=generator_agent,
                        expected_output="JSON list of strings."
                    )
                    crew = Crew(agents=[generator_agent], tasks=[task])
                    gen_result = await crew.kickoff_async()
                    
                    try:
                        res_str = str(gen_result).replace("```json", "").replace("```", "").strip()
                        queries = json.loads(res_str)
                        
                        for query in queries:
                            start_time = time.time()
                            config = {"configurable": {"thread_id": f"bench_{db_name}_{int(start_time)}"}}
                            initial_state = {
                                "user_query": query,
                                "db_type": db_type,
                                "db_name": db_name,
                                "intent": "",
                                "schema": "",
                                "raw_schema": {},
                                "sql": "",
                                "explanation": "",
                                "query_plan": "",
                                "confidence_score": 0,
                                "confidence_level": "",
                                "chart": {},
                                "result": "",
                                "error": "",
                                "retry_count": 0,
                                "role": "admin",
                                "context_used": False,
                                "history": []
                            }
                            
                            final_state = await app_graph.ainvoke(initial_state, config=config)
                            latency = (time.time() - start_time) * 1000
                            
                            results.append({
                                "db_type": db_type,
                                "db": db_name,
                                "query": query,
                                "generated_sql": final_state.get('sql'),
                                "latency_ms": round(latency, 2),
                                "success": not final_state.get('error'),
                                "confidence": final_state.get('confidence_score', 0),
                                "error": final_state.get('error', '')
                            })
                            
                            # Small sleep to avoid rate limits during benchmark
                            await asyncio.sleep(1)
                            
                    except Exception as e:
                        print(f"Failed to process queries for {db_name}: {e}")
            except Exception as e:
                print(f"Failed to benchmark {db_type}: {e}")

        # Calculate Stats
        total = len(results)
        if total == 0:
            return {"accuracy": "0%", "avg_latency": "0ms", "details": []}
            
        successes = sum(1 for r in results if r['success'])
        avg_latency = sum(r['latency_ms'] for r in results) / total
        avg_confidence = sum(r['confidence'] for r in results) / total
        
        return {
            "accuracy": f"{round((successes / total) * 100, 1)}%",
            "avg_latency": f"{round(avg_latency, 0)}ms",
            "avg_confidence": f"{round(avg_confidence, 1)}%",
            "total_queries": total,
            "details": results
        }

BENCHMARK_QUERIES = []
