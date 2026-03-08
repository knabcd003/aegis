import pytest
from httpx import AsyncClient, ASGITransport
import asyncio

from api.main import app
from api.main import state

# Mock the underlying engines so the API tests don't actually trigger live Ollama or MLflow runs
@pytest.fixture(autouse=True)
def mock_engines(monkeypatch):
    class MockDataEngine:
        def get_prices(self, ticker, days, interval="1d"):
            import pandas as pd
            import numpy as np
            if ticker == "FAIL":
                return None
            
            # Generate a simple random walk so VPIN math doesn't divide by zero
            closes = np.cumprod(1 + np.random.normal(0, 0.01, 50)) * 10.0
            
            return pd.DataFrame({
                "date": pd.date_range("2026-01-01", periods=50, freq="1h"),
                "open": closes * 0.99, 
                "high": closes * 1.01, 
                "low": closes * 0.98, 
                "close": closes, 
                "volume": np.random.randint(100, 1000, size=50),
                "returns": np.random.normal(0, 0.01, 50)
            })
            
    # Inject the mock engine directly into the FastAPI global state
    state.data_engine = MockDataEngine()

@pytest.mark.asyncio
async def test_health_check():
    """Verify the root health endpoint returns HTTP 200 and sees the injected DataEngine."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["engines"]["data"] == "healthy"

@pytest.mark.asyncio
async def test_quant_vpin_endpoint():
    """Verify the VPIN endpoint successfully calculates and returns a JSON payload."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/quant/vpin?ticker=AAPL")
    
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "AAPL"
    assert "vpin_score" in data
    assert "is_toxic" in data

@pytest.mark.asyncio
async def test_quant_vpin_fail_ticker():
    """Verify the API correctly handles a 404 when data is missing."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/quant/vpin?ticker=FAIL")
    
    assert response.status_code == 404
    assert "Insufficient intraday data" in response.json()["detail"]

@pytest.mark.asyncio
async def test_mlops_sweep_trigger():
    """Verify the MLflow sandbox endpoint accepts POST payloads and returns a job ID."""
    payload = {
        "tickers": ["AAPL", "NVDA"],
        "n_trials": 5,
        "models_to_test": ["mock-model"]
    }
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/mlops/sweep", json=payload)
        
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert "job_id" in data
