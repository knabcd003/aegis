import signal
import logging
from typing import Optional

from engines.vcl.component import VCLComponent, HealthStatus, HealthResult, ComponentRole
from engines.system.scenario.generator import BlockBootstrapGenerator, BootstrapRequest, ScenarioBatteryResult

logger = logging.getLogger(__name__)

class BlockBootstrapVCL(VCLComponent):
    """
    VCL Wrapper for BlockBootstrapGenerator.
    Enforces mandatory 5s health timeout for Gate 2.
    """
    component_id = "aegis.vcl.scenario_generator"
    version = "1.0.0"
    role = ComponentRole.SCENARIO_GENERATOR
    
    # schemas come from the underlying engine logic
    input_schema = BootstrapRequest 
    output_schema = ScenarioBatteryResult

    def __init__(self, engine: BlockBootstrapGenerator = None):
        if engine is None:
            engine = BlockBootstrapGenerator()
        self.engine = engine

    def health(self) -> HealthResult:
        """
        VCL standard health hook with mandatory 5-second timeout.
        Gate 2 requirement.
        """
        def timeout_handler(signum, frame):
            raise TimeoutError("Scenario Generator Health check exceeded 5 seconds")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(4)

        try:
            # Deterministic local logic usually, but we must follow the contract
            res_dict = self.engine.health()
            signal.alarm(0)
            status_str = res_dict.get("status", "healthy")
            return HealthResult(
                status=HealthStatus.HEALTHY if status_str == "healthy" else HealthStatus.DEGRADED,
                reason=res_dict.get("reason", "")
            )
        except TimeoutError:
            return HealthResult(status=HealthStatus.DEGRADED, reason="Health check timed out (4s)")
        except Exception as e:
            signal.alarm(0)
            logger.error(f"BlockBootstrapVCL health check failed: {e}")
            return HealthResult(status=HealthStatus.OFFLINE, reason=str(e))

    def execute(self, input_data: BootstrapRequest) -> ScenarioBatteryResult:
        """Delegates execution to the underlying engine."""
        return self.engine.execute(input_data)
