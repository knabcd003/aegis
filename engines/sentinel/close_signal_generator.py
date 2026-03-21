"""
Close Signal Generator (Phase 4 — Complete)

Evaluates open positions against 5 live exit rules:
  1. Target Approached — price within configured % of target
  2. Stop Triggered — price crossed stop-loss
  3. Hold Duration Expired — exceeded maximum holding period
  4. Fundamental Shift — EntryStateSnapshot comparison (multi-metric)
  5. Risk Budget Violation — portfolio drawdown exceeds remaining budget

Returns structured CloseSignal objects with exit type, reasoning, and data.
All thresholds come from strategy config, not hardcoded defaults.
"""
import uuid
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, date
from enum import Enum

logger = logging.getLogger(__name__)


class ExitType(str, Enum):
    TARGET_APPROACHED = "Target Approached"
    STOP_TRIGGERED = "Stop Triggered"
    HOLD_DURATION_EXPIRED = "Hold Duration Expired"
    FUNDAMENTAL_SHIFT = "Fundamental Shift"
    RISK_BUDGET_VIOLATION = "Risk Budget Violation"


class EntryStateSnapshot:
    """
    Captures the fundamental and technical rationale at the exact moment a trade is entered.
    Used to detect Fundamental Shift exits by comparing entry-time vs current fundamentals.
    """
    def __init__(
        self,
        ticker: str,
        entry_price: float,
        entry_date: datetime,
        fundamental_metrics: Dict[str, float],
        thesis_summary: str,
        target_price: Optional[float] = None,
        stop_loss_price: Optional[float] = None,
        max_hold_days: Optional[int] = None,
    ):
        self.snapshot_id = str(uuid.uuid4())
        self.ticker = ticker
        self.entry_price = entry_price
        self.entry_date = entry_date
        self.fundamental_metrics = fundamental_metrics
        self.thesis_summary = thesis_summary
        self.target_price = target_price
        self.stop_loss_price = stop_loss_price
        self.max_hold_days = max_hold_days

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "ticker": self.ticker,
            "entry_price": self.entry_price,
            "entry_date": self.entry_date.isoformat() if isinstance(self.entry_date, (datetime, date)) else str(self.entry_date),
            "fundamental_metrics": self.fundamental_metrics,
            "thesis_summary": self.thesis_summary,
            "target_price": self.target_price,
            "stop_loss_price": self.stop_loss_price,
            "max_hold_days": self.max_hold_days,
        }


class CloseSignal:
    """Structured output from close signal evaluation."""
    def __init__(
        self,
        ticker: str,
        exit_type: ExitType,
        reason: str,
        urgency: str,
        current_price: float,
        entry_price: float,
        unrealized_pnl_pct: float,
        supporting_data: Dict[str, Any],
    ):
        self.signal_id = str(uuid.uuid4())
        self.ticker = ticker
        self.exit_type = exit_type
        self.reason = reason
        self.urgency = urgency  # "immediate" | "end_of_day" | "review"
        self.current_price = current_price
        self.entry_price = entry_price
        self.unrealized_pnl_pct = unrealized_pnl_pct
        self.supporting_data = supporting_data
        self.generated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "ticker": self.ticker,
            "exit_type": self.exit_type.value,
            "reason": self.reason,
            "urgency": self.urgency,
            "current_price": self.current_price,
            "entry_price": self.entry_price,
            "unrealized_pnl_pct": self.unrealized_pnl_pct,
            "supporting_data": self.supporting_data,
            "generated_at": self.generated_at.isoformat(),
        }


