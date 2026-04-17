import signal
import logging
from typing import Optional

from engines.vcl.component import VCLComponent, HealthStatus, HealthResult, ComponentRole
from engines.sentinel.mirror_portfolio import CounterfactualTracker, MirrorPortfolioInput, MirrorPortfolioOutput

logger = logging.getLogger(__name__)

class MirrorPortfolioVCL(VCLComponent):
    """
    VCL Wrapper for CounterfactualTracker.
    Enforces mandatory 5s health timeout for Gate 2.
    """
    component_id = "aegis.vcl.mirror_portfolio"
    version = "1.0.0"
    role = ComponentRole.AUDITOR
    input_schema = MirrorPortfolioInput
    output_schema = MirrorPortfolioOutput

    def __init__(self, engine: CounterfactualTracker = None):
        if engine is None:
            engine = CounterfactualTracker(sentinel_id="vcl_test_sentinel")
        self.engine = engine

    def health(self) -> HealthResult:
        """
        VCL standard health hook with mandatory 5-second timeout.
        Gate 2 requirement.
        """
        if self.engine is None:
            return HealthResult(status=HealthStatus.OFFLINE, reason="Engine not initialized")

        def timeout_handler(signum, frame):
            raise TimeoutError("Mirror Portfolio Health check exceeded 5 seconds")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(4)

        try:
            # Underlying engine health
            res = self.engine.health()
            signal.alarm(0)
            return res
        except TimeoutError:
            return HealthResult(status=HealthStatus.DEGRADED, reason="Health check timed out (4s)")
        except Exception as e:
            signal.alarm(0)
            logger.error(f"MirrorPortfolioVCL health check failed: {e}")
            return HealthResult(status=HealthStatus.OFFLINE, reason=str(e))

    def execute(self, input_data: MirrorPortfolioInput) -> MirrorPortfolioOutput:
        """Delegates execution to the underlying engine."""
        if self.engine is None:
            raise RuntimeError("MirrorPortfolioVCL engine not initialized")
        return self.engine.execute(input_data)
