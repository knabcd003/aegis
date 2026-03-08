"""
Systems Router — Tracks the state of deployed autonomous trading systems.

This module acts as the "mission control" data source for the Command Center UI.
It manages an in-memory registry of configured systems, their statuses, and live
activity events. A more robust implementation would use Redis or a database.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from datetime import datetime
import uuid

router = APIRouter()

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
