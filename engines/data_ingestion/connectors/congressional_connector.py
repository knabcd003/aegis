"""
Congressional STOCK Act Connector — Disclosure filings from house.gov and senate.gov.

STOCK Act requires members of Congress to disclose securities transactions
within 45 days of the trade. This connector fetches those disclosures.

Critical timing rule (non-negotiable):
    public_disclosure_ts = disclosure_filing_ts (when the disclosure was filed)
    NEVER = trade_date (when the actual trade occurred)

The 45-day STOCK Act lag is a FEATURE, not a bug. A simulation that uses
trade_date instead of disclosure_filing_ts has lookahead bias — it would know
about Congressional trades before they were legally disclosed to the public.

Data source: House Financial Disclosures API + Senate STOCK Act disclosures.
Both sources are public, no API key required.
"""
import requests
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, date

from engines.data_ingestion.base_connector import BaseConnector


# House Financial Disclosures API (efts.house.gov)
HOUSE_BASE = "https://disclosures-clerk.house.gov/public_disc"
SENATE_BASE = "https://efts.senate.gov/LATEST/search-index"


class CongressionalConnector(BaseConnector):
    """
    Fetches STOCK Act disclosures from House and Senate financial disclosure portals.

    All results use disclosure_filing_ts as public_disclosure_ts.
    The trade_date field is present for completeness but is NEVER used
    as the disclosure date in any simulation or signal computation.
    """

    def __init__(self):
        self._last_successful_fetch_ts: Optional[datetime] = None

    @property
    def name(self) -> str:
        return "congressional"

    @property
    def provides_prices(self) -> bool:
        return False

    @property
    def provides_fundamentals(self) -> bool:
        return False

    @property
    def provides_news(self) -> bool:
        return False

    def get_disclosures(
        self,
        ticker: str,
        as_of_date: Optional[date] = None,
        days_back: int = 365,
    ) -> List[Dict[str, Any]]:
        """
        Fetch Congressional STOCK Act disclosures mentioning a specific ticker.

        Returns list of disclosure records. Point-in-time filtering applied:
        only disclosures where disclosure_filing_ts <= as_of_date are returned.

        Each record includes:
            disclosure_filing_ts: date — when the member filed the disclosure (public)
            trade_date: date — when the actual trade occurred (NOT for simulation use)
            public_disclosure_ts: date — same as disclosure_filing_ts (always)

        Args:
            ticker: Stock ticker to search for
            as_of_date: Simulation date. Only disclosures filed on or before this
                        date are returned. Defaults to today.
            days_back: How many days of history to fetch. Default 365.
        """
        sim_date = as_of_date or date.today()
        start_date = sim_date - timedelta(days=days_back)

        disclosures = []

        # Fetch from House portal
        house_disclosures = self._fetch_house_disclosures(ticker, start_date, sim_date)
        disclosures.extend(house_disclosures)

        # Fetch from Senate portal  
        senate_disclosures = self._fetch_senate_disclosures(ticker, start_date, sim_date)
        disclosures.extend(senate_disclosures)

        # Final point-in-time guard: ensure no disclosure with filing_ts > sim_date
        # leaks through regardless of sub-method behavior (critical for test correctness)
        disclosures = [
            d for d in disclosures
            if d.get("disclosure_filing_ts", "9999-99-99") <= sim_date.isoformat()
        ]

        # Sort by disclosure_filing_ts descending (most recently disclosed first)
        disclosures.sort(
            key=lambda x: x.get("disclosure_filing_ts", ""),
            reverse=True,
        )

        if disclosures:
            self._last_successful_fetch_ts = datetime.utcnow()

        return disclosures

    def _fetch_house_disclosures(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
    ) -> List[Dict[str, Any]]:
        """
        Fetch House Financial Disclosures for a ticker.
        Uses the House disclosure search API.
        """
        try:
            # House disclosures search — PTR (periodic transaction reports) are STOCK Act filings
            url = f"{HOUSE_BASE}/ptr-pdfs/{end_date.year}FD.zip"
            # Note: The House API returns ZIP archives of PDFs which require
            # parsing. For structured data, we use the efts.house.gov endpoint.

            # House clerk EFTS search
            search_url = "https://efts.house.gov/LATEST/search-index"
            params = {
                "q": f'"{ticker}"',
                "dateRange": "custom",
                "fromDate": start_date.isoformat(),
                "toDate": end_date.isoformat(),
                "type": "ptr",  # Periodic Transaction Reports
            }

            resp = requests.get(search_url, params=params, timeout=15)
            if resp.status_code != 200:
                return []

            data = resp.json()
            hits = data.get("hits", {}).get("hits", [])

            disclosures = []
            for hit in hits:
                src = hit.get("_source", {})

                filing_date_str = src.get("FilingDate", src.get("filing_date", ""))
                transaction_date_str = src.get("TransactionDate", src.get("transaction_date", ""))

                try:
                    filing_date = date.fromisoformat(filing_date_str[:10])
                except (ValueError, TypeError):
                    continue

                # Point-in-time check: disclosure must be filed on or before sim date
                if filing_date > end_date:
                    continue

                try:
                    trade_date = date.fromisoformat(transaction_date_str[:10])
                except (ValueError, TypeError):
                    trade_date = None

                disclosures.append({
                    "source": "house",
                    "member_name": src.get("Name", src.get("name", "")),
                    "member_office": src.get("Office", ""),
                    "ticker": ticker,
                    "asset_description": src.get("AssetDescription", src.get("asset_description", "")),
                    "transaction_type": src.get("Type", src.get("type", "")),
                    "amount_range": src.get("Amount", src.get("amount", "")),
                    # TIMING — the critical distinction
                    "trade_date": trade_date.isoformat() if trade_date else None,
                    "disclosure_filing_ts": filing_date.isoformat(),
                    "public_disclosure_ts": filing_date.isoformat(),  # ALWAYS filing date
                    "document_id": src.get("DocID", src.get("doc_id", "")),
                })

            return disclosures

        except Exception as e:
            print(f"[{self.name}] House disclosure fetch error for {ticker}: {e}")
            return []

    def _fetch_senate_disclosures(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
    ) -> List[Dict[str, Any]]:
        """
        Fetch Senate STOCK Act disclosures for a ticker.
        Uses the Senate EFTS search API.
        """
        try:
            params = {
                "q": f'"{ticker}"',
                "dateRange": "custom",
                "fromDate": start_date.isoformat(),
                "toDate": end_date.isoformat(),
                "type": "ptr",
            }

            resp = requests.get(SENATE_BASE, params=params, timeout=15)
            if resp.status_code != 200:
                return []

            data = resp.json()
            hits = data.get("hits", {}).get("hits", [])

            disclosures = []
            for hit in hits:
                src = hit.get("_source", {})

                filing_date_str = src.get("Date_Received", src.get("date_received", ""))
                transaction_date_str = src.get("Transaction_Date", src.get("transaction_date", ""))

                try:
                    filing_date = date.fromisoformat(filing_date_str[:10])
                except (ValueError, TypeError):
                    continue

                if filing_date > end_date:
                    continue

                try:
                    trade_date = date.fromisoformat(transaction_date_str[:10])
                except (ValueError, TypeError):
                    trade_date = None

                disclosures.append({
                    "source": "senate",
                    "member_name": src.get("First_Last", src.get("senator_name", "")),
                    "member_office": "Senate",
                    "ticker": ticker,
                    "asset_description": src.get("Asset_Description", ""),
                    "transaction_type": src.get("Transaction_Type", ""),
                    "amount_range": src.get("Amount", ""),
                    # TIMING — the critical distinction
                    "trade_date": trade_date.isoformat() if trade_date else None,
                    "disclosure_filing_ts": filing_date.isoformat(),
                    "public_disclosure_ts": filing_date.isoformat(),  # ALWAYS filing date
                    "document_id": src.get("Link_To_Document", ""),
                })

            return disclosures

        except Exception as e:
            print(f"[{self.name}] Senate disclosure fetch error for {ticker}: {e}")
            return []

    def get_cluster_buy_signal(
        self,
        ticker: str,
        as_of_date: Optional[date] = None,
        cluster_window_days: int = 45,
        min_cluster_size: int = 3,
    ) -> Dict[str, Any]:
        """
        Check for a Congressional cluster buy signal — multiple members buying
        the same ticker within the cluster_window_days, all visible by as_of_date.

        Returns:
            {
                "cluster_buy": bool,
                "cluster_size": int,
                "members": [str],
                "disclosures": [dict],
                "public_disclosure_ts": str  # most recent disclosure in the cluster
            }
        """
        sim_date = as_of_date or date.today()
        disclosures = self.get_disclosures(
            ticker,
            as_of_date=sim_date,
            days_back=cluster_window_days,
        )

        # Filter to buy transactions only
        buy_disclosures = [
            d for d in disclosures
            if "purchase" in d.get("transaction_type", "").lower()
            or "buy" in d.get("transaction_type", "").lower()
        ]

        cluster_buy = len(buy_disclosures) >= min_cluster_size
        members = list({d["member_name"] for d in buy_disclosures})

        most_recent_ts = max(
            (d["disclosure_filing_ts"] for d in buy_disclosures),
            default=sim_date.isoformat(),
        )

        return {
            "ticker": ticker,
            "cluster_buy": cluster_buy,
            "cluster_size": len(buy_disclosures),
            "unique_members": len(members),
            "members": members[:10],
            "disclosures": buy_disclosures,
            "public_disclosure_ts": most_recent_ts,
        }

    # ── BaseConnector interface ──────────────────────────────────────────

    def get_prices(self, ticker: str, days: int = 30, interval: str = "1d",
                   as_of_date: Optional[date] = None):
        return None

    def get_fundamentals(self, ticker: str, as_of_date: Optional[date] = None):
        return None

    def get_news(self, ticker: str, days: int = 7, as_of_date: Optional[date] = None):
        return []

    def health_check(self) -> bool:
        """Check if House disclosure portal is reachable."""
        try:
            resp = requests.get(
                "https://efts.house.gov/LATEST/search-index",
                params={"q": "AAPL", "type": "ptr"},
                timeout=10,
            )
            return resp.status_code in (200, 400)  # 400 = up but bad params is fine
        except Exception:
            return False
