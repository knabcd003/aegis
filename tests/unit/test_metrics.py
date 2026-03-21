"""
Tests for the Promotion Gate metrics pipeline (Phase 4 Step 0).

Tests verify:
  - Round-trip trade matching (FIFO)
  - Trade count
  - Profit factor (winning/losing, edge cases)
  - Bootstrap p-value
  - Win rate
  - Max drawdown
  - Sharpe / Sortino
  - Full compute_metrics integration
"""
import pytest
import numpy as np
import pandas as pd
from datetime import date, timedelta

from engines.simulation.metrics import (
    match_round_trip_trades,
    compute_trade_count,
    compute_profit_factor,
    compute_bootstrap_pvalue,
    compute_win_rate,
    compute_max_drawdown,
    compute_sharpe,
    compute_sortino,
    compute_metrics,
)


# ---------- Fixtures ----------

def make_trade(ticker: str, action: str, shares: int, fill_price: float,
               fill_date: date, signal_price: float = None) -> dict:
    """Helper to build a trade log entry matching the simulation loop format."""
    return {
        "ticker": ticker,
        "action": action,
        "shares": shares,
        "fill_price": fill_price,
        "fill_date": fill_date,
        "signal_date": fill_date - timedelta(days=1),
        "signal_price": signal_price or fill_price,
        "slippage_drag_usd": 0.0,
    }


@pytest.fixture
def simple_trade_log():
    """3 round-trip trades: 2 winners, 1 loser."""
    return [
        # Trade 1: AAPL — buy 100 @ $150, sell @ $165 → +$1500 (+10%)
        make_trade("AAPL", "BUY", 100, 150.0, date(2024, 1, 2)),
        make_trade("AAPL", "SELL", 100, 165.0, date(2024, 1, 15)),
        # Trade 2: MSFT — buy 50 @ $380, sell @ $350 → -$1500 (-7.9%)
        make_trade("MSFT", "BUY", 50, 380.0, date(2024, 1, 5)),
        make_trade("MSFT", "SELL", 50, 350.0, date(2024, 1, 20)),
        # Trade 3: NVDA — buy 20 @ $500, sell @ $600 → +$2000 (+20%)
        make_trade("NVDA", "BUY", 20, 500.0, date(2024, 2, 1)),
        make_trade("NVDA", "SELL", 20, 600.0, date(2024, 2, 15)),
    ]


@pytest.fixture
def nav_history():
    """30 days of NAV starting at 100k with a ~10% drawdown."""
    dates = pd.date_range("2024-01-02", periods=30, freq="B")
    # Create a curve: rises 5%, drops 10%, recovers to +3%
    nav_values = [100000]
    np.random.seed(42)
    for i in range(29):
        if i < 10:
            change = 1.005  # up
        elif i < 20:
            change = 0.99  # down
        else:
            change = 1.003  # recovery
        nav_values.append(nav_values[-1] * change)
    return [{"date": d.date(), "nav": n} for d, n in zip(dates, nav_values)]


# ---------- Round-Trip Matching ----------

class TestRoundTripMatching:
    def test_basic_fifo_matching(self, simple_trade_log):
        trips = match_round_trip_trades(simple_trade_log)
        assert len(trips) == 3, f"Expected 3 round trips, got {len(trips)}"

    def test_pnl_correct(self, simple_trade_log):
        trips = match_round_trip_trades(simple_trade_log)
        aapl = [t for t in trips if t["ticker"] == "AAPL"][0]
        assert aapl["pnl"] == pytest.approx(1500.0)
        assert aapl["pnl_pct"] == pytest.approx(0.1, abs=0.001)

    def test_losing_trade_negative_pnl(self, simple_trade_log):
        trips = match_round_trip_trades(simple_trade_log)
        msft = [t for t in trips if t["ticker"] == "MSFT"][0]
        assert msft["pnl"] < 0
        assert msft["pnl"] == pytest.approx(-1500.0)

    def test_hold_days_computed(self, simple_trade_log):
        trips = match_round_trip_trades(simple_trade_log)
        aapl = [t for t in trips if t["ticker"] == "AAPL"][0]
        assert aapl["hold_days"] == 13  # Jan 2 → Jan 15

    def test_empty_trade_log(self):
        trips = match_round_trip_trades([])
        assert len(trips) == 0

    def test_unmatched_buy(self):
        """A BUY with no corresponding SELL should not produce a round trip."""
        log = [make_trade("AAPL", "BUY", 100, 150.0, date(2024, 1, 2))]
        trips = match_round_trip_trades(log)
        assert len(trips) == 0

    def test_unfilled_orders_skipped(self):
        """Orders with fill_date=None should be ignored."""
        log = [
            {"ticker": "AAPL", "action": "BUY", "shares": 100, "fill_price": 150.0,
             "fill_date": None, "signal_date": date(2024, 1, 1), "signal_price": 150.0},
        ]
        trips = match_round_trip_trades(log)
        assert len(trips) == 0


