"""
SEC EDGAR Connector — Fetches SEC filing text (10-K, 10-Q, 8-K) for any public company.

No API key required. Uses the SEC EDGAR EFTS full-text search API and filing
archive. SEC requires a User-Agent header with contact info.
"""
import re
import requests
from typing import Dict, List, Optional, Any

from engines.data_ingestion.base_connector import BaseConnector


# SEC requires identifying headers
HEADERS = {
    "User-Agent": "AegisAI research@aegis.ai",
    "Accept-Encoding": "gzip, deflate",
}

# SEC base URLs
EFTS_BASE = "https://efts.sec.gov/LATEST/search-index"
EDGAR_BASE = "https://www.sec.gov/cgi-bin/browse-edgar"
SUBMISSIONS_BASE = "https://data.sec.gov/submissions"
ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar/data"


class SECEdgarConnector(BaseConnector):
    """Fetches SEC filing metadata and text. No API key needed."""

    @property
    def name(self) -> str:
        return "sec_edgar"

    @property
    def provides_prices(self) -> bool:
        return False

    @property
    def provides_fundamentals(self) -> bool:
        return False

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
                    # CIK needs to be zero-padded to 10 digits
                    return str(entry["cik_str"]).zfill(10)

            print(f"[{self.name}] CIK not found for {ticker}")
            return None
        except Exception as e:
            print(f"[{self.name}] Error looking up CIK for {ticker}: {e}")
            return None

    def get_filings_list(self, ticker: str, filing_type: str = "10-K",
                         count: int = 5) -> List[Dict[str, Any]]:
        """
        Get a list of recent filings for a ticker.

        Args:
            ticker: Stock ticker (e.g., "AAPL")
            filing_type: "10-K", "10-Q", "8-K"
            count: Number of filings to return

        Returns:
            List of filing metadata dicts with accession numbers and dates.
        """
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
                if form == filing_type and len(filings) < count:
                    filings.append({
                        "ticker": ticker,
                        "form_type": form,
                        "filing_date": dates[i] if i < len(dates) else "",
                        "accession_number": accessions[i] if i < len(accessions) else "",
                        "primary_document": primary_docs[i] if i < len(primary_docs) else "",
                        "cik": cik,
                    })

            return filings

        except Exception as e:
            print(f"[{self.name}] Error fetching filing list for {ticker}: {e}")
            return []

    def get_filing_text(self, ticker: str, filing_type: str = "10-K",
                        max_chars: int = 50000) -> Optional[Dict[str, Any]]:
        """
        Fetch the most recent filing text for a ticker.

        Returns:
            {
                "ticker": "AAPL",
                "form_type": "10-K",
                "filing_date": "2024-11-01",
                "text": "... filing text ...",
                "sections": { "risk_factors": "...", "business": "..." }
            }
        """
        filings = self.get_filings_list(ticker, filing_type, count=1)
        if not filings:
            print(f"[{self.name}] No {filing_type} filings found for {ticker}")
            return None

        filing = filings[0]
        accession = filing["accession_number"].replace("-", "")
        primary_doc = filing["primary_document"]
        cik = filing["cik"].lstrip("0")

        try:
            url = f"{ARCHIVES_BASE}/{cik}/{accession}/{primary_doc}"
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            raw_text = resp.text

            # Strip HTML tags for cleaner text
            clean_text = re.sub(r'<[^>]+>', ' ', raw_text)
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()

            # Truncate to max_chars
            if len(clean_text) > max_chars:
                clean_text = clean_text[:max_chars]

            # Try to extract key sections
            sections = self._extract_sections(clean_text)

            return {
                "ticker": ticker,
                "form_type": filing_type,
                "filing_date": filing["filing_date"],
                "accession_number": filing["accession_number"],
                "text_length": len(clean_text),
                "text": clean_text,
                "sections": sections,
            }

        except Exception as e:
            print(f"[{self.name}] Error fetching filing text for {ticker}: {e}")
            return None

    def _extract_sections(self, text: str) -> Dict[str, str]:
        """
        Attempt to extract standard 10-K sections from filing text.
        Returns whatever sections we can find.
        """
        sections = {}
        section_markers = {
            "risk_factors": [r"(?i)item\s*1a[\.\s]*risk\s*factors", r"(?i)risk\s*factors"],
            "business": [r"(?i)item\s*1[\.\s]*business"],
            "mda": [r"(?i)item\s*7[\.\s]*management.s\s*discussion"],
            "financial_condition": [r"(?i)financial\s*condition"],
        }

        for section_name, patterns in section_markers.items():
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    # Extract ~5000 chars after the section header
                    start = match.start()
                    end = min(start + 5000, len(text))
                    sections[section_name] = text[start:end].strip()
                    break

        return sections

    # ── BaseConnector interface ──────────────────────────────────────────

    def get_prices(self, ticker: str, days: int = 30):
        return None

    def get_fundamentals(self, ticker: str):
        return None

    def get_news(self, ticker: str, days: int = 7):
        return []

    def health_check(self) -> bool:
        """Check if SEC EDGAR is reachable."""
        try:
            resp = requests.get(
                "https://www.sec.gov/files/company_tickers.json",
                headers=HEADERS, timeout=10
            )
            return resp.status_code == 200
        except Exception:
            return False
