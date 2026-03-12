"""
Audit Chat Router — Wraps the AuditChat class for HTTP access from the frontend.

Maintains active chat sessions in memory (keyed by run_id).
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json
import logging
import os
import mlflow
from datetime import datetime

router = APIRouter()
logger = logging.getLogger("aegis.audit")

# ---------------------------------------------------------------------------
# In-memory session store.  One AuditChat per run_id at a time.
# ---------------------------------------------------------------------------
_sessions: Dict[str, Any] = {}

class AuditMessageRequest(BaseModel):
    run_id: str
    message: str

class AuditMessageResponse(BaseModel):
    response: str
    context_loaded: bool
    deep_traces_loaded: bool

def _get_or_create_session(run_id: str):
    """Lazy-load an AuditChat session for the given run_id."""
    if run_id in _sessions:
        return _sessions[run_id]
    
    try:
        from scripts.audit_chat import AuditChat
        session = AuditChat(run_id=run_id)
        _sessions[run_id] = session
        return session
    except Exception as e:
        logger.error(f"Failed to create audit session for {run_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to init audit session: {str(e)}")


@router.get("/runs")
async def list_available_runs() -> Dict[str, Any]:
    """List MLflow run IDs that can be audited."""
    db_path = "mlflow.db"
    if not os.path.exists(db_path):
        return {"runs": [], "message": "No MLflow database found."}
    
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.execute(
            "SELECT run_uuid, status, start_time FROM runs WHERE status = 'FINISHED' ORDER BY start_time DESC LIMIT 50"
        )
        runs = [{"run_id": row[0], "status": row[1], "start_time": row[2]} for row in cursor.fetchall()]
        conn.close()
        return {"runs": runs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=AuditMessageResponse)
async def audit_chat(request: AuditMessageRequest) -> Dict[str, Any]:
    """
    Send a message to the Audit Chat for a specific run_id.
    
    The first call for a given run_id creates a session and loads context from MLflow.
    Subsequent calls reuse the session so the LLM has full conversation history.
    """
    session = _get_or_create_session(request.run_id)
    
    msg = request.message.strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Handle special commands
    if msg.lower() == "/load_deep_traces":
        session._load_deep_traces()
        return {
            "response": "Deep sub-agent traces loaded into context. You can now ask about Analyst and Risk Manager reasoning.",
            "context_loaded": True,
            "deep_traces_loaded": session.is_subagent_context_loaded
        }
    
    if msg.lower().startswith("/patch "):
        instruction = msg[7:]
        patch_result = session._create_patch(instruction)
        return {
            "response": patch_result,
            "context_loaded": True,
            "deep_traces_loaded": session.is_subagent_context_loaded
        }
    
    # Standard chat: send to LLM via langchain
    try:
        from langchain_core.messages import HumanMessage, AIMessage
        
        session.messages.append(HumanMessage(content=msg))
        response = session.model.invoke(session.messages)
        ai_text = response.content
        session.messages.append(AIMessage(content=ai_text))
        session._log_to_file("USER", msg)
        session._log_to_file("AUDITOR", ai_text)
        
        return {
            "response": ai_text,
            "context_loaded": True,
            "deep_traces_loaded": session.is_subagent_context_loaded
        }
    except Exception as e:
        logger.error(f"Audit chat error: {e}")
        raise HTTPException(status_code=500, detail=f"LLM inference error: {str(e)}")


@router.get("/context/{run_id}")
async def get_audit_context(run_id: str) -> Dict[str, Any]:
    """Return the loaded context (metrics, config, trace count) for a run."""
    session = _get_or_create_session(run_id)
    return {
        "run_id": run_id,
        "metrics": session.metrics,
        "config": session.config,
        "supervisor_trace_count": len(session.supervisor_traces),
        "subagent_trace_count": len(session.subagent_traces),
        "deep_traces_loaded": session.is_subagent_context_loaded
    }
