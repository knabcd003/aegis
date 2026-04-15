from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any
import datetime
import uuid

from api.schemas.intake import IntakeDraft, ValidationResponse, ConfirmResponse
from engines.simulation.orchestrator import SimulationOrchestrator

router = APIRouter()

@router.post("/validate", response_model=ValidationResponse)
async def validate_intake(draft: IntakeDraft):
    # Deterministic Path A validation
    summary = {
        "Risk": draft.risk_tolerance.title(),
        "Horizon": draft.time_horizon.title(),
        "Drawdown Constraint": f"{draft.max_drawdown_target * 100:.1f}%",
        "Intent": draft.raw_desire if draft.raw_desire else "Autonomous Discovery"
    }
    
    contradictions = []
    if draft.risk_tolerance.lower() == "aggressive" and draft.max_drawdown_target <= 0.10:
        contradictions.append("Aggressive risk tolerance contradicts a strict drawdown under 10%.")
    elif draft.risk_tolerance.lower() == "conservative" and draft.max_drawdown_target >= 0.20:
        contradictions.append("Conservative profile is incompatible with a 20%+ drawdown target.")
        
    return ValidationResponse(
        mandate_summary=summary,
        contradictions=contradictions,
        is_valid=len(contradictions) == 0
    )

@router.post("/confirm", response_model=ConfirmResponse)
async def confirm_intake(draft: IntakeDraft, background_tasks: BackgroundTasks):
    workflow_id = f"run_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    
    # Real Bridge: Launch the simulation in the background
    background_tasks.add_task(
        SimulationOrchestrator.run_from_intake, 
        draft, 
        workflow_id
    )
    
    return ConfirmResponse(
        workflow_id=workflow_id,
        status="RUNNING"
    )
