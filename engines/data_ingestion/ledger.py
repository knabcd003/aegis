"""
Immutable Filing Ledger — Point-in-time data integrity for all backtests.

Four rules:
  1. Price bars cached at download time. Never re-fetched for a past date.
  2. SEC filings stored by accession number. Immutable — never overwritten.
  3. Restated/amended filings stored as separate accession numbers, not replacements.
  4. FRED data is exempt — ALFRED vintage timestamps are the source of truth there.

Every record the simulation loop reads has a public_disclosure_ts field.
The simulation loop only sees records where public_disclosure_ts <= simulation_date.
"""
import os
import json
import hashlib
import shutil
from datetime import date, datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd

# ── Ledger root ─────────────────────────────────────────────────────────────

def _ledger_root() -> Path:
    """Return the ledger root, re-reading AEGIS_LEDGER_ROOT on every call.
    This ensures tests can override the path via environment variable or monkeypatch.
    """
    return Path(os.getenv("AEGIS_LEDGER_ROOT", "data/ledger"))


def _prices_dir() -> Path:
    d = _ledger_root() / "prices"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _filings_dir(ticker: str) -> Path:
    d = _ledger_root() / "sec_filings" / ticker.upper()
    d.mkdir(parents=True, exist_ok=True)
    return d


def _macro_dir() -> Path:
    d = _ledger_root() / "macro"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── Price ledger ─────────────────────────────────────────────────────────────

def prices_path(ticker: str, download_date: date) -> Path:
    """One Parquet file per ticker per download date."""
    return _prices_dir() / f"{ticker.upper()}_{download_date.isoformat()}.parquet"


def write_prices(ticker: str, df: pd.DataFrame, download_date: Optional[date] = None) -> Path:
    """
    Write price data to the ledger. Each row must have a 'public_disclosure_ts' column.
    Returns the path written to.

    If a file for this ticker/date already exists, it is NOT overwritten (immutability rule).
    """
    dl_date = download_date or date.today()
    path = prices_path(ticker, dl_date)

    if path.exists():
        return path  # Immutable — never overwrite

    if "public_disclosure_ts" not in df.columns:
        raise ValueError(f"[ledger] DataFrame missing 'public_disclosure_ts' column for {ticker}")

    df.to_parquet(path, index=False, engine="pyarrow")
    return path


def read_prices(ticker: str, as_of_date: date) -> Optional[pd.DataFrame]:
    """
    Read all cached price rows for a ticker where public_disclosure_ts <= as_of_date.
    Reads the most recent ledger file whose download_date <= as_of_date.
    Returns None if no data is found.
    """
    price_dir = _prices_dir()
    prefix = f"{ticker.upper()}_"

    # Find all parquet files for this ticker with download_date <= as_of_date
    candidates: List[Path] = []
    for p in price_dir.glob(f"{prefix}*.parquet"):
        try:
            file_date = date.fromisoformat(p.stem[len(prefix):])
            if file_date <= as_of_date:
                candidates.append(p)
        except ValueError:
            continue

    if not candidates:
        return None

    # Use the most recent download file
    candidates.sort(reverse=True)
    df = pd.read_parquet(candidates[0], engine="pyarrow")

    # Enforce point-in-time: only rows visible on or before as_of_date
    df["public_disclosure_ts"] = pd.to_datetime(df["public_disclosure_ts"])
    mask = df["public_disclosure_ts"].dt.date <= as_of_date
    return df[mask].copy()


# ── SEC filing ledger ────────────────────────────────────────────────────────

def filing_path(ticker: str, accession_number: str) -> Path:
    """Path for a specific filing by accession number."""
    safe_accession = accession_number.replace("/", "_").replace("\\", "_")
    return _filings_dir(ticker) / f"{safe_accession}.json"


def filing_exists(ticker: str, accession_number: str) -> bool:
    return filing_path(ticker, accession_number).exists()


def write_filing(ticker: str, accession_number: str, data: Dict[str, Any]) -> Path:
    """
    Write an SEC filing to the immutable ledger.
    If the accession number already exists, returns the existing path WITHOUT overwriting.

    data must include:
      - accession_number: str
      - public_disclosure_ts: ISO date string (filing date — when it became public)
      - form_type: str
      - ticker: str
    """
    path = filing_path(ticker, accession_number)

    if path.exists():
        return path  # Immutable — never overwrite for same accession number

    required = {"accession_number", "public_disclosure_ts", "form_type", "ticker"}
    missing = required - set(data.keys())
    if missing:
        raise ValueError(f"[ledger] Filing data missing required keys: {missing}")

    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    return path


def read_filing(ticker: str, accession_number: str) -> Optional[Dict[str, Any]]:
    """Read a cached filing. Returns None if not in ledger."""
    path = filing_path(ticker, accession_number)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_filings(ticker: str, form_type: str, as_of_date: date) -> List[Dict[str, Any]]:
    """
    List all cached filings for a ticker and form type where
    public_disclosure_ts <= as_of_date.
    Returns list sorted by disclosure date descending (newest first).
    """
    filing_dir = _filings_dir(ticker)
    filings = []

    for p in filing_dir.glob("*.json"):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if data.get("form_type") != form_type:
                continue
            disclosure_ts = date.fromisoformat(str(data["public_disclosure_ts"])[:10])
            if disclosure_ts <= as_of_date:
                data["_disclosure_date"] = disclosure_ts
                filings.append(data)
        except Exception:
            continue

    filings.sort(key=lambda x: x["_disclosure_date"], reverse=True)
    return filings


# ── Macro ledger (audit snapshots) ──────────────────────────────────────────

def write_macro_snapshot(series_id: str, df: pd.DataFrame) -> Path:
    """
    Write a FRED macro snapshot for audit purposes.
    FRED uses ALFRED vintage timestamps — the snapshot is dated at download time.
    These are NOT immutable (FRED may add new release_ts values on each fetch).
    """
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    path = _macro_dir() / f"FRED_{series_id}_{ts}.parquet"
    df.to_parquet(path, index=False, engine="pyarrow")
    return path


# ── Utility ──────────────────────────────────────────────────────────────────

def ledger_stats() -> Dict[str, Any]:
    """Summary of ledger contents. Useful for health checks and debugging."""
    root = _ledger_root()
    price_files = list(_prices_dir().glob("*.parquet")) if _prices_dir().exists() else []
    macro_files = list(_macro_dir().glob("*.parquet")) if _macro_dir().exists() else []

    filing_count = 0
    filing_dir_root = root / "sec_filings"
    if filing_dir_root.exists():
        for subdir in filing_dir_root.iterdir():
            if subdir.is_dir():
                filing_count += len(list(subdir.glob("*.json")))

    return {
        "ledger_root": str(root),
        "price_files": len(price_files),
        "sec_filing_files": filing_count,
        "macro_snapshot_files": len(macro_files),
    }
