"""
OpenClaw API Router — World Monitor Endpoints

Two authenticated endpoints for the OpenClaw World Monitor:
  1. GET  /api/openclaw/universe/{sentinel_id} — Read known_universe.json
  2. POST /api/openclaw/events — Submit world events (geopolitical, macro, supply chain)

Authentication: Bearer token via OPENCLAW_API_SECRET environment variable.
All requests without a valid token receive 401 Unauthorized.
"""
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Authentication ────────────────────────────────────────────────────────────

def _get_api_secret() -> str:
    """Read the shared secret from environment. Fail loudly if not set."""
    secret = os.environ.get("OPENCLAW_API_SECRET")
    if not secret:
        raise RuntimeError(
            "OPENCLAW_API_SECRET environment variable is not set. "
            "OpenClaw endpoints will reject all requests."
        )
    return secret


async def verify_openclaw_token(authorization: Optional[str] = Header(None)):
    """
    FastAPI dependency that validates the Bearer token on every OpenClaw request.
    Returns 401 if the token is missing or incorrect.
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header",
        )

    try:
        expected_secret = _get_api_secret()
    except RuntimeError as e:
        logger.error(str(e))
        raise HTTPException(
            status_code=500,
            detail="Server misconfiguration: OPENCLAW_API_SECRET not set",
        )

    if authorization != f"Bearer {expected_secret}":
        raise HTTPException(
            status_code=401,
            detail="Invalid Bearer token",
        )

    return True


# ── Models ────────────────────────────────────────────────────────────────────

class WorldEvent(BaseModel):
    """A world event submitted by OpenClaw."""
    event_type: str  # "geopolitical" | "macro" | "supply_chain" | "regulatory"
    title: str
    summary: str
    severity: str  # "low" | "medium" | "high" | "critical"
    affected_tickers: List[str] = []
    affected_sectors: List[str] = []
    source_url: Optional[str] = None
    detected_at: Optional[str] = None


class WorldEventResponse(BaseModel):
    event_id: str
    status: str
    message: str


# ── Event Storage ─────────────────────────────────────────────────────────────

_event_store: List[Dict[str, Any]] = []


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/universe/{sentinel_id}", dependencies=[Depends(verify_openclaw_token)])
async def get_known_universe(sentinel_id: str) -> Dict[str, Any]:
    """
    Returns the Known Universe for a deployed Sentinel.

    OpenClaw reads this to understand:
      - Which tickers are held
      - The thesis for each position
      - Dependency maps (commodity inputs, geographic risk, macro sensitivities)
      - Upcoming events (earnings, regulatory)

    Requires: Bearer token authentication via OPENCLAW_API_SECRET.
    """
    from api.main import state

    if state.sentinel_mgr is None:
        raise HTTPException(status_code=503, detail="Sentinel manager not initialized")

    try:
        universe = state.sentinel_mgr.get_known_universe(sentinel_id)
        return universe
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Sentinel {sentinel_id} not found")


@router.post("/events", dependencies=[Depends(verify_openclaw_token)])
async def submit_world_event(event: WorldEvent) -> WorldEventResponse:
    """
    Submit a world event detected by OpenClaw.

    Events are stored and routed to relevant Sentinels based on affected_tickers.
    Critical severity events trigger immediate Sentinel review.

    Requires: Bearer token authentication via OPENCLAW_API_SECRET.
    """
    import uuid

    event_id = str(uuid.uuid4())
    event_record = {
        "event_id": event_id,
        "received_at": datetime.utcnow().isoformat(),
        **event.model_dump(),
    }

    _event_store.append(event_record)
    logger.info(f"OpenClaw event received: [{event.severity}] {event.title} (affects: {event.affected_tickers})")

    # Route critical events to Sentinel review
    from api.main import state
    if state.sentinel_mgr and event.severity == "critical":
        for sentinel_id, sentinel in state.sentinel_mgr.sentinels.items():
            held_tickers = set(sentinel.portfolio.positions.keys())
            affected = set(event.affected_tickers)
            if held_tickers & affected:
                state.sentinel_mgr.pause_sentinel(
                    sentinel_id,
                    reason=f"Critical world event: {event.title}",
                )
                logger.warning(
                    f"Sentinel {sentinel_id} paused due to critical event: {event.title}"
                )

    return WorldEventResponse(
        event_id=event_id,
        status="received",
        message=f"Event routed to {len(event.affected_tickers)} ticker(s)",
    )


@router.get("/events", dependencies=[Depends(verify_openclaw_token)])
async def list_events(limit: int = 50) -> List[Dict[str, Any]]:
    """List recent world events (most recent first). For audit trail."""
    return list(reversed(_event_store[-limit:]))
