import signal
import logging
from typing import Dict, Any
from pydantic import BaseModel, Field

from engines.vcl.component import VCLComponent, HealthStatus, HealthResult, ComponentRole
from engines.monitoring.connector_health import ConnectorHealthMonitor, ConnectorHealthInput, ConnectorHealthOutput

logger = logging.getLogger(__name__)

class ConnectorHealthVCL(VCLComponent):
    """
    VCL Wrapper for ConnectorHealthMonitor.
    Implements mandatory 5s health timeout for Gate 2 verification.
    """
    component_id = "aegis.vcl.connector_health"
    version = "1.0.0"
    role = ComponentRole.GATE_CONDITION
    input_schema = ConnectorHealthInput
    output_schema = ConnectorHealthOutput

    def __init__(self, engine: ConnectorHealthMonitor = None):
        if engine is None:
            from engines.data_ingestion.data_engine import DataEngine
            data_engine = DataEngine()
            engine = ConnectorHealthMonitor(data_engine=data_engine)
        self.engine = engine

    def health(self) -> HealthResult:
        """
        VCL standard health hook with mandatory 5-second timeout.
        Gate 2 requirement.
        """
        if self.engine is None:
            return HealthResult(status=HealthStatus.OFFLINE, reason="Engine not initialized")

        def timeout_handler(signum, frame):
            raise TimeoutError("Health check exceeded 5 seconds")

        # Set up 4-second alarm (1s buffer before Gate 2's 5s timeout)
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(4)

        try:
            # Check if any connector is offline in the underlying engine
            # This logic mimics the engine's check but adds the VCL-required timeout
            is_offline = self.engine.is_any_connector_offline()
            signal.alarm(0) # Disable alarm

            if is_offline:
                return HealthResult(status=HealthStatus.DEGRADED, reason="One or more connectors offline")
            return HealthResult(status=HealthStatus.HEALTHY)

        except TimeoutError:
            return HealthResult(status=HealthStatus.DEGRADED, reason="Health check timed out (4s)")
        except Exception as e:
            signal.alarm(0) # Disable alarm
            logger.error(f"ConnectorHealthVCL health check failed: {e}")
            return HealthResult(status=HealthStatus.OFFLINE, reason=str(e))

    def execute(self, input_data: ConnectorHealthInput) -> ConnectorHealthOutput:
        """Delegates execution to the underlying engine."""
        if self.engine is None:
            raise RuntimeError("ConnectorHealthVCL engine not initialized")
        return self.engine.execute(input_data)
