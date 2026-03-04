import os
import pytest
import pandas as pd
from typing import Dict, Any

from engines.data_ingestion.data_engine import DataEngine
from engines.data_ingestion.base_connector import BaseConnector

class MockConnector(BaseConnector):
    """A mock connector that returns static data for testing without hitting APIs."""
    
    @property
    def name(self) -> str:
        return "mock_connector"
    
    @property
    def provides_prices(self) -> bool:
        return True
        
    @property
    def provides_fundamentals(self) -> bool:
        return True
        
    @property
    def provides_news(self) -> bool:
        return True

    def get_prices(self, ticker: str, days: int = 30) -> pd.DataFrame:
        if ticker == "FAIL":
            raise Exception("Mock price failure")
        return pd.DataFrame({
            "date": ["2026-01-01", "2026-01-02"],
            "open": [100.0, 101.0],
            "high": [105.0, 106.0],
            "low": [99.0, 100.0],
            "close": [104.0, 105.0],
            "volume": [1000, 2000]
        })
        
    def get_fundamentals(self, ticker: str) -> Dict[str, Any]:
        return {"pe_ratio": 15.5, "short_ratio": 2.1}
        
    def get_news(self, ticker: str, days: int = 7) -> list:
        return [{"headline": "Mock News", "date": "2026-01-01"}]
        
    def health_check(self) -> bool:
        return True

@pytest.fixture
def test_engine(tmp_path):
    """Fixture to provide a pristine engine with a temporary cache directory."""
    engine = DataEngine(data_dir=str(tmp_path))
    engine.register(MockConnector(), priority=1)
    return engine

def test_registry(test_engine):
    """Test that connectors register correctly with priorities."""
    assert test_engine.list_connectors() == ["mock_connector"]

def test_price_caching(test_engine, tmp_path):
    """Test that data is fetched and cached to Parquet."""
    df = test_engine.get_prices("AAPL")
    
    assert df is not None
    assert len(df) == 2
    
    # Check that parquet file was created
    cache_path = tmp_path / "prices" / "AAPL.parquet"
    assert cache_path.exists()
    
    # Second fetch should hit cache
    df2 = test_engine.get_prices("AAPL")
    assert len(df2) == 2

def test_duckdb_queries(test_engine):
    """Test that DuckDB can query cached parquets."""
    # Seed the cache
    test_engine.get_prices("AAPL")
    test_engine.get_prices("NVDA")
    
    # Query across multiple files
    res = test_engine.query_prices(["AAPL", "NVDA"])
    assert len(res) == 4  # 2 rows each
    assert "date" in res.columns
    assert "close" in res.columns

def test_ttl_expiry(test_engine):
    """Test that setting a 0 TTL forces a re-fetch."""
    df1 = test_engine.get_prices("AAPL")
    # ttl_override=0 forces bypassing cache
    df2 = test_engine.get_prices("AAPL", ttl_override=0)
    assert df1 is not None and df2 is not None

def test_full_snapshot(test_engine):
    """Test get_full_snapshot returns required keys."""
    snap = test_engine.get_full_snapshot("AAPL")
    assert snap["ticker"] == "AAPL"
    assert snap["prices"] is not None
    assert snap["fundamentals"] is not None
    assert snap["news"] is not None
