"""
Promotion Gate Evaluator (Phase 4 — Complete)

Three-stage promotion system:
  Stage 1: Backtest → Proving Ground (10 hard metric gates)
  Stage 2: Proving Ground → Live Small (30-day observation)
  Stage 3: Live Small → Live Full (60-day expansion)

Rules:
  - No LLM involvement. Pure deterministic math reading from MLflow.
  - No mock fallback values. If MLflow is unreachable, the gate FAILS.
  - No agent can modify these thresholds.
  - session_quality must be "nominal" for Stage 1 promotion.
"""
import json
import logging
import os
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Tuple, List, Optional
from pydantic import BaseModel, Field

import mlflow

from engines.monitoring.connector_health import ConnectorHealthMonitor
from engines.vcl.component import VCLComponent, HealthStatus, HealthResult, ComponentRole

logger = logging.getLogger(__name__)


class GateStage(str, Enum):
    BACKTEST = "backtest"
    PROVING_GROUND = "proving_ground"
    LIVE_SMALL = "live_small"
    LIVE_FULL = "live_full"


class GateResult(BaseModel):
    """Structured result from a gate evaluation."""
    passed: bool
    stage: GateStage
    reason: str
    failures: List[str] = Field(default_factory=list)
    metrics_snapshot: Dict[str, Any] = Field(default_factory=dict)
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class PromotionGateInput(BaseModel):
    run_id: str = Field(min_length=1)
    session_quality: str = "nominal"
    scenario_pass_rate: Optional[float] = None
    debate_confidence: Optional[int] = None


class PromotionGateOutput(BaseModel):
    gate_result: GateResult


