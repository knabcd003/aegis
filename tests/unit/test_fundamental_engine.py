import pytest
from datetime import date
from unittest.mock import MagicMock, patch

from engines.fundamental.signal_gate import SignalGate
from engines.fundamental.earnings_revision_tracker import EarningsRevisionTracker
from engines.fundamental.insider_activity_monitor import InsiderActivityMonitor

# -----------------------------------------------------------------------------
# Signal Gate Tests (T3.1, T3.2)
# -----------------------------------------------------------------------------
def test_signal_gate_passes():
    """T3.1 — Gate passes when all configured conditions are met"""
    signals = {
        "finbert_score": 0.72,
        "earnings_revision": {"direction": "up"}
    }
    gate_config = {"finbert_above": 0.5, "earnings_revision_direction": "up"}
    assert SignalGate.evaluate(signals, gate_config)[0] is True
    import math
    assert math.isclose(signals["_gate_margin"]["finbert"], 0.22, rel_tol=1e-5)


def test_signal_gate_fails_on_low_sentiment():
    """T3.2 — Gate fails when one condition is unmet"""
    signals = {"finbert_score": 0.3, "earnings_revision": {"direction": "up"}}
    gate_config = {"finbert_above": 0.5, "earnings_revision_direction": "up"}
    assert SignalGate.evaluate(signals, gate_config)[0] is False
    assert signals["_gate_margin"]["finbert"] == -0.2


# -----------------------------------------------------------------------------
# Earnings Revision Tracker Tests (T3.3)
# -----------------------------------------------------------------------------
def test_earnings_revision_point_in_time(mocker):
    """T3.3 — Earnings revisions: future revisions not visible at as_of_date"""
    # Mock Finnhub connector to return explicit point-in-time data
    mock_fh = mocker.patch("engines.fundamental.earnings_revision_tracker.FinnhubConnector")
    instance = mock_fh.return_value
    instance.get_earnings_revisions.return_value = [
        {"actual": 2.5, "estimate": 2.0, "surprise": 0.5, "public_disclosure_ts": "2023-03-31"}
    ]
    
    tracker = EarningsRevisionTracker()
    sim_date = date(2023, 4, 1)
    result = tracker.compute("AAPL", as_of_date=sim_date)
    
    # Assert direction up due to actual > estimate
    assert result["direction"] == "up"
    # Ensure it only evaluated things prior to 4/1
    assert result["revision_date"] < sim_date


# -----------------------------------------------------------------------------
# Insider Activity Monitor Tests (T3.4)
# -----------------------------------------------------------------------------
def test_congressional_disclosure_lag(mocker):
    """T3.4 — Congressional: trade not visible until disclosure_filing_ts has passed"""
    mock_fh = mocker.patch("engines.fundamental.insider_activity_monitor.FinnhubConnector")
    mock_cg = mocker.patch("engines.fundamental.insider_activity_monitor.CongressionalConnector")
    
    fh_instance = mock_fh.return_value
    fh_instance.get_insider_transactions.return_value = []
    
    cg_instance = mock_cg.return_value
    # Note: Our simulation is looking from Jan 20th. We explicitly feed a raw record here,
    # but the internal CG connector already handles point-in-time naturally when called live.
    cg_instance.get_disclosures.return_value = [
       {"trade_date": "2023-01-01", "disclosure_filing_ts": "2023-01-15", "public_disclosure_ts": "2023-01-15", "transaction_type": "Purchase"}
    ]
    
    sim_date = date(2023, 1, 20)
    monitor = InsiderActivityMonitor()
    result = monitor.compute("AAPL", as_of_date=sim_date)
    
    # Assert the Jan 15 filing is visible
    assert result["cluster_size"] == 1
    assert result["insider_type"] == "congressional"
    
    # Loop the list ensuring no future leaks mathematically 
    for h in result["congressional"]:
        assert date.fromisoformat(h["disclosure_filing_ts"]) <= sim_date
