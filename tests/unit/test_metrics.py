import pytest
from datetime import date
import pandas as pd
import numpy as np

from engines.simulation.metrics import compute_metrics
from config.manager import ConfigManager

# T5.1 and T5.2

def test_sharpe_correctness():
    """T5.1 — Sharpe matches hand-calculated value on known returns"""
    # Create an artificial NAV history of known daily returns (+1%, -0.5%, +1.5%, +0.5%)
    nav_history = [
        {"date": "2023-01-01", "nav": 10000.0},
        {"date": "2023-01-02", "nav": 10100.0},  # +1.0%
        {"date": "2023-01-03", "nav": 10049.5},  # -0.5%
        {"date": "2023-01-04", "nav": 10200.24}, # +1.5%
        {"date": "2023-01-05", "nav": 10251.24}  # +0.5%
    ]
    
    returns_pd = pd.Series([0.0, 0.01, -0.005, 0.015, 0.005])
    mean_ret = returns_pd.mean()
    std_ret = returns_pd.std() # pandas default ddof=1
    expected_sharpe = (mean_ret / std_ret) * np.sqrt(252)
    
    # We pass an empty benchmark and an empty holdout set so everything is in optimization
    metrics = compute_metrics(nav_history, pd.Series(dtype=float), holdout_dates=[])
    
    assert "optimization_sharpe" in metrics
    assert abs(metrics["optimization_sharpe"] - expected_sharpe) < 0.01

def test_slippage_drag_always_present():
    """T5.2 — Slippage drag always present, gross >= net always"""
    nav_history = [
        {"date": "2023-01-01", "nav": 10000.0},
        {"date": "2023-01-02", "nav": 10100.0}
    ]
    metrics = compute_metrics(nav_history, pd.Series(dtype=float), holdout_dates=[])
    
    assert "gross_return" in metrics
    assert "net_return" in metrics
    assert "slippage_drag" in metrics
    assert metrics["gross_return"] >= metrics["net_return"]
