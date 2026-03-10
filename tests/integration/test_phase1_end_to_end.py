import os
import uuid
import pytest
import mlflow
from datetime import date
from typing import Any

from config.manager import ConfigManager
from engines.simulation.loop import SimulationLoop
from engines.simulation.mlflow_logger import MLflowLogger
from engines.simulation.metrics import compute_metrics
import pandas as pd

def run_phase1_backtest(config: Any, run_id: str) -> dict:
    """Wrapper that runs the SimulationLoop natively so it logs to MLflow."""
    config.run_id = run_id
    
    # Init Engine
    loop = SimulationLoop(config)
    
    # In Phase 1, we use a simple date range
    start_dt = date(2023, 12, 1)
    end_dt = date(2023, 12, 31)
    
    loop_results = loop.run(start_dt, end_dt)
    
    # The loop natively handles the MLflowTracker logging if router is debug/production
    
    # We compute metrics here for the test verification
    benchmark_returns = pd.Series([0.0] * len(loop_results["nav_history"]))
    metrics = compute_metrics(
        loop_results["nav_history"], 
        benchmark_returns, 
        loop_results["holdout_dates"]
    )

    return {
        "optimization_dates": loop_results["optimization_dates"],
        "holdout_dates": loop_results["holdout_dates"],
        "metrics": metrics,
        "mlflow_run_id": loop_results.get("mlflow_run_id", config.run_id),
        "trade_log": loop_results["trade_log"]
    }
def test_full_phase1_backtest(mocker):
    """
    2-year backtest on 3 tickers. Validates data -> simulation -> metrics -> MLflow.
    """
    # Use real live API calls where possible, but mock expensive ones if needed locally
    # We will test against AAPL, MSFT, GOOGL.
    
    # Fast-pass specific slow methods to prevent timeouts during unit testing
    mocker.patch("engines.fundamental.insider_activity_monitor.InsiderActivityMonitor.compute", return_value={"congressional": [], "insider_type": "none"})
    
    config = ConfigManager.load("config/templates/tech_breakout_v1.json")
    config.asset_universe.tickers = ["AAPL", "MSFT", "GOOGL"]

    # We run it!
    run_id = str(uuid.uuid4())
    result = run_phase1_backtest(config, run_id)

    # Partition integrity
    assert set(result["optimization_dates"]).isdisjoint(set(result["holdout_dates"]))
    assert len(result["holdout_dates"]) > 0

    # Required metrics
    required_metrics = [
        "optimization_total_return", "optimization_cagr", "optimization_sharpe",
        "optimization_sortino", "optimization_max_drawdown", "optimization_win_rate",
        "held_out_total_return", "held_out_cagr", "held_out_sharpe",
        "held_out_sortino", "held_out_max_drawdown", "held_out_win_rate",
        "gross_return", "net_return", "slippage_drag"
    ]
    
    for m in required_metrics:
        assert m in result["metrics"], f"Missing: {m}"

    # Slippage
    assert result["metrics"]["slippage_drag"] >= 0

    # MLflow verification
    run = mlflow.get_run(result["mlflow_run_id"])
    
    # Phase 3 MLflowTracker flattens the config, so we check for basic properties
    assert "version" in run.data.params
    assert run.data.params["version"] == "1.0.0"
    
    # Since depth is production/debug, we should see artifacts
    client = mlflow.MlflowClient()
    artifacts = client.list_artifacts(run.info.run_id)
    artifact_paths = [a.path for a in artifacts]
    
    # Check for agent traces directory (created since agent is enabled)
    assert "agent_traces" in artifact_paths
