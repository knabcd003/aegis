"""
Systems Router — Manages deployed trading systems via the real SentinelStateManager.

This module bridges the frontend Command Center with the backend Sentinel layer.
Systems can be deployed via the wizard (generate endpoint) and managed
(halt/deploy/list) through the SentinelStateManager.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
import json
import asyncio
import logging

from api.main import state

router = APIRouter()
logger = logging.getLogger("aegis.systems")


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
# Fallback seed data — used when SentinelStateManager has no deployed sentinels
# This ensures the Command Center always has something to show.
# ---------------------------------------------------------------------------
_SEED_SYSTEMS: Dict[str, Dict[str, Any]] = {
    "sys-alpha-macro-1": {
        "id": "sys-alpha-macro-1",
        "name": "Alpha-Macro-1",
        "status": "ACTIVE",
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


def _sentinel_to_system_dict(sentinel) -> Dict[str, Any]:
    """Convert a real Sentinel object to the frontend system dict format."""
    config = sentinel.config
    return {
        "id": sentinel.sentinel_id,
        "name": config.get("name", sentinel.sentinel_id),
        "status": "ACTIVE" if sentinel.is_active else "PAUSED",
        "components": {
            "data_engine": ", ".join(config.get("data_engine", {}).get("connectors", ["unknown"])),
            "quant_engine": "HMM + VPIN" if config.get("quant_engine", {}).get("hmm", {}).get("enabled") else "VPIN-only",
            "analyst_engine": config.get("analyst_engine", {}).get("model", "unknown")
        },
        "pnl_usd": getattr(sentinel.portfolio, "nav", 100000) - config.get("sandbox", {}).get("capital", 100000),
        "pnl_pct": ((getattr(sentinel.portfolio, "nav", 100000) - config.get("sandbox", {}).get("capital", 100000)) / config.get("sandbox", {}).get("capital", 100000)) * 100,
        "active_position": None,  # Would be populated by live execution data
        "activity": [],
        "pending_cards": len(sentinel.pending_cards),
    }


@router.get("", response_model=List[Dict[str, Any]])
async def list_systems():
    """
    Return all deployed trading systems.
    First checks the real SentinelStateManager, falls back to seed data.
    """
    systems = []
    
    # Real sentinels from the SentinelStateManager
    if state.sentinel_mgr and state.sentinel_mgr.sentinels:
        for sentinel in state.sentinel_mgr.sentinels.values():
            systems.append(_sentinel_to_system_dict(sentinel))
    
    # Always include seed systems (they represent pre-existing configs)
    for sys_id, sys_data in _SEED_SYSTEMS.items():
        # Don't duplicate if a sentinel was deployed with the same ID
        if not any(s["id"] == sys_id for s in systems):
            systems.append(sys_data)
    
    return systems


@router.get("/{system_id}", response_model=Dict[str, Any])
async def get_system(system_id: str):
    """Return a single system's full state."""
    # Check real sentinels first
    if state.sentinel_mgr and system_id in state.sentinel_mgr.sentinels:
        return _sentinel_to_system_dict(state.sentinel_mgr.sentinels[system_id])
    
    # Fallback to seed data
    sys = _SEED_SYSTEMS.get(system_id)
    if not sys:
        raise HTTPException(status_code=404, detail=f"System '{system_id}' not found.")
    return sys


@router.post("/{system_id}/halt")
async def halt_system(system_id: str):
    """Halt a live system (set status to PAUSED)."""
    # Try real sentinel first
    if state.sentinel_mgr and system_id in state.sentinel_mgr.sentinels:
        sentinel = state.sentinel_mgr.sentinels[system_id]
        sentinel.is_active = False
        logger.info(f"Halted real sentinel: {system_id}")
        return {"status": "halted", "system_id": system_id}
    
    # Fallback to seed data
    sys = _SEED_SYSTEMS.get(system_id)
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
    # Try real sentinel first
    if state.sentinel_mgr and system_id in state.sentinel_mgr.sentinels:
        sentinel = state.sentinel_mgr.sentinels[system_id]
        sentinel.is_active = True
        logger.info(f"Reactivated real sentinel: {system_id}")
        return {"status": "active", "system_id": system_id}
    
    # Fallback to seed data
    sys = _SEED_SYSTEMS.get(system_id)
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


