import pytest
from datetime import datetime, timedelta
from engines.data_ingestion.data_engine import DataEngine
from engines.data_ingestion.base_connector import BaseConnector
from engines.monitoring.connector_health import ConnectorHealthMonitor


class MockConnector(BaseConnector):
    def __init__(self, name: str):
        self._name = name
        self._healthy = True
        self._last_successful_fetch_ts = datetime.now()

    @property
    def name(self) -> str:
        return self._name

    @property
    def provides_prices(self) -> bool: return True
    @property
    def provides_fundamentals(self) -> bool: return False
    @property
    def provides_news(self) -> bool: return False

    def get_prices(self, ticker, days=30, interval="1d", as_of_date=None): return None
    def get_fundamentals(self, ticker, as_of_date=None): return None
    def get_news(self, ticker, days=7, as_of_date=None): return []

    @property
    def last_successful_fetch_ts(self):
        return self._last_successful_fetch_ts

    def health_check(self) -> bool:
        if not self._healthy:
            raise Exception("Connection timeout")
        return True


def test_monitor_healthy_transition():
    engine = DataEngine(data_dir="/tmp/test_aegis_health")
    conn = MockConnector("mock_healthy")
    engine.register(conn)

    monitor = ConnectorHealthMonitor(engine, stale_threshold_hours=24)
    # Initially DEGRADED before first check
    assert monitor.get_connector_state("mock_healthy") == ConnectorHealthMonitor.STATE_DEGRADED
    
    monitor.run_health_checks()
    assert monitor.get_connector_state("mock_healthy") == ConnectorHealthMonitor.STATE_MONITORING
    assert monitor.can_generate_signals() is True


def test_monitor_asymmetry_rule_offline_on_exception():
    engine = DataEngine(data_dir="/tmp/test_aegis_health")
    conn = MockConnector("mock_flaky")
    engine.register(conn)

    monitor = ConnectorHealthMonitor(engine)
    monitor.run_health_checks()
    assert monitor.get_connector_state("mock_flaky") == ConnectorHealthMonitor.STATE_MONITORING

    # Break the connector
    conn._healthy = False
    monitor.run_health_checks()
    
    # Asymmetry rule: exception immediately sets it OFFLINE
    assert monitor.get_connector_state("mock_flaky") == ConnectorHealthMonitor.STATE_OFFLINE
    assert monitor.can_generate_signals() is False


def test_monitor_stale_data_downgrades():
    engine = DataEngine(data_dir="/tmp/test_aegis_health")
    conn = MockConnector("mock_stale")
    engine.register(conn)

    monitor = ConnectorHealthMonitor(engine, stale_threshold_hours=24)
    
    # 10 hours old (safe)
    conn._last_successful_fetch_ts = datetime.now() - timedelta(hours=10)
    monitor.run_health_checks()
    assert monitor.get_connector_state("mock_stale") == ConnectorHealthMonitor.STATE_MONITORING

    # 14 hours old (ambiguous -> DEGRADED)
    conn._last_successful_fetch_ts = datetime.now() - timedelta(hours=14)
    monitor.run_health_checks()
    assert monitor.get_connector_state("mock_stale") == ConnectorHealthMonitor.STATE_DEGRADED
    # Signals can still generate if just degraded
    assert monitor.can_generate_signals() is True

    # 25 hours old (critically stale -> OFFLINE)
    conn._last_successful_fetch_ts = datetime.now() - timedelta(hours=25)
    monitor.run_health_checks()
    assert monitor.get_connector_state("mock_stale") == ConnectorHealthMonitor.STATE_OFFLINE
    # Signals immediately suspended
    assert monitor.can_generate_signals() is False
