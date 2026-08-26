"""
Yahoo Finance Connector — Primary data source for the Data Ingestion Engine.
No API key required. Uses the yfinance library.

v6 update: all returned data includes public_disclosure_ts. Price bars use the
bar date as the disclosure date (same-day public). Immutable price cache via
ledger.py — price data is written once and never re-fetched for a past date.
"""
import os
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, date

from engines.data_ingestion.base_connector import BaseConnector
from engines.data_ingestion import ledger


class YFinanceConnector(BaseConnector):
    """Fetches market data via Yahoo Finance (free, no API key)."""

    def __init__(self):
        self._last_successful_fetch_ts: Optional[datetime] = datetime.utcnow()

    @property
    def last_successful_fetch_ts(self) -> Optional[datetime]:
        return self._last_successful_fetch_ts

    @property
    def name(self) -> str:
        return "yfinance"

    @property
    def provides_prices(self) -> bool:
        return True

    @property
    def provides_fundamentals(self) -> bool:
        return True

    @property
    def provides_news(self) -> bool:
        return True

    # ── Prices ───────────────────────────────────────────────────────────

    def get_prices(
        self,
        ticker: str,
        days: int = 30,
        interval: str = "1d",
        as_of_date: Optional[date] = None,
    ) -> Optional[pd.DataFrame]:
        """
        Fetch daily OHLCV data. Returns public_disclosure_ts on every row.

        Point-in-time: if as_of_date is provided, only rows where
        public_disclosure_ts <= as_of_date are returned.

        Immutable cache: for daily bars, checks the ledger first. Fetches from
        YFinance only if no cached data exists for this ticker/date range.
        """
        try:
            sim_date = as_of_date or date.today()

            # --- Try ledger cache first (immutable, point-in-time) ---
            if interval == "1d":
                cached = ledger.read_prices(ticker, as_of_date=sim_date)
                if cached is not None and not cached.empty:
                    return cached

            # --- Fetch from YFinance ---
            stock = yf.Ticker(ticker)
            end = datetime.combine(sim_date, datetime.min.time()) + timedelta(days=1)
            start = end - timedelta(days=days)

            df = stock.history(start=start, end=end, interval=interval, auto_adjust=False)

            if df.empty:
                print(f"[{self.name}] No price data returned for {ticker}")
                return None

            df = df.reset_index()
            if "Datetime" in df.columns:
                df = df.rename(columns={"Datetime": "date"})
            else:
                df = df.rename(columns={"Date": "date"})

            df = df.rename(columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            })
            df = df[["date", "open", "high", "low", "close", "volume"]].copy()

            # Add public_disclosure_ts: for daily bars, the bar date IS the disclosure date
            df["date"] = pd.to_datetime(df["date"]).dt.date
            df["public_disclosure_ts"] = pd.to_datetime(df["date"])

            # Point-in-time filter
            mask = df["public_disclosure_ts"].dt.date <= sim_date
            df = df[mask].copy()

            df["date"] = df["date"].astype(str)

            # Cache to ledger (write-once, immutable)
            if interval == "1d" and not df.empty:
                try:
                    ledger.write_prices(ticker, df, download_date=date.today())
                except Exception as e:
                    print(f"[{self.name}] Ledger write warning for {ticker}: {e}")

            self._last_successful_fetch_ts = datetime.utcnow()
            return df

        except Exception as e:
            print(f"[{self.name}] Error fetching prices for {ticker}: {e}")
            return None

    # ── Fundamentals ─────────────────────────────────────────────────────

    def get_fundamentals(
        self,
        ticker: str,
        as_of_date: Optional[date] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch fundamental metrics. Includes public_disclosure_ts.

        Note: YFinance fundamentals are current-state snapshots — not point-in-time.
        For strict point-in-time fundamentals use SEC EDGAR connector (Form 10-Q/10-K).
        YFinance fundamentals are suitable for exploratory analysis only.
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            if not info or "symbol" not in info:
                print(f"[{self.name}] No fundamental data for {ticker}")
                return None

            # public_disclosure_ts for fundamentals is today (live snapshot)
            disclosure_ts = (as_of_date or date.today()).isoformat()

            fundamentals = {
                "ticker": ticker,
                "public_disclosure_ts": disclosure_ts,
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "market_cap": info.get("marketCap"),
                "eps": info.get("trailingEps"),
                "revenue": info.get("totalRevenue"),
                "profit_margin": info.get("profitMargins"),
                "earnings_date": None,
                "analyst_rating": info.get("recommendationKey"),
                "target_price": info.get("targetMeanPrice"),
                "52w_high": info.get("fiftyTwoWeekHigh"),
                "52w_low": info.get("fiftyTwoWeekLow"),
                "dividend_yield": info.get("dividendYield"),
                "beta": info.get("beta"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "short_ratio": info.get("shortRatio"),
                "shares_short": info.get("sharesShort"),
                "short_pct_float": info.get("shortPercentOfFloat"),
                "held_pct_insiders": info.get("heldPercentInsiders"),
                "held_pct_institutions": info.get("heldPercentInstitutions"),
            }

            try:
                cal = stock.calendar
                if cal is not None:
                    if isinstance(cal, dict) and "Earnings Date" in cal:
                        dates = cal["Earnings Date"]
                        if dates:
                            fundamentals["earnings_date"] = str(dates[0]) if isinstance(dates, list) else str(dates)
                    elif isinstance(cal, pd.DataFrame) and not cal.empty:
                        if "Earnings Date" in cal.index:
                            fundamentals["earnings_date"] = str(cal.loc["Earnings Date"].iloc[0])
            except Exception:
                pass

            self._last_successful_fetch_ts = datetime.utcnow()
            return fundamentals

        except Exception as e:
            print(f"[{self.name}] Error fetching fundamentals for {ticker}: {e}")
            return None

    # ── News ─────────────────────────────────────────────────────────────

    def get_news(
        self,
        ticker: str,
        days: int = 7,
        as_of_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent news headlines. Includes public_disclosure_ts on each item.
        public_disclosure_ts = article published date.

        If as_of_date is provided, only articles published on or before that date
        are returned.
        """
        try:
            stock = yf.Ticker(ticker)
            raw_news = stock.news

            if not raw_news:
                return []

            sim_date = as_of_date or date.today()
            news_items = []

            for item in raw_news:
                content = item.get("content", item)
                if isinstance(content, dict):
                    headline = content.get("title", "")
                    pub_date = content.get("pubDate", content.get("providerPublishTime", ""))
                    source = content.get("provider", {})
                    if isinstance(source, dict):
                        source = source.get("displayName", "Unknown")
                    url = content.get("canonicalUrl", {})
                    if isinstance(url, dict):
                        url = url.get("url", "")
                else:
                    headline = item.get("title", "")
                    pub_date = item.get("providerPublishTime", "")
                    source = item.get("publisher", "Unknown")
                    url = item.get("link", "")

                # Parse pub_date to a datetime
                if isinstance(pub_date, (int, float)):
                    pub_dt = datetime.fromtimestamp(pub_date)
                else:
                    try:
                        pub_dt = datetime.fromisoformat(str(pub_date).replace("Z", "+00:00"))
                    except Exception:
                        pub_dt = datetime.now()

                disclosure_date = pub_dt.date()

                # Point-in-time filter
                if disclosure_date > sim_date:
                    continue

                news_items.append({
                    "headline": headline,
                    "date": pub_dt.strftime("%Y-%m-%d %H:%M"),
                    "source": source,
                    "url": url,
                    "public_disclosure_ts": disclosure_date.isoformat(),
                })

            self._last_successful_fetch_ts = datetime.utcnow()
            return news_items

        except Exception as e:
            print(f"[{self.name}] Error fetching news for {ticker}: {e}")
            return []

    # ── Financial Statements ─────────────────────────────────────────────

    def get_financials(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetch balance sheet, income statement, and cash flow (quarterly).
        Note: not point-in-time — use SEC EDGAR connector for backtest fundamentals.
        """
        try:
            stock = yf.Ticker(ticker)
            balance = stock.quarterly_balance_sheet
            income = stock.quarterly_income_stmt
            cashflow = stock.quarterly_cashflow

            if balance is None or balance.empty:
                print(f"[{self.name}] No financial data for {ticker}")
                return None

            latest = {}
            if not balance.empty:
                col = balance.columns[0]
                latest["total_assets"] = self._safe_val(balance, "Total Assets", col)
                latest["total_debt"] = self._safe_val(balance, "Total Debt", col)
                latest["total_equity"] = self._safe_val(balance, "Stockholders Equity", col)
                latest["cash_and_equivalents"] = self._safe_val(balance, "Cash And Cash Equivalents", col)
                latest["balance_sheet_date"] = str(col.date()) if hasattr(col, "date") else str(col)

            if income is not None and not income.empty:
                col = income.columns[0]
                latest["total_revenue"] = self._safe_val(income, "Total Revenue", col)
                latest["net_income"] = self._safe_val(income, "Net Income", col)
                latest["operating_income"] = self._safe_val(income, "Operating Income", col)
                latest["ebitda"] = self._safe_val(income, "EBITDA", col)
                latest["gross_profit"] = self._safe_val(income, "Gross Profit", col)

            if cashflow is not None and not cashflow.empty:
                col = cashflow.columns[0]
                latest["operating_cashflow"] = self._safe_val(cashflow, "Operating Cash Flow", col)
                latest["free_cashflow"] = self._safe_val(cashflow, "Free Cash Flow", col)

            self._last_successful_fetch_ts = datetime.utcnow()
            return {
                "ticker": ticker,
                "latest_quarter": latest,
                "balance_sheet_quarters": len(balance.columns),
                "income_quarters": len(income.columns) if income is not None else 0,
                "cashflow_quarters": len(cashflow.columns) if cashflow is not None else 0,
            }

        except Exception as e:
            print(f"[{self.name}] Error fetching financials for {ticker}: {e}")
            return None

    def _safe_val(self, df: pd.DataFrame, row_label: str, col) -> Optional[float]:
        try:
            if row_label in df.index:
                val = df.loc[row_label, col]
                if pd.notna(val):
                    return float(val)
        except Exception:
            pass
        return None

    # ── Options, Insider, Recommendations — unchanged, kept for compatibility ─

    def get_options(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Fetch nearest-expiry options chain. Not point-in-time."""
        try:
            stock = yf.Ticker(ticker)
            expirations = stock.options
            if not expirations:
                return None
            nearest_exp = expirations[0]
            chain = stock.option_chain(nearest_exp)
            calls, puts = chain.calls, chain.puts
            total_call_vol = calls["volume"].sum() if "volume" in calls.columns else 0
            total_put_vol = puts["volume"].sum() if "volume" in puts.columns else 0
            put_call_ratio = (total_put_vol / total_call_vol) if total_call_vol > 0 else None
            return {
                "ticker": ticker,
                "nearest_expiration": nearest_exp,
                "put_call_volume_ratio": round(put_call_ratio, 3) if put_call_ratio else None,
                "public_disclosure_ts": date.today().isoformat(),
            }
        except Exception as e:
            print(f"[{self.name}] Error fetching options for {ticker}: {e}")
            return None

    def get_insider_activity(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetch insider transactions. Each transaction includes a 'date' field.
        Note: for point-in-time insider activity in backtests, use InsiderActivityMonitor
        in engines/fundamental/ which enforces disclosure lag correctly.
        """
        try:
            stock = yf.Ticker(ticker)
            result: Dict[str, Any] = {
                "ticker": ticker,
                "public_disclosure_ts": date.today().isoformat(),
            }
            try:
                insider_txns = stock.insider_transactions
                if insider_txns is not None and not insider_txns.empty:
                    txns = []
                    for _, row in insider_txns.head(10).iterrows():
                        txns.append({
                            "insider": str(row.get("Insider", row.get("insider", ""))),
                            "relation": str(row.get("Relation", row.get("position", ""))),
                            "transaction": str(row.get("Transaction", row.get("transaction", ""))),
                            "shares": self._to_num(row.get("Shares", row.get("shares", 0))),
                            "value": self._to_num(row.get("Value", row.get("value", 0))),
                            "date": str(row.get("Start Date", row.get("startDate", ""))),
                        })
                    result["insider_transactions"] = txns
                else:
                    result["insider_transactions"] = []
            except Exception:
                result["insider_transactions"] = []
            self._last_successful_fetch_ts = datetime.utcnow()
            return result
        except Exception as e:
            print(f"[{self.name}] Error fetching insider activity for {ticker}: {e}")
            return None

    def get_recommendations(self, ticker: str) -> List[Dict[str, Any]]:
        """Fetch analyst recommendation summary by period."""
        try:
            stock = yf.Ticker(ticker)
            recs = stock.recommendations
            if recs is None or recs.empty:
                return []
            items = []
            for _, row in recs.iterrows():
                strong_buy = int(row.get("strongBuy", 0))
                buy = int(row.get("buy", 0))
                hold = int(row.get("hold", 0))
                sell = int(row.get("sell", 0))
                strong_sell = int(row.get("strongSell", 0))
                total = strong_buy + buy + hold + sell + strong_sell
                items.append({
                    "period": str(row.get("period", "")),
                    "strong_buy": strong_buy, "buy": buy, "hold": hold,
                    "sell": sell, "strong_sell": strong_sell, "total": total,
                    "bullish_pct": round((strong_buy + buy) / total * 100, 1) if total > 0 else 0,
                })
            return items
        except Exception as e:
            print(f"[{self.name}] Error fetching recommendations for {ticker}: {e}")
            return []

    def _to_num(self, val) -> Optional[float]:
        try:
            if val is None or (isinstance(val, float) and np.isnan(val)):
                return None
            return float(val)
        except (ValueError, TypeError):
            return None
