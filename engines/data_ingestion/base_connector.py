"""
Base Connector Interface — Abstract contract for all data source connectors.

v6 update: all connector methods must return records with a `public_disclosure_ts`
field indicating when the data became publicly available. The simulation loop uses
this to enforce point-in-time discipline — no record with public_disclosure_ts >
simulation_date is ever used in a backtest decision.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime, date
import pandas as pd


class BaseConnector(ABC):
    """Abstract base class for all data connectors."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable connector name (e.g., 'yfinance', 'alpaca')."""
        ...

    @property
    @abstractmethod
    def provides_prices(self) -> bool:
        """Whether this connector can return price data."""
        ...

    @property
    @abstractmethod
    def provides_fundamentals(self) -> bool:
        """Whether this connector can return fundamental metrics."""
        ...

    @property
    @abstractmethod
    def provides_news(self) -> bool:
        """Whether this connector can return news data."""
        ...

    @abstractmethod
    def get_prices(
        self,
        ticker: str,
        days: int = 30,
        interval: str = "1d",
        as_of_date: Optional[date] = None,
    ) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV price data.

        Returns DataFrame with columns:
            date, open, high, low, close, volume, public_disclosure_ts

        public_disclosure_ts is the date the bar became public — for daily bars
        this equals the date of the bar itself.

        If as_of_date is provided, only rows where public_disclosure_ts <= as_of_date
        are returned. If None, returns all available data.

        Returns None on failure.
        """
        ...

    @abstractmethod
    def get_fundamentals(
        self,
        ticker: str,
        as_of_date: Optional[date] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch fundamental metrics.

        Every returned dict must include:
            public_disclosure_ts: date — when this data became publicly available

        Returns dict with keys: pe_ratio, market_cap, eps, revenue,
        earnings_date, analyst_rating, public_disclosure_ts (or None for failures).
        """
        ...

    @abstractmethod
    def get_news(
        self,
        ticker: str,
        days: int = 7,
        as_of_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent news items.

        Every returned dict must include:
            public_disclosure_ts: date — the article's published date

        Returns list of dicts sorted newest first. Empty list on failure.
        """
        ...

    @property
    def last_successful_fetch_ts(self) -> Optional[datetime]:
        """
        Timestamp of the most recent successful data fetch.
        Used by the Connector Health Monitor (Phase 4).
        Connectors should update _last_successful_fetch_ts on each successful call.
        """
        return getattr(self, "_last_successful_fetch_ts", None)

    def health_check(self) -> bool:
        """Quick test that this connector can reach its data source."""
        try:
            result = self.get_prices("AAPL", days=5)
            return result is not None and len(result) > 0
        except Exception:
            return False