class PromotionGate(VCLComponent):
    """
    Three-stage gatekeeper for strategy promotion.

    All thresholds are hardcoded constants. No configuration overrides.
    No agent modifies these values. Ever.
    """
    component_id = "aegis.simulation.promotion_gate"
    version = "1.0.0"
    role = ComponentRole.GATE_CONDITION
    input_schema = PromotionGateInput
    output_schema = PromotionGateOutput


    # ========================
    # Stage 1: Backtest → Proving Ground
    # ========================
    BACKTEST_GATE = {
        "min_oos_sharpe": 1.0,
        "max_drawdown": -0.15,  # negative number (e.g., -15% max)
        "min_trades": 100,
        "min_profit_factor": 1.3,
        "min_walk_forward_efficiency": 0.50,
        "max_correlation_existing": 0.60,
        "max_pvalue": 0.05,
        "min_scenario_pass_rate": 0.70,
        "min_debate_confidence": 65,
        "required_session_quality": "nominal",
    }

    # Non-configurable invariants (apply across ALL stages)
    HELD_OUT_DEGRADATION_MAX = 0.35
    CIRCUIT_BREAKER_MAX_TRIGGERS = 0

    # ========================
    # Stage 2: Proving Ground → Live Small (max 10% allocation)
    # ========================
    PROVING_GROUND_GATE = {
        "min_observation_days": 30,
        "min_signals_generated": 5,
        "max_win_rate_degradation": 0.15,
        "max_drawdown_vs_backtest": 0.05,
        "max_signal_frequency_ratio": 3.0,
        "require_explicit_sign_off": True,
    }

    # ========================
    # Stage 3: Live Small → Live Full
    # ========================
    LIVE_EXPANSION_GATE = {
        "min_live_days": 60,
        "min_live_sharpe": 0.5,
        "max_circuit_breaker_triggers": 0,
        "min_positive_months": 2,
    }

    def __init__(self, health_monitor: ConnectorHealthMonitor):
        self.health_monitor = health_monitor
        self._evaluated_runs: Dict[str, GateResult] = {}

    def execute(self, input_data: PromotionGateInput) -> PromotionGateOutput:
        """VCL standard execute hook for stage 1 evaluation."""
        result = self.evaluate_backtest(
            run_id=input_data.run_id,
            session_quality=input_data.session_quality,
            scenario_pass_rate=input_data.scenario_pass_rate,
            debate_confidence=input_data.debate_confidence
        )
        return PromotionGateOutput(gate_result=result)

    def health(self) -> HealthResult:
        """Uses the dependent health monitor to assess overall readiness."""
        if self.health_monitor.is_any_connector_offline():
            return HealthResult(status=HealthStatus.DEGRADED, reason="Underlying connectors offline")
        return HealthResult(status=HealthStatus.HEALTHY)


    # ========================
    # Stage 1 Evaluation
    # ========================
    def evaluate_backtest(
        self,
        run_id: str,
        session_quality: str = "nominal",
        scenario_pass_rate: Optional[float] = None,
        debate_confidence: Optional[int] = None,
    ) -> GateResult:
        """
        Evaluates an MLflow run against the BACKTEST_GATE.
        Returns GateResult with pass/fail and all failure reasons.

        Does NOT fall back to mock values. If MLflow is unreachable, the gate fails.
        """
        # Prevent re-evaluation
        if run_id in self._evaluated_runs:
            prev = self._evaluated_runs[run_id]
            return GateResult(
                passed=False,
                stage=GateStage.BACKTEST,
                reason=f"Run {run_id} already evaluated at {prev.evaluated_at.isoformat()}. "
                       f"Previous result: {'PASSED' if prev.passed else 'FAILED'}",
            )

        failures: List[str] = []

        # 1. Health gate — all connectors must be online
        if self.health_monitor.is_any_connector_offline():
            failures.append(
                "CONNECTOR_OFFLINE: One or more data connectors are OFFLINE"
            )
        if self.health_monitor.is_any_connector_degraded():
            failures.append(
                "CONNECTOR_DEGRADED: One or more data connectors are DEGRADED"
            )

        # 2. Session quality gate
        if session_quality != self.BACKTEST_GATE["required_session_quality"]:
            failures.append(
                f"SESSION_DEGRADED: Session quality '{session_quality}' is not "
                f"'{self.BACKTEST_GATE['required_session_quality']}'. "
                f"Degraded sessions cannot produce promoted strategies."
            )

        # 3. Fetch run metrics from MLflow — NO FALLBACK
        try:
            run = mlflow.get_run(run_id)
            metrics = run.data.metrics
        except Exception as e:
            logger.error(f"Failed to fetch run {run_id} from MLflow: {e}")
            result = GateResult(
                passed=False,
                stage=GateStage.BACKTEST,
                reason=f"MLFLOW_UNREACHABLE: Cannot read metrics for run {run_id}: {e}",
                failures=[f"MLFLOW_UNREACHABLE: {e}"],
            )
            self._evaluated_runs[run_id] = result
            return result

        # 4. Apply all 10 hard metric gates
        metrics_snapshot = {}

        # 4a. OOS Sharpe
        oos_sharpe = metrics.get("optimization_sharpe", 0.0)
        metrics_snapshot["oos_sharpe"] = oos_sharpe
        if oos_sharpe < self.BACKTEST_GATE["min_oos_sharpe"]:
            failures.append(
                f"OOS_SHARPE: {oos_sharpe:.3f} < {self.BACKTEST_GATE['min_oos_sharpe']}"
            )

        # 4b. Max drawdown
        max_dd = metrics.get("optimization_max_drawdown", -1.0)
        metrics_snapshot["max_drawdown"] = max_dd
        if max_dd < self.BACKTEST_GATE["max_drawdown"]:
            failures.append(
                f"MAX_DRAWDOWN: {max_dd:.3f} exceeds limit {self.BACKTEST_GATE['max_drawdown']}"
            )

        # 4c. Trade count
        trade_count = metrics.get("trade_count", 0)
        metrics_snapshot["trade_count"] = trade_count
        if trade_count < self.BACKTEST_GATE["min_trades"]:
            failures.append(
                f"TRADE_COUNT: {trade_count} < {self.BACKTEST_GATE['min_trades']}"
            )

        # 4d. Profit factor
        profit_factor = metrics.get("profit_factor", 0.0)
        metrics_snapshot["profit_factor"] = profit_factor
        if profit_factor < self.BACKTEST_GATE["min_profit_factor"]:
            failures.append(
                f"PROFIT_FACTOR: {profit_factor:.3f} < {self.BACKTEST_GATE['min_profit_factor']}"
            )

        # 4e. Walk-forward efficiency
        wfe = metrics.get("walk_forward_efficiency", 0.0)
        metrics_snapshot["walk_forward_efficiency"] = wfe
        if wfe < self.BACKTEST_GATE["min_walk_forward_efficiency"]:
            failures.append(
                f"WALK_FORWARD: {wfe:.3f} < {self.BACKTEST_GATE['min_walk_forward_efficiency']}"
            )

        # 4f. Correlation with existing strategies
        corr = metrics.get("correlation_with_existing", 0.0)
        metrics_snapshot["correlation_existing"] = corr
        if corr > self.BACKTEST_GATE["max_correlation_existing"]:
            failures.append(
                f"CORRELATION: {corr:.3f} > {self.BACKTEST_GATE['max_correlation_existing']}"
            )

        # 4g. P-value
        pvalue = metrics.get("bootstrap_pvalue", 1.0)
        metrics_snapshot["pvalue"] = pvalue
        if pvalue > self.BACKTEST_GATE["max_pvalue"]:
            failures.append(
                f"PVALUE: {pvalue:.4f} > {self.BACKTEST_GATE['max_pvalue']}"
            )

        # 4h. Held-out degradation (non-configurable invariant)
        held_out_degradation = metrics.get("held_out_degradation", 1.0)
        metrics_snapshot["held_out_degradation"] = held_out_degradation
        if held_out_degradation > self.HELD_OUT_DEGRADATION_MAX:
            failures.append(
                f"HELD_OUT_DEGRADATION: {held_out_degradation:.3f} > "
                f"{self.HELD_OUT_DEGRADATION_MAX} (non-configurable invariant)"
            )

        # 4i. Scenario pass rate (from FinDebate, not in MLflow yet — use explicit arg)
        if scenario_pass_rate is not None:
            metrics_snapshot["scenario_pass_rate"] = scenario_pass_rate
            if scenario_pass_rate < self.BACKTEST_GATE["min_scenario_pass_rate"]:
                failures.append(
                    f"SCENARIO_PASS_RATE: {scenario_pass_rate:.3f} < "
                    f"{self.BACKTEST_GATE['min_scenario_pass_rate']}"
                )
        else:
            failures.append(
                "SCENARIO_PASS_RATE: Not provided — scenario battery must run before promotion"
            )

        # 4j. Debate confidence (from FinDebate, not in MLflow yet — use explicit arg)
        if debate_confidence is not None:
            metrics_snapshot["debate_confidence"] = debate_confidence
            if debate_confidence < self.BACKTEST_GATE["min_debate_confidence"]:
                failures.append(
                    f"DEBATE_CONFIDENCE: {debate_confidence} < "
                    f"{self.BACKTEST_GATE['min_debate_confidence']}"
                )
        else:
            failures.append(
                "DEBATE_CONFIDENCE: Not provided — FinDebate must score before promotion"
            )

        # 5. Build result
        passed = len(failures) == 0
        reason = "All gates passed" if passed else f"{len(failures)} gate(s) failed"

        result = GateResult(
            passed=passed,
            stage=GateStage.BACKTEST,
            reason=reason,
            failures=failures,
            metrics_snapshot=metrics_snapshot,
        )

        self._evaluated_runs[run_id] = result

        # 6. If passed, generate promotion artifact
        if passed:
            self._generate_promotion_artifact(run_id, metrics_snapshot)

        logger.info(
            f"Promotion Gate Stage 1 for run {run_id}: "
            f"{'PASSED' if passed else 'FAILED'} — {reason}"
        )

        return result

    # ========================
    # Stage 2 Evaluation
    # ========================
    def evaluate_proving_ground(
        self,
        sentinel_id: str,
        observation_days: int,
        signals_generated: int,
        backtest_win_rate: float,
        live_win_rate: float,
        backtest_max_drawdown: float,
        live_max_drawdown: float,
        backtest_signal_frequency: float,
        live_signal_frequency: float,
        user_signed_off: bool,
    ) -> GateResult:
        """
        Evaluates a Proving Ground strategy for promotion to Live Small.
        """
        failures: List[str] = []
        gate = self.PROVING_GROUND_GATE

        if observation_days < gate["min_observation_days"]:
            failures.append(
                f"OBSERVATION_DAYS: {observation_days} < {gate['min_observation_days']}"
            )

        if signals_generated < gate["min_signals_generated"]:
            failures.append(
                f"SIGNALS: {signals_generated} < {gate['min_signals_generated']}"
            )

        win_rate_deg = backtest_win_rate - live_win_rate
        if win_rate_deg > gate["max_win_rate_degradation"]:
            failures.append(
                f"WIN_RATE_DEGRADATION: {win_rate_deg:.3f} > {gate['max_win_rate_degradation']}"
            )

        dd_excess = abs(live_max_drawdown) - abs(backtest_max_drawdown)
        if dd_excess > gate["max_drawdown_vs_backtest"]:
            failures.append(
                f"DRAWDOWN_EXCESS: {dd_excess:.3f} > {gate['max_drawdown_vs_backtest']}"
            )

        if backtest_signal_frequency > 0:
            freq_ratio = live_signal_frequency / backtest_signal_frequency
            if freq_ratio > gate["max_signal_frequency_ratio"]:
                failures.append(
                    f"SIGNAL_FREQUENCY: {freq_ratio:.2f}x > {gate['max_signal_frequency_ratio']}x"
                )

        if gate["require_explicit_sign_off"] and not user_signed_off:
            failures.append("SIGN_OFF: Human must explicitly approve first live trade")

        passed = len(failures) == 0
        return GateResult(
            passed=passed,
            stage=GateStage.PROVING_GROUND,
            reason="All gates passed" if passed else f"{len(failures)} gate(s) failed",
            failures=failures,
        )

    # ========================
    # Stage 3 Evaluation
    # ========================
    def evaluate_live_expansion(
        self,
        sentinel_id: str,
        live_days: int,
        live_sharpe: float,
        circuit_breaker_triggers: int,
        positive_months: int,
    ) -> GateResult:
        """
        Evaluates a Live Small strategy for expansion to Live Full.
        """
        failures: List[str] = []
        gate = self.LIVE_EXPANSION_GATE

        if live_days < gate["min_live_days"]:
            failures.append(f"LIVE_DAYS: {live_days} < {gate['min_live_days']}")

        if live_sharpe < gate["min_live_sharpe"]:
            failures.append(f"LIVE_SHARPE: {live_sharpe:.3f} < {gate['min_live_sharpe']}")

        if circuit_breaker_triggers > gate["max_circuit_breaker_triggers"]:
            failures.append(
                f"CIRCUIT_BREAKER: {circuit_breaker_triggers} triggers — "
                f"one trigger = permanent disqualification"
            )

        if positive_months < gate["min_positive_months"]:
            failures.append(
                f"POSITIVE_MONTHS: {positive_months} < {gate['min_positive_months']}"
            )

        passed = len(failures) == 0
        return GateResult(
            passed=passed,
            stage=GateStage.LIVE_SMALL,
            reason="All gates passed" if passed else f"{len(failures)} gate(s) failed",
            failures=failures,
        )

    # ========================
    # Promotion Artifact
    # ========================
    def _generate_promotion_artifact(
        self, run_id: str, metrics_snapshot: Dict[str, Any]
    ) -> str:
        """
        Generates a locked promotion artifact: frozen config + lineage + metrics.
        Written to MLflow as an artifact and to local filesystem.
        """
        artifact = {
            "run_id": run_id,
            "promoted_at": datetime.utcnow().isoformat(),
            "gate_stage": GateStage.BACKTEST.value,
            "metrics_at_promotion": metrics_snapshot,
            "gate_thresholds": self.BACKTEST_GATE,
            "invariants": {
                "held_out_degradation_max": self.HELD_OUT_DEGRADATION_MAX,
                "circuit_breaker_max_triggers": self.CIRCUIT_BREAKER_MAX_TRIGGERS,
            },
        }

        # Write locally
        artifact_dir = f"data/promotions/{run_id}"
        os.makedirs(artifact_dir, exist_ok=True)
        artifact_path = f"{artifact_dir}/promotion_artifact.json"
        with open(artifact_path, "w") as f:
            json.dump(artifact, f, indent=2)

        # Log to MLflow
        try:
            with mlflow.start_run(run_id=run_id):
                mlflow.log_artifact(artifact_path, "promotion")
                mlflow.set_tag("promoted_to_sentinel", "true")
                mlflow.set_tag("promotion_timestamp", artifact["promoted_at"])
        except Exception as e:
            logger.error(f"Failed to log promotion artifact to MLflow: {e}")

        logger.info(f"Generated Promotion Artifact for run {run_id} at {artifact_path}")
        return artifact_path

    def get_evaluation_history(self) -> Dict[str, Dict[str, Any]]:
        """Returns all evaluation results for audit trail."""
        return {
            run_id: result.to_dict()
            for run_id, result in self._evaluated_runs.items()
        }