# ---------- Trade Count ----------

class TestTradeCount:
    def test_count_matches_round_trips(self, simple_trade_log):
        trips = match_round_trip_trades(simple_trade_log)
        assert compute_trade_count(trips) == 3

    def test_count_zero_for_empty(self):
        assert compute_trade_count([]) == 0


# ---------- Profit Factor ----------

class TestProfitFactor:
    def test_basic_profit_factor(self, simple_trade_log):
        trips = match_round_trip_trades(simple_trade_log)
        pf = compute_profit_factor(trips)
        # Winners: $1500 + $2000 = $3500
        # Losers: $1500
        # PF = 3500/1500 = 2.333...
        assert pf == pytest.approx(3500 / 1500, abs=0.01)

    def test_all_winners(self):
        """No losers → profit factor should be inf (capped to 999 in compute_metrics)."""
        log = [
            make_trade("AAPL", "BUY", 100, 100.0, date(2024, 1, 2)),
            make_trade("AAPL", "SELL", 100, 120.0, date(2024, 1, 15)),
        ]
        trips = match_round_trip_trades(log)
        pf = compute_profit_factor(trips)
        assert pf == float("inf")

    def test_all_losers(self):
        log = [
            make_trade("AAPL", "BUY", 100, 120.0, date(2024, 1, 2)),
            make_trade("AAPL", "SELL", 100, 100.0, date(2024, 1, 15)),
        ]
        trips = match_round_trip_trades(log)
        pf = compute_profit_factor(trips)
        assert pf == 0.0

    def test_empty_returns_zero(self):
        assert compute_profit_factor([]) == 0.0


# ---------- Bootstrap P-Value ----------

class TestBootstrapPvalue:
    def test_strong_strategy_low_pvalue(self):
        """A strategy with strongly positive mean return should have low p-value."""
        # Mix of positive and negative returns, but mean is strongly positive.
        # Shuffling disrupts the ordering but preserves the distribution,
        # so we need many returns with a clearly positive mean vs std.
        rng = np.random.RandomState(99)
        trips = [
            {"pnl": v, "pnl_pct": v / 1000}
            for v in rng.normal(loc=50, scale=20, size=100)
        ]
        pval = compute_bootstrap_pvalue(trips, n_permutations=1000, seed=42)
        # With a strongly positive mean, permutation test should show significance
        assert pval < 0.10, f"Strong strategy should have p<0.10, got {pval}"

    def test_random_strategy_high_pvalue(self):
        """A strategy with random returns should have high p-value."""
        rng = np.random.RandomState(123)
        trips = [
            {"pnl": rng.normal(0, 100), "pnl_pct": rng.normal(0, 0.05)}
            for _ in range(50)
        ]
        pval = compute_bootstrap_pvalue(trips, n_permutations=1000, seed=42)
        assert pval > 0.1, f"Random strategy should have p>0.1, got {pval}"

    def test_too_few_trades(self):
        """Less than 5 trades returns p-value of 1.0."""
        trips = [{"pnl": 100, "pnl_pct": 0.05}] * 3
        assert compute_bootstrap_pvalue(trips) == 1.0


# ---------- Win Rate ----------

