import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from engines.quant.hmm_model import MarketRegimeHMM

def generate_synthetic_data(days: int = 150) -> pd.DataFrame:
    """Generate fake SPY close prices mimicking two distinct regimes."""
    dates = [datetime(2025, 1, 1) + timedelta(days=i) for i in range(days)]
    
    # Regime 1: Bull Market (low vol, positive drift) - Days 0-100
    r1_returns = np.random.normal(loc=0.001, scale=0.005, size=100)
    
    # Regime 2: Bear Crash (high vol, negative drift) - Days 100-150
    # Make it extremely distinct: -3% daily drift, 5% daily volatility
    r2_returns = np.random.normal(loc=-0.03, scale=0.05, size=50)
    
    all_returns = np.concatenate([r1_returns, r2_returns])
    
    # Convert returns to prices starting at $100
    prices = [100.0]
    for r in all_returns:
        prices.append(prices[-1] * np.exp(r))
        
    df = pd.DataFrame({
        "date": dates,
        "close": prices[1:] # Drop initial $100 seed
    })
    return df

@pytest.fixture
def synthetic_df():
    return generate_synthetic_data()

def test_hmm_initialization():
    hmm = MarketRegimeHMM(n_components=3)
    assert hmm.name == "GaussianHMM_3State"
    assert not hmm.is_trained

def test_hmm_synthetic_training(synthetic_df):
    """Test that the HMM can identify two distinct regimes in synthetic data."""
    # We use 2 components because we deliberately built a 2-regime dataset
    hmm = MarketRegimeHMM(n_components=2)
    hmm.train(synthetic_df)
    
    assert hmm.is_trained
    assert len(hmm.state_labels) == 2
    
    # Check that labels properly mapped Bull and Bear based on Volatility
    assert MarketRegimeHMM.REGIME_BULL in hmm.state_labels.values()
    assert MarketRegimeHMM.REGIME_BEAR in hmm.state_labels.values()
    
    # Test Inference
    result = hmm.predict(synthetic_df)
    assert "current_regime" in result
    assert "current_probabilities" in result
    assert "sequence" in result
    
    # Given the last 50 days were our violent crash, the final state MUST be Bear
    assert result["current_regime"] == MarketRegimeHMM.REGIME_BEAR
    assert result["current_probabilities"][MarketRegimeHMM.REGIME_BEAR] > 0.5

@pytest.mark.integration
def test_hmm_covid_crash_validation():
    """
    Validation Test: Hit the real DataEngine for SPY 2019-2020.
    Verify the HMM successfully flags the March 2020 crash. 
    """
    from engines.data_ingestion.data_engine import DataEngine
    from engines.data_ingestion.connectors.yfinance_connector import YFinanceConnector
    from engines.data_ingestion.connectors.fred_connector import FREDConnector
    
    import warnings
    warnings.filterwarnings("ignore")
    
    engine = DataEngine(data_dir="/tmp/aegis_test_data")
    engine.register(YFinanceConnector(), priority=1)
    
    # Fetch SPY prices 365 Days prior to June 2020 (encompassing the Feb/Mar 2020 crash)
    # yfinance history uses actual dates. We need historical prices up to June 2020
    # To reliably get older data without relying on days, we will manually use yfinance
    import yfinance as yf
    spy = yf.Ticker("SPY").history(start="2019-01-01", end="2020-06-01")
    spy = spy.reset_index()
    spy.rename(columns={"Close": "close", "Date": "date"}, inplace=True)
    
    if spy.empty:
        pytest.skip("Could not fetch historical SPY data from yfinance.")
    
    hmm = MarketRegimeHMM(n_components=3)
    hmm.train(spy)
    
    # Let's assess the state on Feb 1st, 2020 (Pre-Crash Bull)
    pre_crash = spy[spy["date"] < "2020-02-01"].copy()
    pre_res = hmm.predict(pre_crash)
    # Should generally be Bullish or at least not Bearish
    assert pre_res["current_regime"] != MarketRegimeHMM.REGIME_BEAR
    
    # Let's assess the state on March 20th, 2020 (Peak Crash)
    crash = spy[spy["date"] < "2020-03-21"].copy()
    crash_res = hmm.predict(crash)
    # The math MUST identify this unique high-variance event
    assert crash_res["current_regime"] in [MarketRegimeHMM.REGIME_BEAR, MarketRegimeHMM.REGIME_VOLATILE]

def test_hmm_save_load(synthetic_df, tmp_path):
    hmm = MarketRegimeHMM(n_components=2, model_dir=str(tmp_path))
    hmm.train(synthetic_df)
    hmm.save("test_model.joblib")
    
    hmm2 = MarketRegimeHMM(model_dir=str(tmp_path))
    hmm2.load("test_model.joblib")
    
    assert hmm2.is_trained
    assert hmm2.n_components == 2
    assert hmm2.state_labels == hmm.state_labels
