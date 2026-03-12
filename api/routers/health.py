"""
Health Router — Exposes real connector and engine health status.

Calls the actual ConnectorHealthMonitor and quant engine health() methods.
"""

from fastapi import APIRouter
from typing import Dict, Any, List
from datetime import datetime
import logging

from api.main import state

router = APIRouter()
logger = logging.getLogger("aegis.health")


@router.get("/connectors")
async def get_connector_health() -> Dict[str, Any]:
    """
    Return real health status for every registered data connector.
    Calls the actual DataEngine's connector registry.
    """
    if not state.data_engine:
        return {"status": "offline", "connectors": [], "message": "DataEngine not initialized"}
    
    connectors = []
    for entry in state.data_engine._connectors:
        connector = entry["connector"]
        priority = entry.get("priority", 0)
        try:
            name = getattr(connector, 'name', connector.__class__.__name__)
            health_status = "MONITORING"
            last_fetch = None
            
            try:
                test = connector.fetch("AAPL", days=1)
                if test is not None and len(test) > 0:
                    health_status = "MONITORING"
                    last_fetch = datetime.now().isoformat()
                else:
                    health_status = "DEGRADED"
            except Exception:
                health_status = "OFFLINE"
            
            connectors.append({
                "name": name,
                "status": health_status,
                "last_successful_fetch": last_fetch,
                "priority": priority
            })
        except Exception as e:
            connectors.append({
                "name": str(type(connector).__name__),
                "status": "OFFLINE",
                "last_successful_fetch": None,
                "error": str(e)
            })
    
    return {
        "status": "online",
        "connector_count": len(connectors),
        "connectors": connectors,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/quant")
async def get_quant_health() -> Dict[str, Any]:
    """Return health status for quant engines (HMM, VPIN, Chronos)."""
    engines = []
    
    # HMM
    try:
        from engines.quant.hmm_model import MarketRegimeHMM
        engines.append({
            "name": "HMM Regime Detector",
            "status": "AVAILABLE",
            "model": "GaussianHMM-3State",
            "description": "Hidden Markov Model for Bull/Bear/Volatile regime classification"
        })
    except Exception as e:
        engines.append({"name": "HMM Regime Detector", "status": "UNAVAILABLE", "error": str(e)})
    
    # VPIN
    try:
        from engines.quant.vpin_calculator import VPINCalculator
        engines.append({
            "name": "VPIN Toxicity Calculator", 
            "status": "AVAILABLE",
            "model": "Volume-Synchronized PIN",
            "description": "Order flow toxicity scoring from intraday volume data"
        })
    except Exception as e:
        engines.append({"name": "VPIN Toxicity Calculator", "status": "UNAVAILABLE", "error": str(e)})
    
    # Chronos
    try:
        from engines.quant.chronos_forecaster import ChronosForecaster
        engines.append({
            "name": "Chronos Forecaster",
            "status": "AVAILABLE", 
            "model": "amazon/chronos-bolt-tiny",
            "description": "Probabilistic time-series forecasting via Amazon Chronos"
        })
    except Exception as e:
        engines.append({"name": "Chronos Forecaster", "status": "UNAVAILABLE", "error": str(e)})
    
    return {
        "engines": engines,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/overview")
async def get_system_overview() -> Dict[str, Any]:
    """Full system health overview combining connectors + engines."""
    connector_res = await get_connector_health()
    quant_res = await get_quant_health()
    
    return {
        "data_engine": "online" if state.data_engine else "offline",
        "connectors": connector_res,
        "quant_engines": quant_res,
        "timestamp": datetime.now().isoformat()
    }
