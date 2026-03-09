import json
import os
import shutil
import mlflow
from typing import Dict, Any, List

from config.schema import AegisConfig


class MLflowLogger:
    """
    Handles logging of config, metrics, and trace artifacts to MLflow based on `logging.depth`.
    """
    def __init__(self, config: AegisConfig):
        self.config = config
        self.run_id = config.run_id
        self.depth = config.routing.logging.depth
        
        # In a real environment, this might connect to a remote tracking server
        mlflow.set_tracking_uri("sqlite:///mlruns.db")
        mlflow.set_experiment(f"aegis_{config.routing.mode}")

    def log_run_start(self, holdout_dates: List[str]):
        """Runs immediately before the first simulation day to seal the config and partition."""
        with mlflow.start_run(run_name=self.run_id) as run:
            self._mlflow_run_id = run.info.run_id # MLflow internal ID
            
            # Log exact params
            mlflow.log_param("config_id", self.config.config_id)
            mlflow.log_param("run_type", self.config.routing.mode)
            mlflow.log_param("config_fingerprint", self.config.fingerprint)
            mlflow.log_param("holdout_dates", str(holdout_dates))
            
            # Log config json
            os.makedirs(f"data/runs/{self.run_id}", exist_ok=True)
            config_path = f"data/runs/{self.run_id}/config.json"
            with open(config_path, "w") as f:
                f.write(self.config.model_dump_json(indent=2))
            
            mlflow.log_artifact(config_path)

    def log_run_end(self, metrics: Dict[str, float], trade_log: List[Dict], nav_history: List[Dict], gate_events: List[Dict]):
        """Runs at the end of the simulation to log metrics and detailed traces."""
        with mlflow.start_run(run_id=self._mlflow_run_id):
            # Log all numerical metrics
            mlflow.log_metrics(metrics)
            
            run_dir = f"data/runs/{self.run_id}"
            os.makedirs(run_dir, exist_ok=True)
            
            # minimal logs just config + metrics (handled above)
            if self.depth == "minimal":
                return
                
            # production logs trace summaries
            if self.depth in ["production", "debug"]:
                # Metrics JSON
                metrics_path = f"{run_dir}/metrics.json"
                with open(metrics_path, "w") as f:
                    json.dump(metrics, f, indent=2)
                mlflow.log_artifact(metrics_path)
                
                # NAV History CSV
                import pandas as pd
                nav_df = pd.DataFrame(nav_history)
                nav_path = f"{run_dir}/portfolio_nav.csv"
                nav_df.to_csv(nav_path, index=False)
                mlflow.log_artifact(nav_path)
                
                # Gate Events JSONL
                events_path = f"{run_dir}/recommendation_trace.jsonl"
                with open(events_path, "w") as f:
                    for e in gate_events:
                        e_copy = dict(e)
                        if "date" in e_copy: e_copy["date"] = str(e_copy["date"])
                        f.write(json.dumps(e_copy) + "\n")
                mlflow.log_artifact(events_path)
                
                # Trade Log JSONL
                trades_path = f"{run_dir}/trade_log.jsonl"
                with open(trades_path, "w") as f:
                    for t in trade_log:
                        # Serialize dates
                        if "signal_date" in t: t["signal_date"] = str(t["signal_date"])
                        if "fill_date" in t: t["fill_date"] = str(t["fill_date"])
                        f.write(json.dumps(t) + "\n")
                mlflow.log_artifact(trades_path)
                
            if self.depth == "debug":
                # In Phase 4, this logs exact prompts/responses for LLMs.
                pass
                
        # Cleanup local run directory after logging to mlflow
        if os.path.exists(run_dir):
            shutil.rmtree(run_dir)