class TestWinRate:
    def test_basic_win_rate(self, simple_trade_log):
        trips = match_round_trip_trades(simple_trade_log)
        wr = compute_win_rate(trips)
        assert wr == pytest.approx(2 / 3, abs=0.01)

    def test_empty(self):
        assert compute_win_rate([]) == 0.0


# ---------- Max Drawdown ----------

class TestMaxDrawdown:
    def test_known_drawdown(self):
        """100 → 120 → 90 → 110: drawdown = (90-120)/120 = -0.25"""
        nav = pd.Series([100, 120, 90, 110])
        dd = compute_max_drawdown(nav)
        assert dd == pytest.approx(-0.25, abs=0.01)

    def test_no_drawdown(self):
        nav = pd.Series([100, 110, 120, 130])
        dd = compute_max_drawdown(nav)
        assert dd == 0.0

    def test_empty_series(self):
        assert compute_max_drawdown(pd.Series([])) == 0.0


# ---------- Sharpe / Sortino ----------

class TestSharpe:
    def test_positive_sharpe(self):
        returns = pd.Series([0.01, 0.02, 0.01, 0.015, 0.005])
        s = compute_sharpe(returns)
        assert s > 0

    def test_zero_std(self):
        returns = pd.Series([0.0, 0.0, 0.0])
        assert compute_sharpe(returns) == 0.0


class TestSortino:
    def test_positive_sortino(self):
        returns = pd.Series([0.01, -0.005, 0.02, -0.003, 0.01])
        s = compute_sortino(returns)
        assert s > 0

    def test_no_downside(self):
        returns = pd.Series([0.01, 0.02, 0.03])
        assert compute_sortino(returns) == 0.0


# ---------- Full Integration ----------

class TestComputeMetrics:
    def test_all_metrics_present(self, nav_history, simple_trade_log):
        holdout_dates = [d["date"].isoformat() for d in nav_history[20:]]
        metrics = compute_metrics(nav_history, simple_trade_log, holdout_dates)

        required_keys = [
            "optimization_sharpe", "optimization_max_drawdown", "optimization_total_return",
            "held_out_sharpe", "held_out_max_drawdown", "held_out_total_return",
            "trade_count", "profit_factor", "win_rate", "bootstrap_pvalue",
            "walk_forward_efficiency", "correlation_with_existing",
            "held_out_degradation", "sharpe", "max_drawdown",
        ]
        for key in required_keys:
            assert key in metrics, f"Missing metric: {key}"

    def test_trade_count_correct(self, nav_history, simple_trade_log):
        holdout_dates = [d["date"].isoformat() for d in nav_history[20:]]
        metrics = compute_metrics(nav_history, simple_trade_log, holdout_dates)
        assert metrics["trade_count"] == 3

    def test_profit_factor_correct(self, nav_history, simple_trade_log):
        holdout_dates = [d["date"].isoformat() for d in nav_history[20:]]
        metrics = compute_metrics(nav_history, simple_trade_log, holdout_dates)
        assert metrics["profit_factor"] == pytest.approx(3500 / 1500, abs=0.01)

    def test_walk_forward_is_zero_stub(self, nav_history, simple_trade_log):
        holdout_dates = [d["date"].isoformat() for d in nav_history[20:]]
        metrics = compute_metrics(nav_history, simple_trade_log, holdout_dates)
        # Must be 0.0 until walk-forward implemented — this forces gate failure
        assert metrics["walk_forward_efficiency"] == 0.0

    def test_inf_profit_factor_capped(self, nav_history):
        """All-winner trade log should cap profit factor at 999."""
        all_winners = [
            make_trade("AAPL", "BUY", 100, 100.0, date(2024, 1, 2)),
            make_trade("AAPL", "SELL", 100, 120.0, date(2024, 1, 15)),
        ]
        holdout_dates = [d["date"].isoformat() for d in nav_history[20:]]
        metrics = compute_metrics(nav_history, all_winners, holdout_dates)
        assert metrics["profit_factor"] == 999.0

    def test_empty_nav_returns_error(self):
        metrics = compute_metrics([], [], [])
        assert "error" in metrics
