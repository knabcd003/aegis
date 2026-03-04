"""
FRED Connector — Federal Reserve Economic Data for macro indicators.

Provides: Fed funds rate, CPI, GDP, unemployment, 10Y treasury yield,
Treasury yield spread (10Y-2Y), VIX.

Works in two modes:
1. With FRED API key (fredapi) — full access to all FRED series
2. Without key — uses yfinance to get VIX and treasury ETF proxies
"""
import os
import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from engines.data_ingestion.base_connector import BaseConnector


# Key FRED series IDs
FRED_SERIES = {
    "fed_funds_rate": "FEDFUNDS",        # Federal Funds Effective Rate
    "cpi": "CPIAUCSL",                    # Consumer Price Index
    "gdp": "GDP",                          # Gross Domestic Product
    "unemployment": "UNRATE",              # Unemployment Rate
    "treasury_10y": "DGS10",              # 10-Year Treasury Constant Maturity
    "treasury_2y": "DGS2",                # 2-Year Treasury Constant Maturity
    "treasury_spread": "T10Y2Y",          # 10Y-2Y Spread
    "inflation_expectation": "T5YIE",      # 5-Year Breakeven Inflation
}


class FREDConnector(BaseConnector):
    """
    Fetches macro indicators from FRED (with key) or yfinance fallback.
    """

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.getenv("FRED_API_KEY")
        self._fred = None

    @property
    def name(self) -> str:
        return "fred"

    @property
    def provides_prices(self) -> bool:
        return False

    @property
    def provides_fundamentals(self) -> bool:
        return False

    @property
    def provides_news(self) -> bool:
        return False

    def _init_fred(self) -> bool:
        """
        Try to initialize fredapi. Returns True if successful.
        Falls back to yfinance-based macro data if no key/package.
        """
        if self._fred is not None:
            return True

        if not self._api_key:
            return False

        try:
            import ssl
            # macOS SSL fix for urllib used by fredapi
            try:
                _create_unverified_https_context = ssl._create_unverified_context
            except AttributeError:
                pass
            else:
                ssl._create_default_https_context = _create_unverified_https_context

            from fredapi import Fred
            self._fred = Fred(api_key=self._api_key)
            return True
        except ImportError:
            print(f"[{self.name}] fredapi not installed, using yfinance fallback")
            return False
        except Exception as e:
            print(f"[{self.name}] Error initializing FRED: {e}")
            return False

    def get_macro(self) -> Dict[str, Any]:
        """
        Fetch current macro indicators.
        Uses FRED API if available, otherwise falls back to yfinance.
        """
        if self._init_fred():
            return self._get_macro_from_fred()
        else:
            return self._get_macro_from_yfinance()

    def _get_macro_from_fred(self) -> Dict[str, Any]:
        """Fetch macro data directly from FRED API."""
        macro = {"source": "fred_api"}

        for name, series_id in FRED_SERIES.items():
            try:
                data = self._fred.get_series(series_id, observation_start="2020-01-01")
                if data is not None and len(data) > 0:
                    latest = data.dropna().iloc[-1]
                    macro[name] = {
                        "value": float(latest),
                        "date": str(data.dropna().index[-1].date()),
                    }
            except Exception as e:
                print(f"[{self.name}] Error fetching {name}: {e}")
                macro[name] = None

        return macro

    def _get_macro_from_yfinance(self) -> Dict[str, Any]:
        """
        Fallback: get key macro proxies from yfinance.
        Uses VIX index, treasury yield ETFs, and market indices.
        """
        macro = {"source": "yfinance_fallback"}

        # VIX (fear gauge)
        try:
            vix = yf.Ticker("^VIX")
            hist = vix.history(period="5d")
            if not hist.empty:
                macro["vix"] = {
                    "value": round(float(hist["Close"].iloc[-1]), 2),
                    "date": str(hist.index[-1].date()),
                }
        except Exception as e:
            print(f"[{self.name}] Error fetching VIX: {e}")

        # 10-Year Treasury Yield (^TNX)
        try:
            tnx = yf.Ticker("^TNX")
            hist = tnx.history(period="5d")
            if not hist.empty:
                macro["treasury_10y"] = {
                    "value": round(float(hist["Close"].iloc[-1]), 3),
                    "date": str(hist.index[-1].date()),
                }
        except Exception as e:
            print(f"[{self.name}] Error fetching 10Y yield: {e}")

        # 2-Year Treasury Yield (^IRX is 13-week, use 2Y via TWO)
        try:
            two = yf.Ticker("^TWO")
            hist = two.history(period="5d")
            if not hist.empty:
                macro["treasury_2y"] = {
                    "value": round(float(hist["Close"].iloc[-1]), 3),
                    "date": str(hist.index[-1].date()),
                }
        except Exception as e:
            print(f"[{self.name}] Error fetching 2Y yield: {e}")

        # Compute yield spread if we have both
        if "treasury_10y" in macro and "treasury_2y" in macro:
            spread = macro["treasury_10y"]["value"] - macro["treasury_2y"]["value"]
            macro["treasury_spread"] = {
                "value": round(spread, 3),
                "date": macro["treasury_10y"]["date"],
                "note": "10Y - 2Y yield (negative = inverted curve)"
            }

        # S&P 500 (market baseline)
        try:
            spy = yf.Ticker("^GSPC")
            hist = spy.history(period="5d")
            if not hist.empty:
                macro["sp500"] = {
                    "value": round(float(hist["Close"].iloc[-1]), 2),
                    "date": str(hist.index[-1].date()),
                }
        except Exception as e:
            print(f"[{self.name}] Error fetching S&P 500: {e}")

        # Dollar Index (DXY)
        try:
            dxy = yf.Ticker("DX-Y.NYB")
            hist = dxy.history(period="5d")
            if not hist.empty:
                macro["dollar_index"] = {
                    "value": round(float(hist["Close"].iloc[-1]), 2),
                    "date": str(hist.index[-1].date()),
                }
        except Exception as e:
            print(f"[{self.name}] Error fetching DXY: {e}")

        return macro

    def get_vix_history(self, days: int = 90) -> Optional[pd.DataFrame]:
        """
        Get VIX time-series for regime detection models.
        Always uses yfinance regardless of FRED key.
        """
        try:
            vix = yf.Ticker("^VIX")
            end = datetime.now()
            start = end - timedelta(days=days)
            df = vix.history(start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"))

            if df.empty:
                return None

            df = df.reset_index()
            df = df.rename(columns={"Date": "date", "Close": "close", "Volume": "volume"})
            df = df[["date", "close"]].copy()
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
            return df

        except Exception as e:
            print(f"[{self.name}] Error fetching VIX history: {e}")
            return None

    # ── BaseConnector interface ──────────────────────────────────────────

    def get_prices(self, ticker: str, days: int = 30):
        return None

    def get_fundamentals(self, ticker: str):
        return None

    def get_news(self, ticker: str, days: int = 7):
        return []

    def health_check(self) -> bool:
        """Check if macro data is retrievable."""
        try:
            macro = self.get_macro()
            return "vix" in macro or "fed_funds_rate" in macro
        except Exception:
            return False
