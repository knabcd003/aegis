"""
Yahoo Finance Connector — Primary data source for prices, fundamentals, and news.
No API key required. Uses the yfinance library.
"""
import yfinance as yf
import pandas as pd
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

    def get_prices(self, ticker: str, days: int = 30) -> Optional[pd.DataFrame]:
        """
        Fetch daily OHLCV data for the given ticker.
        Returns a standardized DataFrame or None on failure.
        """
        try:
            stock = yf.Ticker(ticker)
            end = datetime.now()
            start = end - timedelta(days=days)
            df = stock.history(start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"))

            if df.empty:
                print(f"[{self.name}] No price data returned for {ticker}")
                return None

            # Normalize to our standard schema
            df = df.reset_index()
            df = df.rename(columns={
                "Date": "date",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            })

            # Keep only the columns we need, drop dividends/stock splits
            df = df[["date", "open", "high", "low", "close", "volume"]].copy()

            # Ensure date is a string in YYYY-MM-DD format
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

            return df

        except Exception as e:
            print(f"[{self.name}] Error fetching prices for {ticker}: {e}")
            return None

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

            # Map yfinance keys to our standard schema
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
            }

            # Get earnings date if available
            try:
                cal = stock.calendar
                if cal is not None and not cal.empty if isinstance(cal, pd.DataFrame) else cal:
                    if isinstance(cal, dict) and "Earnings Date" in cal:
                        dates = cal["Earnings Date"]
                        if dates:
                            fundamentals["earnings_date"] = str(dates[0]) if isinstance(dates, list) else str(dates)
            except Exception:
                pass  # Earnings date is optional

            return fundamentals

        except Exception as e:
            print(f"[{self.name}] Error fetching fundamentals for {ticker}: {e}")
            return None

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
                # yfinance news structure can vary by version
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

                # Convert Unix timestamp if needed
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
