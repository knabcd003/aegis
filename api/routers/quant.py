from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
from datetime import datetime

# We will import the global state from main to access the initialized engines
from api.main import state
from engines.quant.hmm_model import MarketRegimeHMM
from engines.quant.vpin_calculator import VPINCalculator
from engines.quant.chronos_forecaster import ChronosForecaster

router = APIRouter()

# Lazy-loaded models to save RAM until requested
_hmm_model: Optional[MarketRegimeHMM] = None
_vpin_calc: Optional[VPINCalculator] = None
_forecaster: Optional[ChronosForecaster] = None

def get_hmm() -> MarketRegimeHMM:
    global _hmm_model
    if _hmm_model is None:
        _hmm_model = MarketRegimeHMM(n_components=3)
    return _hmm_model

def get_vpin() -> VPINCalculator:
    global _vpin_calc
    if _vpin_calc is None:
        _vpin_calc = VPINCalculator(threshold=0.85)
    return _vpin_calc

def get_forecaster() -> ChronosForecaster:
    global _forecaster
    if _forecaster is None:
        _forecaster = ChronosForecaster(model_name="amazon/chronos-bolt-tiny")
    return _forecaster

@router.get("/regime")
async def get_regime(ticker: str = Query(..., description="Stock ticker symbol (e.g., AAPL)")) -> Dict[str, Any]:
    """Calculate the current Hidden Markov Model market regime (Bull/Bear/Volatile)."""
    if not state.data_engine:
        raise HTTPException(status_code=503, detail="Data Engine is offline")
        
    prices = state.data_engine.get_prices(ticker, days=500)
    if prices is None or prices.empty:
        raise HTTPException(status_code=404, detail=f"Could not fetch historical prices for {ticker}")
        
    hmm = get_hmm()
    if not hmm.is_trained:
        hmm.train(prices)
    res = hmm.predict(prices)
    if "error" in res:
        raise HTTPException(status_code=500, detail=res["error"])
    regime = res["current_regime"]
    
    return {
        "ticker": ticker,
        "timestamp": datetime.now().isoformat(),
        "regime": regime,
        "model": "HMM-3State"
    }

@router.get("/vpin")
async def get_vpin_toxicity(ticker: str = Query(..., description="Stock ticker symbol")) -> Dict[str, Any]:
    """Calculate the Volume-Synchronized Probability of Informed Trading (Order Flow Toxicity)."""
    if not state.data_engine:
        raise HTTPException(status_code=503, detail="Data Engine is offline")
        
    # VPIN requires intraday data (e.g. 1m or 5m bars)
    prices = state.data_engine.get_prices(ticker, days=5, interval="5m")
    if prices is None or len(prices) < 50:
        raise HTTPException(status_code=404, detail=f"Insufficient intraday data for {ticker} to calculate VPIN")
        
    vpin_calc = get_vpin()
    vpin_result = vpin_calc.predict(prices)
    
    if "error" in vpin_result:
        raise HTTPException(status_code=500, detail=vpin_result["error"])
        
    return {
        "ticker": ticker,
        "timestamp": datetime.now().isoformat(),
        "vpin_score": round(vpin_result.get("vpin", 0.0), 4),
        "is_toxic": vpin_result.get("is_toxic", False),
        "threshold": vpin_result.get("threshold_used", 0.85)
    }

@router.get("/forecast")
async def get_price_forecast(
    ticker: str = Query(..., description="Stock ticker symbol"),
    horizon: int = Query(14, description="Days to forecast into the future")
) -> Dict[str, Any]:
    """Generate a probabilistic price forecast using Amazon Chronos-Bolt."""
    if not state.data_engine:
        raise HTTPException(status_code=503, detail="Data Engine is offline")
        
    prices = state.data_engine.get_prices(ticker, days=365)
    if prices is None or prices.empty:
        raise HTTPException(status_code=404, detail=f"Could not fetch prices for {ticker}")
        
    forecaster = get_forecaster()
    try:
        # Expected to return low, median, high bounds
        bounds = forecaster.predict(prices, horizon=horizon)
        
        # Format the output cleanly for the frontend charts
        return {
            "ticker": ticker,
            "horizon_days": horizon,
            "forecast": [
                {
                    "step": i + 1,
                    "low": round(bounds["low"][i], 2),
                    "median": round(bounds["median"][i], 2),
                    "high": round(bounds["high"][i], 2)
                }
                for i in range(len(bounds["median"]))
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
