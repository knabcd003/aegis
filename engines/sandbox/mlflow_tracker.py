import os
import json
import numpy as np
import pandas as pd
from typing import Dict, Any
import mlflow

class MLflowTracker:
    def __init__(self, tracking_uri: str = "sqlite:///mlflow.db"):
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment("Aegis_AI_Phase3")

    def log_run(self, config_dump: Dict[str, Any], results: Dict[str, Any], run_type: str = "optimization"):
        """Logs configuration, partitioned metrics, and artifacts to MLflow."""
        run_name = config_dump.get("run_id", "unknown_run")
        with mlflow.start_run(run_name=run_name) as run:
            # 1. Log configuration (flattened)
            mlflow.set_tag("run_type", run_type)
            flat_config = self._flatten_dict(config_dump)
            for k, v in flat_config.items():
                # MLflow defines a max length of 250 characters for string parameter values
                mlflow.log_param(k, str(v)[:250])

            # 2. Compute partitioned metrics
            opt_dates = set(results.get("optimization_dates", []))
            holdout_dates = set(results.get("holdout_dates", []))
            
            nav_history = results.get("nav_history", [])
            trade_log = results.get("trade_log", [])
            
            # Helper to compute Return and Sharpe
            def compute_metrics_for_partition(dates_set: set) -> Dict[str, float]:
                partition_navs = [n["nav"] for n in nav_history if n["date"].isoformat() in dates_set]
                partition_trades = [t for t in trade_log if t.get("fill_date") and t["fill_date"].isoformat() in dates_set]
                
                if not partition_navs:
                    return {"return": 0.0, "sharpe": 0.0, "trades": 0.0, "win_rate": 0.0}
                    
                total_return = (partition_navs[-1] - partition_navs[0]) / partition_navs[0]
                
                # Approximate Sharpe
                nav_series = pd.Series(partition_navs)
                pct_change = nav_series.pct_change().dropna()
                mean_pct = pct_change.mean()
                std_pct = pct_change.std()
                sharpe = (mean_pct / std_pct) * np.sqrt(252) if std_pct and std_pct > 0 else 0.0
                
                # Check trades for win rate (simplification: sell price > buy price for the same ticker)
                # We would need to match P&L properly, but for now we just count trades
                num_trades = len(partition_trades)
                
                return {
                    "return": float(total_return),
                    "sharpe": float(sharpe),
                    "trades": float(num_trades)
                }

            opt_metrics = compute_metrics_for_partition(opt_dates)
            holdout_metrics = compute_metrics_for_partition(holdout_dates)

            # Log Optimization Metrics (Visible to Agent)
            mlflow.log_metric("opt_total_return", opt_metrics["return"])
            mlflow.log_metric("opt_sharpe", opt_metrics["sharpe"])
            mlflow.log_metric("opt_num_trades", opt_metrics["trades"])

            # Log Holdout Metrics (SEALED: Used for final evaluation, not agent feedback)
            if float(holdout_metrics["trades"]) > 0 or float(holdout_metrics["return"]) != 0:
                mlflow.log_metric("holdout_total_return", holdout_metrics["return"])
                mlflow.log_metric("holdout_sharpe", holdout_metrics["sharpe"])
                mlflow.log_metric("holdout_num_trades", holdout_metrics["trades"])

            # 3. Log Latency Distributions
            node_latencies_log = results.get("node_latencies_log", [])
            if node_latencies_log:
                df_lat = pd.DataFrame(node_latencies_log)
                
                # Log summary stats for each node
                for node_name in df_lat["node"].unique():
                    node_df = df_lat[df_lat["node"] == node_name]
                    mlflow.log_metric(f"{node_name}_latency_avg", float(node_df["latency"].mean()))
                    mlflow.log_metric(f"{node_name}_latency_max", float(node_df["latency"].max()))
                    mlflow.log_metric(f"{node_name}_latency_min", float(node_df["latency"].min()))
                    mlflow.log_metric(f"{node_name}_latency_std", float(node_df["latency"].std()) if len(node_df) > 1 else 0.0)

                # Save raw CSV artifact
                os.makedirs("debug/telemetry", exist_ok=True)
                lat_path = f"debug/telemetry/node_latencies_{run_name}.csv"
                df_lat.to_csv(lat_path, index=False)
                mlflow.log_artifact(lat_path, "telemetry")

            # 4. Log Artifacts
            trace_events = results.get("trace_events", [])
            if trace_events:
                os.makedirs("debug/traces", exist_ok=True)
                trace_path = f"debug/traces/recommendation_trace_{run_name}.jsonl"
                with open(trace_path, "w") as f:
                    for t in trace_events:
                        f.write(json.dumps(t) + "\n")
                mlflow.log_artifact(trace_path, "agent_traces")
                
            return run.info.run_id # Return the run ID so orchestrator can harvest it

    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """Flattens nested dictionaries for flat MLflow parameter logging."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
