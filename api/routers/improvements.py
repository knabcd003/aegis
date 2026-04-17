"""
Improvement Proposals Router — Serves real improvement proposals from the ImprovementAgent.

Analyzes finished MLflow runs and generates exactly ONE parameter mutation per call.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel
import json
import os
import logging

router = APIRouter()
logger = logging.getLogger("aegis.improvements")


class ProposalRequest(BaseModel):
    run_id: str
    model: str = "qwen3:8b"


class ProposalAction(BaseModel):
    proposal_id: str
    action: str  # "approve" | "reject"


# In-memory store of generated proposals (production: Redis or DB)
_PROPOSALS: Dict[str, Dict[str, Any]] = {}


@router.post("/generate")
async def generate_proposal(request: ProposalRequest) -> Dict[str, Any]:
    """
    Analyzes a finished MLflow run and generates a single parameter mutation proposal.
    Uses the real ImprovementAgent calling Ollama.
    """
    import mlflow

    # 1. Fetch the run from MLflow
    try:
        client = mlflow.tracking.MlflowClient(tracking_uri="sqlite:///mlflow.db")
        run = client.get_run(request.run_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Run not found: {e}")

    if run.info.status != "FINISHED":
        raise HTTPException(status_code=400, detail=f"Run {request.run_id} is not FINISHED (status: {run.info.status})")

    # 2. Extract metrics and config
    metrics = run.data.metrics
    params = run.data.params

    # Reconstruct config from params (params are stored as flat key-value pairs)
    config_dump = {}
    for k, v in params.items():
        try:
            config_dump[k] = json.loads(v)
        except (json.JSONDecodeError, TypeError):
            config_dump[k] = v

    # 3. Find trace file
    trace_path = None
    artifacts_dir = run.info.artifact_uri
    if artifacts_dir and artifacts_dir.startswith("file://"):
        artifacts_dir = artifacts_dir[7:]
    
    # Look for trace file in artifacts
    possible_trace_paths = [
        os.path.join(artifacts_dir, "agent_trace.jsonl") if artifacts_dir else None,
        os.path.join("data", "runs", request.run_id, "agent_trace.jsonl"),
    ]
    for p in possible_trace_paths:
        if p and os.path.exists(p):
            trace_path = p
            break

    if not trace_path:
        # Create an empty temp trace so the agent can still analyze metrics
        trace_path = f"/tmp/empty_trace_{request.run_id}.jsonl"
        with open(trace_path, "w") as f:
            f.write("")

    # 4. Call the real ImprovementAgent
    try:
        from engines.analyst.improvement_agent import ImprovementAgent
        agent = ImprovementAgent(model=request.model)
        proposal = agent.analyze_run(config_dump, metrics, trace_path, run_id=request.run_id)

    except Exception as e:
        logger.error(f"ImprovementAgent failed: {e}")
        raise HTTPException(status_code=500, detail=f"ImprovementAgent error: {str(e)}")

    # 5. Store and return
    mutation = proposal.mutation
    result = {
        "proposal_id": mutation.proposal_id,
        "run_id": request.run_id,
        "target_param": mutation.target_parameter,
        "current_value": mutation.current_value,
        "proposed_value": mutation.proposed_value,
        "rationale": mutation.rationale,
        "target_category": mutation.target_category,
        "status": "PENDING",
    }
    _PROPOSALS[mutation.proposal_id] = result
    return result


@router.get("/pending")
async def list_pending_proposals() -> Dict[str, Any]:
    """Return all proposals that haven't been acted on yet."""
    pending = [p for p in _PROPOSALS.values() if p.get("status") == "PENDING"]
    return {"proposals": pending, "count": len(pending)}


@router.post("/action")
async def act_on_proposal(action: ProposalAction) -> Dict[str, Any]:
    """Approve or reject a proposal."""
    proposal = _PROPOSALS.get(action.proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail=f"Proposal '{action.proposal_id}' not found.")

    if action.action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'.")

    proposal["status"] = action.action.upper() + "D"  # APPROVED or REJECTED

    if action.action == "approve":
        # In production: apply the mutation via ImprovementAgent.apply_mutation()
        # and trigger a re-backtest with the new config
        logger.info(f"Proposal {action.proposal_id} APPROVED — mutation would be applied.")

    return {"status": proposal["status"], "proposal_id": action.proposal_id}
