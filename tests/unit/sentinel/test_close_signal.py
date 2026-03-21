"""
Tests for the Close Signal Generator (Phase 4 Step 2).

Tests verify:
  - All 5 exit types trigger correctly
  - Thresholds from config override defaults
  - Fundamental shift checks multiple metrics, not just EPS
  - Priority ordering in evaluate_position
  - Edge cases (no target, no stop, zero values)
  - CloseSignal structure
"""
import pytest
from datetime import datetime, timedelta

from engines.sentinel.close_signal_generator import (
    CloseSignalGenerator,
    EntryStateSnapshot,
    CloseSignal,
    ExitType,
)


# ---------- Fixtures ----------

@pytest.fixture
def snapshot():
    """Standard entry state snapshot for testing."""
    return EntryStateSnapshot(
        ticker="AAPL",
        entry_price=150.0,
        entry_date=datetime(2024, 1, 15),
        fundamental_metrics={
            "eps": 6.50,
            "revenue": 95000.0,
            "pe_ratio": 23.0,
            "debt_to_equity": 1.50,
            "gross_margin": 0.45,
        },
        thesis_summary="Strong iPhone cycle + Services growth",
        target_price=180.0,
        stop_loss_price=135.0,
        max_hold_days=90,
    )


@pytest.fixture
def generator():
    """Close signal generator with standard config."""
    return CloseSignalGenerator(
        max_hold_days=90,
        max_portfolio_drawdown_pct=0.15,
    )


@pytest.fixture
def healthy_fundamentals():
    """Fundamentals that have NOT shifted."""
    return {
        "eps": 6.40,
        "revenue": 94000.0,
        "pe_ratio": 24.0,
        "debt_to_equity": 1.55,
        "gross_margin": 0.44,
    }


# ---------- Rule 1: Target Approached ----------

class TestTargetApproached:
    def test_price_above_target(self, generator, snapshot):
        signal = generator.check_target_approached(185.0, snapshot)
        assert signal is not None
        assert signal.exit_type == ExitType.TARGET_APPROACHED
        assert signal.current_price == 185.0
        assert signal.urgency == "end_of_day"

    def test_price_at_target(self, generator, snapshot):
        signal = generator.check_target_approached(180.0, snapshot)
        assert signal is not None
        assert signal.exit_type == ExitType.TARGET_APPROACHED

    def test_price_below_target(self, generator, snapshot):
        signal = generator.check_target_approached(170.0, snapshot)
        assert signal is None

    def test_no_target_defined(self, generator):
        snap = EntryStateSnapshot(
            ticker="MSFT", entry_price=380.0, entry_date=datetime(2024, 1, 1),
            fundamental_metrics={}, thesis_summary="Test",
        )
        signal = generator.check_target_approached(400.0, snap)
        assert signal is None  # Can't evaluate without a target


# ---------- Rule 2: Stop Triggered ----------

class TestStopTriggered:
    def test_price_below_stop(self, generator, snapshot):
        signal = generator.check_stop_triggered(130.0, snapshot)
        assert signal is not None
        assert signal.exit_type == ExitType.STOP_TRIGGERED
        assert signal.urgency == "immediate"

    def test_price_at_stop(self, generator, snapshot):
        signal = generator.check_stop_triggered(135.0, snapshot)
        assert signal is not None
        assert signal.exit_type == ExitType.STOP_TRIGGERED

    def test_price_above_stop(self, generator, snapshot):
        signal = generator.check_stop_triggered(145.0, snapshot)
        assert signal is None

    def test_negative_pnl_on_stop(self, generator, snapshot):
        signal = generator.check_stop_triggered(130.0, snapshot)
        assert signal.unrealized_pnl_pct < 0


# ---------- Rule 3: Hold Duration ----------

class TestHoldDuration:
    def test_expired(self, generator, snapshot):
        future = datetime(2024, 5, 1)  # >90 days from Jan 15
        signal = generator.check_hold_duration(future, snapshot)
        assert signal is not None
        assert signal.exit_type == ExitType.HOLD_DURATION_EXPIRED

    def test_not_expired(self, generator, snapshot):
        recent = datetime(2024, 2, 1)  # 17 days from Jan 15
        signal = generator.check_hold_duration(recent, snapshot)
        assert signal is None

    def test_exactly_at_limit(self, generator, snapshot):
        at_limit = datetime(2024, 1, 15) + timedelta(days=90)
        signal = generator.check_hold_duration(at_limit, snapshot)
        assert signal is not None


# ---------- Rule 4: Fundamental Shift ----------

