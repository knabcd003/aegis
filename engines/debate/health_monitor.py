from typing import Callable, Optional
import time

class BearWinRateMonitor:
    """
    Computes rolling 30-day Bear Win Rate by querying historical
    verdicts from MLflow tracking. Used for Glass Box alerts.
    """
    def __init__(self, mlflow_client: Any, experiment_id: str, alert_threshold: float = 0.75, window_days: int = 30):
        self.mlflow_client = mlflow_client
        self.experiment_id = experiment_id
        self.alert_threshold = alert_threshold
        self.window_days = window_days

    def evaluate(self) -> dict:
        """
        Reads historical data via MLflow search_runs() API with a date range filter
        to compute the rolling win rate.
        """
        now = time.time()
        start_time_ms = int((now - (self.window_days * 86400)) * 1000)
        
        filter_string = f"metrics.bear_won >= 0 AND attributes.start_time >= {start_time_ms}"
        
        try:
            runs = self.mlflow_client.search_runs(
                experiment_ids=[self.experiment_id],
                filter_string=filter_string
            )
            
            if runs is None or len(runs) == 0:
                return {"bear_win_rate": 0.0, "total_debates": 0, "alert_triggered": False}

            # If runs is a pandas DataFrame (mlflow returns dfs by default)
            if hasattr(runs, "empty") and not runs.empty:
                if "metrics.bear_won" in runs.columns:
                    bear_wins = int(runs["metrics.bear_won"].sum())
                    total = len(runs)
                else:
                    return {"bear_win_rate": 0.0, "total_debates": 0, "alert_triggered": False}
            else:
                # Handle generic list of raw Run objects
                bear_wins = sum(1 for r in runs if r.data.metrics.get("bear_won", 0) > 0)
                total = len(runs)
                
            rate = bear_wins / total if total > 0 else 0.0
            
            return {
                "bear_win_rate": rate,
                "total_debates": total,
                "bear_wins": bear_wins,
                "bull_wins": total - bear_wins,
                "alert_triggered": rate > self.alert_threshold
            }
            
        except Exception as e:
            # Safe degradation if MLflow is uninitialized
            return {"error": str(e), "alert_triggered": False}
