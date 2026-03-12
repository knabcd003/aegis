"""
Mirror Portfolio Tracker (Phase 4)
Tracks the counterfactual state of a Sentinel's portfolio assuming 100% acceptance
of all generated Signal Cards. Used for gap analysis to quantify human override cost/benefit.
"""
from typing import Dict, Any, List
from datetime import datetime
import pandas as pd

class MirrorPosition:
    def __init__(self, ticker: str, entry_price: float, quantity: int, decision: str):
        self.ticker = ticker
        self.entry_price = entry_price
        self.quantity = quantity
        self.decision = decision
        self.current_price = entry_price

    @property
    def value(self) -> float:
        return self.quantity * self.current_price

    @property
    def return_pct(self) -> float:
        return (self.current_price - self.entry_price) / self.entry_price

class MirrorPortfolio:
    """A purely counterfactual portfolio tracking Sentinel's unadulterated signals."""
    def __init__(self, initial_cash: float = 100000.0):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions: Dict[str, MirrorPosition] = {}
        self.nav_history: List[Dict[str, Any]] = []

    @property
    def nav(self) -> float:
        return self.cash + sum(p.value for p in self.positions.values())

    def record_nav(self, current_date: datetime):
        self.nav_history.append({
            "date": current_date.isoformat(),
            "nav": self.nav
        })

class CounterfactualTracker:
    """
    Maintains the Mirror Portfolio and calculates the Human Override Gap.
    """
    def __init__(self, sentinel_id: str, initial_cash: float = 100000.0):
        self.sentinel_id = sentinel_id
        # The AI's pure vision
        self.mirror = MirrorPortfolio(initial_cash)
        
        # We also need a reference to the actual human-modified nav for gap analysis
        self._actual_nav = initial_cash
        self._actual_nav_history: List[Dict[str, Any]] = []

    def handle_signal_resolution(self, ticker: str, decision: str, action: str, 
                                 execution_price: float, quantity: int, current_date: datetime):
        """
        Processes a signal regardless of whether the user accepted or declined it.
        The Mirror ALWAYS executes the AI's signal.
        """
        # MOCK Execution logic for the mirror
        if decision == "BUY":
            cost = execution_price * quantity
            if self.mirror.cash >= cost:
                self.mirror.cash -= cost
                if ticker in self.mirror.positions:
                    # Simple average cost for mock
                    p = self.mirror.positions[ticker]
                    total_val = (p.quantity * p.entry_price) + cost
                    p.quantity += quantity
                    p.entry_price = total_val / p.quantity
                    p.current_price = execution_price
                else:
                    self.mirror.positions[ticker] = MirrorPosition(ticker, execution_price, quantity, decision)
                    
        elif decision == "SELL":
            if ticker in self.mirror.positions:
                p = self.mirror.positions[ticker]
                revenue = execution_price * min(quantity, p.quantity)
                self.mirror.cash += revenue
                p.quantity -= min(quantity, p.quantity)
                p.current_price = execution_price
                if p.quantity == 0:
                    del self.mirror.positions[ticker]

        # Record snapshot
        self.mirror.record_nav(current_date)

    def sync_actual_nav(self, actual_nav: float, current_date: datetime):
        """Called by SentinelStateManager to update the user's actual NAV over time."""
        self._actual_nav = actual_nav
        self._actual_nav_history.append({
            "date": current_date.isoformat(),
            "nav": actual_nav
        })

    def get_gap_analysis(self) -> Dict[str, Any]:
        """Calculates the cost/benefit of user overrides (DECLINEd cards)."""
        mirror_nav = self.mirror.nav
        
        # Absolute gap in dollars
        absolute_gap = self._actual_nav - mirror_nav
        
        # Returns
        mirror_return = (mirror_nav - self.mirror.initial_cash) / self.mirror.initial_cash
        actual_return = (self._actual_nav - self.mirror.initial_cash) / self.mirror.initial_cash
        
        # Positive gap means human outperformed AI. Negative means overriding cost money.
        return {
            "sentinel_id": self.sentinel_id,
            "actual_nav": self._actual_nav,
            "mirror_nav": mirror_nav,
            "absolute_gap": absolute_gap,
            "actual_return_pct": actual_return,
            "mirror_return_pct": mirror_return,
            "human_outperformance": actual_return > mirror_return
        }