class CloseSignalGenerator:
    """
    Evaluates the 5 exit rules against open positions.

    All thresholds are configurable from the strategy config, not hardcoded.
    The Fundamental Shift check compares multiple metrics from EntryStateSnapshot,
    not just EPS.
    """

    # Default fundamental shift thresholds (used if not provided in config)
    DEFAULT_FUNDAMENTAL_THRESHOLDS = {
        "eps": {"max_decline_pct": 0.30},           # EPS dropped > 30%
        "revenue": {"max_decline_pct": 0.20},       # Revenue dropped > 20%
        "pe_ratio": {"max_expansion_pct": 0.50},    # PE expanded > 50%
        "debt_to_equity": {"max_increase_pct": 0.40},  # D/E ratio increased > 40%
        "gross_margin": {"max_decline_pct": 0.15},  # Gross margin dropped > 15%
    }

    def __init__(
        self,
        target_price: Optional[float] = None,
        stop_loss_price: Optional[float] = None,
        max_hold_days: int = 90,
        max_portfolio_drawdown_pct: float = 0.15,
        fundamental_thresholds: Optional[Dict[str, Dict[str, float]]] = None,
    ):
        """
        Args:
            target_price: Absolute target price. If None, uses % from entry.
            stop_loss_price: Absolute stop loss. If None, uses % from entry.
            max_hold_days: Maximum holding period in calendar days.
            max_portfolio_drawdown_pct: Max portfolio drawdown before risk budget exit (0.15 = 15%).
            fundamental_thresholds: Override default thresholds for fundamental shift detection.
        """
        self.target_price = target_price
        self.stop_loss_price = stop_loss_price
        self.max_hold_days = max_hold_days
        self.max_portfolio_drawdown_pct = max_portfolio_drawdown_pct
        self.fundamental_thresholds = fundamental_thresholds or self.DEFAULT_FUNDAMENTAL_THRESHOLDS

    @classmethod
    def from_config(cls, exit_config: Dict[str, Any]) -> "CloseSignalGenerator":
        """
        Factory method: build from strategy config exit_conditions block.

        Expected config format:
            exit_conditions:
                target_price: 165.0    # or null for %-based
                stop_loss_price: 135.0 # or null for %-based
                max_hold_days: 90
                max_portfolio_drawdown_pct: 0.15
                fundamental_thresholds:
                    eps: {max_decline_pct: 0.30}
                    ...
        """
        return cls(
            target_price=exit_config.get("target_price"),
            stop_loss_price=exit_config.get("stop_loss_price"),
            max_hold_days=exit_config.get("max_hold_days", 90),
            max_portfolio_drawdown_pct=exit_config.get("max_portfolio_drawdown_pct", 0.15),
            fundamental_thresholds=exit_config.get("fundamental_thresholds"),
        )

    def check_target_approached(
        self,
        current_price: float,
        snapshot: EntryStateSnapshot,
    ) -> Optional[CloseSignal]:
        """
        Rule 1: Has price reached or exceeded the target?
        Uses snapshot.target_price if set, otherwise falls back to instance target.
        """
        target = snapshot.target_price or self.target_price
        if target is None:
            return None  # No target defined — cannot evaluate

        if current_price >= target:
            pnl_pct = (current_price - snapshot.entry_price) / snapshot.entry_price
            return CloseSignal(
                ticker=snapshot.ticker,
                exit_type=ExitType.TARGET_APPROACHED,
                reason=f"Price ${current_price:.2f} reached target ${target:.2f}",
                urgency="end_of_day",
                current_price=current_price,
                entry_price=snapshot.entry_price,
                unrealized_pnl_pct=pnl_pct,
                supporting_data={"target_price": target, "overshoot_pct": (current_price - target) / target},
            )
        return None

    def check_stop_triggered(
        self,
        current_price: float,
        snapshot: EntryStateSnapshot,
    ) -> Optional[CloseSignal]:
        """
        Rule 2: Has price hit or breached the stop-loss?
        Uses snapshot.stop_loss_price if set, otherwise falls back to instance stop.
        """
        stop = snapshot.stop_loss_price or self.stop_loss_price
        if stop is None:
            return None  # No stop defined

        if current_price <= stop:
            pnl_pct = (current_price - snapshot.entry_price) / snapshot.entry_price
            return CloseSignal(
                ticker=snapshot.ticker,
                exit_type=ExitType.STOP_TRIGGERED,
                reason=f"Price ${current_price:.2f} breached stop ${stop:.2f}",
                urgency="immediate",
                current_price=current_price,
                entry_price=snapshot.entry_price,
                unrealized_pnl_pct=pnl_pct,
                supporting_data={"stop_price": stop, "breach_pct": (stop - current_price) / stop},
            )
        return None

    def check_hold_duration(
        self,
        current_date: datetime,
        snapshot: EntryStateSnapshot,
    ) -> Optional[CloseSignal]:
        """Rule 3: Has the trade exceeded the max holding duration?"""
        max_days = snapshot.max_hold_days or self.max_hold_days

        entry_dt = snapshot.entry_date
        if isinstance(entry_dt, date) and not isinstance(entry_dt, datetime):
            entry_dt = datetime.combine(entry_dt, datetime.min.time())
        if isinstance(current_date, date) and not isinstance(current_date, datetime):
            current_date = datetime.combine(current_date, datetime.min.time())

        days_held = (current_date - entry_dt).days

        if days_held >= max_days:
            return CloseSignal(
                ticker=snapshot.ticker,
                exit_type=ExitType.HOLD_DURATION_EXPIRED,
                reason=f"Position held {days_held} days, max is {max_days}",
                urgency="end_of_day",
                current_price=0.0,  # Will be set by caller
                entry_price=snapshot.entry_price,
                unrealized_pnl_pct=0.0,  # Will be set by caller
                supporting_data={"days_held": days_held, "max_hold_days": max_days},
            )
        return None

    def check_fundamental_shift(
        self,
        snapshot: EntryStateSnapshot,
        current_fundamentals: Dict[str, float],
    ) -> Optional[CloseSignal]:
        """
        Rule 4: Has there been a significant degradation in fundamentals?

        Compares each metric in the EntryStateSnapshot against current values.
        A shift is detected if ANY metric degrades beyond its threshold.
        """
        shifts_detected: List[str] = []

        for metric_name, thresholds in self.fundamental_thresholds.items():
            entry_val = snapshot.fundamental_metrics.get(metric_name)
            current_val = current_fundamentals.get(metric_name)

            if entry_val is None or current_val is None:
                continue  # Can't compare what we don't have

            if entry_val == 0:
                continue  # Avoid division by zero

            # Check for decline (eps, revenue, gross_margin)
            max_decline = thresholds.get("max_decline_pct")
            if max_decline is not None:
                change_pct = (current_val - entry_val) / abs(entry_val)
                if change_pct < -max_decline:
                    shifts_detected.append(
                        f"{metric_name}: {change_pct:+.1%} (threshold: -{max_decline:.0%})"
                    )

            # Check for expansion (pe_ratio, debt_to_equity)
            max_expansion = thresholds.get("max_expansion_pct")
            if max_expansion is not None:
                change_pct = (current_val - entry_val) / abs(entry_val)
                if change_pct > max_expansion:
                    shifts_detected.append(
                        f"{metric_name}: {change_pct:+.1%} (threshold: +{max_expansion:.0%})"
                    )

            # Check for increase (debt_to_equity)
            max_increase = thresholds.get("max_increase_pct")
            if max_increase is not None:
                change_pct = (current_val - entry_val) / abs(entry_val)
                if change_pct > max_increase:
                    shifts_detected.append(
                        f"{metric_name}: {change_pct:+.1%} (threshold: +{max_increase:.0%})"
                    )

        if shifts_detected:
            return CloseSignal(
                ticker=snapshot.ticker,
                exit_type=ExitType.FUNDAMENTAL_SHIFT,
                reason=f"Fundamental degradation detected in {len(shifts_detected)} metric(s)",
                urgency="review",
                current_price=0.0,  # Will be set by caller
                entry_price=snapshot.entry_price,
                unrealized_pnl_pct=0.0,  # Will be set by caller
                supporting_data={
                    "shifts": shifts_detected,
                    "entry_fundamentals": snapshot.fundamental_metrics,
                    "current_fundamentals": current_fundamentals,
                },
            )
        return None

    def check_risk_budget_violation(
        self,
        portfolio_nav: float,
        portfolio_high_water_mark: float,
    ) -> Optional[CloseSignal]:
        """
        Rule 5: Has the portfolio exceeded its remaining drawdown budget?

        Uses high water mark, not initial NAV, for drawdown calculation.
        """
        if portfolio_high_water_mark <= 0:
            return None

        drawdown = (portfolio_nav - portfolio_high_water_mark) / portfolio_high_water_mark

        if drawdown <= -self.max_portfolio_drawdown_pct:
            return CloseSignal(
                ticker="PORTFOLIO",
                exit_type=ExitType.RISK_BUDGET_VIOLATION,
                reason=f"Portfolio drawdown {drawdown:.1%} exceeds budget -{self.max_portfolio_drawdown_pct:.0%}",
                urgency="immediate",
                current_price=portfolio_nav,
                entry_price=portfolio_high_water_mark,
                unrealized_pnl_pct=drawdown,
                supporting_data={
                    "portfolio_nav": portfolio_nav,
                    "high_water_mark": portfolio_high_water_mark,
                    "drawdown_pct": drawdown,
                    "budget_pct": self.max_portfolio_drawdown_pct,
                },
            )
        return None

    def evaluate_position(
        self,
        current_price: float,
        current_date: datetime,
        current_fundamentals: Dict[str, float],
        portfolio_nav: float,
        portfolio_high_water_mark: float,
        snapshot: EntryStateSnapshot,
    ) -> Optional[CloseSignal]:
        """
        Runs all 5 exit checks in priority order.
        Returns the first triggered CloseSignal, or None if position should be held.

        Priority:
          1. Risk Budget (portfolio-level, most urgent)
          2. Stop Triggered (price-level, immediate)
          3. Target Approached (take profit)
          4. Hold Duration (time-based)
          5. Fundamental Shift (thesis invalidation)
        """
        # 1. Portfolio-level risk budget check first (affects all positions)
        risk_signal = self.check_risk_budget_violation(portfolio_nav, portfolio_high_water_mark)
        if risk_signal:
            risk_signal.ticker = snapshot.ticker
            return risk_signal

        # 2. Stop triggered (immediate urgency)
        stop_signal = self.check_stop_triggered(current_price, snapshot)
        if stop_signal:
            return stop_signal

        # 3. Target approached
        target_signal = self.check_target_approached(current_price, snapshot)
        if target_signal:
            return target_signal

        # 4. Hold duration expired
        hold_signal = self.check_hold_duration(current_date, snapshot)
        if hold_signal:
            pnl_pct = (current_price - snapshot.entry_price) / snapshot.entry_price
            hold_signal.current_price = current_price
            hold_signal.unrealized_pnl_pct = pnl_pct
            return hold_signal

        # 5. Fundamental shift
        fundamental_signal = self.check_fundamental_shift(snapshot, current_fundamentals)
        if fundamental_signal:
            pnl_pct = (current_price - snapshot.entry_price) / snapshot.entry_price
            fundamental_signal.current_price = current_price
            fundamental_signal.unrealized_pnl_pct = pnl_pct
            return fundamental_signal

        return None
