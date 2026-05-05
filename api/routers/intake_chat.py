from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import json
import os
import asyncio
from api.schemas.intake import V9IntakeSchema
from api.prompts.intake_stages import STAGE_PROMPTS
from engines.system.llm_adapter import LLMAdapter

router = APIRouter()
llm_adapter = LLMAdapter()
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
    elif stage == 3:
        p = schema_wip.get("performance_targets", {})
        h = schema_wip.get("mandate_hard_constraints", {})
        flags["3"]["return_target"] = p.get("target_annual_return_pct") is not None
        flags["3"]["horizon"] = h.get("horizon_allocation") is not None
        return flags["3"]["return_target"] and flags["3"]["horizon"]
    elif stage == 4:
        u = schema_wip.get("universe_mandate", {})
        s = schema_wip.get("strategy_intent", {})
        flags["4"]["universe"] = u.get("raw_desire") is not None
        flags["4"]["strategy"] = s.get("catalyst_preferences") is not None
        return flags["4"]["universe"] and flags["4"]["strategy"]
    elif stage == 5:
        c = schema_wip.get("mandate_hard_constraints", {})
        flags["5"]["max_strats"] = c.get("max_concurrent_live_strategies") is not None
        return flags["5"]["max_strats"]
    elif stage == 6:
        m = schema_wip.get("mandate_priority_hierarchy", {})
        flags["6"]["priority"] = m.get("ordered_priorities") is not None
        return flags["6"]["priority"]
    elif stage == 7:
        f = schema_wip.get("filing_notes", {})
        if f.get("conversation_quality_note") == "CONFIRMED":
            flags["7"]["synthesis_approved"] = True
            return True
        return False

async def call_llm(prompt_template: str, transcript: list, stage: int, schema_wip: dict, session_id: str) -> dict:
    system_msg = prompt_template
    system_msg += f"\n\nCURRENT SCHEMA_WIP:\n{json.dumps(schema_wip, indent=2)}\n\n"
    
    messages = [{"role": "system", "content": system_msg}]
    for msg in transcript:
        # Convert 'system' to 'assistant' for LiteLLM if needed, but 'system' usually works as a generic system msg.
        # It's better to map 'system' from transcript to 'assistant' so the LLM knows it's its own past response.
        r = "assistant" if msg["role"] == "system" else msg["role"]
        messages.append({"role": r, "content": msg["content"]})
        
    try:
        response = await asyncio.to_thread(
            llm_adapter.invoke,
            messages=messages,
            role="intake_advisor",
            workflow_id=session_id,
            node_id=f"intake_stage_{stage}"
        )
        content = response.content
        
        # Try to find JSON block using regex if backticks aren't present
        import re
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        else:
            # Fallback regex to find first { and last }
            start = content.find('{')
            end = content.rfind('}')
            if start != -1 and end != -1:
                content = content[start:end+1]
                
        parsed = json.loads(content.strip())
        return parsed
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"LLM call failed: {e}")
        return {
            "conversational_message": "I'm having trouble connecting to my reasoning engine right now. Could you please rephrase or try again in a moment?",
            "schema_patch": {}
        }

@router.post("", response_model=ChatResponse)
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
    llm_output = await call_llm(prompt_template, recent_transcript, stage, session["schema_wip"], req.session_id)
    
    # Apply schema patch
    patch = llm_output.get("schema_patch", {})
    if patch:
        session["schema_wip"] = merge_patch(session["schema_wip"], patch)
        
    reply = llm_output.get("conversational_message", "")
    session["transcript"].append({"role": "system", "content": reply})
    
    # Evaluate exit conditions
    if evaluate_stage_exit(stage, session["schema_wip"], session["stage_completion_flags"]):
        if stage <= 7:
            session["current_stage"] += 1
            
    save_session(session)
    return ChatResponse(session_id=session["session_id"], response=reply, current_stage=session["current_stage"], schema_wip=session["schema_wip"])
