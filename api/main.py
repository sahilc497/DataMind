import logging
import time
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from contextlib import asynccontextmanager
from db.factory import DatabaseFactory
from graph.workflow import app_graph
from utils.benchmark_runner import BenchmarkRunner, BENCHMARK_QUERIES
from config import settings

# Mechanical Intelligence Imports
from services.mechanical_reasoning_engine import MechanicalReasoningEngine
from services.failure_prediction_model import FailurePredictionModel
from services.simulation_engine import SimulationEngine
from services.maintenance_advisor import MaintenanceAdvisor
from services.auto_insights import AutoInsightGenerator

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Warm up ML model
    try:
        FailurePredictionModel.ensure_trained()
        logger.info("Failure prediction model initialized")
    except Exception as e:
        logger.warning(f"ML model init warning: {e}")
    yield
    # Shutdown
    await DatabaseFactory.close_all()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Sentinel — Industrial Intelligence Platform", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════
#  REQUEST MODELS
# ═══════════════════════════════════════════════

class ChatRequest(BaseModel):
    query: str
    db_type: str = "postgres"
    database: str = "postgres"
    thread_id: str = "default_user"
    role: str = "user"
    mode: str = "data"  # "data" or "mechanical"

class PredictRequest(BaseModel):
    machine_id: int
    hours_lookback: int = 48

class SimulateRequest(BaseModel):
    machine_id: int
    scenario: str  # e.g., "increase load by 20%"

class RecommendRequest(BaseModel):
    machine_id: int

# ═══════════════════════════════════════════════
#  HELPER: Fetch sensor data from mechanical DB
# ═══════════════════════════════════════════════

async def _get_sensor_data(machine_id: int, hours: int = 48):
    """Fetch recent sensor data for a machine from mech_ai_demo DB."""
    try:
        db_type = settings.MECHANICAL_DB_TYPE
        db = await DatabaseFactory.get_db(db_type, settings.MECHANICAL_DB)
        sql = f"""SELECT temperature, vibration, pressure, rpm, load_percentage, timestamp 
                  FROM sensor_logs 
                  WHERE machine_id = {machine_id} 
                  AND timestamp > NOW() - INTERVAL {hours} HOUR
                  ORDER BY timestamp ASC"""
        result = await db.execute_query(sql)
        return result if isinstance(result, list) else []
    except Exception as e:
        logger.error(f"Error fetching sensor data: {e}")
        return []

async def _get_all_machines():
    """Fetch all machines from mech_ai_demo DB."""
    try:
        db_type = settings.MECHANICAL_DB_TYPE
        db = await DatabaseFactory.get_db(db_type, settings.MECHANICAL_DB)
        result = await db.execute_query("SELECT machine_id, machine_name, type, installation_date, status FROM machines ORDER BY machine_id")
        return result if isinstance(result, list) else []
    except Exception as e:
        logger.error(f"Error fetching machines: {e}")
        return []

# ═══════════════════════════════════════════════
#  EXISTING ENDPOINTS (PRESERVED)
# ═══════════════════════════════════════════════

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
            "history": [],
            # Mechanical fields
            "mode": request.mode,
            "mechanical_analysis": None,
            "prediction": None,
            "recommendation": None,
            "insights": None,
        }
        
        config = {"configurable": {"thread_id": request.thread_id}}
        final_state = await app_graph.ainvoke(initial_state, config=config)
        
        latency = round(time.time() - start_time, 2)
        
        response = {
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
            "latency": f"{latency}s",
            "mode": request.mode,
        }
        
        # Add mechanical intelligence fields if in mechanical mode
        if request.mode == "mechanical":
            response["mechanical_analysis"] = final_state.get("mechanical_analysis")
            response["prediction"] = final_state.get("prediction")
            response["recommendation"] = final_state.get("recommendation")
            response["insights"] = final_state.get("insights")
        
        return response
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

# ═══════════════════════════════════════════════
#  MECHANICAL INTELLIGENCE ENDPOINTS (NEW)
# ═══════════════════════════════════════════════

