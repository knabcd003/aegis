"""
Portfolio Router — Serves portfolio tracking data and gap analysis.

Uses the MirrorPortfolio / CounterfactualTracker from engines/sentinel
to calculate the Human Override Gap (AI-only vs human-modified returns).
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging
import os
import json
from engines.sentinel.freshness_validator import FreshnessValidator, SignalFreshnessState
from engines.sentinel.price_feed import FinnhubPriceFeed

router = APIRouter()
logger = logging.getLogger("aegis.portfolio")

# Singleton validator instance
freshness_validator = FreshnessValidator(price_feed=FinnhubPriceFeed())


class PortfolioSnapshot(BaseModel):
    sentinel_id: str
    actual_nav: float
    mirror_nav: float
    absolute_gap: float
    actual_return_pct: float
    mirror_return_pct: float
    human_outperformance: bool


# In-memory tracker registry (in production: tied to SentinelStateManager)
_TRACKERS: Dict[str, Any] = {}


def _ensure_trackers():
    """
    Lazily create CounterfactualTrackers for deployed systems.
    In production, these would be persistent and updated in realtime
    by the SentinelStateManager.
    """
    from api.main import state
    
    if not hasattr(state, 'sentinel_mgr') or not state.sentinel_mgr:
        return
    
    for sid, sentinel in state.sentinel_mgr.sentinels.items():
        if sid not in _TRACKERS:
            try:
                from engines.sentinel.mirror_portfolio import CounterfactualTracker
                tracker = CounterfactualTracker(
                    sentinel_id=sid,
                    initial_cash=sentinel.config.get("sandbox", {}).get("capital", 100000)
                )
                # Sync with current NAV
                tracker.sync_actual_nav(sentinel.portfolio.nav, datetime.now())
                _TRACKERS[sid] = tracker
            except Exception as e:
                logger.error(f"Failed to create tracker for {sid}: {e}")


@router.get("/overview")
async def portfolio_overview() -> Dict[str, Any]:
    """
    Return portfolio overview for all deployed sentinels including gap analysis.
    """
    _ensure_trackers()
    
    snapshots = []
    total_actual_nav = 0.0
    total_mirror_nav = 0.0
    
    for sid, tracker in _TRACKERS.items():
        gap = tracker.get_gap_analysis()
        snapshots.append(gap)
        total_actual_nav += gap["actual_nav"]
        total_mirror_nav += gap["mirror_nav"]
    
    # Also check if we have any backtest run results with portfolio_nav.csv
    run_navs = _load_backtest_navs()
    
    return {
        "sentinels": snapshots,
        "total_actual_nav": total_actual_nav,
        "total_mirror_nav": total_mirror_nav,
        "total_gap": total_actual_nav - total_mirror_nav,
        "backtest_navs": run_navs,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/nav-history/{sentinel_id}")
async def nav_history(sentinel_id: str) -> Dict[str, Any]:
    """Return the NAV time series for a specific sentinel."""
    _ensure_trackers()
    
    tracker = _TRACKERS.get(sentinel_id)
    if not tracker:
        raise HTTPException(status_code=404, detail=f"No tracker for sentinel '{sentinel_id}'")
    
    return {
        "sentinel_id": sentinel_id,
        "mirror_nav_history": tracker.mirror.nav_history,
        "actual_nav_history": tracker._actual_nav_history,
    }


def _load_backtest_navs() -> List[Dict[str, Any]]:
    """
    Load portfolio_nav.csv files from completed MLflow runs to show historical backtest equity curves.
    """
    navs = []
    
    # Check data/runs directory
    runs_dir = "data/runs"
    if os.path.exists(runs_dir):
        for run_id in os.listdir(runs_dir):
            nav_path = os.path.join(runs_dir, run_id, "portfolio_nav.csv")
            if os.path.exists(nav_path):
                try:
                    import csv
                    with open(nav_path, "r") as f:
                        reader = csv.DictReader(f)
                        rows = list(reader)
                    if rows:
                        start_val = float(rows[0].get("nav", 100000))
                        end_val = float(rows[-1].get("nav", 100000))
                        navs.append({
                            "run_id": run_id,
                            "start_nav": start_val,
                            "end_nav": end_val,
                            "return_pct": ((end_val - start_val) / start_val) * 100,
                            "data_points": len(rows)
                        })
                except Exception as e:
                    logger.warning(f"Failed to parse {nav_path}: {e}")
    
    # Also check mlruns directory
    mlruns_dir = "mlruns/1"
    if os.path.exists(mlruns_dir):
        for run_id in os.listdir(mlruns_dir):
            nav_path = os.path.join(mlruns_dir, run_id, "artifacts", "portfolio_nav.csv")
            if os.path.exists(nav_path):
                try:
                    import csv
                    with open(nav_path, "r") as f:
                        reader = csv.DictReader(f)
                        rows = list(reader)
                    if rows:
                        start_val = float(rows[0].get("nav", 100000))
                        end_val = float(rows[-1].get("nav", 100000))
                        navs.append({
                            "run_id": run_id[:16],
                            "start_nav": start_val,
                            "end_nav": end_val,
                            "return_pct": ((end_val - start_val) / start_val) * 100,
                            "data_points": len(rows)
                        })
                except Exception as e:
                    logger.warning(f"Failed to parse {nav_path}: {e}")
    
    return navs

@router.get("/signals/{signal_id}/freshness")
async def get_signal_freshness(signal_id: str) -> SignalFreshnessState:
    """
    Evaluates whether a pending SignalCard is still valid for entry.
    Checks dynamic price deviation against threshold and session quality.
    """
    from api.main import state
    if not state.sentinel_mgr:
        raise HTTPException(status_code=500, detail="Sentinel State Manager offline")

    # Search for the signal card across all active sentinels' pending queues
    target_card = None
    for sid, sentinel in state.sentinel_mgr.sentinels.items():
        for card in sentinel.pending_cards:
            if card.card_id == signal_id:
                target_card = card
                break
        if target_card:
            break
            
    if not target_card:
        # It may have been resolved (accepted/declined) already
        raise HTTPException(status_code=404, detail="Signal card not found or already resolved")
        
    return freshness_validator.validate_signal_freshness(target_card)
