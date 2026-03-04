import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os

from engines.quant.chronos_forecaster import ChronosForecaster

# Skip tests if model weights are explicitly disabled to save CI minutes, 
# or run them locally since we are downloading a large 200MB+ model.
RUN_HEAVY_TESTS = os.environ.get("RUN_HEAVY_TESTS", "1") == "1"

def generate_synthetic_trend(days: int = 90) -> pd.DataFrame:
    """
    Generate fake price data with a strict linear upward trend and minimal noise.
    """
    dates = [datetime(2025, 1, 1) + timedelta(days=i) for i in range(days)]
    
    # Starting at 100, add 1.0 per day, plus tiny noise
    prices = 100.0 + np.arange(days) * 1.0 + np.random.normal(0, 0.1, size=days)
    
    df = pd.DataFrame({
        "date": dates,
        "close": prices
    })
    return df

@pytest.fixture
def test_data():
    return generate_synthetic_trend()

def test_chronos_initialization():
    calc = ChronosForecaster()
    assert calc.name == "ChronosBolt"
    assert calc.model_name == "amazon/chronos-bolt-base"

@pytest.mark.skipif(not RUN_HEAVY_TESTS, reason="Downloads 200MB model")
def test_chronos_synthetic_trend(test_data):
    """
    Test that Chronos-Bolt correctly predicts that an unambiguous straight 
    linear upward trend will continue going up.
    """
    from engines.quant.chronos_forecaster import HAS_CHRONOS
    if not HAS_CHRONOS:
        pytest.skip("Chronos not installed")
        
    calc = ChronosForecaster()
    # Predict next 5 days
    res = calc.predict(test_data, prediction_length=5)
    
    assert "error" not in res
    assert "median" in res
    assert len(res["median"]) == 5
    
    last_historical_price = test_data["close"].iloc[-1]
    last_predicted_price = res["median"][-1]
    
    # Assert the model expects the price to be higher in 5 days than it is today
    # (Because the input signal was a perfectly uniform straight line up)
    assert last_predicted_price > last_historical_price
    
@pytest.mark.integration
@pytest.mark.skipif(not RUN_HEAVY_TESTS, reason="Downloads 200MB model")
def test_chronos_real_data_validation():
    """
    Validation Test: Hit real DataEngine for 90 days of SPY data.
    """
    from engines.data_ingestion.data_engine import DataEngine
    from engines.data_ingestion.connectors.yfinance_connector import YFinanceConnector
    from engines.quant.chronos_forecaster import HAS_CHRONOS
    
    if not HAS_CHRONOS:
        pytest.skip("Chronos not installed")
        
    engine = DataEngine(data_dir="/tmp/aegis_test_data")
    engine.register(YFinanceConnector(), priority=1)
    
    df = engine.get_prices("SPY", days=90, interval="1d")
    
    if df is None or df.empty:
        pytest.skip("Could not fetch intraday data for chronos integration test.")
        
    calc = ChronosForecaster()
    res = calc.predict(df, prediction_length=7)
    
    assert "error" not in res
    assert len(res["median"]) == 7
    assert len(res["lower_bound"]) == 7
    assert len(res["upper_bound"]) == 7
    
    # Check that bounds make logical sense
    for i in range(7):
        assert res["lower_bound"][i] <= res["median"][i] <= res["upper_bound"][i]
