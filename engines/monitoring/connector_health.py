"""
Connector Health Monitor (Phase 4)
Monitors the state of all data connectors registered with the Data Engine.
Implements the 3-state system (MONITORING, DEGRADED, OFFLINE) and asymmetry rule.
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
import asyncio
import logging
from pydantic import BaseModel, Field

from engines.data_ingestion.data_engine import DataEngine
from engines.vcl.component import VCLComponent, HealthStatus, HealthResult, ComponentRole

logger = logging.getLogger(__name__)

class ConnectorHealthInput(BaseModel):
    # Empty input, it just triggers the check based on its internal state
    trigger: bool = True

class ConnectorHealthOutput(BaseModel):
    states: Dict[str, str] = Field(description="Map of connector name to health state")
    any_offline: bool
    any_degraded: bool
    can_generate_signals: bool

class ConnectorHealthMonitor(VCLComponent):
    """
    Monitors connector health.
    States:
        - MONITORING: Healthy and functional.
        - DEGRADED: Partial failure or stale data (ambiguous states).
        - OFFLINE: Completely unreachable or critically stale.
    """
    
    STATE_MONITORING = "MONITORING"
    STATE_DEGRADED = "DEGRADED"
    STATE_OFFLINE = "OFFLINE"

    component_id = "aegis.system.connector_health_monitor"
    version = "1.0.0"
    role = ComponentRole.GATE_CONDITION
    input_schema = ConnectorHealthInput
    output_schema = ConnectorHealthOutput

    def __init__(self, data_engine: DataEngine, stale_threshold_hours: int = 24):
        self.data_engine = data_engine
        self.stale_threshold_hours = stale_threshold_hours
        self._status_cache: Dict[str, str] = {}
        self._last_check_ts: Dict[str, datetime] = {}
        
        # Initialize all known connectors to DEGRADED until proven MONITORING
        for connector_name in self.data_engine.list_connectors():
            self._status_cache[connector_name] = self.STATE_DEGRADED
            self._last_check_ts[connector_name] = datetime.min

    def execute(self, input_data: ConnectorHealthInput) -> ConnectorHealthOutput:
        """VCL standard execution hook."""
        states = self.run_health_checks()
        return ConnectorHealthOutput(
            states=states,
            any_offline=self.is_any_connector_offline(),
            any_degraded=self.is_any_connector_degraded(),
            can_generate_signals=self.can_generate_signals()
        )

    def health(self) -> HealthResult:
        """VCL standard health hook."""
        # The monitor itself is always healthy if it can execute
        return HealthResult(status=HealthStatus.HEALTHY)

            
    def get_connector_state(self, connector_name: str) -> str:
        """Get the current state of a connector."""
        return self._status_cache.get(connector_name, self.STATE_OFFLINE)

    def is_any_connector_offline(self) -> bool:
        """Returns True if ANY registered connector is OFFLINE."""
        return any(state == self.STATE_OFFLINE for state in self._status_cache.values())

    def is_any_connector_degraded(self) -> bool:
        """Returns True if ANY registered connector is DEGRADED."""
        return any(state == self.STATE_DEGRADED for state in self._status_cache.values())

    def can_generate_signals(self) -> bool:
        """
        Signals generation is immediately suspended if ANY connector is OFFLINE.
        DEGRADED connectors still allow generation (though promotion is blocked).
        """
        return not self.is_any_connector_offline()

    def run_health_checks(self) -> Dict[str, str]:
        """
        Run health checks on all registered connectors and apply the asymmetry rule:
        If an exception is raised, or if there's no successful fetch recently, 
        state degrades to DEGRADED or OFFLINE.
        """
        now = datetime.now()
        
        for entry in self.data_engine._connectors:
            conn = entry["connector"]
            connector_name = conn.name
            
            try:
                is_healthy = conn.health_check()
                last_fetch = getattr(conn, "last_successful_fetch_ts", None)
                
                if not is_healthy:
                    # Asymmetry rule: if it explicitly fails the health check (ping), 
                    # we assume it's totally unreachable.
                    self._set_state(connector_name, self.STATE_OFFLINE)
                    continue

                if last_fetch is None:
                    # Healthy ping but never successfully fetched data?
                    # Ambiguous — downgrade to DEGRADED.
                    self._set_state(connector_name, self.STATE_DEGRADED)
                    continue
                    
                age = now - last_fetch
                if age > timedelta(hours=self.stale_threshold_hours):
                    # Data is critically stale.
                    self._set_state(connector_name, self.STATE_OFFLINE)
                elif age > timedelta(hours=self.stale_threshold_hours / 2.0):
                    # Data is getting stale. Ambiguous — downgrade to DEGRADED.
                    self._set_state(connector_name, self.STATE_DEGRADED)
                else:
                    self._set_state(connector_name, self.STATE_MONITORING)

            except Exception as e:
                logger.error(f"Health check failed for {connector_name}: {e}")
                # Asymmetry rule: unhandled exceptions during check = OFFLINE
                self._set_state(connector_name, self.STATE_OFFLINE)
                
            self._last_check_ts[connector_name] = now
            
        return self._status_cache.copy()

    def _set_state(self, connector_name: str, new_state: str) -> None:
        """Update state and log transitions."""
        old_state = self._status_cache.get(connector_name)
        if old_state != new_state:
            logger.warning(f"Connector '{connector_name}' transitioned {old_state} -> {new_state}")
            self._status_cache[connector_name] = new_state

    async def monitor_loop(self, check_interval_seconds: int = 1800):
        """
        Coroutine that continuously checks connector health.
        Defaults to checking every 30 minutes (1800s).
        """
        logger.info(f"Starting Connector Health Monitor daemon (interval={check_interval_seconds}s)")
        while True:
            self.run_health_checks()
            await asyncio.sleep(check_interval_seconds)
