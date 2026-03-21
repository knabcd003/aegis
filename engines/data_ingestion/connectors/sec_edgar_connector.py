"""
SEC EDGAR Connector — Fetches SEC filing text (10-K, 10-Q, 8-K, Form 4).

v6 update:
- All filings are stored in the immutable ledger by accession number.
- public_disclosure_ts = the SEC filing date (when it became publicly available).
- as_of_date filtering ensures no filing with public_disclosure_ts > as_of_date
  is returned in a simulation.
- DeBERTa-v3-large NLI cross-encoder loaded as a class-level singleton at startup
  for two-stage segment obfuscation detection (Trap 1, §XIII).
"""
import re
import os
import json
import requests
from typing import Dict, List, Optional, Any
from datetime import date, datetime

from engines.data_ingestion.base_connector import BaseConnector
from engines.data_ingestion import ledger


# SEC requires identifying headers
HEADERS = {
    "User-Agent": "AegisAI research@aegis.ai",
    "Accept-Encoding": "gzip, deflate",
}

SUBMISSIONS_BASE = "https://data.sec.gov/submissions"
ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar/data"

# ── NLI singleton (now in engines/nli/segment_classifier.py) ──────────────────
# Backward-compatible imports for code that references these directly.
from engines.nli.segment_classifier import (
    classify_segment_change,
    get_nli_model as _get_nli_model,
)


