import pytest
from unittest.mock import MagicMock, patch
from engines.sentinel.promotion_gate import PromotionGate

@pytest.fixture
def mock_health_monitor():
    monitor = MagicMock()
    monitor.is_any_connector_offline.return_value = False
    monitor.is_any_connector_degraded.return_value = False
    return monitor

def test_promotion_health_gate(mock_health_monitor):
    gate = PromotionGate(mock_health_monitor)
    
    # Simulate degraded health
    mock_health_monitor.is_any_connector_degraded.return_value = True
    
    approved, reason = gate.evaluate_run("run_1", {})
    assert approved is False
    assert "DEGRADED" in reason

@patch('engines.sentinel.promotion_gate.mlflow')
def test_promotion_guardrails(mock_mlflow, mock_health_monitor):
    gate = PromotionGate(mock_health_monitor)
    
    mock_run = MagicMock()
    mock_mlflow.get_run.return_value = mock_run

    # Test 1: Exceeds degradation
    mock_run.data.metrics = {"held_out_degradation": 0.40, "held_out_sharpe": 1.5}
    approved, reason = gate.evaluate_run("run_2", {})
    assert approved is False
    assert "Degradation" in reason

    # Test 2: Fails Sharpe
    mock_run.data.metrics = {"held_out_degradation": 0.20, "held_out_sharpe": 0.50}
    approved, reason = gate.evaluate_run("run_3", {})
    assert approved is False
    assert "Sharpe" in reason

    # Test 3: Success
    mock_run.data.metrics = {"held_out_degradation": 0.20, "held_out_sharpe": 1.5}
    approved, reason = gate.evaluate_run("run_4", {})
    assert approved is True
    assert "Approved" in reason

    # Test 4: Cannot evaluate twice
    approved, reason = gate.evaluate_run("run_4", {})
    assert approved is False
    assert "already been evaluated" in reason
