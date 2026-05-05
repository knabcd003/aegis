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
        if drawdown is not None:
            dd_val = drawdown if drawdown > 1.0 else drawdown * 100
            summary["Max Drawdown"] = f"{dd_val:.1f}%"
        else:
            summary["Max Drawdown"] = "Not Set"
        
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
        
        # Priority vs Preference mutually exclusive conflicts
    if schema.mandate_priority_hierarchy and schema.mandate_priority_hierarchy.preference_flexibility:
        flex = schema.mandate_priority_hierarchy.preference_flexibility
        immovables = [f for f in flex if f.flexibility == "immovable"]
        if len(immovables) > 5:
            hard_errors.append("Too many 'immovable' preferences specified. Conflict resolution impossible.")
            
    # Horizon Weights sum to 1.0
    if schema.mandate_hard_constraints and schema.mandate_hard_constraints.horizon_allocation:
        allocs = schema.mandate_hard_constraints.horizon_allocation
        total_weight = sum([h.capital_weight for h in allocs if h.capital_weight is not None])
        # Tolerate slight floating point math issues
        if total_weight > 0 and abs(total_weight - 1.0) > 0.01:
            hard_errors.append(f"Horizon allocation weights must sum to 1.0, got {total_weight:.2f}")

    # 401k account type with non-ETF assets
    if schema.mandate_hard_constraints and schema.mandate_hard_constraints.account_type and "401k" in schema.mandate_hard_constraints.account_type.lower():
        if schema.mandate_hard_constraints.universe_hard_filters and schema.mandate_hard_constraints.universe_hard_filters.asset_classes_permitted:
            assets = [a.lower() for a in schema.mandate_hard_constraints.universe_hard_filters.asset_classes_permitted]
            if any("etf" not in a and "mutual_fund" not in a for a in assets):
                hard_errors.append("Account type 401k specified but non-ETF/Mutual Fund asset classes are permitted.")
            
    # 3. Soft Contradiction Detection
    if schema.filing_notes and schema.filing_notes.contradictions:
        for c in schema.filing_notes.contradictions:
            if isinstance(c, dict) and "description" in c:
                soft_contradictions.append(c["description"])
            else:
                soft_contradictions.append(str(c))
            
    # Implied Sharpe ratio contradiction
    if schema.performance_targets and schema.performance_targets.target_annual_return_pct and schema.mandate_hard_constraints and schema.mandate_hard_constraints.max_portfolio_drawdown_pct:
        target_return = schema.performance_targets.target_annual_return_pct
        max_dd = schema.mandate_hard_constraints.max_portfolio_drawdown_pct
        if max_dd > 0 and (target_return / max_dd) > 2.0:
            soft_contradictions.append(f"Target return of {target_return*100:.1f}% with max drawdown of {max_dd*100:.1f}% implies an unrealistic Sharpe ratio. Strategy may struggle to find signals.")
            
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
