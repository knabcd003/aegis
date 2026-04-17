import signal
import logging
from typing import Optional

from engines.vcl.component import VCLComponent, HealthStatus, HealthResult, ComponentRole
from engines.sentinel.close_signal_generator import CloseSignalGenerator, CloseSignalInput, CloseSignalOutput

logger = logging.getLogger(__name__)

class CloseSignalGeneratorVCL(VCLComponent):
    """
    VCL Wrapper for CloseSignalGenerator.
    Enforces mandatory 5s health timeout for Gate 2.
    """
    component_id = "aegis.vcl.close_signal_generator"
    version = "1.0.0"
    role = ComponentRole.SIGNAL_GENERATOR
    input_schema = CloseSignalInput
    output_schema = CloseSignalOutput

    def __init__(self, engine: CloseSignalGenerator = None):
        if engine is None:
            engine = CloseSignalGenerator()
        self.engine = engine

    def health(self) -> HealthResult:
        """
        VCL standard health hook with mandatory 5-second timeout.
        Gate 2 requirement.
        """
        if self.engine is None:
            return HealthResult(status=HealthStatus.OFFLINE, reason="Engine not initialized")

        def timeout_handler(signum, frame):
            raise TimeoutError("Close Signal Health check exceeded 5 seconds")

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
            logger.error(f"CloseSignalGeneratorVCL health check failed: {e}")
            return HealthResult(status=HealthStatus.OFFLINE, reason=str(e))

    def execute(self, input_data: CloseSignalInput) -> CloseSignalOutput:
        """Delegates execution to the underlying engine."""
        if self.engine is None:
            raise RuntimeError("CloseSignalGeneratorVCL engine not initialized")
        return self.engine.execute(input_data)
