"""
Tests for the Promotion Gate (Phase 4 Step 1).

Tests verify:
  - Stage 1 (Backtest → Proving Ground): all 10 gates individually and together
  - Stage 2 (Proving Ground → Live Small): observation period, signal quality
  - Stage 3 (Live Small → Live Full): sustained performance
  - MLflow failure handling (no fallback to mock values)
  - Session quality enforcement
  - Re-evaluation prevention
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock
import os

from engines.sentinel.promotion_gate import (
    PromotionGate,
    GateStage,
    GateResult,
)


# ---------- Fixtures ----------

@pytest.fixture
def mock_health_monitor():
    """A healthy ConnectorHealthMonitor (all connectors online)."""
    monitor = MagicMock()
    monitor.is_any_connector_offline.return_value = False
    monitor.is_any_connector_degraded.return_value = False
    return monitor


@pytest.fixture
def gate(mock_health_monitor):
    return PromotionGate(mock_health_monitor)


@pytest.fixture
def passing_metrics():
    """MLflow metrics that pass ALL Stage 1 gates."""
    return {
        "optimization_sharpe": 1.5,
        "optimization_max_drawdown": -0.10,
        "trade_count": 150,
        "profit_factor": 1.8,
        "walk_forward_efficiency": 0.65,
        "correlation_with_existing": 0.30,
        "bootstrap_pvalue": 0.01,
        "held_out_degradation": 0.20,
    }


def mock_mlflow_run(metrics: dict):
    """Creates a mock MLflow run with given metrics."""
    run = MagicMock()
    run.data.metrics = metrics
    return run


# ---------- Stage 1: Basic Pass/Fail ----------

class TestStage1BasicFlow:
    def test_all_gates_pass(self, gate, passing_metrics):
        """Happy path: all metrics above thresholds → PASS."""
        with patch("mlflow.get_run", return_value=mock_mlflow_run(passing_metrics)):
            result = gate.evaluate_backtest(
                "run_001",
                session_quality="nominal",
                scenario_pass_rate=0.85,
                debate_confidence=80,
            )
        assert result.passed is True
        assert result.stage == GateStage.BACKTEST
        assert len(result.failures) == 0

    def test_no_mlflow_fallback(self, gate):
        """MLflow unreachable → gate FAILS, no mock values."""
        with patch("mlflow.get_run", side_effect=Exception("Connection refused")):
            result = gate.evaluate_backtest("run_002")
        assert result.passed is False
        assert "MLFLOW_UNREACHABLE" in result.failures[0]

    def test_duplicate_evaluation_blocked(self, gate, passing_metrics):
        """Same run cannot be evaluated twice."""
        with patch("mlflow.get_run", return_value=mock_mlflow_run(passing_metrics)):
            gate.evaluate_backtest(
                "run_003",
                scenario_pass_rate=0.85,
                debate_confidence=80,
            )
            result = gate.evaluate_backtest("run_003")
        assert result.passed is False
        assert "already evaluated" in result.reason


# ---------- Stage 1: Individual Gate Failures ----------

class TestStage1IndividualGates:
    def _evaluate_with_override(self, gate, passing_metrics, **overrides):
        """Evaluate with specific metric overrides."""
        metrics = {**passing_metrics, **overrides}
        with patch("mlflow.get_run", return_value=mock_mlflow_run(metrics)):
            return gate.evaluate_backtest(
                f"run_{id(overrides)}",
                scenario_pass_rate=overrides.pop("scenario_pass_rate", 0.85),
                debate_confidence=overrides.pop("debate_confidence", 80),
            )

    def test_sharpe_below_threshold(self, gate, passing_metrics):
        result = self._evaluate_with_override(
            gate, passing_metrics, optimization_sharpe=0.5
        )
        assert result.passed is False
        assert any("OOS_SHARPE" in f for f in result.failures)

    def test_drawdown_exceeds_limit(self, gate, passing_metrics):
        result = self._evaluate_with_override(
            gate, passing_metrics, optimization_max_drawdown=-0.25
        )
        assert result.passed is False
        assert any("MAX_DRAWDOWN" in f for f in result.failures)

    def test_too_few_trades(self, gate, passing_metrics):
        result = self._evaluate_with_override(
            gate, passing_metrics, trade_count=50
        )
        assert result.passed is False
        assert any("TRADE_COUNT" in f for f in result.failures)

    def test_low_profit_factor(self, gate, passing_metrics):
        result = self._evaluate_with_override(
            gate, passing_metrics, profit_factor=0.9
        )
        assert result.passed is False
        assert any("PROFIT_FACTOR" in f for f in result.failures)

    def test_low_walk_forward(self, gate, passing_metrics):
        result = self._evaluate_with_override(
            gate, passing_metrics, walk_forward_efficiency=0.30
        )
        assert result.passed is False
        assert any("WALK_FORWARD" in f for f in result.failures)

    def test_high_correlation(self, gate, passing_metrics):
        result = self._evaluate_with_override(
            gate, passing_metrics, correlation_with_existing=0.80
        )
        assert result.passed is False
        assert any("CORRELATION" in f for f in result.failures)

    def test_high_pvalue(self, gate, passing_metrics):
        result = self._evaluate_with_override(
            gate, passing_metrics, bootstrap_pvalue=0.15
        )
        assert result.passed is False
        assert any("PVALUE" in f for f in result.failures)

    def test_high_held_out_degradation(self, gate, passing_metrics):
        result = self._evaluate_with_override(
            gate, passing_metrics, held_out_degradation=0.50
        )
        assert result.passed is False
        assert any("HELD_OUT_DEGRADATION" in f for f in result.failures)

    def test_low_scenario_pass_rate(self, gate, passing_metrics):
        result = self._evaluate_with_override(
            gate, passing_metrics, scenario_pass_rate=0.50
        )
        assert result.passed is False
        assert any("SCENARIO_PASS_RATE" in f for f in result.failures)

    def test_low_debate_confidence(self, gate, passing_metrics):
        result = self._evaluate_with_override(
            gate, passing_metrics, debate_confidence=40
        )
        assert result.passed is False
        assert any("DEBATE_CONFIDENCE" in f for f in result.failures)

    def test_missing_scenario_rate_fails(self, gate, passing_metrics):
        """scenario_pass_rate=None should fail (must run before promotion)."""
        with patch("mlflow.get_run", return_value=mock_mlflow_run(passing_metrics)):
            result = gate.evaluate_backtest(
                "run_scenario_none",
                scenario_pass_rate=None,
                debate_confidence=80,
            )
        assert result.passed is False
        assert any("SCENARIO_PASS_RATE: Not provided" in f for f in result.failures)

    def test_missing_debate_confidence_fails(self, gate, passing_metrics):
        """debate_confidence=None should fail (must score before promotion)."""
        with patch("mlflow.get_run", return_value=mock_mlflow_run(passing_metrics)):
            result = gate.evaluate_backtest(
                "run_debate_none",
                scenario_pass_rate=0.85,
                debate_confidence=None,
            )
        assert result.passed is False
        assert any("DEBATE_CONFIDENCE: Not provided" in f for f in result.failures)


# ---------- Session Quality ----------

class TestSessionQuality:
    def test_degraded_session_blocked(self, gate, passing_metrics):
        with patch("mlflow.get_run", return_value=mock_mlflow_run(passing_metrics)):
            result = gate.evaluate_backtest(
                "run_degraded",
                session_quality="degraded",
                scenario_pass_rate=0.85,
                debate_confidence=80,
            )
        assert result.passed is False
        assert any("SESSION_DEGRADED" in f for f in result.failures)

    def test_severely_degraded_blocked(self, gate, passing_metrics):
        with patch("mlflow.get_run", return_value=mock_mlflow_run(passing_metrics)):
            result = gate.evaluate_backtest(
                "run_severely_degraded",
                session_quality="severely_degraded",
                scenario_pass_rate=0.85,
                debate_confidence=80,
            )
        assert result.passed is False
        assert any("SESSION_DEGRADED" in f for f in result.failures)


# ---------- Connector Health ----------

class TestConnectorHealthGate:
    def test_offline_connector_blocks(self, gate, passing_metrics):
        gate.health_monitor.is_any_connector_offline.return_value = True
        with patch("mlflow.get_run", return_value=mock_mlflow_run(passing_metrics)):
            result = gate.evaluate_backtest(
                "run_offline",
                scenario_pass_rate=0.85,
                debate_confidence=80,
            )
        assert result.passed is False
        assert any("CONNECTOR_OFFLINE" in f for f in result.failures)

    def test_degraded_connector_blocks(self, gate, passing_metrics):
        gate.health_monitor.is_any_connector_degraded.return_value = True
        with patch("mlflow.get_run", return_value=mock_mlflow_run(passing_metrics)):
            result = gate.evaluate_backtest(
                "run_degraded_conn",
                scenario_pass_rate=0.85,
                debate_confidence=80,
            )
        assert result.passed is False
        assert any("CONNECTOR_DEGRADED" in f for f in result.failures)


# ---------- Stage 2: Proving Ground ----------

class TestStage2ProvingGround:
    def test_all_pass(self, gate):
        result = gate.evaluate_proving_ground(
            sentinel_id="sent_001",
            observation_days=45,
            signals_generated=10,
            backtest_win_rate=0.60,
            live_win_rate=0.55,
            backtest_max_drawdown=-0.10,
            live_max_drawdown=-0.12,
            backtest_signal_frequency=1.0,
            live_signal_frequency=2.0,
            user_signed_off=True,
        )
        assert result.passed is True

    def test_insufficient_observation(self, gate):
        result = gate.evaluate_proving_ground(
            sentinel_id="sent_002",
            observation_days=15,
            signals_generated=10,
            backtest_win_rate=0.60,
            live_win_rate=0.55,
            backtest_max_drawdown=-0.10,
            live_max_drawdown=-0.12,
            backtest_signal_frequency=1.0,
            live_signal_frequency=2.0,
            user_signed_off=True,
        )
        assert result.passed is False
        assert any("OBSERVATION_DAYS" in f for f in result.failures)

    def test_no_sign_off_fails(self, gate):
        result = gate.evaluate_proving_ground(
            sentinel_id="sent_003",
            observation_days=45,
            signals_generated=10,
            backtest_win_rate=0.60,
            live_win_rate=0.55,
            backtest_max_drawdown=-0.10,
            live_max_drawdown=-0.12,
            backtest_signal_frequency=1.0,
            live_signal_frequency=2.0,
            user_signed_off=False,
        )
        assert result.passed is False
        assert any("SIGN_OFF" in f for f in result.failures)

    def test_excessive_win_rate_degradation(self, gate):
        result = gate.evaluate_proving_ground(
            sentinel_id="sent_004",
            observation_days=45,
            signals_generated=10,
            backtest_win_rate=0.60,
            live_win_rate=0.30,  # 30% degradation
            backtest_max_drawdown=-0.10,
            live_max_drawdown=-0.12,
            backtest_signal_frequency=1.0,
            live_signal_frequency=2.0,
            user_signed_off=True,
        )
        assert result.passed is False
        assert any("WIN_RATE_DEGRADATION" in f for f in result.failures)


# ---------- Stage 3: Live Expansion ----------

class TestStage3LiveExpansion:
    def test_all_pass(self, gate):
        result = gate.evaluate_live_expansion(
            sentinel_id="sent_001",
            live_days=90,
            live_sharpe=1.0,
            circuit_breaker_triggers=0,
            positive_months=3,
        )
        assert result.passed is True

    def test_circuit_breaker_disqualifies(self, gate):
        """One circuit breaker trigger = permanent disqualification."""
        result = gate.evaluate_live_expansion(
            sentinel_id="sent_002",
            live_days=90,
            live_sharpe=1.0,
            circuit_breaker_triggers=1,
            positive_months=3,
        )
        assert result.passed is False
        assert any("CIRCUIT_BREAKER" in f for f in result.failures)

    def test_insufficient_live_days(self, gate):
        result = gate.evaluate_live_expansion(
            sentinel_id="sent_003",
            live_days=30,
            live_sharpe=1.0,
            circuit_breaker_triggers=0,
            positive_months=3,
        )
        assert result.passed is False
        assert any("LIVE_DAYS" in f for f in result.failures)

    def test_low_live_sharpe(self, gate):
        result = gate.evaluate_live_expansion(
            sentinel_id="sent_004",
            live_days=90,
            live_sharpe=0.2,
            circuit_breaker_triggers=0,
            positive_months=3,
        )
        assert result.passed is False
        assert any("LIVE_SHARPE" in f for f in result.failures)


# ---------- Multi-Failure Reporting ----------

class TestMultiFailure:
    def test_multiple_failures_all_reported(self, gate):
        """Multiple gate failures should ALL be reported, not short-circuit."""
        bad_metrics = {
            "optimization_sharpe": 0.3,
            "optimization_max_drawdown": -0.30,
            "trade_count": 10,
            "profit_factor": 0.5,
            "walk_forward_efficiency": 0.10,
            "correlation_with_existing": 0.90,
            "bootstrap_pvalue": 0.50,
            "held_out_degradation": 0.60,
        }
        with patch("mlflow.get_run", return_value=mock_mlflow_run(bad_metrics)):
            result = gate.evaluate_backtest(
                "run_all_bad",
                session_quality="nominal",
                scenario_pass_rate=0.30,
                debate_confidence=20,
            )
        assert result.passed is False
        # All 10 gates should fail
        assert len(result.failures) == 10, (
            f"Expected 10 failures, got {len(result.failures)}: {result.failures}"
        )


# ---------- Gate Result Structure ----------

class TestGateResult:
    def test_result_serializable(self, gate, passing_metrics):
        with patch("mlflow.get_run", return_value=mock_mlflow_run(passing_metrics)):
            result = gate.evaluate_backtest(
                "run_serial",
                scenario_pass_rate=0.85,
                debate_confidence=80,
            )
        d = result.to_dict()
        assert "passed" in d
        assert "stage" in d
        assert "failures" in d
        assert "metrics_snapshot" in d
        assert "evaluated_at" in d

    def test_metrics_snapshot_captured(self, gate, passing_metrics):
        with patch("mlflow.get_run", return_value=mock_mlflow_run(passing_metrics)):
            result = gate.evaluate_backtest(
                "run_snapshot",
                scenario_pass_rate=0.85,
                debate_confidence=80,
            )
        assert result.metrics_snapshot["oos_sharpe"] == 1.5
        assert result.metrics_snapshot["trade_count"] == 150
        assert result.metrics_snapshot["profit_factor"] == 1.8
