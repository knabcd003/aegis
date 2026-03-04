"""
Base Connector Interface — Abstract contract for all data source connectors.
Every connector (yfinance, FRED, Alpaca, etc.) implements this interface
so downstream systems never know or care where data came from.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
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
    def get_prices(self, ticker: str, days: int = 30, interval: str = "1d") -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV price data.
        interval: e.g., '1d', '1m', '5m', '1h'

        Returns DataFrame with columns: date, open, high, low, close, volume
        Sorted by date ascending. Returns None on failure.
        """
        ...

    @abstractmethod
    def get_fundamentals(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetch fundamental metrics.

        Returns dict with keys: pe_ratio, market_cap, eps, revenue,
        earnings_date, analyst_rating (or None for unavailable fields).
        """
        ...

    @abstractmethod
    def get_news(self, ticker: str, days: int = 7) -> List[Dict[str, Any]]:
        """
        Fetch recent news items.

        Returns list of dicts with keys: headline, date, source, url
        Sorted by date descending (newest first). Empty list on failure.
        """
        ...

    def health_check(self) -> bool:
        """Quick test that this connector can reach its data source."""
        try:
            result = self.get_prices("AAPL", days=5)
            return result is not None and len(result) > 0
        except Exception:
            return False
