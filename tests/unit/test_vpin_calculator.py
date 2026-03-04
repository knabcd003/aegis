import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from engines.quant.vpin_calculator import VPINCalculator

def generate_intraday_data(bars: int = 390, toxic_fraction: float = 0.2) -> pd.DataFrame:
    """
    Generate fake 1-minute intraday data.
    - Majority of the day is a random walk with normal volume.
    - The last portion of the day experiences heavy informed selling (high volume, price drop) -> Toxic flow.
    """
    dates = [datetime(2025, 1, 1, 9, 30) + timedelta(minutes=i) for i in range(bars)]
    
    normal_bars = int(bars * (1 - toxic_fraction))
    toxic_bars = bars - normal_bars
    
    # Normal trading (balanced buy/sell, small price changes, average volume)
    returns_normal = np.random.normal(0, 0.0005, size=normal_bars)
    vol_normal = np.random.normal(1000, 200, size=normal_bars)
    
    # Toxic institutional dumping (constant negative drift, massive volume)
    returns_toxic = np.random.normal(-0.002, 0.001, size=toxic_bars)
    vol_toxic = np.random.normal(5000, 1000, size=toxic_bars) # 5x volume
    
    all_returns = np.concatenate([returns_normal, returns_toxic])
    all_vols = np.concatenate([vol_normal, vol_toxic])
    all_vols = np.abs(all_vols) # no negative volume
    
    prices = [100.0]
    for r in all_returns:
        prices.append(prices[-1] * np.exp(r))
        
    df = pd.DataFrame({
        "date": dates,
        "close": prices[1:],
        "volume": all_vols
    })
    return df

@pytest.fixture
def test_data():
    return generate_intraday_data()

def test_vpin_initialization():
    calc = VPINCalculator(threshold=0.85)
    assert calc.name == "VPIN_EWMA"
    assert calc.threshold == 0.85

def test_vpin_synthetic_toxic_detection(test_data):
    """
    Test that the VPIN estimator successfully flags the toxic flow 
    inserted at the end of the synthetic dataset.
    """
    calc = VPINCalculator(threshold=0.25) # lowered to account for synthetic distribution
    res = calc.predict(test_data)
    
    assert "error" not in res
    assert "vpin" in res
    assert "is_toxic" in res
    
    vpin_score = res["vpin"]
    assert 0.0 <= vpin_score <= 1.0
    
    # Because we explicitly appended a massive volume, heavy negative drift block,
    # the probability of informed trading (VPIN) should have spiked.
    assert res["is_toxic"] is True, f"VPIN {vpin_score} failed to flag toxic dump"

@pytest.mark.integration
def test_vpin_real_data_validation():
    """
    Validation Test: Hit real DataEngine for 1-minute AAPL data.
    Ensure flowrisk doesn't crash on real-world jagged arrays.
    """
    from engines.data_ingestion.data_engine import DataEngine
    from engines.data_ingestion.connectors.yfinance_connector import YFinanceConnector
    
    engine = DataEngine(data_dir="/tmp/aegis_test_data")
    engine.register(YFinanceConnector(), priority=1)
    
    # Fetch 1m intraday data
    df = engine.get_prices("AAPL", days=2, interval="1m")
    
    if df is None or df.empty or len(df) < 50:
        pytest.skip("Could not fetch intraday data for VPIN integration test.")
        
    calc = VPINCalculator()
    res = calc.predict(df)
    
    assert "error" not in res
    assert "vpin" in res
    assert 0.0 <= res["vpin"] <= 1.0
    assert isinstance(res["is_toxic"], bool)
