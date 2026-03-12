import pytest
from datetime import datetime
from engines.sentinel.mirror_portfolio import CounterfactualTracker

def test_mirror_portfolio_execution():
    tracker = CounterfactualTracker("sentinel_123", initial_cash=100000.0)
    
    # Mirror buys 100 shares of AAPL at $150
    tracker.handle_signal_resolution(
        ticker="AAPL",
        decision="BUY",
        action="ACCEPTED",  # The user action doesn't matter to the mirror
        execution_price=150.0,
        quantity=100,
        current_date=datetime.now()
    )
    
    assert tracker.mirror.cash == 85000.0
    assert "AAPL" in tracker.mirror.positions
    assert tracker.mirror.positions["AAPL"].quantity == 100
    assert tracker.mirror.nav == 100000.0  # Cash + Stock = 100k

    # Price goes to $200
    tracker.mirror.positions["AAPL"].current_price = 200.0
    assert tracker.mirror.nav == 105000.0

    # Sell 50 shares at $200
    tracker.handle_signal_resolution(
        ticker="AAPL",
        decision="SELL",
        action="DECLINED",  # Even if user declines the sell, the mirror does it
        execution_price=200.0,
        quantity=50,
        current_date=datetime.now()
    )

    assert tracker.mirror.cash == 95000.0
    assert tracker.mirror.positions["AAPL"].quantity == 50
    assert tracker.mirror.nav == 105000.0

def test_gap_analysis():
    tracker = CounterfactualTracker("sentinel_123", initial_cash=100000.0)
    
    # Mirror makes 5k
    tracker.handle_signal_resolution("AAPL", "BUY", "ACCEPTED", 150.0, 100, datetime.now())
    tracker.mirror.positions["AAPL"].current_price = 200.0
    
    # Actual user made 2k total because they declined half the signals
    tracker.sync_actual_nav(102000.0, datetime.now())
    
    gap = tracker.get_gap_analysis()
    
    assert gap["absolute_gap"] == -3000.0  # User is down 3k vs the AI
    assert gap["human_outperformance"] is False
    assert gap["actual_return_pct"] == 0.02
    assert gap["mirror_return_pct"] == 0.05
