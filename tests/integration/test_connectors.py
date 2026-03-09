"""
Integration tests for the live data connectors (Step 1).
These tests hit live APIs to ensure our point-in-time logic and immutable ledger
work end-to-end with real payloads, not just mocks.

Requires setting FINNHUB_API_KEY and FRED_API_KEY in the environment or .env file.
"""
import os
import pytest
from datetime import date, timedelta
from dotenv import load_dotenv

# Load keys from .env if present
load_dotenv()

# We mark these as integration so they can be skipped during fast unit test runs
pytestmark = pytest.mark.integration

# -----------------------------------------------------------------------------
# YFinance (Free, No Key)
# -----------------------------------------------------------------------------
def test_yfinance_live_prices():
    """Verify YFinance price fetching and ledger cache work with real data."""
    from engines.data_ingestion.connectors.yfinance_connector import YFinanceConnector
    from engines.data_ingestion import ledger
    
    connector = YFinanceConnector()
    # Fetch 5 days of history for MSFT
    df = connector.get_prices("MSFT", days=5)
    
    assert df is not None
    assert not df.empty
    assert "public_disclosure_ts" in df.columns
    
    # Verify it was written to the immutable ledger
    stats = ledger.ledger_stats()
    assert stats["price_files"] > 0
    
    # Read back from ledger using as_of_date
    cached_df = ledger.read_prices("MSFT", as_of_date=date.today())
    assert cached_df is not None
    assert not cached_df.empty
    assert "public_disclosure_ts" in cached_df.columns

# -----------------------------------------------------------------------------
# SEC EDGAR (Free, No Key, Rate Limited)
# -----------------------------------------------------------------------------
def test_sec_edgar_live_filings_and_nli():
    """Verify SEC EDGAR text retrieval, immutable cache, and the DeBERTa NLI gate."""
    from engines.data_ingestion.connectors.sec_edgar_connector import SECEdgarConnector, classify_segment_change
    from engines.data_ingestion import ledger
    
    connector = SECEdgarConnector()
    
    # 1. Fetch a recent 10-K for AAPL
    filings = connector.get_filings_list("AAPL", "10-K", count=1)
    assert len(filings) == 1
    
    accession = filings[0]["accession_number"]
    
    # 2. Fetch the text (this writes it to the ledger)
    text_data = connector.get_filing_text("AAPL", "10-K", max_chars=5000)
    assert text_data is not None
    assert "text" in text_data
    assert len(text_data["text"]) > 0
    
    # 3. Verify it's in the immutable ledger
    accession = filings[0]["accession_number"]
    assert ledger.filing_exists("AAPL", accession)
    
    # 4. Test the NLI Gate (Stage 1 of Trap 1)
    # This will trigger the ~183MB download of DeBERTa if not already cached
    res_entailment = classify_segment_change("Azure Revenue", "Azure Revenue")
    assert res_entailment == "ENTAILMENT"
    
    res_neutral = classify_segment_change("Azure Revenue", "Azure and AI Cloud Services")
    assert res_neutral in ("NEUTRAL", "CONTRADICTION")

# -----------------------------------------------------------------------------
# FinBERT (Local Model)
# -----------------------------------------------------------------------------
def test_finbert_live_inference():
    """Verify FinBERT model pipeline inference."""
    pytest.skip("Skipping FinBERT in integration tests to avoid a 430MB model download and torch compatibility checks.")
        
    from engines.data_ingestion.connectors.finbert_connector import FinBERTConnector
    
    connector = FinBERTConnector()
    
    # Test positive sentiment block
    res = connector.score_text("Apple reported record breaking profits this quarter.", source_disclosure_ts="2023-01-01")
    assert res["sentiment"] == "positive"
    assert res["public_disclosure_ts"] == "2023-01-01"

# -----------------------------------------------------------------------------
# Congressional Disclosures (Free, HTML Parsing)
# -----------------------------------------------------------------------------
def test_congressional_live_disclosures():
    """Verify Congressional STOCK Act parsing logic against live house/senate pages."""
    from engines.data_ingestion.connectors.congressional_connector import CongressionalConnector
    
    connector = CongressionalConnector()
    
    # Run a broad fetch across all tickers for a recent date to ensure we hit data
    # We use a broad request (MSFT usually has activity, or we get empty list but valid parsing)
    disclosures = connector.get_disclosures("MSFT", days_back=365, as_of_date=date.today())
    
    # We can't guarantee a senator traded MSFT in the last 365 days, 
    # but if they did, ensure lookahead bias guard is active.
    for d in disclosures:
        assert d["public_disclosure_ts"] == d["disclosure_filing_ts"]
        assert d["public_disclosure_ts"] >= d["trade_date"]

# -----------------------------------------------------------------------------
# Authed Endpoints (Depends on API Keys)
# -----------------------------------------------------------------------------
@pytest.mark.skipif(not os.getenv("FINNHUB_API_KEY"), reason="FINNHUB_API_KEY not set in .env")
def test_finnhub_live_endpoints():
    """Verify Finnhub news, insiders, and earnings revisions."""
    from engines.data_ingestion.connectors.finnhub_connector import FinnhubConnector
    
    connector = FinnhubConnector()
    
    # Get recent news
    news = connector.get_news("AAPL", days=5, as_of_date=date.today())
    if len(news) > 0:
        assert "public_disclosure_ts" in news[0]
        
    # Get insider transactions
    insiders = connector.get_insider_transactions("AAPL", as_of_date=date.today())
    if len(insiders) > 0:
        assert "public_disclosure_ts" in insiders[0]
        
    # Get earnings info
    earnings = connector.get_earnings_revisions("AAPL", as_of_date=date.today())
    if len(earnings) > 0:
        assert "public_disclosure_ts" in earnings[0]

@pytest.mark.skipif(not os.getenv("FRED_API_KEY"), reason="FRED_API_KEY not set in .env")
def test_fred_live_macro():
    """Verify ALFRED vintage fetching for macro data."""
    from engines.data_ingestion.connectors.fred_connector import FREDConnector
    from engines.data_ingestion import ledger
    
    connector = FREDConnector()
    macro = connector.get_macro(as_of_date=date.today())
    
    # Assert primary source is fred_api not fallback
    assert macro["source"] == "fred_api"
    assert "public_disclosure_ts" in macro["treasury_10y"]
    
    # Verify audit snapshot written
    stats = ledger.ledger_stats()
    assert stats["macro_snapshot_files"] > 0
