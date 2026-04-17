import signal
import logging
from typing import Optional

from engines.vcl.component import VCLComponent, HealthStatus, HealthResult, ComponentRole
from engines.sentinel.promotion_gate import PromotionGate, PromotionGateInput, PromotionGateOutput

logger = logging.getLogger(__name__)

class PromotionGateVCL(VCLComponent):
    """
    VCL Wrapper for PromotionGate.
    Enforces mandatory 5s health timeout for Gate 2.
    """
    component_id = "aegis.vcl.promotion_gate"
    version = "1.0.0"
    role = ComponentRole.GATE_CONDITION
    input_schema = PromotionGateInput
    output_schema = PromotionGateOutput

    def __init__(self, engine: PromotionGate = None):
        if engine is None:
            from engines.data_ingestion.data_engine import DataEngine
            from engines.monitoring.connector_health import ConnectorHealthMonitor
            data_engine = DataEngine()
            health_monitor = ConnectorHealthMonitor(data_engine=data_engine)
            engine = PromotionGate(health_monitor=health_monitor)
        self.engine = engine

    def health(self) -> HealthResult:
        """
        VCL standard health hook with mandatory 5-second timeout.
        Gate 2 requirement.
        """
        if self.engine is None:
            return HealthResult(status=HealthStatus.OFFLINE, reason="Engine not initialized")

        def timeout_handler(signum, frame):
            raise TimeoutError("Promotion Gate Health check exceeded 5 seconds")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(4)

        try:
            # The underlying engine's health check
            res = self.engine.health()
            signal.alarm(0)
            return res
        except TimeoutError:
            return HealthResult(status=HealthStatus.DEGRADED, reason="Health check timed out (4s)")
        except Exception as e:
            signal.alarm(0)
            logger.error(f"PromotionGateVCL health check failed: {e}")
            return HealthResult(status=HealthStatus.OFFLINE, reason=str(e))

    def execute(self, input_data: PromotionGateInput) -> PromotionGateOutput:
        """Delegates execution to the underlying engine's unified evaluate interface."""
        if self.engine is None:
            raise RuntimeError("PromotionGateVCL engine not initialized")
        
        # PromotionGate already has an execute() that wraps evaluate_backtest.
        # We will use the direct evaluate() interface for full flexibility.
        res = self.engine.evaluate(
            run_id=input_data.run_id,
            session_quality=input_data.session_quality,
            scenario_pass_rate=input_data.scenario_pass_rate,
            debate_confidence=input_data.debate_confidence
        )
        return PromotionGateOutput(gate_result=res)
