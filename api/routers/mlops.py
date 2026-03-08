from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import sqlite3
import pandas as pd
import json
import os

from api.main import state

router = APIRouter()

class SweepRequest(BaseModel):
    tickers: List[str]
    n_trials: int = 10
    models_to_test: List[str] = ["qwen2.5:14b", "llama3.1:8b"]

@router.post("/sweep")
async def launch_optuna_sweep(
    request: SweepRequest, 
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Launch an Optuna hyperparameter sweep in the background.
    This simulates the Darwinian Sandbox, discovering the highest alpha configs.
    """
    if not state.data_engine:
        raise HTTPException(status_code=503, detail="Data Engine is offline")
        
    job_id = f"sweep_{len(request.tickers)}_{request.n_trials}trials"
    
    def background_run_sweep():
        # In a real app, this imports orchestrator.py and runs the Optuna study
        pass
        
    background_tasks.add_task(background_run_sweep)
    
    return {
        "status": "accepted",
        "job_id": job_id,
        "message": f"MLflow Sandbox Sweep started for {request.n_trials} trials across {len(request.tickers)} tickers."
    }

@router.get("/runs")
async def get_mlflow_runs(limit: int = 20) -> Dict[str, Any]:
    """
    Query the local MLflow SQLite database directly to return the leaderboard
    of the best historically backtested Agent topologies and Quant thresholds.
    """
    db_path = "mlflow.db"
    if not os.path.exists(db_path):
        return {"status": "success", "count": 0, "runs": [], "message": "No MLflow database found."}
        
    try:
        # Connect directly to the underlying MLflow DB for lighting fast reads
        conn = sqlite3.connect(db_path)
        
        # This query joins the runs with their hyperparameters and metrics
        query = f"""
        SELECT 
            r.run_uuid,
            r.status,
            r.start_time,
            m1.value as sharpe_ratio,
            m2.value as max_drawdown,
            p1.value as hmm_length,
            p2.value as vpin_threshold,
            p3.value as llm_model
        FROM runs r
        LEFT JOIN metrics m1 ON r.run_uuid = m1.run_uuid AND m1.key = 'sharpe_ratio'
        LEFT JOIN metrics m2 ON r.run_uuid = m2.run_uuid AND m2.key = 'max_drawdown'
        LEFT JOIN params p1 ON r.run_uuid = p1.run_uuid AND p1.key = 'hmm_window_length'
        LEFT JOIN params p2 ON r.run_uuid = p2.run_uuid AND p2.key = 'vpin_toxic_threshold'
        LEFT JOIN params p3 ON r.run_uuid = p3.run_uuid AND p3.key = 'worker_llm_model'
        WHERE r.status = 'FINISHED' AND m1.value IS NOT NULL
        ORDER BY m1.value DESC
        LIMIT {limit};
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Convert nan to None for JSON serialization
        df = df.where(pd.notnull(df), None)
        
        runs = df.to_dict(orient="records")
        
        return {
            "status": "success",
            "count": len(runs),
            "leaderboard": runs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
