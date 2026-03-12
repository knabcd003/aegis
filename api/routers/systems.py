"""
Systems Router — Tracks the state of deployed autonomous trading systems.

This module acts as the "mission control" data source for the Command Center UI.
It manages an in-memory registry of configured systems, their statuses, and live
activity events. A more robust implementation would use Redis or a database.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
import json
import asyncio

router = APIRouter()

class GenerateSystemRequest(BaseModel):
    thesis: str
    trading_style: str  # e.g., "swing", "intraday", "position"
    risk_tolerance: str # e.g., "conservative", "moderate", "aggressive"
    diversification: str # e.g., "concentrated", "broad"

class GenerateSystemResponse(BaseModel):
    status: str
    message: str
    config: Dict[str, Any]

# ---------------------------------------------------------------------------
# In-memory System Registry
# In production this would be persisted to Redis / Postgres.
# Keys = system ID, values = system config + live state.
# ---------------------------------------------------------------------------
_SYSTEMS: Dict[str, Dict[str, Any]] = {
    "sys-alpha-macro-1": {
        "id": "sys-alpha-macro-1",
        "name": "Alpha-Macro-1",
        "status": "ACTIVE",  # ACTIVE | PAUSED | BACKTESTING
        "components": {
            "data_engine": "YFinance + FRED",
            "quant_engine": "HMM-3State + VPIN",
            "analyst_engine": "14b Qwen Supervisor"
        },
        "pnl_usd": 4520.0,
        "pnl_pct": 2.4,
        "active_position": {
            "ticker": "AAPL",
            "direction": "LONG",
            "shares": 140,
            "entry_price": 150.24
        },
        "activity": [
            {
                "ts": "2026-03-07T09:30:12",
                "event": "BUY",
                "ticker": "AAPL",
                "rationale": "Regime=Bull, VPIN=0.12 (non-toxic). Favorable entry."
            },
            {
                "ts": "2026-03-07T08:00:01",
                "event": "SCAN_START",
                "ticker": "AAPL",
                "rationale": "Market open scan initiated for watchlist."
            }
        ]
    },
    "sys-sentiment-bot-b": {
        "id": "sys-sentiment-bot-b",
        "name": "Sentiment-Bot-B",
        "status": "PAUSED",
        "components": {
            "data_engine": "NewsAPI + FinBERT",
            "quant_engine": "VPIN-only",
            "analyst_engine": "DeepSeek Llama"
        },
        "pnl_usd": -120.0,
        "pnl_pct": -0.1,
        "active_position": None,
        "activity": [
            {
                "ts": "2026-03-06T14:22:00",
                "event": "SELL",
                "ticker": "NVDA",
                "rationale": "FinBERT sentiment turned sharply negative (score: -0.82). Liquidated to avoid drawdown."
            }
        ]
    }
}


@router.get("", response_model=List[Dict[str, Any]])
async def list_systems():
    """Return all deployed or paused trading systems."""
    return list(_SYSTEMS.values())


@router.get("/{system_id}", response_model=Dict[str, Any])
async def get_system(system_id: str):
    """Return a single system's full state including activity log."""
    sys = _SYSTEMS.get(system_id)
    if not sys:
        raise HTTPException(status_code=404, detail=f"System '{system_id}' not found.")
    return sys


@router.post("/{system_id}/halt")
async def halt_system(system_id: str):
    """Halt a live system (set status to PAUSED)."""
    sys = _SYSTEMS.get(system_id)
    if not sys:
        raise HTTPException(status_code=404, detail=f"System '{system_id}' not found.")
    sys["status"] = "PAUSED"
    sys["activity"].insert(0, {
        "ts": datetime.now().isoformat(),
        "event": "HALT",
        "ticker": sys.get("active_position", {}).get("ticker", "N/A") if sys.get("active_position") else "N/A",
        "rationale": "System manually halted by operator."
    })
    return {"status": "halted", "system_id": system_id}


@router.post("/{system_id}/deploy")
async def deploy_system(system_id: str):
    """Re-activate a paused system."""
    sys = _SYSTEMS.get(system_id)
    if not sys:
        raise HTTPException(status_code=404, detail=f"System '{system_id}' not found.")
    sys["status"] = "ACTIVE"
    sys["activity"].insert(0, {
        "ts": datetime.now().isoformat(),
        "event": "DEPLOY",
        "ticker": "N/A",
        "rationale": "System reactivated by operator."
    })
    return {"status": "active", "system_id": system_id}

