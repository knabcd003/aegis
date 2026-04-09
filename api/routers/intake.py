from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import datetime
import uuid
import asyncio

# For mockup dispatching until Engine components hook broadcasting internally
from api.routers.pipeline_events import broadcaster

router = APIRouter()

class IntakeDraft(BaseModel):
    risk_tolerance: str
    time_horizon: str
    max_drawdown_target: float
    raw_desire: str
    is_path_b: bool = False

class ValidationResponse(BaseModel):
    mandate_summary: Dict[str, str]
    contradictions: List[str]
    is_valid: bool

class ConfirmResponse(BaseModel):
    workflow_id: str
    status: str

@router.post("/validate", response_model=ValidationResponse)
async def validate_intake(draft: IntakeDraft):
    # This is where we will hook up `MandateProfile.from_path_a` or schema execution
    # For now, deterministic simulation of contradictions
    
    summary = {
        "Risk": draft.risk_tolerance.title(),
        "Horizon": draft.time_horizon.title(),
        "Drawdown Constraint": f"{draft.max_drawdown_target * 100:.1f}%",
        "Intent": draft.raw_desire if draft.raw_desire else "Autonomous Discovery (No Preference)"
    }
    
    contradictions = []
    
    # Mathematical Contradictions Check
    if draft.risk_tolerance.lower() == "aggressive" and draft.max_drawdown_target <= 0.10:
        contradictions.append("Aggressive risk tolerance contradicts a strict drawdown under 10%.")
    elif draft.risk_tolerance.lower() == "conservative" and draft.max_drawdown_target >= 0.20:
        contradictions.append("Conservative profile is incompatible with a 20%+ drawdown target.")
        
    return ValidationResponse(
        mandate_summary=summary,
        contradictions=contradictions,
        is_valid=len(contradictions) == 0
    )


async def mock_start_pipeline(workflow_id: str):
    # Sends a sample node_start to guarantee the WebSocket backend acts when Confirmation is clicked
    await asyncio.sleep(1) # delay slightly to allow component mounting
    await broadcaster.broadcast({
        "event_id": f"evt_{uuid.uuid4().hex[:6]}",
        "workflow_id": workflow_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "event_type": "node_start",
        "node_id": "intake",
        "session_quality": "nominal",
        "payload": {}
    })
    
@router.post("/confirm", response_model=ConfirmResponse)
async def confirm_intake(draft: IntakeDraft, background_tasks: BackgroundTasks):
    workflow_id = f"run_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    
    # Kicks off async execution guaranteeing actual pipeline launch logic is invoked behind the API
    background_tasks.add_task(mock_start_pipeline, workflow_id)
    
    return ConfirmResponse(
        workflow_id=workflow_id,
        status="RUNNING"
    )
