import pytest
import pandas as pd
from typing import Dict, Any

from engines.data_ingestion.data_engine import DataEngine
from engines.data_ingestion.base_connector import BaseConnector

class FailingConnector(BaseConnector):
    """A mock connector that always fails."""
    @property
    def name(self) -> str: return "failing_connector"
    @property
    def provides_prices(self) -> bool: return True
    @property
    def provides_fundamentals(self) -> bool: return True
    @property
    def provides_news(self) -> bool: return True
    
    def get_prices(self, ticker: str, days: int = 30):
        # Simulate network error or rate limit
        raise ConnectionError("API Rate Limit Exceeded")
        
    def get_fundamentals(self, ticker: str):
        # Simulate missing data
        return None
        
    def get_news(self, ticker: str, days: int = 7):
        return []

class BackupConnector(BaseConnector):
    """A mock connector that succeeds."""
    @property
    def name(self) -> str: return "backup_connector"
    @property
    def provides_prices(self) -> bool: return True
    @property
    def provides_fundamentals(self) -> bool: return True
    @property
    def provides_news(self) -> bool: return True
    
    def get_prices(self, ticker: str, days: int = 30):
        return pd.DataFrame({
            "date": ["2026-01-01"], "open": [10.0], "high": [11.0], 
            "low": [9.0], "close": [10.5], "volume": [1000]
        })

    def get_news(self, ticker: str, days: int = 7):
        return []

    def get_fundamentals(self, ticker: str):
        return {"pe_ratio": 20.0}

def test_engine_graceful_failure(tmp_path):
    """Test that the engine catches exceptions and returns None instead of crashing."""
    engine = DataEngine(data_dir=str(tmp_path))
    engine.register(FailingConnector(), priority=1)
    
    # Even though it raises ConnectionError inside, the engine catches it
    result = engine.get_prices("AAPL")
    assert result is None
    
    # Missing data also returns None safely
    fund = engine.get_fundamentals("AAPL")
    assert fund is None

def test_engine_fallback_priority(tmp_path):
    """Test that the engine falls back to a lower priority connector if the primary fails."""
    engine = DataEngine(data_dir=str(tmp_path))
    
    # Register failing connector at priority 1
    engine.register(FailingConnector(), priority=1)
    # Register backup connector at priority 2
    engine.register(BackupConnector(), priority=2)
    
    # Engine should try Failing (fails), then try Backup (succeeds)
    result = engine.get_prices("AAPL")
    
    assert result is not None
    assert len(result) == 1
    assert result["close"].iloc[0] == 10.5
