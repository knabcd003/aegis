"""
Yahoo Finance Connector — Primary data source for the Data Ingestion Engine.
No API key required. Uses the yfinance library.

Provides: prices, fundamentals, news, financial statements, options chains,
insider/institutional activity, analyst recommendations.
"""
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from engines.data_ingestion.base_connector import BaseConnector


class YFinanceConnector(BaseConnector):
    """Fetches market data via Yahoo Finance (free, no API key)."""

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

    def get_prices(self, ticker: str, days: int = 30, interval: str = "1d") -> Optional[pd.DataFrame]:
        """
        Fetch daily or intraday OHLCV data for the given ticker.
        Returns a standardized DataFrame or None on failure.
        """
        try:
            stock = yf.Ticker(ticker)
            end = datetime.now()
            start = end - timedelta(days=days)
            
            # yfinance requires 'start'/'end' as strings for daily, but datetimes for intraday
            # but history() also accepts datetimes objects.
            df = stock.history(start=start, end=end, interval=interval)

            if df.empty:
                print(f"[{self.name}] No price data returned for {ticker} (interval={interval})")
                return None

            df = df.reset_index()
            # Depending on timezone/interval, index might be 'Datetime' or 'Date'
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
            
            if interval == "1d":
                df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
            else:
                df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d %H:%M:%S")
                
            return df

        except Exception as e:
            print(f"[{self.name}] Error fetching prices for {ticker}: {e}")
            return None

    # ── Fundamentals ─────────────────────────────────────────────────────

    def get_fundamentals(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetch fundamental metrics for the given ticker.
        Returns a standardized dict or None on failure.
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            if not info or "symbol" not in info:
                print(f"[{self.name}] No fundamental data for {ticker}")
                return None

            fundamentals = {
                "ticker": ticker,
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

            # Get earnings date if available
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

            return fundamentals

        except Exception as e:
            print(f"[{self.name}] Error fetching fundamentals for {ticker}: {e}")
            return None

    # ── News ─────────────────────────────────────────────────────────────

    def get_news(self, ticker: str, days: int = 7) -> List[Dict[str, Any]]:
        """
        Fetch recent news headlines for the given ticker.
        Returns a list of standardized news dicts (newest first).
        """
        try:
            stock = yf.Ticker(ticker)
            raw_news = stock.news

            if not raw_news:
                return []

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

                if isinstance(pub_date, (int, float)):
                    pub_date = datetime.fromtimestamp(pub_date).strftime("%Y-%m-%d %H:%M")

                news_items.append({
                    "headline": headline,
                    "date": str(pub_date),
                    "source": source,
                    "url": url,
                })

            return news_items

        except Exception as e:
            print(f"[{self.name}] Error fetching news for {ticker}: {e}")
            return []

    # ── Financial Statements ─────────────────────────────────────────────

    def get_financials(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetch balance sheet, income statement, and cash flow.
        Returns a dict with 3 DataFrames (quarterly data), or None on failure.
        """
        try:
            stock = yf.Ticker(ticker)

            balance = stock.quarterly_balance_sheet
            income = stock.quarterly_income_stmt
            cashflow = stock.quarterly_cashflow

            if balance is None or balance.empty:
                print(f"[{self.name}] No financial data for {ticker}")
                return None

            # Pull latest quarter's key figures
            latest = {}

            # Balance sheet
            if not balance.empty:
                col = balance.columns[0]  # Most recent quarter
                latest["total_assets"] = self._safe_val(balance, "Total Assets", col)
                latest["total_debt"] = self._safe_val(balance, "Total Debt", col)
                latest["total_equity"] = self._safe_val(balance, "Stockholders Equity", col)
                latest["cash_and_equivalents"] = self._safe_val(balance, "Cash And Cash Equivalents", col)
                latest["balance_sheet_date"] = str(col.date()) if hasattr(col, "date") else str(col)

            # Income statement
            if income is not None and not income.empty:
                col = income.columns[0]
                latest["total_revenue"] = self._safe_val(income, "Total Revenue", col)
                latest["net_income"] = self._safe_val(income, "Net Income", col)
                latest["operating_income"] = self._safe_val(income, "Operating Income", col)
                latest["ebitda"] = self._safe_val(income, "EBITDA", col)
                latest["gross_profit"] = self._safe_val(income, "Gross Profit", col)

            # Cash flow
            if cashflow is not None and not cashflow.empty:
                col = cashflow.columns[0]
                latest["operating_cashflow"] = self._safe_val(cashflow, "Operating Cash Flow", col)
                latest["free_cashflow"] = self._safe_val(cashflow, "Free Cash Flow", col)
                latest["capex"] = self._safe_val(cashflow, "Capital Expenditure", col)

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
        """Safely extract a value from a financial statement DataFrame."""
        try:
            if row_label in df.index:
                val = df.loc[row_label, col]
                if pd.notna(val):
                    return float(val)
        except Exception:
            pass
        return None

    # ── Options Chain ────────────────────────────────────────────────────

    def get_options(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetch the nearest-expiry options chain with IV, open interest,
        and computed put/call ratio.
        """
        try:
            stock = yf.Ticker(ticker)
            expirations = stock.options

            if not expirations:
                print(f"[{self.name}] No options data for {ticker}")
                return None

            # Use nearest expiration
            nearest_exp = expirations[0]
            chain = stock.option_chain(nearest_exp)

            calls = chain.calls
            puts = chain.puts

            # Compute put/call ratio from volume
            total_call_vol = calls["volume"].sum() if "volume" in calls.columns else 0
            total_put_vol = puts["volume"].sum() if "volume" in puts.columns else 0
            put_call_ratio = (total_put_vol / total_call_vol) if total_call_vol > 0 else None

            # Compute put/call OI ratio
            total_call_oi = calls["openInterest"].sum() if "openInterest" in calls.columns else 0
            total_put_oi = puts["openInterest"].sum() if "openInterest" in puts.columns else 0
            put_call_oi_ratio = (total_put_oi / total_call_oi) if total_call_oi > 0 else None

            # Average IV across ATM options (middle 20% of strikes)
            avg_call_iv = None
            if "impliedVolatility" in calls.columns:
                mid_start = len(calls) // 4
                mid_end = 3 * len(calls) // 4
                mid_calls = calls.iloc[mid_start:mid_end]
                iv_vals = mid_calls["impliedVolatility"].dropna()
                if len(iv_vals) > 0:
                    avg_call_iv = float(iv_vals.mean())

            avg_put_iv = None
            if "impliedVolatility" in puts.columns:
                mid_start = len(puts) // 4
                mid_end = 3 * len(puts) // 4
                mid_puts = puts.iloc[mid_start:mid_end]
                iv_vals = mid_puts["impliedVolatility"].dropna()
                if len(iv_vals) > 0:
                    avg_put_iv = float(iv_vals.mean())

            return {
                "ticker": ticker,
                "nearest_expiration": nearest_exp,
                "num_expirations": len(expirations),
                "num_call_strikes": len(calls),
                "num_put_strikes": len(puts),
                "total_call_volume": int(total_call_vol) if not pd.isna(total_call_vol) else 0,
                "total_put_volume": int(total_put_vol) if not pd.isna(total_put_vol) else 0,
                "put_call_volume_ratio": round(put_call_ratio, 3) if put_call_ratio else None,
                "total_call_oi": int(total_call_oi) if not pd.isna(total_call_oi) else 0,
                "total_put_oi": int(total_put_oi) if not pd.isna(total_put_oi) else 0,
                "put_call_oi_ratio": round(put_call_oi_ratio, 3) if put_call_oi_ratio else None,
                "avg_atm_call_iv": round(avg_call_iv, 4) if avg_call_iv else None,
                "avg_atm_put_iv": round(avg_put_iv, 4) if avg_put_iv else None,
            }

        except Exception as e:
            print(f"[{self.name}] Error fetching options for {ticker}: {e}")
            return None

    # ── Insider & Institutional Activity ─────────────────────────────────

    def get_insider_activity(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Fetch insider transactions, institutional holders, and mutual fund holders.
        """
        try:
            stock = yf.Ticker(ticker)
            result: Dict[str, Any] = {"ticker": ticker}

            # Insider transactions
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
                    result["insider_transaction_count"] = len(insider_txns)
                else:
                    result["insider_transactions"] = []
                    result["insider_transaction_count"] = 0
            except Exception:
                result["insider_transactions"] = []
                result["insider_transaction_count"] = 0

            # Institutional holders
            try:
                inst = stock.institutional_holders
                if inst is not None and not inst.empty:
                    holders = []
                    for _, row in inst.head(5).iterrows():
                        holders.append({
                            "holder": str(row.get("Holder", "")),
                            "shares": self._to_num(row.get("Shares", 0)),
                            "pct_held": self._to_num(row.get("% Out", row.get("pctHeld", 0))),
                        })
                    result["top_institutional_holders"] = holders
                else:
                    result["top_institutional_holders"] = []
            except Exception:
                result["top_institutional_holders"] = []

            # Mutual fund holders
            try:
                mf = stock.mutualfund_holders
                if mf is not None and not mf.empty:
                    result["mutual_fund_holder_count"] = len(mf)
                else:
                    result["mutual_fund_holder_count"] = 0
            except Exception:
                result["mutual_fund_holder_count"] = 0

            return result

        except Exception as e:
            print(f"[{self.name}] Error fetching insider activity for {ticker}: {e}")
            return None

    # ── Analyst Recommendations History ──────────────────────────────────

    def get_recommendations(self, ticker: str) -> List[Dict[str, Any]]:
        """
        Fetch analyst recommendation summary by period.
        Returns list of period summaries (newest first).
        """
        try:
            stock = yf.Ticker(ticker)
            recs = stock.recommendations

            if recs is None or recs.empty:
                return []

            items = []
            for _, row in recs.iterrows():
                period = str(row.get("period", ""))
                strong_buy = int(row.get("strongBuy", 0))
                buy = int(row.get("buy", 0))
                hold = int(row.get("hold", 0))
                sell = int(row.get("sell", 0))
                strong_sell = int(row.get("strongSell", 0))
                total = strong_buy + buy + hold + sell + strong_sell

                items.append({
                    "period": period,
                    "strong_buy": strong_buy,
                    "buy": buy,
                    "hold": hold,
                    "sell": sell,
                    "strong_sell": strong_sell,
                    "total": total,
                    "bullish_pct": round((strong_buy + buy) / total * 100, 1) if total > 0 else 0,
                })

            return items

        except Exception as e:
            print(f"[{self.name}] Error fetching recommendations for {ticker}: {e}")
            return []

    # ── Utility ──────────────────────────────────────────────────────────

    def _to_num(self, val) -> Optional[float]:
        """Safely convert a value to float."""
        try:
            if val is None or (isinstance(val, float) and np.isnan(val)):
                return None
            return float(val)
        except (ValueError, TypeError):
            return None