@router.post("/generate", response_model=GenerateSystemResponse)
async def generate_system(request: GenerateSystemRequest) -> Dict[str, Any]:
    """
    Dynamically generates a full Sentinel configuration matching the system_blueprint.md schema.
    Uses Dual-Generation Architecture: Rule-Based Scaffold + LLM Feature Selection.
    """
    # 1. Rule-Based Scaffold: Deterministic mapping of structural params
    style = request.trading_style.lower()
    risk = request.risk_tolerance.lower()
    div = request.diversification.lower()
    
    scaffold_config: Dict[str, Any] = {
        "config_id": f"gen-{uuid.uuid4().hex[:6]}",
        "name": f"{risk.capitalize()} {style.capitalize()} Generator",
        "version": "1.0",
        "created_at": datetime.now().isoformat(),
        "template_base": f"custom_{style}",
        "trading_style": style,
        "asset_universe": {
            "type": "custom",
            "tickers": [], # To be filled
            "benchmark": "SPY"
        },
        "data_engine": {
            "connectors": ["yfinance"],
            "lookback_days": 252
        },
        "quant_engine": {
            "hmm": {"enabled": True, "n_components": 3, "training_window_days": 750},
            "vpin": {"enabled": True, "toxicity_threshold": 0.8},
            "position_sizing": {"method": "equal_weight", "max_position_pct": 0.1}
        },
        "analyst_engine": {
            "provider": "ollama",
            "model": "qwen3:8b",
            "pipeline": ["analyst", "risk_manager"]
        },
        "sandbox": {
            "slippage_bps": 10,
            "promotion_criteria": {
                "sharpe_min": 1.0,
                "alpha_min_pct": 3.0,
                "max_drawdown_pct": 15.0
            }
        }
    }
    
    # Apply structural rules
    if risk == "conservative":
        scaffold_config["quant_engine"]["vpin"]["toxicity_threshold"] = 0.65
        scaffold_config["quant_engine"]["position_sizing"]["max_position_pct"] = 0.05
        scaffold_config["sandbox"]["promotion_criteria"]["max_drawdown_pct"] = 8.0
        scaffold_config["sandbox"]["promotion_criteria"]["sharpe_min"] = 1.2
    elif risk == "aggressive":
        scaffold_config["quant_engine"]["vpin"]["toxicity_threshold"] = 0.90
        scaffold_config["quant_engine"]["position_sizing"]["max_position_pct"] = 0.25
        scaffold_config["sandbox"]["promotion_criteria"]["max_drawdown_pct"] = 25.0
        scaffold_config["sandbox"]["promotion_criteria"]["sharpe_min"] = 0.8
        
    if style == "intraday":
        scaffold_config["data_engine"]["lookback_days"] = 30
        if "alpaca" not in scaffold_config["data_engine"]["connectors"]:
            scaffold_config["data_engine"]["connectors"].append("alpaca")
            
    if div == "broad":
        scaffold_config["asset_universe"]["tickers"] = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "JNJ", "V", "WMT"]
    elif div == "concentrated":
        scaffold_config["asset_universe"]["tickers"] = ["AAPL", "MSFT", "NVDA"]
        
    # 2. LLM Feature Selection (Simulated Network Call)
    # In production, this would invoke Langchain to evaluate thesis string
    await asyncio.sleep(2) # Simulate LLM thinking latency
    
    llm_features = {}
    thesis_lower = request.thesis.lower()
    
    # Mock LLM reasoning based on thesis keywords
    if "sentiment" in thesis_lower or "news" in thesis_lower or "earnings" in thesis_lower:
        llm_features["finbert"] = {"enabled": True, "sources": ["news"], "score_threshold": 0.6}
        if "finnhub" not in scaffold_config["data_engine"]["connectors"]:
            scaffold_config["data_engine"]["connectors"].append("finnhub")
            
    if "macro" in thesis_lower or "fed" in thesis_lower or "inflation" in thesis_lower:
        llm_features["fred"] = {"enabled": True}
        if "fred" not in scaffold_config["data_engine"]["connectors"]:
            scaffold_config["data_engine"]["connectors"].append("fred")
            
    if "sec" in thesis_lower or "filing" in thesis_lower or "10-k" in thesis_lower:
        if "sec_edgar" not in scaffold_config["data_engine"]["connectors"]:
            scaffold_config["data_engine"]["connectors"].append("sec_edgar")
            
    # 3. Merge & Validate
    data_engine_config: Dict[str, Any] = scaffold_config.get("data_engine", {})
    data_engine_config.update(llm_features)
    scaffold_config["data_engine"] = data_engine_config
    
    # Ideally, we would explicitly validate `scaffold_config` against a Pydantic Model here 
    # to guarantee schema compliance before returning to the frontend.
    
    return {
        "status": "success",
        "message": "Config generated successfully.",
        "config": scaffold_config
    }
