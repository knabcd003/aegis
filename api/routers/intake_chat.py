from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import json
import os
from api.schemas.intake import V9IntakeSchema
from api.prompts.intake_stages import STAGE_PROMPTS

router = APIRouter()
SESSIONS_DIR = "data/sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str

class ChatResponse(BaseModel):
    session_id: str
    response: str
    current_stage: int
    schema_wip: Dict[str, Any]

def get_session(session_id: str) -> dict:
    if not session_id:
        return create_new_session()
    filepath = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if not os.path.exists(filepath):
        return create_new_session()
    with open(filepath, "r") as f:
        return json.load(f)

def save_session(session: dict):
    filepath = os.path.join(SESSIONS_DIR, f"{session['session_id']}.json")
    with open(filepath, "w") as f:
        json.dump(session, f, indent=2)

def create_new_session() -> dict:
    session_id = f"sess_{uuid.uuid4().hex[:8]}"
    return {
        "session_id": session_id,
        "current_stage": 0,
        "transcript": [],
        "schema_wip": V9IntakeSchema().model_dump(by_alias=True),
        "stage_completion_flags": {
            "1": {"capital": False, "account_type": False},
            "2": {"drawdown_limit": False, "volatility_tolerance": False, "gap_risk": False, "time_risk": False, "regret_asymmetry": False, "loss_history": False},
            "3": {"return_target": False, "horizon": False},
            "4": {"universe": False, "strategy": False},
            "5": {"execution_windows": False, "max_strats": False},
            "6": {"priority": False, "flexibility": False},
            "7": {"synthesis_approved": False}
        },
        "locked": False
    }

def merge_patch(target: dict, patch: dict):
    # Basic JSON Merge Patch implementation (RFC 7396)
    for key, value in patch.items():
        if value is None:
            if key in target:
                del target[key]
        elif isinstance(value, dict):
            target[key] = merge_patch(target.get(key, {}), value)
        else:
            target[key] = value
    return target

def evaluate_stage_exit(stage: int, schema_wip: dict, flags: dict) -> bool:
    """Check if all required sub-objectives for the current stage are captured in schema_wip."""
    if stage == 1:
        c = schema_wip.get("mandate_hard_constraints", {})
        flags["1"]["capital"] = c.get("investable_capital") is not None
        flags["1"]["account_type"] = c.get("account_type") is not None
        return flags["1"]["capital"] and flags["1"]["account_type"]
    elif stage == 2:
        c = schema_wip.get("mandate_hard_constraints", {})
        r = schema_wip.get("risk_profile", {})
        flags["2"]["drawdown_limit"] = c.get("max_portfolio_drawdown_pct") is not None
        flags["2"]["volatility_tolerance"] = r.get("volatility_tolerance") is not None
        # Simplified for mock
        return flags["2"]["drawdown_limit"]
    # ... mock implementation for other stages
    return True

def mock_llm_call(prompt: str, transcript: list, current_stage: int) -> dict:
    # This is a mock. In reality, we'd inject the prompt to an LLM.
    # We return a dummy conversational message and an empty merge patch.
    # To test progression, we'll patch the required fields artificially based on stage.
    patch = {}
    msg = f"[Mock Stage {current_stage} Response]"
    if current_stage == 1:
        patch = {"mandate_hard_constraints": {"investable_capital": 100000, "account_type": "margin"}}
        msg = "I've noted your capital and account type. Let's move to risk."
    elif current_stage == 2:
        patch = {"mandate_hard_constraints": {"max_portfolio_drawdown_pct": 0.15}}
        msg = "Got the 15% drawdown limit."
    
    return {
        "conversational_message": msg,
        "schema_patch": patch
    }

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    session = get_session(req.session_id)
    if session.get("locked"):
        raise HTTPException(status_code=400, detail="Session is locked.")
        
    session["transcript"].append({"role": "user", "content": req.message})
    stage = session["current_stage"]
    
    # Stage 0: Hardcoded Orientation
    if stage == 0:
        reply = "Welcome to Aegis Intake. I'll ask you some questions. Ready?"
        session["current_stage"] = 1
        session["transcript"].append({"role": "system", "content": reply})
        save_session(session)
        return ChatResponse(session_id=session["session_id"], response=reply, current_stage=1, schema_wip=session["schema_wip"])
        
    # Stage 1-7: LLM-driven
    prompt_template = STAGE_PROMPTS.get(stage, "")
    recent_transcript = session["transcript"][-10:] # Bound token spend
    
    # In a real app, construct the full prompt combining template, schema_wip, and transcript
    llm_output = mock_llm_call(prompt_template, recent_transcript, stage)
    
    # Apply schema patch
    patch = llm_output.get("schema_patch", {})
    if patch:
        session["schema_wip"] = merge_patch(session["schema_wip"], patch)
        
    reply = llm_output.get("conversational_message", "")
    session["transcript"].append({"role": "system", "content": reply})
    
    # Evaluate exit conditions
    if evaluate_stage_exit(stage, session["schema_wip"], session["stage_completion_flags"]):
        if stage < 7:
            session["current_stage"] += 1
            
    save_session(session)
    return ChatResponse(session_id=session["session_id"], response=reply, current_stage=session["current_stage"], schema_wip=session["schema_wip"])
