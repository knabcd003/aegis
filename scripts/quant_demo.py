import sys
import os

# Add root project dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from engines.data_ingestion.data_engine import DataEngine
from engines.data_ingestion.connectors.yfinance_connector import YFinanceConnector
from engines.quant.hmm_model import MarketRegimeHMM
from engines.quant.portfolio_optimizer import HierarchicalRiskParityOptimizer
from engines.quant.vpin_calculator import VPINCalculator

def run_quant_demo():
    print("Initializing Data Engine...")
    engine = DataEngine(data_dir="/tmp/aegis_demo_data")
    engine.register(YFinanceConnector(), priority=1)
    
    # 1. Regime Detection (needs daily SPY and VIX)
    print("\n" + "="*50)
    print("--- 1. Market Regime Detection (HMM) ---")
    print("Fetching SPY and ^VIX daily data for the last 2 years...")
    spy_df = engine.get_prices("SPY", days=730, interval="1d")
    vix_df = engine.get_prices("^VIX", days=730, interval="1d")
    
    if spy_df is not None and vix_df is not None and not spy_df.empty and not vix_df.empty:
        # Align indices
        # ensure dates match
        spy_df['vix'] = vix_df['close']
        spy_df = spy_df.dropna()
        
        hmm = MarketRegimeHMM()
        print("Training unsupervised Gaussian HMM on historical data to discover regimes...")
        hmm.train(spy_df)
        
        print("Running inference on current market data...")
        regime_res = hmm.predict(spy_df)
        if "error" in regime_res:
             print(f"HMM Error: {regime_res['error']}")
        else:
            print(f"\n=> Current Market Regime: **{regime_res.get('current_regime')}**")
            probs = regime_res.get('regime_probabilities', {})
            print("=> Regime Probabilities:")
            for k, v in probs.items():
                print(f"     {k}: {v*100:.2f}%")
    else:
        print("Failed to fetch SPY/VIX data.")

    # 2. Portfolio Optimization
    print("\n" + "="*50)
    print("--- 2. Portfolio Optimization (Hierarchical Risk Parity) ---")
    tickers = ["AAPL", "MSFT", "NVDA", "TLT", "GLD", "JPM", "XOM"]
    print(f"Fetching 2 years of daily data for basket: {tickers}")
    prices = {}
    for t in tickers:
        df = engine.get_prices(t, days=730, interval="1d")
        if df is not None and not df.empty:
            prices[t] = df['close']
            
    if prices:
        price_df = pd.DataFrame(prices).dropna()
        opt = HierarchicalRiskParityOptimizer()
        print("Running HRP ML clustering optimization on covariance matrix...")
        weights = opt.predict(price_df)
        
        if "error" in weights:
            print(f"HRP Error: {weights['error']}")
        else:
            print("\n=> Optimal HRP Target Portfolio Weights:")
            # sort by weight
            sorted_weights = sorted(weights.items(), key=lambda x: float(x[1]), reverse=True)
            for t, w in sorted_weights:
                print(f"     {t}: {float(w)*100:.2f}%")
    else:
        print("Failed to fetch portfolio data.")
        
    # 3. VPIN Toxicity
    print("\n" + "="*50)
    print("--- 3. Order Flow Toxicity (VPIN) ---")
    print("Fetching 1-minute intraday data for heavily traded volume (SPY) over last 2 days...")
    spy_intraday = engine.get_prices("SPY", days=2, interval="1m")
    if spy_intraday is not None and not spy_intraday.empty:
        vpin = VPINCalculator(threshold=0.8)
        print("Calculating Recursive EWMA VPIN on volume-synchronized buckets...")
        vpin_res = vpin.predict(spy_intraday)
        
        if "error" in vpin_res:
            print(f"VPIN Error: {vpin_res['error']}")
        else:
            print(f"\n=> Current VPIN Toxicity Score: {vpin_res.get('vpin', 0):.4f} (Scale: 0.0 -> 1.0)")
            toxic = vpin_res.get('is_toxic')
            flag_str = "⚠️ TOXIC FLOW DETECTED" if toxic else "✅ NORMAL FLOW"
            print(f"=> Status: {flag_str} (Threshold used: {vpin.threshold})")
    else:
        print("Failed to fetch intraday data.")

if __name__ == '__main__':
    run_quant_demo()
