import argparse
import sys
from datetime import date
from config.manager import ConfigManager
from engines.simulation.loop import SimulationLoop
from engines.simulation.mlflow_logger import MLflowLogger
from engines.simulation.metrics import compute_metrics
import pandas as pd

def main():
    parser = argparse.ArgumentParser(description="Run Aegis Phase 1 Backtest")
    parser.add_argument("--config", type=str, required=True, help="Path to JSON config file")
    parser.add_argument("--start", type=str, default="2022-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, default="2023-12-31", help="End date (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    print(f"Loading config from {args.config}...")
    try:
        config = ConfigManager.load(args.config)
    except Exception as e:
        print(f"Config Error: {e}")
        sys.exit(1)
        
    print(f"Config loaded. Fingerprint: {config.fingerprint}")
    print(f"Run ID: {config.run_id}")
    print(f"Universe: {len(config.asset_universe.tickers)} tickers")
    
    start_dt = date.fromisoformat(args.start)
    end_dt = date.fromisoformat(args.end)
    
    logger = MLflowLogger(config)
    
    # Pre-calculate deterministic holdout partition for MLflow transparency
    all_dates = pd.date_range(start_dt, end_dt, freq='B').date.tolist()
    num_holdout = int(len(all_dates) * 0.2)
    import hashlib
    import numpy as np
    seed_int = int(hashlib.md5(config.run_id.encode('utf-8'), usedforsecurity=False).hexdigest(), 16) % (2**32)
    np.random.seed(seed_int)
    holdout_dates = sorted(np.random.choice(all_dates, num_holdout, replace=False))
    holdout_str = [d.isoformat() for d in holdout_dates]

    print("Sealing partition and logging start...")
    logger.log_run_start(holdout_dates=holdout_str) 
    
    loop = SimulationLoop(config)
    loop_results = loop.run(start_dt, end_dt)
    
    print(f"\nSimulation complete. Executed {len(loop_results['trade_log'])} trades.")
    
    # Calculate dummy benchmark for now
    b_returns = pd.Series([0.0] * len(loop_results["nav_history"]))
    
    metrics = compute_metrics(
        loop_results["nav_history"],
        b_returns,
        loop_results["holdout_dates"]
    )
    
    print("\n--- Strategy Metrics ---")
    print(f"Optimization Sharpe: {metrics.get('optimization_sharpe', 0):.2f}")
    print(f"Held-out Sharpe:     {metrics.get('held_out_sharpe', 0):.2f}")
    print(f"Slippage Drag (USD): ${metrics.get('slippage_drag', 0):.2f}")
    
    print("\nWriting artifacts to MLflow...")
    logger.log_run_end(
        metrics=metrics,
        trade_log=loop_results["trade_log"],
        nav_history=loop_results["nav_history"],
        gate_events=loop_results["gate_events"]
    )
    
    print(f"Done! MLflow tracking URI: sqlite:///mlruns.db")

if __name__ == "__main__":
    main()
