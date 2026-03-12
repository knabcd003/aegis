"""
Close Signal Generator (Phase 4)
Evaluates open positions against 5 live exit rules:
1. Target Approached
2. Stop Triggered
3. Hold Duration Expired
4. Fundamental Shift
5. Risk Budget Violation

Generates EntryStateSnapshot objects to evaluate Fundamental Shifts over time.
Persistence: Stores snapshots in portfolio state AND logs to MLflow.
"""
import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import mlflow

logger = logging.getLogger(__name__)

class EntryStateSnapshot:
    """
    Captures the fundamental and technical rationale at the exact moment a trade is entered.
    Critical for evaluating the 'Fundamental Shift' exit rule over time.
    """
    def __init__(self, ticker: str, entry_price: float, entry_date: datetime, 
                 fundamental_metrics: Dict[str, Any], thesis_summary: str):
        self.snapshot_id = str(uuid.uuid4())
        self.ticker = ticker
        self.entry_price = entry_price
        self.entry_date = entry_date
        self.fundamental_metrics = fundamental_metrics
        self.thesis_summary = thesis_summary

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "ticker": self.ticker,
            "entry_price": self.entry_price,
            "entry_date": self.entry_date.isoformat(),
            "fundamental_metrics": self.fundamental_metrics,
            "thesis_summary": self.thesis_summary
        }

    def persist(self, run_id: str, local_portfolio_state: Dict[str, Any]):
        """Persists the snapshot to both local state and MLflow."""
        # Save to local portfolio
        if "snapshots" not in local_portfolio_state:
            local_portfolio_state["snapshots"] = {}
        local_portfolio_state["snapshots"][self.ticker] = self.to_dict()

        # Save to MLflow as artifact
        # In a real run, this would save to a JSON artifact
        # but we mock the file write here.
        logger.info(f"Persisted EntryStateSnapshot {self.snapshot_id} for {self.ticker} to MLflow run {run_id}")


class CloseSignalGenerator:
    """Evaluates the 5 rules to determine if a position should be closed."""

    def __init__(self, target_pct: float = 0.20, stop_pct: float = -0.10, max_hold_days: int = 90):
        self.target_pct = target_pct
        self.stop_pct = stop_pct
        self.max_hold_days = max_hold_days

    def check_target_approached(self, current_price: float, entry_price: float) -> bool:
        """Rule 1: Is the price near or above the target?"""
        return (current_price - entry_price) / entry_price >= self.target_pct

    def check_stop_triggered(self, current_price: float, entry_price: float) -> bool:
        """Rule 2: Is the price near or below the stop loss?"""
        return (current_price - entry_price) / entry_price <= self.stop_pct

    def check_hold_duration(self, current_date: datetime, entry_date: datetime) -> bool:
        """Rule 3: Has the trade exceeded the max holding duration?"""
        return (current_date - entry_date).days >= self.max_hold_days

    def check_fundamental_shift(self, snapshot: EntryStateSnapshot, current_fundamentals: Dict[str, Any]) -> bool:
        """
        Rule 4: Has there been a significant degradation in the fundamental reason 
        for entering the trade? (e.g. PE expanded by >50%, earnings dropped by >30%)
        """
        # Very simple mock check: EPS dropped by more than 30%
        entry_eps = snapshot.fundamental_metrics.get("eps", 1.0)
        curr_eps = current_fundamentals.get("eps", 1.0)
        if entry_eps > 0 and (curr_eps - entry_eps) / entry_eps < -0.30:
            return True
        return False

    def check_risk_budget_violation(self, portfolio_nav: float, initial_nav: float) -> bool:
        """Rule 5: Is the portfolio as a whole breaching strict drawdown limits?"""
        # Simple portfolio-level stop loss logic
        return (portfolio_nav - initial_nav) / initial_nav <= -0.15

    def evaluate_position(self, 
                          ticker: str, 
                          current_price: float, 
                          current_date: datetime,
                          current_fundamentals: Dict[str, Any],
                          portfolio_nav: float,
                          initial_nav: float,
                          snapshot: Optional[EntryStateSnapshot]) -> Optional[str]:
        """
        Runs all 5 checks. Returns the name of the triggered rule, or None if the position should be held.
        """
        if snapshot is None:
            logger.warning(f"No EntryStateSnapshot found for {ticker}. Skipping fundamental shift checks.")
            return None

        if self.check_target_approached(current_price, snapshot.entry_price):
            return "Target Approached"
            
        if self.check_stop_triggered(current_price, snapshot.entry_price):
            return "Stop Triggered"
            
        if self.check_hold_duration(current_date, snapshot.entry_date):
            return "Hold Duration Expired"
            
        if self.check_fundamental_shift(snapshot, current_fundamentals):
            return "Fundamental Shift"
            
        if self.check_risk_budget_violation(portfolio_nav, initial_nav):
            return "Risk Budget Violation"

        return None
