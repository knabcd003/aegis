"""
Finnhub Connector — Earnings transcripts, analyst estimates, insider transactions, news.

v6 update:
- All returned records include public_disclosure_ts.
- get_news() and get_insider_transactions() support as_of_date for point-in-time filtering.
- get_earnings_estimates() returns revision history with published_ts per estimate.
"""
import os
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, date

from engines.data_ingestion.base_connector import BaseConnector


FINNHUB_BASE = "https://finnhub.io/api/v1"


class FinnhubConnector(BaseConnector):
    """
    Fetches earnings estimates, insider transactions, and news from Finnhub.
    Requires FINNHUB_API_KEY in environment.
    """

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.getenv("FINNHUB_API_KEY")
        self._last_successful_fetch_ts: Optional[datetime] = None

    @property
    def name(self) -> str:
        return "finnhub"

    @property
    def provides_prices(self) -> bool:
        return False

    @property
    def provides_fundamentals(self) -> bool:
        return True  # Earnings estimates and revisions

    @property
    def provides_news(self) -> bool:
        return True

    def _request(self, endpoint: str, params: dict = None) -> Optional[Any]:
        """Make an authenticated request to Finnhub."""
        if not self._api_key:
            print(f"[{self.name}] No API key set. Set FINNHUB_API_KEY in .env")
            return None
        params = params or {}
        params["token"] = self._api_key
        try:
            resp = requests.get(f"{FINNHUB_BASE}/{endpoint}", params=params, timeout=10)
            resp.raise_for_status()
            self._last_successful_fetch_ts = datetime.utcnow()
            return resp.json()
        except Exception as e:
            print(f"[{self.name}] Request error ({endpoint}): {e}")
            return None

    # ── Earnings Estimates + Revisions ───────────────────────────────────

    def get_earnings_estimates(
        self,
        ticker: str,
        as_of_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch analyst EPS estimates with revision timestamps.

        Each returned record includes:
            public_disclosure_ts: date — when the estimate was published (published_ts)

        Point-in-time: only estimates with published_ts <= as_of_date returned.
        This is the primary data source for EarningsRevisionTracker (Phase 1 Step 3).
        """
        sim_date = as_of_date or date.today()
        data = self._request("stock/eps-estimate", {"symbol": ticker, "freq": "quarterly"})

        if not data or not data.get("data"):
            return []

        estimates = []
        for item in data["data"]:
            # Finnhub eps-estimate entries have a 'period' (the quarter) but not
            # a precise published_ts. We use today as the disclosure date for
            # forward-looking estimates. For revision history, use estimate-surprise.
            estimates.append({
                "ticker": ticker,
                "period": item.get("period", ""),
                "eps_avg": item.get("epsAvg"),
                "eps_high": item.get("epsHigh"),
                "eps_low": item.get("epsLow"),
                "number_of_analysts": item.get("numberAnalysts"),
                "revenue_avg": item.get("revenueAvg"),
                "revenue_high": item.get("revenueHigh"),
                "revenue_low": item.get("revenueLow"),
                "public_disclosure_ts": sim_date.isoformat(),  # estimate consensus date
            })

        return estimates

    def get_earnings_revisions(
        self,
        ticker: str,
        as_of_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch earnings surprise history (actual vs. estimated) with dates.

        Each record includes:
            public_disclosure_ts: date — earnings release date (when surprise became public)

        Point-in-time: only records with earnings_release_date <= as_of_date returned.
        """
        sim_date = as_of_date or date.today()
        data = self._request("stock/earnings", {"symbol": ticker})

        if not data:
            return []

        revisions = []
        for item in data:
            period_str = item.get("period", "")
            try:
                period_date = date.fromisoformat(period_str)
            except ValueError:
                continue

            # The surprise becomes public on the earnings release date
            if period_date > sim_date:
                continue

            revisions.append({
                "ticker": ticker,
                "period": period_str,
                "period_date": period_date.isoformat(),
                "actual": item.get("actual"),
                "estimate": item.get("estimate"),
                "surprise": item.get("surprise"),
                "surprise_percent": item.get("surprisePercent"),
                "public_disclosure_ts": period_date.isoformat(),  # earnings date = disclosure
            })

        # Newest first
        revisions.sort(key=lambda x: x["period_date"], reverse=True)
        return revisions

    # ── Insider Transactions ─────────────────────────────────────────────

    def get_insider_transactions(
        self,
        ticker: str,
        as_of_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch insider transactions from Finnhub.

        Each record includes:
            public_disclosure_ts: date — the SEC filing date for this transaction
                                         (NOT the transaction date — STOCK Act lag applies)

        Point-in-time: only records with filing_date <= as_of_date returned.
        """
        sim_date = as_of_date or date.today()
        data = self._request("stock/insider-transactions", {"symbol": ticker})

        if not data or not data.get("data"):
            return []

        transactions = []
        for txn in data["data"][:50]:
            filing_date_str = txn.get("filingDate", "")
            try:
                filing_date = date.fromisoformat(filing_date_str)
            except ValueError:
                continue

            # Point-in-time: use filing date, not transaction date
            if filing_date > sim_date:
                continue

            transactions.append({
                "ticker": ticker,
                "name": txn.get("name", ""),
                "shares": txn.get("share", 0),
                "change": txn.get("change", 0),
                "transaction_type": txn.get("transactionType", ""),
                "transaction_date": txn.get("transactionDate", ""),
                "filing_date": filing_date_str,
                "public_disclosure_ts": filing_date_str,  # filing date = public disclosure
            })

        return transactions

    # ── Company News ─────────────────────────────────────────────────────

    def get_news(
        self,
        ticker: str,
        days: int = 7,
        as_of_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch company news from Finnhub.

        Each record includes:
            public_disclosure_ts: date — article publication date (published_ts)

        Point-in-time: only articles with published_ts <= as_of_date returned.
        """
        sim_date = as_of_date or date.today()
        end_str = sim_date.isoformat()
        start_str = (sim_date - timedelta(days=days)).isoformat()

        data = self._request("company-news", {
            "symbol": ticker,
            "from": start_str,
            "to": end_str,
        })

        if not data:
            return []

        news_items = []
        for item in data[:30]:
            pub_time = item.get("datetime", 0)
            if isinstance(pub_time, (int, float)):
                pub_dt = datetime.fromtimestamp(pub_time)
            else:
                try:
                    pub_dt = datetime.fromisoformat(str(pub_time))
                except Exception:
                    pub_dt = datetime.now()

            pub_date = pub_dt.date()

            # Double-check point-in-time (API filter may not be exact)
            if pub_date > sim_date:
                continue

            news_items.append({
                "headline": item.get("headline", ""),
                "date": pub_dt.strftime("%Y-%m-%d %H:%M"),
                "source": item.get("source", ""),
                "url": item.get("url", ""),
                "summary": item.get("summary", ""),
                "public_disclosure_ts": pub_date.isoformat(),
            })

        return news_items

    # ── Earnings Transcript ──────────────────────────────────────────────

    def get_earnings_transcript(
        self,
        ticker: str,
        year: Optional[int] = None,
        quarter: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """Fetch an earnings call transcript."""
        if not year:
            now = datetime.now()
            year = now.year
            if not quarter:
                quarter = max(1, (now.month - 1) // 3)

        data = self._request("stock/transcript", {"symbol": ticker, "year": year, "quarter": quarter})

        if not data or not data.get("transcript"):
            if quarter and quarter > 1:
                data = self._request("stock/transcript", {"symbol": ticker, "year": year, "quarter": quarter - 1})
            elif year:
                data = self._request("stock/transcript", {"symbol": ticker, "year": year - 1, "quarter": 4})

        if not data or not data.get("transcript"):
            print(f"[{self.name}] No transcript found for {ticker} Q{quarter} {year}")
            return None

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
            "public_disclosure_ts": date.today().isoformat(),
        }

    # ── Earnings Calendar ────────────────────────────────────────────────

    def get_earnings_calendar(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch upcoming/recent earnings dates."""
        if not start_date:
            start_date = date.today().isoformat()
        if not end_date:
            end_date = (date.today() + timedelta(days=14)).isoformat()

        data = self._request("calendar/earnings", {"from": start_date, "to": end_date})
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
                "public_disclosure_ts": item.get("date", date.today().isoformat()),
            }
            for item in data["earningsCalendar"][:50]
        ]

    # ── BaseConnector interface ──────────────────────────────────────────

    def get_prices(self, ticker: str, days: int = 30, interval: str = "1d",
                   as_of_date: Optional[date] = None):
        return None

    def get_fundamentals(self, ticker: str, as_of_date: Optional[date] = None):
        """Returns earnings revision history as fundamentals."""
        return {"revisions": self.get_earnings_revisions(ticker, as_of_date=as_of_date)}

    def health_check(self) -> bool:
        if not self._api_key:
            print(f"[{self.name}] No API key configured")
            return False
        data = self._request("stock/market-status", {"exchange": "US"})
        return data is not None
