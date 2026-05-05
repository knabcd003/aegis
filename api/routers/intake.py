from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any
import datetime
import uuid
import json
import os

from api.schemas.intake import V9IntakeSchema, ValidationResponse, ConfirmResponse
from engines.simulation.orchestrator import SimulationOrchestrator

router = APIRouter()

MANDATES_DIR = "data/mandates"
SESSIONS_DIR = "data/sessions"

os.makedirs(MANDATES_DIR, exist_ok=True)
os.makedirs(SESSIONS_DIR, exist_ok=True)

@router.post("/validate", response_model=ValidationResponse)
async def validate_intake(schema: V9IntakeSchema):
    hard_errors = []
    soft_contradictions = []
    inferred_flags = []
    
    # 1. Mandate Summary Generation
    summary = {}
    if schema.mandate_hard_constraints:
        drawdown = schema.mandate_hard_constraints.max_portfolio_drawdown_pct
        summary["Max Drawdown"] = f"{drawdown * 100:.1f}%" if drawdown is not None else "Not Set"
        
        concurrent = schema.mandate_hard_constraints.max_concurrent_live_strategies
        summary["Max Concurrent Strats"] = str(concurrent) if concurrent is not None else "Not Set"
        
        horizon_allocs = schema.mandate_hard_constraints.horizon_allocation
        if horizon_allocs:
            alloc_strs = [f"{h.label.title()} ({h.capital_weight * 100:.0f}%)" for h in horizon_allocs if h.label and h.capital_weight]
            summary["Horizon Allocation"] = ", ".join(alloc_strs) if alloc_strs else "Not Set"
        
        if schema.mandate_hard_constraints.universe_hard_filters:
            vol_floor = schema.mandate_hard_constraints.universe_hard_filters.min_avg_daily_volume_usd
            if vol_floor is not None:
                summary["Volume Floor"] = f"${vol_floor / 1e6:.1f}M/day"
    
    if schema.universe_mandate and schema.universe_mandate.raw_desire:
        summary["Intent"] = schema.universe_mandate.raw_desire
        
    # 2. Hard Error Detection
    if not schema.mandate_hard_constraints or schema.mandate_hard_constraints.max_portfolio_drawdown_pct is None:
        hard_errors.append("Missing required Tier 1 constraint: max_portfolio_drawdown_pct.")
    
    if not schema.mandate_hard_constraints or schema.mandate_hard_constraints.investable_capital is None:
        hard_errors.append("Missing required Tier 1 constraint: investable_capital.")
        
    # Priority vs Preference mutually exclusive conflicts (example mock check)
    if schema.mandate_priority_hierarchy and schema.mandate_priority_hierarchy.preference_flexibility:
        flex = schema.mandate_priority_hierarchy.preference_flexibility
        immovables = [f for f in flex if f.flexibility == "immovable"]
        if len(immovables) > 3:
            hard_errors.append("Too many 'immovable' preferences specified. Conflict resolution impossible.")
            
    # 3. Soft Contradiction Detection
    if schema.filing_notes and schema.filing_notes.contradictions:
        for c in schema.filing_notes.contradictions:
            soft_contradictions.append(c)
            
    # 4. Inferred Flags Detection
    # Traverse string fields to find tags
    schema_dump = schema.model_dump()
    def find_tags(obj):
        if isinstance(obj, str):
            if "[INFERRED]" in obj or "[ASSUMED]" in obj:
                inferred_flags.append(f"System inferred: {obj}")
        elif isinstance(obj, dict):
            for v in obj.values():
                find_tags(v)
        elif isinstance(obj, list):
            for v in obj:
                find_tags(v)
    
    find_tags(schema_dump)
        
    return ValidationResponse(
        mandate_summary=summary,
        hard_errors=hard_errors,
        soft_contradictions=soft_contradictions,
        inferred_flags=inferred_flags,
        is_valid=len(hard_errors) == 0
    )

@router.post("/confirm", response_model=ConfirmResponse)
async def confirm_intake(schema: V9IntakeSchema, background_tasks: BackgroundTasks, session_id: str = None):
    # 1. Final Assembly & Cleaning
    # Dump using non-aliased names first
    clean_schema = schema.model_dump(by_alias=False, exclude_none=False)
    
    # Strip builder notes, tier markers, and note fields
    def strip_annotations(d):
        if isinstance(d, dict):
            return {k: strip_annotations(v) for k, v in d.items() if k not in ("note", "builder_note", "tier", "for_llm", "path_note", "schema_version", "path")}
        elif isinstance(d, list):
            return [strip_annotations(v) for v in d]
        else:
            return d
            
    final_dict = strip_annotations(clean_schema)
    
    # Generate ID and Persistence
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    mandate_id = f"mandate_{timestamp}_{uuid.uuid4().hex[:6]}"
    workflow_id = f"run_{timestamp}_{uuid.uuid4().hex[:6]}"
    
    filepath = os.path.join(MANDATES_DIR, f"{mandate_id}.json")
    with open(filepath, "w") as f:
        json.dump(final_dict, f, indent=2)
        
    # Session Invalidation (if Path A)
    if session_id:
        session_path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
        if os.path.exists(session_path):
            with open(session_path, "r") as f:
                session_data = json.load(f)
            session_data["locked"] = True
            session_data["mandate_id"] = mandate_id
            with open(session_path, "w") as f:
                json.dump(session_data, f, indent=2)
    
    # Real Bridge: Launch the simulation in the background
    background_tasks.add_task(
        SimulationOrchestrator.run_from_intake, 
        schema,  # Optionally pass mandate_id or the dict
        workflow_id
    )
    
    return ConfirmResponse(
        workflow_id=workflow_id,
        status="RUNNING"
    )
