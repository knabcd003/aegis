import pytest
from datetime import datetime, timedelta
from engines.sentinel.close_signal_generator import CloseSignalGenerator, EntryStateSnapshot

def test_entry_state_persistence():
    snapshot = EntryStateSnapshot(
        ticker="AAPL",
        entry_price=100.0,
        entry_date=datetime(2023, 1, 1),
        fundamental_metrics={"eps": 5.0, "pe_ratio": 20.0},
        thesis_summary="Strong cash flow."
    )
    
    local_state = {}
    
    # Assert it stores to local dict correctly
    snapshot.persist("run_123", local_state)
    assert "snapshots" in local_state
    assert "AAPL" in local_state["snapshots"]
    assert local_state["snapshots"]["AAPL"]["entry_price"] == 100.0

def test_exit_rules():
    generator = CloseSignalGenerator(target_pct=0.20, stop_pct=-0.10, max_hold_days=90)
    
    entry_date = datetime(2023, 1, 1)
    snapshot = EntryStateSnapshot(
        ticker="AAPL",
        entry_price=100.0,
        entry_date=entry_date,
        fundamental_metrics={"eps": 5.0},
        thesis_summary="Test"
    )
    
    # Target Approached (120 >= 100 * 1.20)
    reason = generator.evaluate_position(
        "AAPL", current_price=121.0, current_date=entry_date + timedelta(days=10),
        current_fundamentals={"eps": 5.0}, portfolio_nav=100000, initial_nav=100000, snapshot=snapshot
    )
    assert reason == "Target Approached"
    
    # Stop Triggered (90 <= 100 * 0.90)
    reason = generator.evaluate_position(
        "AAPL", current_price=89.0, current_date=entry_date + timedelta(days=10),
        current_fundamentals={"eps": 5.0}, portfolio_nav=100000, initial_nav=100000, snapshot=snapshot
    )
    assert reason == "Stop Triggered"
    
    # Hold Duration Expired (91 days > 90)
    reason = generator.evaluate_position(
        "AAPL", current_price=105.0, current_date=entry_date + timedelta(days=91),
        current_fundamentals={"eps": 5.0}, portfolio_nav=100000, initial_nav=100000, snapshot=snapshot
    )
    assert reason == "Hold Duration Expired"
    
    # Fundamental Shift (EPS drops from 5.0 to 3.0 = -40% drop)
    reason = generator.evaluate_position(
        "AAPL", current_price=105.0, current_date=entry_date + timedelta(days=10),
        current_fundamentals={"eps": 3.0}, portfolio_nav=100000, initial_nav=100000, snapshot=snapshot
    )
    assert reason == "Fundamental Shift"
    
    # Risk Budget Violation (Portfolio down 20%)
    reason = generator.evaluate_position(
        "AAPL", current_price=105.0, current_date=entry_date + timedelta(days=10),
        current_fundamentals={"eps": 5.0}, portfolio_nav=80000, initial_nav=100000, snapshot=snapshot
    )
    assert reason == "Risk Budget Violation"
    
    # No trigger (Hold)
    reason = generator.evaluate_position(
        "AAPL", current_price=105.0, current_date=entry_date + timedelta(days=10),
        current_fundamentals={"eps": 5.0}, portfolio_nav=100000, initial_nav=100000, snapshot=snapshot
    )
    assert reason is None