class TestFundamentalShift:
    def test_no_shift(self, generator, snapshot, healthy_fundamentals):
        signal = generator.check_fundamental_shift(snapshot, healthy_fundamentals)
        assert signal is None

    def test_eps_drop_triggers(self, generator, snapshot):
        bad_fundamentals = {
            "eps": 4.0,  # -38% from 6.5 → exceeds 30% threshold
            "revenue": 94000.0,
            "pe_ratio": 24.0,
            "debt_to_equity": 1.55,
            "gross_margin": 0.44,
        }
        signal = generator.check_fundamental_shift(snapshot, bad_fundamentals)
        assert signal is not None
        assert signal.exit_type == ExitType.FUNDAMENTAL_SHIFT
        assert "eps" in signal.supporting_data["shifts"][0]

    def test_pe_expansion_triggers(self, generator, snapshot):
        bad_fundamentals = {
            "eps": 6.40,
            "revenue": 94000.0,
            "pe_ratio": 40.0,  # +74% from 23.0 → exceeds 50% threshold
            "debt_to_equity": 1.55,
            "gross_margin": 0.44,
        }
        signal = generator.check_fundamental_shift(snapshot, bad_fundamentals)
        assert signal is not None
        assert any("pe_ratio" in s for s in signal.supporting_data["shifts"])

    def test_multiple_shifts_detected(self, generator, snapshot):
        bad_fundamentals = {
            "eps": 3.0,       # -54%, triggers
            "revenue": 60000.0,  # -37%, triggers
            "pe_ratio": 40.0,    # +74%, triggers
            "debt_to_equity": 3.0,  # +100%, triggers
            "gross_margin": 0.30,   # -33%, triggers
        }
        signal = generator.check_fundamental_shift(snapshot, bad_fundamentals)
        assert signal is not None
        assert len(signal.supporting_data["shifts"]) >= 3

    def test_missing_metrics_skipped(self, generator, snapshot):
        """Metrics not present in either snapshot or current are skipped."""
        partial = {"eps": 6.30}  # Only EPS present, rest missing
        signal = generator.check_fundamental_shift(snapshot, partial)
        assert signal is None  # EPS didn't decline enough


# ---------- Rule 5: Risk Budget ----------

class TestRiskBudget:
    def test_drawdown_exceeded(self, generator):
        signal = generator.check_risk_budget_violation(
            portfolio_nav=83000.0,
            portfolio_high_water_mark=100000.0,  # -17% drawdown
        )
        assert signal is not None
        assert signal.exit_type == ExitType.RISK_BUDGET_VIOLATION
        assert signal.urgency == "immediate"

    def test_within_budget(self, generator):
        signal = generator.check_risk_budget_violation(
            portfolio_nav=92000.0,
            portfolio_high_water_mark=100000.0,  # -8% drawdown
        )
        assert signal is None

    def test_exactly_at_threshold(self, generator):
        signal = generator.check_risk_budget_violation(
            portfolio_nav=85000.0,
            portfolio_high_water_mark=100000.0,  # exactly -15%
        )
        assert signal is not None


# ---------- evaluate_position: Priority ----------

class TestEvaluatePosition:
    def test_risk_budget_highest_priority(self, generator, snapshot, healthy_fundamentals):
        """Risk budget violation should trigger even if stop isn't hit."""
        signal = generator.evaluate_position(
            current_price=160.0,      # Price is above entry (no stop)
            current_date=datetime(2024, 2, 1),
            current_fundamentals=healthy_fundamentals,
            portfolio_nav=80000.0,    # But portfolio is in deep drawdown
            portfolio_high_water_mark=100000.0,
            snapshot=snapshot,
        )
        assert signal is not None
        assert signal.exit_type == ExitType.RISK_BUDGET_VIOLATION

    def test_stop_before_target(self, generator, snapshot, healthy_fundamentals):
        """If price triggers both stop and target (shouldn't happen), stop wins."""
        # Use a snapshot where stop is above entry (unusual but tests priority)
        snapshot.stop_loss_price = 200.0  # Stop above everything
        snapshot.target_price = 200.0     # Target also at 200
        signal = generator.evaluate_position(
            current_price=200.0,
            current_date=datetime(2024, 2, 1),
            current_fundamentals=healthy_fundamentals,
            portfolio_nav=100000.0,
            portfolio_high_water_mark=100000.0,
            snapshot=snapshot,
        )
        assert signal is not None
        assert signal.exit_type == ExitType.STOP_TRIGGERED

    def test_no_exit_triggered(self, generator, snapshot, healthy_fundamentals):
        """Normal conditions → no close signal."""
        signal = generator.evaluate_position(
            current_price=155.0,
            current_date=datetime(2024, 2, 1),
            current_fundamentals=healthy_fundamentals,
            portfolio_nav=100000.0,
            portfolio_high_water_mark=100000.0,
            snapshot=snapshot,
        )
        assert signal is None


# ---------- Config Factory ----------

class TestFromConfig:
    def test_from_exit_config(self):
        config = {
            "target_price": 200.0,
            "stop_loss_price": 170.0,
            "max_hold_days": 60,
            "max_portfolio_drawdown_pct": 0.10,
        }
        gen = CloseSignalGenerator.from_config(config)
        assert gen.target_price == 200.0
        assert gen.stop_loss_price == 170.0
        assert gen.max_hold_days == 60
        assert gen.max_portfolio_drawdown_pct == 0.10

    def test_defaults_on_missing_keys(self):
        gen = CloseSignalGenerator.from_config({})
        assert gen.max_hold_days == 90
        assert gen.max_portfolio_drawdown_pct == 0.15


# ---------- CloseSignal Structure ----------

class TestCloseSignalStructure:
    def test_serializable(self, generator, snapshot):
        signal = generator.check_target_approached(185.0, snapshot)
        d = signal.to_dict()
        assert "signal_id" in d
        assert "exit_type" in d
        assert "reason" in d
        assert "urgency" in d
        assert "supporting_data" in d
        assert d["exit_type"] == "Target Approached"


# ---------- EntryStateSnapshot ----------

class TestEntryStateSnapshot:
    def test_snapshot_serializable(self, snapshot):
        d = snapshot.to_dict()
        assert d["ticker"] == "AAPL"
        assert d["entry_price"] == 150.0
        assert d["target_price"] == 180.0
        assert d["stop_loss_price"] == 135.0
        assert "fundamental_metrics" in d
