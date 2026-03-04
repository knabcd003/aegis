"""
Historical Data Store — Parquet-based market data cache with look-ahead bias protection.
Downloads bulk data from Alpaca/FMP and stores as Parquet for fast, columnar access.
"""
import os
import sys
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.market_api import AlpacaClient, FMPClient

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "market")
PRICES_DIR = os.path.join(DATA_DIR, "prices")
FUNDAMENTALS_DIR = os.path.join(DATA_DIR, "fundamentals")


class HistoricalDataStore:
    """
    Manages Parquet-based historical market data.
    All read operations enforce look-ahead bias protection via as_of_date filtering.
    """

    def __init__(self):
        os.makedirs(PRICES_DIR, exist_ok=True)
        os.makedirs(FUNDAMENTALS_DIR, exist_ok=True)

    # ── Download & Persist ──────────────────────────────────────────────

    def download_historical_data(
        self, tickers: List[str], start_date: str, end_date: str
    ) -> Dict[str, bool]:
        """
        Bulk downloads OHLCV price data and fundamental snapshots from Alpaca/FMP.
        Stores each ticker as a separate Parquet file.
        Returns a dict of {ticker: success_bool}.
        """
        alpaca = AlpacaClient()
        fmp = FMPClient()
        results = {}

        for ticker in tickers:
            try:
                # ── Prices ──
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                days = (end_dt - start_dt).days + 30  # buffer for SMA lookback

                prices = alpaca.get_historical_prices(ticker, days=days)
                if prices:
                    df_prices = pd.DataFrame(prices)
                    df_prices["date"] = pd.to_datetime(df_prices["date"])
                    # Filter to requested range
                    df_prices = df_prices[
                        (df_prices["date"] >= start_date) & (df_prices["date"] <= end_date)
                    ]
                    df_prices = df_prices.sort_values("date").reset_index(drop=True)
                    pq.write_table(
                        pa.Table.from_pandas(df_prices),
                        os.path.join(PRICES_DIR, f"{ticker}.parquet"),
                    )

                # ── Fundamentals (snapshot per quarter) ──
                metrics = fmp.get_company_metrics(ticker)
                if metrics:
                    df_fund = pd.DataFrame([{
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "pe_ratio": metrics.get("pe_ratio"),
                        "pb_ratio": metrics.get("pb_ratio"),
                        "roe": metrics.get("roe"),
                    }])
                    fund_path = os.path.join(FUNDAMENTALS_DIR, f"{ticker}.parquet")
                    if os.path.exists(fund_path):
                        existing = pq.read_table(fund_path).to_pandas()
                        df_fund = pd.concat([existing, df_fund]).drop_duplicates(
                            subset=["date"], keep="last"
                        )
                    pq.write_table(
                        pa.Table.from_pandas(df_fund),
                        fund_path,
                    )

                results[ticker] = True
                print(f"[DataStore] Downloaded {ticker}: {len(prices)} price bars")

            except Exception as e:
                print(f"[DataStore] Failed to download {ticker}: {e}")
                results[ticker] = False

        return results

    # ── Read with Look-Ahead Bias Protection ────────────────────────────

    def get_prices(
        self, ticker: str, as_of_date: str, lookback_days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Returns price data for a ticker, only up to as_of_date (inclusive).
        Prevents look-ahead bias by never returning future data.
        """
        path = os.path.join(PRICES_DIR, f"{ticker}.parquet")
        if not os.path.exists(path):
            return []

        df = pq.read_table(path).to_pandas()
        df["date"] = pd.to_datetime(df["date"])
        as_of = pd.to_datetime(as_of_date)

        # Only data up to as_of_date
        df = df[df["date"] <= as_of]

        # Trim to lookback window
        if lookback_days:
            cutoff = as_of - timedelta(days=lookback_days)
            df = df[df["date"] >= cutoff]

        df = df.sort_values("date")
        return [
            {"date": row["date"].strftime("%Y-%m-%d"), "close": float(row["close"]), "volume": int(row["volume"])}
            for _, row in df.iterrows()
        ]

    def get_fundamentals(self, ticker: str, as_of_date: str) -> Dict[str, Any]:
        """
        Returns the most recent fundamental snapshot on or before as_of_date.
        """
        path = os.path.join(FUNDAMENTALS_DIR, f"{ticker}.parquet")
        if not os.path.exists(path):
            return {}

        df = pq.read_table(path).to_pandas()
        df["date"] = pd.to_datetime(df["date"])
        df = df[df["date"] <= pd.to_datetime(as_of_date)]

        if df.empty:
            return {}

        latest = df.sort_values("date").iloc[-1]
        return {
            "pe_ratio": latest.get("pe_ratio"),
            "pb_ratio": latest.get("pb_ratio"),
            "roe": latest.get("roe"),
        }

    # ── Introspection ───────────────────────────────────────────────────

    def list_available_tickers(self) -> List[str]:
        """Lists all tickers with downloaded price data."""
        files = [f.replace(".parquet", "") for f in os.listdir(PRICES_DIR) if f.endswith(".parquet")]
        return sorted(files)

    def get_date_range(self, ticker: str) -> Optional[Dict[str, str]]:
        """Returns the min/max dates available for a ticker."""
        path = os.path.join(PRICES_DIR, f"{ticker}.parquet")
        if not os.path.exists(path):
            return None

        df = pq.read_table(path).to_pandas()
        df["date"] = pd.to_datetime(df["date"])
        return {
            "start": df["date"].min().strftime("%Y-%m-%d"),
            "end": df["date"].max().strftime("%Y-%m-%d"),
            "trading_days": len(df),
        }
