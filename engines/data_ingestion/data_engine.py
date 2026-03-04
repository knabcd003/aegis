"""
Data Ingestion Engine — Central data layer for the Aegis trading system.

All downstream systems (Quant, Analyst, Sentinel) call this engine.
It manages connectors, caches data to Parquet/JSON, and provides DuckDB queries.
No system ever imports yfinance/FRED/Alpaca directly.
"""
import os
import json
import time
import duckdb
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any, Type

from engines.data_ingestion.base_connector import BaseConnector


# ── Cache TTL defaults (seconds) ────────────────────────────────────────
CACHE_TTL = {
    "prices":        86400,    # 1 day
    "fundamentals":  604800,   # 1 week
    "financials":    604800,   # 1 week
    "options":       3600,     # 1 hour
    "insiders":      86400,    # 1 day
    "news":          3600,     # 1 hour
    "recommendations": 86400,  # 1 day
    "macro":         86400,    # 1 day
}


class DataEngine:
    """
    Central data access layer.

    Usage:
        engine = DataEngine()
        engine.register(YFinanceConnector(), priority=1)
        prices = engine.get_prices("AAPL", days=30)
    """

    def __init__(self, data_dir: str = "data"):
        self._connectors: List[Dict[str, Any]] = []   # [{connector, priority}]
        self._data_dir = Path(data_dir)
        self._db: Optional[duckdb.DuckDBPyConnection] = None

        # Create cache directories
        for subdir in ["prices", "fundamentals", "financials", "options",
                       "insiders", "news", "recommendations", "macro", "sentiment"]:
            (self._data_dir / subdir).mkdir(parents=True, exist_ok=True)

    # ── Connector Registry ───────────────────────────────────────────────

    def register(self, connector: BaseConnector, priority: int = 10) -> None:
        """Register a connector with a priority (lower = tried first)."""
        self._connectors.append({"connector": connector, "priority": priority})
        self._connectors.sort(key=lambda c: c["priority"])
        print(f"[engine] Registered {connector.name} (priority={priority})")

    def list_connectors(self) -> List[str]:
        """Return names of registered connectors in priority order."""
        return [c["connector"].name for c in self._connectors]

    def _get_connectors_for(self, capability: str) -> List[BaseConnector]:
        """Return connectors that provide a specific capability, in priority order."""
        cap_map = {
            "prices": "provides_prices",
            "fundamentals": "provides_fundamentals",
            "news": "provides_news",
        }
        attr = cap_map.get(capability)
        if attr:
            return [c["connector"] for c in self._connectors
                    if getattr(c["connector"], attr, False)]
        # For methods not in base interface, check if connector has the method
        return [c["connector"] for c in self._connectors
                if hasattr(c["connector"], f"get_{capability}")]

    # ── Cache Management ─────────────────────────────────────────────────

    def _cache_path(self, data_type: str, key: str, ext: str = "json") -> Path:
        """Build the cache file path."""
        return self._data_dir / data_type / f"{key}.{ext}"

    def _is_cache_fresh(self, path: Path, ttl_key: str, ttl_override: Optional[int] = None) -> bool:
        """Check if a cached file exists and is within TTL."""
        if not path.exists():
            return False
        age = time.time() - path.stat().st_mtime
        ttl = ttl_override if ttl_override is not None else CACHE_TTL.get(ttl_key, 86400)
        return age < ttl

    def _write_json_cache(self, path: Path, data: Any) -> None:
        """Write data to JSON cache."""
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def _read_json_cache(self, path: Path) -> Any:
        """Read data from JSON cache."""
        with open(path, "r") as f:
            return json.load(f)

    def _write_parquet_cache(self, path: Path, df: pd.DataFrame) -> None:
        """Write DataFrame to Parquet cache."""
        df.to_parquet(path, index=False)

    def _read_parquet_cache(self, path: Path) -> pd.DataFrame:
        """Read DataFrame from Parquet cache."""
        return pd.read_parquet(path)

    # ── Data Access Methods ──────────────────────────────────────────────

    def get_prices(self, ticker: str, days: int = 30, interval: str = "1d",
                   ttl_override: Optional[int] = None) -> Optional[pd.DataFrame]:
        """Fetch OHLCV prices — cache-first with fallback across connectors."""
        # Append interval to cache key so daily vs intraday are stored separately
        cache_key = ticker if interval == "1d" else f"{ticker}_{interval}"
        cache_path = self._cache_path("prices", cache_key, ext="parquet")

        # Check cache
        if self._is_cache_fresh(cache_path, "prices", ttl_override):
            df = self._read_parquet_cache(cache_path)
            print(f"[engine] Prices for {ticker} ({interval}): served from cache")
            return df

        # Try connectors in priority order
        for conn in self._get_connectors_for("prices"):
            try:
                df = conn.get_prices(ticker, days=days, interval=interval)
                if df is not None and not df.empty:
                    self._write_parquet_cache(cache_path, df)
                    print(f"[engine] Prices for {ticker} ({interval}): fetched from {conn.name}, cached to Parquet")
                    return df
            except Exception as e:
                print(f"[engine] {conn.name} failed for prices/{ticker} ({interval}): {e}")
                continue

        # Serve stale cache if all connectors fail
        if cache_path.exists():
            print(f"[engine] All connectors failed for prices/{ticker} ({interval}), serving stale cache")
            return self._read_parquet_cache(cache_path)

        return None

    def get_fundamentals(self, ticker: str,
                         ttl_override: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Fetch fundamental metrics — cache-first with fallback."""
        cache_path = self._cache_path("fundamentals", ticker)

        if self._is_cache_fresh(cache_path, "fundamentals", ttl_override):
            print(f"[engine] Fundamentals for {ticker}: served from cache")
            return self._read_json_cache(cache_path)

        for conn in self._get_connectors_for("fundamentals"):
            try:
                data = conn.get_fundamentals(ticker)
                if data:
                    self._write_json_cache(cache_path, data)
                    print(f"[engine] Fundamentals for {ticker}: fetched from {conn.name}, cached")
                    return data
            except Exception as e:
                print(f"[engine] {conn.name} failed for fundamentals/{ticker}: {e}")
                continue

        if cache_path.exists():
            print(f"[engine] All connectors failed, serving stale fundamentals for {ticker}")
            return self._read_json_cache(cache_path)

        return None

    def get_news(self, ticker: str, days: int = 7,
                 ttl_override: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch news headlines — cache-first with fallback."""
        cache_path = self._cache_path("news", ticker)

        if self._is_cache_fresh(cache_path, "news", ttl_override):
            print(f"[engine] News for {ticker}: served from cache")
            return self._read_json_cache(cache_path)

        for conn in self._get_connectors_for("news"):
            try:
                data = conn.get_news(ticker, days)
                if data:
                    self._write_json_cache(cache_path, data)
                    print(f"[engine] News for {ticker}: fetched from {conn.name}, cached")
                    return data
            except Exception as e:
                print(f"[engine] {conn.name} failed for news/{ticker}: {e}")
                continue

        if cache_path.exists():
            return self._read_json_cache(cache_path)

        return []

    def get_financials(self, ticker: str,
                       ttl_override: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Fetch financial statements — cache-first."""
        cache_path = self._cache_path("financials", ticker)

        if self._is_cache_fresh(cache_path, "financials", ttl_override):
            print(f"[engine] Financials for {ticker}: served from cache")
            return self._read_json_cache(cache_path)

        for conn in self._get_connectors_for("financials"):
            try:
                data = conn.get_financials(ticker)
                if data:
                    self._write_json_cache(cache_path, data)
                    print(f"[engine] Financials for {ticker}: fetched from {conn.name}, cached")
                    return data
            except Exception as e:
                print(f"[engine] {conn.name} failed for financials/{ticker}: {e}")
                continue

        if cache_path.exists():
            return self._read_json_cache(cache_path)
        return None

    def get_options(self, ticker: str,
                    ttl_override: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Fetch options chain — cache-first."""
        cache_path = self._cache_path("options", ticker)

        if self._is_cache_fresh(cache_path, "options", ttl_override):
            print(f"[engine] Options for {ticker}: served from cache")
            return self._read_json_cache(cache_path)

        for conn in self._get_connectors_for("options"):
            try:
                data = conn.get_options(ticker)
                if data:
                    self._write_json_cache(cache_path, data)
                    print(f"[engine] Options for {ticker}: fetched from {conn.name}, cached")
                    return data
            except Exception as e:
                print(f"[engine] {conn.name} failed for options/{ticker}: {e}")
                continue

        if cache_path.exists():
            return self._read_json_cache(cache_path)
        return None

    def get_insider_activity(self, ticker: str,
                             ttl_override: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Fetch insider + institutional activity — cache-first."""
        cache_path = self._cache_path("insiders", ticker)

        if self._is_cache_fresh(cache_path, "insiders", ttl_override):
            print(f"[engine] Insider activity for {ticker}: served from cache")
            return self._read_json_cache(cache_path)

        for conn in self._get_connectors_for("insider_activity"):
            try:
                data = conn.get_insider_activity(ticker)
                if data:
                    self._write_json_cache(cache_path, data)
                    print(f"[engine] Insider activity for {ticker}: fetched from {conn.name}, cached")
                    return data
            except Exception as e:
                print(f"[engine] {conn.name} failed for insiders/{ticker}: {e}")
                continue

        if cache_path.exists():
            return self._read_json_cache(cache_path)
        return None

    def get_recommendations(self, ticker: str,
                            ttl_override: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch analyst recommendations — cache-first."""
        cache_path = self._cache_path("recommendations", ticker)

        if self._is_cache_fresh(cache_path, "recommendations", ttl_override):
            print(f"[engine] Recommendations for {ticker}: served from cache")
            return self._read_json_cache(cache_path)

        for conn in self._get_connectors_for("recommendations"):
            try:
                data = conn.get_recommendations(ticker)
                if data:
                    self._write_json_cache(cache_path, data)
                    print(f"[engine] Recommendations for {ticker}: fetched from {conn.name}, cached")
                    return data
            except Exception as e:
                print(f"[engine] {conn.name} failed for recommendations/{ticker}: {e}")
                continue

        if cache_path.exists():
            return self._read_json_cache(cache_path)
        return []

    # ── Bulk Operations ──────────────────────────────────────────────────

    def get_full_snapshot(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch ALL available data for a ticker in one call.
        Returns a comprehensive dict with all data types.
        """
        return {
            "ticker": ticker,
            "prices": self.get_prices(ticker),
            "fundamentals": self.get_fundamentals(ticker),
            "financials": self.get_financials(ticker),
            "options": self.get_options(ticker),
            "insider_activity": self.get_insider_activity(ticker),
            "news": self.get_news(ticker),
            "recommendations": self.get_recommendations(ticker),
        }

    # ── DuckDB Query Layer ───────────────────────────────────────────────

    @property
    def db(self) -> duckdb.DuckDBPyConnection:
        """Lazy DuckDB connection."""
        if self._db is None:
            self._db = duckdb.connect(":memory:")
        return self._db

    def query(self, sql: str) -> pd.DataFrame:
        """
        Run SQL over cached Parquet files.

        Tables are auto-registered from cached Parquet files.
        Example: engine.query("SELECT * FROM 'data/prices/AAPL.parquet' WHERE close > 250")
        """
        return self.db.execute(sql).fetchdf()

    def query_prices(self, tickers: List[str],
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Query cached price data for multiple tickers via DuckDB.
        Automatically loads all available Parquet files.
        """
        parquet_files = []
        for ticker in tickers:
            path = self._cache_path("prices", ticker, ext="parquet")
            if path.exists():
                parquet_files.append(str(path))

        if not parquet_files:
            return pd.DataFrame()

        # Build query
        files_str = ", ".join(f"'{f}'" for f in parquet_files)
        sql = f"SELECT * FROM read_parquet([{files_str}])"

        conditions = []
        if start_date:
            conditions.append(f"date >= '{start_date}'")
        if end_date:
            conditions.append(f"date <= '{end_date}'")

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        sql += " ORDER BY date"

        return self.db.execute(sql).fetchdf()

    # ── Health Check ─────────────────────────────────────────────────────

    def health_check(self) -> Dict[str, Any]:
        """Check status of all registered connectors and cache."""
        status = {
            "connectors": {},
            "cache": {},
        }

        for entry in self._connectors:
            conn = entry["connector"]
            try:
                healthy = conn.health_check()
                status["connectors"][conn.name] = {
                    "healthy": healthy,
                    "priority": entry["priority"],
                }
            except Exception as e:
                status["connectors"][conn.name] = {
                    "healthy": False,
                    "error": str(e),
                    "priority": entry["priority"],
                }

        # Cache stats
        for subdir in ["prices", "fundamentals", "financials", "options",
                       "insiders", "news", "recommendations"]:
            dir_path = self._data_dir / subdir
            files = list(dir_path.glob("*"))
            status["cache"][subdir] = len(files)

        return status