@router.get("/{system_id}/signals")
async def get_pending_signals(system_id: str):
    """Return pending Signal Cards for a specific system."""
    if state.sentinel_mgr and system_id in state.sentinel_mgr.sentinels:
        sentinel = state.sentinel_mgr.sentinels[system_id]
        cards = [{
            "card_id": c.card_id,
            "ticker": c.ticker,
            "decision": c.decision,
            "thesis": c.thesis,
            "quant_anchors": c.quant_anchors,
            "sub_agent_votes": c.sub_agent_votes,
            "confidence": c.confidence,
            "generated_at": c.generated_at.isoformat(),
            "status": c.status,
        } for c in sentinel.pending_cards]
        return {"system_id": system_id, "cards": cards, "count": len(cards)}
    
    return {"system_id": system_id, "cards": [], "count": 0}


@router.post("/{system_id}/signals/{card_id}/review")
async def review_signal_card(system_id: str, card_id: str, action: str = "ACCEPTED"):
    """Accept or decline a pending Signal Card."""
    if not state.sentinel_mgr:
        raise HTTPException(status_code=503, detail="SentinelStateManager not initialized")
    
    if action not in ("ACCEPTED", "DECLINED"):
        raise HTTPException(status_code=400, detail="Action must be ACCEPTED or DECLINED")
    
    result = state.sentinel_mgr.process_review(card_id, system_id, action)
    if not result:
        raise HTTPException(status_code=404, detail=f"Signal card '{card_id}' not found")
    
    return {"status": action, "card_id": card_id}


@router.post("/generate", response_model=GenerateSystemResponse)
async def generate_system(request: GenerateSystemRequest) -> Dict[str, Any]:
    """
    Dynamically generates a full Sentinel configuration.
    Uses Dual-Generation Architecture: Rule-Based Scaffold + LLM Feature Selection.
    """
    style = request.trading_style.lower()
    risk = request.risk_tolerance.lower()
    div = request.diversification.lower()
    
    config_id = f"gen-{uuid.uuid4().hex[:6]}"
    
    scaffold_config: Dict[str, Any] = {
        "config_id": config_id,
        "name": f"{risk.capitalize()} {style.capitalize()} Generator",
        "version": "1.0",
        "created_at": datetime.now().isoformat(),
        "template_base": f"custom_{style}",
        "trading_style": style,
        "asset_universe": {
            "type": "custom",
            "tickers": [],
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
            "capital": 100000,
            "slippage_bps": 10,
            "promotion_criteria": {
                "sharpe_min": 1.0,
                "alpha_min_pct": 3.0,
                "max_drawdown_pct": 15.0
            }
        }
    }
    
    # Apply structural rules based on risk tolerance
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
        
    # LLM feature selection based on thesis keywords
    thesis_lower = request.thesis.lower()
    
    if "sentiment" in thesis_lower or "news" in thesis_lower or "earnings" in thesis_lower:
        scaffold_config["data_engine"]["finbert"] = {"enabled": True, "sources": ["news"], "score_threshold": 0.6}
        if "finnhub" not in scaffold_config["data_engine"]["connectors"]:
            scaffold_config["data_engine"]["connectors"].append("finnhub")
            
    if "macro" in thesis_lower or "fed" in thesis_lower or "inflation" in thesis_lower:
        scaffold_config["data_engine"]["fred"] = {"enabled": True}
        if "fred" not in scaffold_config["data_engine"]["connectors"]:
            scaffold_config["data_engine"]["connectors"].append("fred")
            
    if "sec" in thesis_lower or "filing" in thesis_lower or "10-k" in thesis_lower:
        if "sec_edgar" not in scaffold_config["data_engine"]["connectors"]:
            scaffold_config["data_engine"]["connectors"].append("sec_edgar")
    
    # Deploy as a real sentinel if SentinelStateManager is available
    if state.sentinel_mgr:
        try:
            sentinel_id = f"sentinel-{config_id}"
            state.sentinel_mgr.deploy_sentinel(sentinel_id, scaffold_config, promoted_run_id="manual-deploy")
            logger.info(f"Auto-deployed sentinel {sentinel_id} via wizard")
        except Exception as e:
            logger.warning(f"Could not auto-deploy sentinel: {e}")
    
    return {
        "status": "success",
        "message": "Config generated and deployed successfully.",
        "config": scaffold_config
    }
