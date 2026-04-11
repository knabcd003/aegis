"""
MLflow Tracker (Phase 4 — Complete)

Logs simulation results to MLflow with all Promotion Gate metrics.
Uses engines.simulation.metrics for computation.
"""
import os
import json
import numpy as np
import pandas as pd
from typing import Dict, Any, List
import mlflow

from engines.simulation.metrics import compute_metrics


class MLflowTracker:
    def __init__(self, tracking_uri: str = "sqlite:///mlruns.db"):
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment("Aegis_AI_Phase4")

    def log_run(
        self,
        config_dump: Dict[str, Any],
        results: Dict[str, Any],
        run_type: str = "optimization",
    ) -> str:
        """
        Logs configuration, all Promotion Gate metrics, and artifacts to MLflow.
        Returns the MLflow run ID.
        """
        run_name = config_dump.get("run_id", "unknown_run")

        with mlflow.start_run(run_name=run_name) as run:
            # 1. Log configuration (flattened)
            mlflow.set_tag("run_type", run_type)
            flat_config = self._flatten_dict(config_dump)
            for k, v in flat_config.items():
                mlflow.log_param(k, str(v)[:250])

            # 2. Compute all metrics via the metrics module
            nav_history = results.get("nav_history", [])
            trade_log = results.get("trade_log", [])
            holdout_dates = results.get("holdout_dates", [])

            metrics = compute_metrics(
                nav_history=nav_history,
                trade_log=trade_log,
                holdout_dates=holdout_dates,
            )

            # Log all numerical metrics to MLflow
            for key, value in metrics.items():
                if isinstance(value, (int, float)) and key != "error":
                    mlflow.log_metric(key, float(value))

            # 3. Log latency distributions (if present)
            node_latencies_log = results.get("node_latencies_log", [])
            if node_latencies_log:
                df_lat = pd.DataFrame(node_latencies_log)
                for node_name in df_lat["node"].unique():
                    node_df = df_lat[df_lat["node"] == node_name]
                    mlflow.log_metric(
                        f"{node_name}_latency_avg",
                        float(node_df["latency"].mean()),
                    )
                    mlflow.log_metric(
                        f"{node_name}_latency_max",
                        float(node_df["latency"].max()),
                    )
                    mlflow.log_metric(
                        f"{node_name}_latency_min",
                        float(node_df["latency"].min()),
                    )
                    mlflow.log_metric(
                        f"{node_name}_latency_std",
                        float(node_df["latency"].std()) if len(node_df) > 1 else 0.0,
                    )

                os.makedirs("debug/telemetry", exist_ok=True)
                lat_path = f"debug/telemetry/node_latencies_{run_name}.csv"
                df_lat.to_csv(lat_path, index=False)
                mlflow.log_artifact(lat_path, "telemetry")

            # 4. Log trade-level artifacts
            # Round-trip trade log as JSON artifact
            from engines.simulation.metrics import match_round_trip_trades

            round_trips = match_round_trip_trades(trade_log)
            if round_trips:
                os.makedirs("debug/trades", exist_ok=True)
                rt_path = f"debug/trades/round_trips_{run_name}.json"
                # Serialize dates to strings
                serializable_trips = []
                for rt in round_trips:
                    rt_copy = dict(rt)
                    for key in ("entry_date", "exit_date"):
                        if key in rt_copy:
                            rt_copy[key] = str(rt_copy[key])
                    serializable_trips.append(rt_copy)
                with open(rt_path, "w") as f:
                    json.dump(serializable_trips, f, indent=2)
                mlflow.log_artifact(rt_path, "trades")

            # Agent traces (if present)
            trace_events = results.get("trace_events", [])
            if trace_events:
                os.makedirs("debug/traces", exist_ok=True)
                trace_path = f"debug/traces/recommendation_trace_{run_name}.jsonl"
                with open(trace_path, "w") as f:
                    for t in trace_events:
                        f.write(json.dumps(t) + "\n")
                mlflow.log_artifact(trace_path, "agent_traces")

            return run.info.run_id

    def _flatten_dict(
        self, d: Dict[str, Any], parent_key: str = "", sep: str = "."
    ) -> Dict[str, Any]:
        """Flattens nested dictionaries for flat MLflow parameter logging."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