class SECEdgarConnector(BaseConnector):
    """Fetches SEC filing metadata and text. Stores filings immutably by accession number."""

    def __init__(self):
        self._last_successful_fetch_ts: Optional[datetime] = None
        # Trigger NLI singleton load at construction time (startup cost, not per-filing)
        _get_nli_model()

    @property
    def _nli_model(self):
        """Access to the class-level NLI singleton for testing."""
        return _get_nli_model()

    @property
    def name(self) -> str:
        return "sec_edgar"

    @property
    def provides_prices(self) -> bool:
        return False

    @property
    def provides_fundamentals(self) -> bool:
        return True  # Filing-level fundamental data

    @property
    def provides_news(self) -> bool:
        return False

    def _get_cik(self, ticker: str) -> Optional[str]:
        """Look up the CIK number for a ticker symbol."""
        try:
            url = "https://www.sec.gov/files/company_tickers.json"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            for entry in data.values():
                if entry.get("ticker", "").upper() == ticker.upper():
                    return str(entry["cik_str"]).zfill(10)
            print(f"[{self.name}] CIK not found for {ticker}")
            return None
        except Exception as e:
            print(f"[{self.name}] Error looking up CIK for {ticker}: {e}")
            return None

    def get_filings_list(
        self,
        ticker: str,
        filing_type: str = "10-K",
        count: int = 5,
        as_of_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get a list of recent SEC filings for a ticker.

        public_disclosure_ts = filing_date from SEC EDGAR (when it became public).
        If as_of_date is provided, only filings with filing_date <= as_of_date returned.

        Checks ledger cache first. Falls back to EDGAR API.
        """
        sim_date = as_of_date or date.today()

        # --- Ledger cache ---
        cached = ledger.list_filings(ticker, filing_type, as_of_date=sim_date)
        if len(cached) >= count:
            return cached[:count]

        # --- Fetch from EDGAR ---
        cik = self._get_cik(ticker)
        if not cik:
            return []

        try:
            url = f"{SUBMISSIONS_BASE}/CIK{cik}.json"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            recent = data.get("filings", {}).get("recent", {})
            forms = recent.get("form", [])
            dates = recent.get("filingDate", [])
            accessions = recent.get("accessionNumber", [])
            primary_docs = recent.get("primaryDocument", [])

            filings = []
            for i, form in enumerate(forms):
                if form != filing_type:
                    continue
                filing_date_str = dates[i] if i < len(dates) else ""
                accession_num = accessions[i] if i < len(accessions) else ""

                try:
                    filing_date = date.fromisoformat(filing_date_str)
                except ValueError:
                    continue

                # Point-in-time filter
                if filing_date > sim_date:
                    continue

                filing_data = {
                    "ticker": ticker,
                    "form_type": form,
                    "filing_date": filing_date_str,
                    "public_disclosure_ts": filing_date_str,  # filing date = disclosure date
                    "accession_number": accession_num,
                    "primary_document": primary_docs[i] if i < len(primary_docs) else "",
                    "cik": cik,
                }

                # Write to ledger (immutable — won't overwrite if exists)
                if accession_num:
                    try:
                        ledger.write_filing(ticker, accession_num, filing_data)
                    except Exception as e:
                        print(f"[{self.name}] Ledger write warning: {e}")

                filings.append(filing_data)

                if len(filings) >= count:
                    break

            self._last_successful_fetch_ts = datetime.utcnow()
            return filings

        except Exception as e:
            print(f"[{self.name}] Error fetching filing list for {ticker}: {e}")
            return []

    def get_filing_text(
        self,
        ticker: str,
        filing_type: str = "10-K",
        max_chars: int = 50000,
        as_of_date: Optional[date] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch the most recent filing text for a ticker as of as_of_date.

        Checks ledger for cached filing first. Downloads from EDGAR only if not cached.
        Once downloaded, the JSON is stored in the ledger by accession number
        and never re-fetched (immutability rule).
        """
        filings = self.get_filings_list(ticker, filing_type, count=1, as_of_date=as_of_date)
        if not filings:
            print(f"[{self.name}] No {filing_type} filings found for {ticker}")
            return None

        filing = filings[0]
        accession = filing["accession_number"]
        accession_clean = accession.replace("-", "")
        primary_doc = filing.get("primary_document", "")
        cik = filing["cik"].lstrip("0")

        # --- Check ledger for full text cache ---
        cached = ledger.read_filing(ticker, accession)
        if cached and "text" in cached:
            return cached

        # --- Download from EDGAR ---
        try:
            url = f"{ARCHIVES_BASE}/{cik}/{accession_clean}/{primary_doc}"
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            raw_text = resp.text

            clean_text = re.sub(r'<[^>]+>', ' ', raw_text)
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            if len(clean_text) > max_chars:
                clean_text = clean_text[:max_chars]

            sections = self._extract_sections(clean_text)

            full_data = {
                "ticker": ticker,
                "form_type": filing_type,
                "filing_date": filing["filing_date"],
                "public_disclosure_ts": filing["filing_date"],
                "accession_number": accession,
                "text_length": len(clean_text),
                "text": clean_text,
                "sections": sections,
            }

            # Store in ledger — immutable from this point forward
            try:
                ledger.write_filing(ticker, accession, full_data)
            except Exception as e:
                print(f"[{self.name}] Ledger write warning for text: {e}")

            self._last_successful_fetch_ts = datetime.utcnow()
            return full_data

        except Exception as e:
            print(f"[{self.name}] Error fetching filing text for {ticker}: {e}")
            return None

    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Extract standard 10-K/10-Q sections from filing text."""
        sections = {}
        section_markers = {
            "risk_factors": [r"(?i)item\s*1a[.\s]*risk\s*factors", r"(?i)risk\s*factors"],
            "business": [r"(?i)item\s*1[.\s]*business"],
            "mda": [r"(?i)item\s*7[.\s]*management.s\s*discussion"],
            "financial_condition": [r"(?i)financial\s*condition"],
        }
        for section_name, patterns in section_markers.items():
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    start = match.start()
                    end = min(start + 5000, len(text))
                    sections[section_name] = text[start:end].strip()
                    break
        return sections

    # ── BaseConnector interface ──────────────────────────────────────────

    def get_prices(self, ticker: str, days: int = 30, interval: str = "1d",
                   as_of_date: Optional[date] = None):
        return None

    def get_fundamentals(self, ticker: str, as_of_date: Optional[date] = None):
        """Returns the most recent filing metadata as a fundamentals dict."""
        filing = self.get_filing_text(ticker, "10-K", as_of_date=as_of_date)
        if not filing:
            filing = self.get_filing_text(ticker, "10-Q", as_of_date=as_of_date)
        return filing

    def get_news(self, ticker: str, days: int = 7, as_of_date: Optional[date] = None):
        return []

    def health_check(self) -> bool:
        try:
            resp = requests.get(
                "https://www.sec.gov/files/company_tickers.json",
                headers=HEADERS, timeout=10
            )
            return resp.status_code == 200
        except Exception:
            return False
