import pytest
from engines.data_ingestion.connectors.finbert_connector import FinBERTConnector
from engines.data_ingestion.connectors.sec_edgar_connector import SECEdgarConnector
from engines.data_ingestion.connectors.fred_connector import FREDConnector

@pytest.mark.integration
def test_finbert_sentiment():
    """Test local FinBERT model scoring."""
    fb = FinBERTConnector()
    res = fb.score_text("Apple reported record profits this quarter.")
    assert res["sentiment"] == "positive"
    assert res["score"] > 0.5

@pytest.mark.integration
@pytest.mark.skip(reason="Avoid hitting SEC API too often during CI")
def test_sec_edgar_retrieval():
    """Test retrieving text from EDGAR."""
    edgar = SECEdgarConnector()
    filings = edgar.get_filings_list("AAPL", "10-K", count=1)
    assert len(filings) == 1
    
    text = edgar.get_filing_text("AAPL", "10-K", max_chars=1000)
    assert text is not None
    assert "text" in text
    assert len(text["text"]) > 0

def test_fred_yfinance_fallback():
    """Test FRED connector correctly falls back to yfinance."""
    fred = FREDConnector(api_key=None) # Force no key
    macro = fred.get_macro()
    assert macro["source"] == "yfinance_fallback"
    assert "vix" in macro
    assert "sp500" in macro
