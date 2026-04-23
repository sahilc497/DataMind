import logging
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from db.factory import DatabaseFactory
from graph.workflow import app_graph
from utils.benchmark_runner import BenchmarkRunner, BENCHMARK_QUERIES

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure connections are warm if needed
    yield
    # Shutdown
    await DatabaseFactory.close_all()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Text-to-SQL Enterprise Platform", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str
    db_type: str = "postgres"
    database: str = "postgres"
    thread_id: str = "default_user"
    role: str = "user" # Default to restricted mode

@app.post("/chat")
async def chat(request: ChatRequest):
    start_time = time.time()
    try:
        initial_state = {
            "user_query": request.query,
            "db_type": request.db_type,
            "db_name": request.database,
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
            "role": request.role,
            "context_used": False,
            "history": [] # This can be fetched from a DB in a real production app
        }
        
        config = {"configurable": {"thread_id": request.thread_id}}
        final_state = await app_graph.ainvoke(initial_state, config=config)
        
        latency = round(time.time() - start_time, 2)
        
        return {
            "intent": final_state.get("intent"),
            "sql": final_state.get("sql"),
            "explanation": final_state.get("explanation"),
            "query_plan": final_state.get("query_plan"),
            "confidence_score": final_state.get("confidence_score"),
            "confidence_level": final_state.get("confidence_level"),
            "result": final_state.get("result"),
            "chart": final_state.get("chart"),
            "error": final_state.get("error"),
            "context_used": final_state.get("context_used", False),
            "latency": f"{latency}s"
        }
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/databases")
async def get_databases(db_type: str = "postgres"):
    try:
        db = await DatabaseFactory.get_db(db_type)
        dbs = await db.list_databases()
        return {"databases": dbs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/benchmark")
async def run_system_benchmark():
    try:
        stats = await BenchmarkRunner.run_benchmark(BENCHMARK_QUERIES)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