@app.get("/dashboard")
async def get_dashboard():
    """Get fleet-wide machine health overview."""
    try:
        machines = await _get_all_machines()
        if not machines:
            return {"machines": [], "fleet_insights": [{"text": "No machines found. Run init_mechanical_db.py first.", "severity": "medium", "type": "setup"}]}
        
        dashboard_machines = []
        for m in machines:
            mid = m.get("machine_id", m.get("id", 0))
            sensor_data = await _get_sensor_data(mid, hours=72)
            
            health = MechanicalReasoningEngine.get_machine_health_status(sensor_data)
            prediction = FailurePredictionModel.predict(sensor_data)
            
            dashboard_machines.append({
                "id": mid,
                "name": m.get("machine_name", m.get("name", f"Machine {mid}")),
                "type": m.get("type", "Unknown"),
                "location": m.get("location", ""),
                "status": m.get("status", "unknown"),
                "health": health,
                "prediction": prediction,
                "metrics": health.get("metrics", {})
            })
        
        fleet_data = {"machines": dashboard_machines}
        fleet_insights = AutoInsightGenerator.generate_fleet_insights(fleet_data)
        
        return {
            "machines": dashboard_machines,
            "fleet_insights": fleet_insights,
            "total_machines": len(machines),
            "critical_count": sum(1 for m in dashboard_machines if m["health"].get("status") == "critical"),
            "warning_count": sum(1 for m in dashboard_machines if m["health"].get("status") == "warning"),
            "healthy_count": sum(1 for m in dashboard_machines if m["health"].get("status") == "healthy"),
        }
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict")
async def predict_failure(request: PredictRequest):
    """Predict failure probability for a specific machine."""
    try:
        sensor_data = await _get_sensor_data(request.machine_id, request.hours_lookback)
        if not sensor_data:
            raise HTTPException(status_code=404, detail=f"No sensor data found for machine {request.machine_id}")
        
        prediction = FailurePredictionModel.predict(sensor_data)
        diagnoses = MechanicalReasoningEngine.analyze_machine(sensor_data)
        
        return {
            "machine_id": request.machine_id,
            "prediction": prediction,
            "diagnoses": diagnoses,
            "data_points_analyzed": len(sensor_data)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simulate")
async def simulate_scenario(request: SimulateRequest):
    """Run a what-if simulation for a machine."""
    try:
        sensor_data = await _get_sensor_data(request.machine_id, 24)
        if not sensor_data:
            raise HTTPException(status_code=404, detail=f"No sensor data found for machine {request.machine_id}")
        
        # Get current state from latest readings
        metrics = MechanicalReasoningEngine._compute_metrics(sensor_data)
        current_state = {
            "temperature": metrics.get("avg_temperature", 65),
            "vibration": metrics.get("avg_vibration", 2.0),
            "pressure": metrics.get("avg_pressure", 120),
            "rpm": metrics.get("avg_rpm", 2000),
            "load_percent": metrics.get("avg_load", 60),
            "efficiency": metrics.get("avg_efficiency", 85),
        }
        
        result = SimulationEngine.simulate(request.scenario, current_state)
        return {"machine_id": request.machine_id, "scenario": request.scenario, **result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Simulation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/insights")
async def get_insights():
    """Get auto-generated insights for all machines."""
    try:
        machines = await _get_all_machines()
        all_insights = []
        
        for m in machines:
            mid = m.get("machine_id", m.get("id", 0))
            sensor_data = await _get_sensor_data(mid, 72)
            if sensor_data:
                machine_insights = AutoInsightGenerator.generate_from_data(sensor_data)
                for insight in machine_insights:
                    insight["machine_id"] = mid
                    insight["machine_name"] = m.get("machine_name", m.get("name", f"Machine {mid}"))
                all_insights.extend(machine_insights)
        
        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        all_insights.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 4))
        
        return {"insights": all_insights[:20], "total_machines_analyzed": len(machines)}
    except Exception as e:
        logger.error(f"Insights error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recommend")
async def get_recommendations():
    """Get maintenance recommendations for all machines needing attention."""
    try:
        machines = await _get_all_machines()
        recommendations = []
        
        for m in machines:
            mid = m.get("machine_id", m.get("id", 0))
            sensor_data = await _get_sensor_data(mid, 72)
            
            diagnoses = MechanicalReasoningEngine.analyze_machine(sensor_data)
            prediction = FailurePredictionModel.predict(sensor_data)
            
            if diagnoses or prediction.get("failure_probability", 0) > 0.25:
                rec = MaintenanceAdvisor.generate_recommendations(
                    diagnoses=diagnoses,
                    prediction=prediction,
                    machine_name=m.get("machine_name", m.get("name", f"Machine {mid}"))
                )
                rec["machine_id"] = mid
                recommendations.append(rec)
        
        recommendations.sort(key=lambda r: {"critical": 0, "high": 1, "medium": 2, "low": 3, "routine": 4}.get(r.get("urgency", "routine"), 5))
        
        return {"recommendations": recommendations, "machines_needing_attention": len(recommendations)}
    except Exception as e:
        logger.error(f"Recommendations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
