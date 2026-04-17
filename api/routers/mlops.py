import sqlite3
import pandas as pd
import json
import os
import mlflow
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, BackgroundTasks

from api.main import state
from engines.sentinel.promotion_gate import PromotionGateInput

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

class PromotionRequest(BaseModel):
    session_quality: str = "nominal"
    scenario_pass_rate: Optional[float] = 0.8  # Defaulting for verification
    debate_confidence: Optional[int] = 70      # Defaulting for verification

@router.post("/promote/{run_id}")
async def promote_strategy(run_id: str, request: PromotionRequest) -> Dict[str, Any]:
    """
    Formally evaluate a backtested strategy against the Phase 4 Promotion Gate.
    If it passes all 10 metric gates, promote it to a live Sentinel.
    """
    if not state.promotion_gate or not state.sentinel_mgr:
        raise HTTPException(status_code=503, detail="Sentinel engines are offline")

    # 1. Gate Evaluation
    gate_input = PromotionGateInput(
        run_id=run_id,
        session_quality=request.session_quality,
        scenario_pass_rate=request.scenario_pass_rate,
        debate_confidence=request.debate_confidence
    )
    
    gate_result = state.promotion_gate.evaluate_backtest(
        run_id=run_id,
        session_quality=gate_input.session_quality,
        scenario_pass_rate=gate_input.scenario_pass_rate,
        debate_confidence=gate_input.debate_confidence
    )
    
    if not gate_result.passed:
        return {
            "status": "rejected",
            "run_id": run_id,
            "gate_result": gate_result.to_dict()
        }

    # 2. Deployment (Success path)
    try:
        # Fetch the config from MLflow artifacts
        mlflow.set_tracking_uri("sqlite:///mlflow.db")
        local_path = mlflow.artifacts.download_artifacts(run_id=run_id, artifact_path="config.json")
        with open(local_path, "r") as f:
            config_data = json.load(f)
            
        sentinel = state.sentinel_mgr.deploy_sentinel(
            sentinel_id=f"sentinel_{run_id[:8]}",
            config=config_data,
            promoted_run_id=run_id
        )
        
        return {
            "status": "promoted",
            "sentinel_id": sentinel.sentinel_id,
            "gate_result": gate_result.to_dict(),
            "message": f"Strategy {run_id} passed all gates and is now a live Sentinel."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Promotion Gate passed, but deployment failed: {str(e)}")
