import signal
import logging
from typing import Optional

from engines.vcl.component import VCLComponent, HealthStatus, HealthResult, ComponentRole
from engines.nli.segment_classifier import SegmentClassifier, SegmentClassificationInput, SegmentClassificationOutput

logger = logging.getLogger(__name__)

class NLISegmentClassifierVCL(VCLComponent):
    """
    VCL Wrapper for SegmentClassifier (NLI).
    Enforces mandatory 5s health timeout for Gate 2.
    """
    component_id = "aegis.vcl.nli_classifier"
    version = "1.0.0"
    role = ComponentRole.SIGNAL_GENERATOR
    input_schema = SegmentClassificationInput
    output_schema = SegmentClassificationOutput

    def __init__(self, engine: SegmentClassifier = None):
        # If no engine provided, we'll use the singleton instance in execute/health
        self._engine = engine

    @property
    def engine(self) -> SegmentClassifier:
        if self._engine is None:
            self._engine = SegmentClassifier.get_instance()
        return self._engine

    def health(self) -> HealthResult:
        """
        VCL standard health hook with mandatory 5-second timeout.
        Gate 2 requirement.
        """
        def timeout_handler(signum, frame):
            raise TimeoutError("NLI Health check exceeded 5 seconds")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(4) # 4s alarm for 5s goal

        try:
            # Check model availability
            is_avail = self.engine.is_available
            signal.alarm(0)

            if not is_avail:
                return HealthResult(
                    status=HealthStatus.DEGRADED, 
                    reason="NLI model failed to load, using conservative fallback"
                )
            return HealthResult(status=HealthStatus.HEALTHY)

        except TimeoutError:
            return HealthResult(status=HealthStatus.DEGRADED, reason="Health check timed out (4s)")
        except Exception as e:
            signal.alarm(0)
            logger.error(f"NLISegmentClassifierVCL health check failed: {e}")
            return HealthResult(status=HealthStatus.OFFLINE, reason=str(e))

    def execute(self, input_data: SegmentClassificationInput) -> SegmentClassificationOutput:
        """Delegates to the SegmentClassifier engine."""
        return self.engine.execute(input_data)
