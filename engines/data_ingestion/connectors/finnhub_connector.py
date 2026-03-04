"""
Finnhub Connector — Earnings transcripts, insider transactions, and real-time news.

Requires a free API key from https://finnhub.io/register
Free tier: 60 calls/minute, which is plenty for our use case.
"""
import os
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from engines.data_ingestion.base_connector import BaseConnector


FINNHUB_BASE = "https://finnhub.io/api/v1"


class FinnhubConnector(BaseConnector):
    """
    Fetches earnings transcripts, insider transactions, and news from Finnhub.
    Requires FINNHUB_API_KEY in environment.
    """

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.getenv("FINNHUB_API_KEY")

    @property
    def name(self) -> str:
        return "finnhub"

    @property
    def provides_prices(self) -> bool:
        return False

    @property
    def provides_fundamentals(self) -> bool:
        return False

    @property
    def provides_news(self) -> bool:
        return True  # Company news

    def _request(self, endpoint: str, params: dict = None) -> Optional[Any]:
        """Make an authenticated request to Finnhub."""
        if not self._api_key:
            print(f"[{self.name}] No API key set. Set FINNHUB_API_KEY in .env")
            return None

        params = params or {}
        params["token"] = self._api_key

        try:
            resp = requests.get(
                f"{FINNHUB_BASE}/{endpoint}",
                params=params,
                timeout=10
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[{self.name}] Request error ({endpoint}): {e}")
            return None

    # ── Earnings Transcripts ─────────────────────────────────────────────

    def get_earnings_transcript(self, ticker: str,
                                year: Optional[int] = None,
                                quarter: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch an earnings call transcript.

        Args:
            ticker: Stock symbol (e.g., "AAPL")
            year: Fiscal year (defaults to current year)
            quarter: Fiscal quarter 1-4 (defaults to most recent)

        Returns:
            Dict with transcript text, or None.
        """
        if not year:
            now = datetime.now()
            year = now.year
            # Estimate most recent quarter
            if not quarter:
                quarter = max(1, (now.month - 1) // 3)

        data = self._request("stock/transcript", {
            "symbol": ticker,
            "year": year,
            "quarter": quarter,
        })

        if not data or not data.get("transcript"):
            # Try previous quarter
            if quarter and quarter > 1:
                data = self._request("stock/transcript", {
                    "symbol": ticker,
                    "year": year,
                    "quarter": quarter - 1,
                })
            elif year:
                data = self._request("stock/transcript", {
                    "symbol": ticker,
                    "year": year - 1,
                    "quarter": 4,
                })

        if not data or not data.get("transcript"):
            print(f"[{self.name}] No transcript found for {ticker} Q{quarter} {year}")
            return None

        # Flatten the transcript segments
        full_text = ""
        speakers = []
        for segment in data.get("transcript", []):
            speaker = segment.get("name", "Unknown")
            speech = segment.get("speech", [])
            text = " ".join(speech) if isinstance(speech, list) else str(speech)
            full_text += f"\n{speaker}: {text}\n"
            if speaker not in speakers:
                speakers.append(speaker)

        return {
            "ticker": ticker,
            "year": data.get("year", year),
            "quarter": data.get("quarter", quarter),
            "participant_count": len(speakers),
            "speakers": speakers[:10],
            "text_length": len(full_text),
            "text": full_text,
        }

    # ── Insider Transactions ─────────────────────────────────────────────

    def get_insider_transactions(self, ticker: str) -> List[Dict[str, Any]]:
        """Fetch insider transactions from Finnhub."""
        data = self._request("stock/insider-transactions", {"symbol": ticker})

        if not data or not data.get("data"):
            return []

        transactions = []
        for txn in data["data"][:20]:
            transactions.append({
                "name": txn.get("name", ""),
                "share": txn.get("share", 0),
                "change": txn.get("change", 0),
                "transaction_type": txn.get("transactionType", ""),
                "filing_date": txn.get("filingDate", ""),
                "transaction_date": txn.get("transactionDate", ""),
            })

        return transactions

    # ── Company News ─────────────────────────────────────────────────────

    def get_news(self, ticker: str, days: int = 7) -> List[Dict[str, Any]]:
        """Fetch company news from Finnhub."""
        end = datetime.now()
        start = end - timedelta(days=days)

        data = self._request("company-news", {
            "symbol": ticker,
            "from": start.strftime("%Y-%m-%d"),
            "to": end.strftime("%Y-%m-%d"),
        })

        if not data:
            return []

        news_items = []
        for item in data[:20]:
            pub_time = item.get("datetime", 0)
            if isinstance(pub_time, (int, float)):
                pub_time = datetime.fromtimestamp(pub_time).strftime("%Y-%m-%d %H:%M")

            news_items.append({
                "headline": item.get("headline", ""),
                "date": str(pub_time),
                "source": item.get("source", ""),
                "url": item.get("url", ""),
                "summary": item.get("summary", ""),
            })

        return news_items

    # ── Earnings Calendar ────────────────────────────────────────────────

    def get_earnings_calendar(self, start_date: Optional[str] = None,
                              end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch earnings calendar for upcoming/recent earnings.
        """
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")
        if not end_date:
            end_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")

        data = self._request("calendar/earnings", {
            "from": start_date,
            "to": end_date,
        })

        if not data or not data.get("earningsCalendar"):
            return []

        return [
            {
                "symbol": item.get("symbol", ""),
                "date": item.get("date", ""),
                "eps_estimate": item.get("epsEstimate"),
                "eps_actual": item.get("epsActual"),
                "revenue_estimate": item.get("revenueEstimate"),
                "revenue_actual": item.get("revenueActual"),
                "hour": item.get("hour", ""),
            }
            for item in data["earningsCalendar"][:50]
        ]

    # ── BaseConnector interface ──────────────────────────────────────────

    def get_prices(self, ticker: str, days: int = 30):
        return None

    def get_fundamentals(self, ticker: str):
        return None

    def health_check(self) -> bool:
        """Check if Finnhub API is accessible."""
        if not self._api_key:
            print(f"[{self.name}] No API key configured")
            return False
        # Simple ping using market status
        data = self._request("stock/market-status", {"exchange": "US"})
        return data is not None
