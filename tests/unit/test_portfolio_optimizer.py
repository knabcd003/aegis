import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from engines.quant.portfolio_optimizer import HierarchicalRiskParityOptimizer

def generate_correlated_synthetic_prices(days: int = 100) -> pd.DataFrame:
    """
    Generate prices for 3 assets (A, B, C).
    - A and C are perfectly correlated.
    - B is uncorrelated.
    """
    dates = [datetime(2025, 1, 1) + timedelta(days=i) for i in range(days)]
    
    # Asset B: Independent random walk
    returns_B = np.random.normal(0.0005, 0.01, size=days)
    
    # Asset A: Independent random walk
    returns_A = np.random.normal(0.001, 0.015, size=days)
    
    # Asset C: Essentially identical to A with tiny noise (highly correlated)
    returns_C = returns_A + np.random.normal(0, 0.001, size=days)

    prices_A = 100 * np.exp(np.cumsum(returns_A))
    prices_B = 100 * np.exp(np.cumsum(returns_B))
    prices_C = 100 * np.exp(np.cumsum(returns_C))
    
    df = pd.DataFrame({
        "date": dates,
        "A": prices_A,
        "B": prices_B,
        "C": prices_C
    })
    return df

@pytest.fixture
def synthetic_prices():
    return generate_correlated_synthetic_prices()

def test_hrp_initialization():
    opt = HierarchicalRiskParityOptimizer()
    assert opt.name == "HierarchicalRiskParity"

def test_hrp_synthetic_clustering(synthetic_prices):
    """
    Test that HRP correctly clusters correlated assets.
    Given A and C are basically the same asset, HRP should allocate ~50% to B,
    and split the remaining 50% between A and C (e.g. ~25% each).
    Naive optimization would just do ~33% to all three.
    """
    opt = HierarchicalRiskParityOptimizer()
    weights = opt.predict(synthetic_prices)
    
    assert "error" not in weights
    assert set(weights.keys()) == {"A", "B", "C"}
    
    # Sum of weights should roughly equal 1.0 (allow tiny float imprecision)
    total_weight = sum(weights.values())
    assert abs(total_weight - 1.0) < 1e-4
    
    # Assert B (the uncorrelated asset) gets a significantly higher weight than A or C
    # because A and C are clustered together and forced to share one branch of risk.
    assert weights["B"] > weights["A"]
    assert weights["B"] > weights["C"]
    
    # B should be roughly double A or C
    assert weights["B"] > 0.40 # Should be around ~50%
    assert weights["A"] < 0.35 # Should be around ~25%
    assert weights["C"] < 0.35 # Should be around ~25%

@pytest.mark.integration
def test_hrp_real_data_validation():
    """
    Validation Test: Hit the real DataEngine for historical prices.
    Ensure optimization doesn't crash on messy real-world data and returns valid weights.
    """
    import yfinance as yf
    
    # Fetch 2 years of data for a mix of Tech and Safe Havens
    tickers = ["AAPL", "MSFT", "GLD", "TLT"]
    prices = {}
    for t in tickers:
        df = yf.Ticker(t).history(period="2y")
        if df.empty:
            pytest.skip(f"Could not fetch {t}")
        prices[t] = df["Close"]
        
    price_df = pd.DataFrame(prices).dropna()
    
    if price_df.empty:
        pytest.skip("Could not align historical prices.")
        
    opt = HierarchicalRiskParityOptimizer()
    weights = opt.predict(price_df)
    
    assert "error" not in weights
    assert set(weights.keys()) == set(tickers)
    
    total_weight = sum(weights.values())
    assert abs(total_weight - 1.0) < 1e-4
    
    # All weights must be non-negative (long only) and <= 1.0
    for ticker, w in weights.items():
        assert 0.0 <= w <= 1.0
