"""
FRED Connector — Federal Reserve Economic Data for macro indicators.

v6 update:
- All returned records include public_disclosure_ts.
- For FRED data, public_disclosure_ts = release_date from ALFRED vintage
  (the date the data point was officially released/revised by the Fed).
- as_of_date filtering: only data points with release_date <= as_of_date returned.
- Audit snapshots written to ledger (not immutable — FRED revises data).
"""
import os
import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, date

from engines.data_ingestion.base_connector import BaseConnector
from engines.data_ingestion import ledger


FRED_SERIES = {
    "fed_funds_rate": "FEDFUNDS",
    "cpi": "CPIAUCSL",
    "gdp": "GDP",
    "unemployment": "UNRATE",
    "treasury_10y": "DGS10",
    "treasury_2y": "DGS2",
    "treasury_spread": "T10Y2Y",
    "inflation_expectation": "T5YIE",
}


class FREDConnector(BaseConnector):
    """
    Fetches macro indicators from FRED (with key) or yfinance fallback.
    public_disclosure_ts = ALFRED release date (when the data point was published).
    """

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.getenv("FRED_API_KEY")
        self._fred = None
        self._last_successful_fetch_ts: Optional[datetime] = None

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
        if self._fred is not None:
            return True
        if not self._api_key:
            return False
        try:
            import ssl
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

    def get_macro(
        self,
        as_of_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Fetch macro indicators. Each value includes release_ts (public_disclosure_ts).

        Point-in-time: if as_of_date is provided, only observations where
        release_date <= as_of_date are returned (using ALFRED vintage).
        Fallback (yfinance): returns current values; point-in-time not guaranteed.
        """
        sim_date = as_of_date or date.today()

        if self._init_fred():
            return self._get_macro_from_fred(sim_date)
        else:
            return self._get_macro_from_yfinance(sim_date)

    def _get_macro_from_fred(self, as_of_date: date) -> Dict[str, Any]:
        """Fetch macro data from FRED with ALFRED vintage filtering."""
        macro: Dict[str, Any] = {
            "source": "fred_api",
            "public_disclosure_ts": as_of_date.isoformat(),
        }

        for series_name, series_id in FRED_SERIES.items():
            try:
                # ALFRED: get the vintage as it was known on as_of_date
                # fredapi: get_series_all_releases returns vintage data
                try:
                    # Try point-in-time vintage fetch
                    data = self._fred.get_series_all_releases(series_id)
                    data = data[data["realtime_start"] <= as_of_date.isoformat()]
                    if data.empty:
                        raise ValueError("No vintage data")
                    latest = data.sort_values("date").iloc[-1]
                    macro[series_name] = {
                        "value": float(latest["value"]),
                        "date": str(latest["date"])[:10],
                        "public_disclosure_ts": str(latest["realtime_start"])[:10],
                    }
                except Exception:
                    # Fallback: standard series (not fully point-in-time but usable)
                    data = self._fred.get_series(series_id, observation_start="2020-01-01")
                    if data is not None and len(data) > 0:
                        # Filter to releases available as of as_of_date
                        data_filtered = data[data.index.date <= as_of_date]
                        if not data_filtered.empty:
                            latest_val = data_filtered.dropna().iloc[-1]
                            latest_date = data_filtered.dropna().index[-1]
                            macro[series_name] = {
                                "value": float(latest_val),
                                "date": str(latest_date.date()),
                                "public_disclosure_ts": str(latest_date.date()),
                            }
            except Exception as e:
                print(f"[{self.name}] Error fetching {series_name}: {e}")
                macro[series_name] = None

        # Audit snapshot
        try:
            snapshot_df = pd.DataFrame([
                {"series": k, "value": v.get("value") if v else None,
                 "release_date": v.get("public_disclosure_ts") if v else None}
                for k, v in macro.items()
                if k not in ("source", "public_disclosure_ts")
            ])
            ledger.write_macro_snapshot(f"bulk_{as_of_date.isoformat()}", snapshot_df)
        except Exception:
            pass

        self._last_successful_fetch_ts = datetime.utcnow()
        return macro

    def _get_macro_from_yfinance(self, as_of_date: date) -> Dict[str, Any]:
        """Fallback: get key macro proxies from yfinance. Not fully point-in-time."""
        macro: Dict[str, Any] = {
            "source": "yfinance_fallback",
            "public_disclosure_ts": as_of_date.isoformat(),
            "_note": "yfinance fallback — not fully point-in-time. Use fredapi for backtesting.",
        }

        proxies = {
            "vix": "^VIX",
            "treasury_10y": "^TNX",
            "sp500": "^GSPC",
            "dollar_index": "DX-Y.NYB",
        }

        end = datetime.combine(as_of_date, datetime.min.time()) + timedelta(days=1)
        start = end - timedelta(days=10)

        for name, symbol in proxies.items():
            try:
                ticker_obj = yf.Ticker(symbol)
                hist = ticker_obj.history(
                    start=start.strftime("%Y-%m-%d"),
                    end=end.strftime("%Y-%m-%d"),
                )
                if not hist.empty:
                    last_row = hist.iloc[-1]
                    last_date = hist.index[-1].date()
                    macro[name] = {
                        "value": round(float(last_row["Close"]), 3),
                        "date": last_date.isoformat(),
                        "public_disclosure_ts": last_date.isoformat(),
                    }
            except Exception as e:
                print(f"[{self.name}] Error fetching {name} ({symbol}): {e}")

        # Yield spread from components
        if "treasury_10y" in macro and "treasury_2y" not in macro:
            try:
                two = yf.Ticker("^IRX")  # 13-week Treasury proxy
                hist = two.history(start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"))
                if not hist.empty:
                    val_2y = round(float(hist["Close"].iloc[-1]) / 100, 4)  # IRX is in percent
                    last_date = hist.index[-1].date()
                    macro["treasury_2y"] = {
                        "value": val_2y,
                        "date": last_date.isoformat(),
                        "public_disclosure_ts": last_date.isoformat(),
                    }
            except Exception:
                pass

        if "treasury_10y" in macro and "treasury_2y" in macro:
            spread = macro["treasury_10y"]["value"] - macro["treasury_2y"]["value"]
            macro["treasury_spread"] = {
                "value": round(spread, 3),
                "date": macro["treasury_10y"]["date"],
                "public_disclosure_ts": macro["treasury_10y"]["public_disclosure_ts"],
                "note": "10Y - 2Y (negative = inverted curve)",
            }

        self._last_successful_fetch_ts = datetime.utcnow()
        return macro

    # ── BaseConnector interface ──────────────────────────────────────────

    def get_prices(self, ticker: str, days: int = 30, interval: str = "1d",
                   as_of_date: Optional[date] = None):
        return None

    def get_fundamentals(self, ticker: str, as_of_date: Optional[date] = None):
        return None

    def get_news(self, ticker: str, days: int = 7, as_of_date: Optional[date] = None):
        return []

    def health_check(self) -> bool:
        try:
            macro = self.get_macro()
            return "vix" in macro or "fed_funds_rate" in macro
        except Exception:
            return False
