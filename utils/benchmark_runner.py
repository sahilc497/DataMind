import time
import asyncio
from graph.workflow import app_graph

class BenchmarkRunner:
    @staticmethod
    async def run_benchmark(dummy_queries=None):
        """
        Dynamically discovers databases, generates queries, and runs benchmark.
        """
        from agents.db_agent import DBTools
        from agents.schema_agent import SchemaTools
        from config import settings
        from crewai import Agent, Task, Crew
        import json
        from db.connection import db_manager

        # 1. Discover Databases
        dbs = await DBTools.list_databases()
        user_dbs = [db for db in dbs if db not in ['postgres', 'template1', 'template0']]
        
        all_benchmark_queries = []
        
        # 2. Generate Queries for each DB
        generator_agent = Agent(
            role='Benchmark Architect',
            goal='Generate realistic business questions for a given database schema.',
            backstory='You are an expert data analyst who knows what users typically ask from databases.',
            llm=f"mistral/{settings.MISTRAL_MODEL_FAST}"
        )

        for db_name in user_dbs:
            print(f"Generating benchmark queries for database: {db_name}")
            await db_manager.switch_database(db_name)
            schema = await SchemaTools.extract_schema()
            
            task = Task(
                description=f"Based on this schema for database '{db_name}':\n{schema}\n"
                            f"Generate 3 diverse natural language questions a user might ask. "
                            f"Include one simple list, one aggregation, and one filter. "
                            f"Return ONLY a JSON list of strings. No markdown.",
                agent=generator_agent,
                expected_output="JSON list of strings."
            )
            crew = Crew(agents=[generator_agent], tasks=[task])
            result = await crew.kickoff_async()
            
            try:
                # Clean result if it has markdown blocks
                res_str = str(result).replace("```json", "").replace("```", "").strip()
                queries = json.loads(res_str)
                for q in queries:
                    all_benchmark_queries.append({"db": db_name, "query": q})
            except Exception as e:
                print(f"Failed to generate queries for {db_name}: {e}")
                all_benchmark_queries.append({"db": db_name, "query": "List all tables"})

        # 3. Run benchmarks sequentially
        results = []
        import random
        for q_data in all_benchmark_queries:
            db_name = q_data['db']
            query = q_data['query']
            print(f"Benchmarking query in {db_name}: {query}")
            
            # Switch to correct DB before invoke
            await db_manager.switch_database(db_name)
            
            start_time = time.time()
            try:
                config = {"configurable": {"thread_id": f"benchmark_{int(start_time)}_{random.randint(0,1000)}"}}
                state = {
                    "user_query": query,
                    "intent": "",
                    "db_name": db_name,
                    "schema": "",
                    "sql": "",
                    "explanation": "",
                    "confidence_score": 0,
                    "confidence_level": "",
                    "chart": {},
                    "result": "",
                    "error": "",
                    "retry_count": 0,
                    "role": "admin",
                    "context_used": False
                }
                final_state = await app_graph.ainvoke(state, config=config)
                
                latency = (time.time() - start_time) * 1000
                is_success = not final_state.get('error')
                
                results.append({
                    "db": db_name,
                    "query": query,
                    "generated_sql": final_state.get('sql'),
                    "latency_ms": round(latency, 2),
                    "success": is_success,
                    "confidence": final_state.get('confidence_score', 0),
                    "error": final_state.get('error', '')
                })
            except Exception as e:
                results.append({
                    "db": db_name,
                    "query": query,
                    "error": str(e),
                    "success": False,
                    "latency_ms": 0,
                    "confidence": 0
                })
            
            # Throttle between queries
            await asyncio.sleep(2)

        total_time = sum(r.get('latency_ms', 0) for r in results)
        success_count = sum(1 for r in results if r.get('success'))

        avg_latency = total_time / len(results) if results else 0
        accuracy = (success_count / len(results)) * 100 if results else 0
        
        return {
            "accuracy": f"{round(accuracy, 2)}%",
            "avg_latency": f"{round(avg_latency, 2)}ms",
            "success_rate": f"{round(accuracy, 2)}%",
            "details": results
        }

# Remove sample benchmark set as it's now dynamic
BENCHMARK_QUERIES = []
