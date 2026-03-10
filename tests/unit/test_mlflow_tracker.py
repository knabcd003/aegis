import pytest
import os
import json
from unittest.mock import patch, MagicMock
from engines.sandbox.mlflow_tracker import MLflowTracker

def test_mlflow_tracker_flatten_dict():
    tracker = MLflowTracker(tracking_uri="sqlite:///:memory:")
    nested = {
        "a": 1,
        "b": {
            "c": 2,
            "d": {
                "e": "3"
            }
        }
    }
    flat = tracker._flatten_dict(nested)
    assert flat == {"a": 1, "b.c": 2, "b.d.e": "3"}

@patch("engines.sandbox.mlflow_tracker.mlflow")
def test_mlflow_tracker_log_run(mock_mlflow):
    tracker = MLflowTracker(tracking_uri="sqlite:///:memory:")
    
    mock_run = MagicMock()
    mock_run.__enter__.return_value.info.run_id = "test_run_123"
    mock_mlflow.start_run.return_value = mock_run

    config_dump = {"run_id": "test_1", "param1": "val1"}
    
    # Mock some fake results with empty dates to avoid pandas dependency issues during unit test
    results = {
        "optimization_dates": [],
        "holdout_dates": [],
        "trade_log": [],
        "nav_history": [],
        "trace_events": []
    }
    
    run_id = tracker.log_run(config_dump, results)
    
    assert run_id == "test_run_123"
    mock_mlflow.log_param.assert_called_with("param1", "val1")
    mock_mlflow.log_metric.assert_any_call("opt_total_return", 0.0)
    mock_mlflow.log_metric.assert_any_call("opt_sharpe", 0.0)
    mock_mlflow.log_metric.assert_any_call("opt_num_trades", 0.0)
