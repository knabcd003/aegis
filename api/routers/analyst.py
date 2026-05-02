"""
Analyst Router — v7 Stub

The v6 EpisodicMemory/ChromaDB analyst pipeline has been archived to _v6_archive/analyst/.
v7 uses the autonomous pipeline (AegisState + MLflow artifacts) for all reasoning traces.
These endpoints are preserved as stubs to prevent 404s from any remaining frontend calls.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from fastapi import Query

router = APIRouter()


@router.get("/memory")
async def get_episodic_memory(
    ticker: Optional[str] = Query(None),
    outcome: Optional[str] = Query(None),
    limit: int = Query(10),
) -> Dict[str, Any]:
    """v6 episodic memory endpoint — archived. Returns empty results."""
    return {
        "status": "archived",
        "message": "v6 EpisodicMemory has been archived. v7 uses MLflow artifact traces.",
        "count": 0,
        "memories": [],
    }


@router.post("/thesis/async")
async def generate_thesis_async() -> Dict[str, Any]:
    """v6 thesis generation — archived."""
    raise HTTPException(
        status_code=410,
        detail="v6 thesis generation has been archived. Use the v7 autonomous pipeline.",
    )
