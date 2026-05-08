from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any

from api.schemas.intake import V9IntakeSchema
from api.prompts.section_validators import CONFIRM_SYNTHESIS_PROMPT
from engines.system.llm_adapter import LLMAdapter
import json

router = APIRouter()
llm_adapter = LLMAdapter()

class ReviewResponse(BaseModel):
    schema_updated: V9IntakeSchema
    hard_errors: List[str]
    cross_section_contradictions: List[str]
    is_valid: bool

@router.post("/review", response_model=ReviewResponse)
async def review_intake(schema: V9IntakeSchema):
    hard_errors = []
    
    # 1. Deterministic Tier 1 Validation Pass
    if not schema.mandate_hard_constraints or schema.mandate_hard_constraints.max_portfolio_drawdown_pct is None:
        hard_errors.append("Missing required Tier 1 constraint: max_portfolio_drawdown_pct.")
    
    if not schema.mandate_hard_constraints or schema.mandate_hard_constraints.investable_capital is None:
        hard_errors.append("Missing required Tier 1 constraint: investable_capital.")

    if schema.mandate_priority_hierarchy and schema.mandate_priority_hierarchy.preference_flexibility:
        flex = schema.mandate_priority_hierarchy.preference_flexibility
        immovables = [f for f in flex if f.flexibility == "immovable"]
        if len(immovables) > 5:
            hard_errors.append("Too many 'immovable' preferences specified. Conflict resolution impossible.")
            
    # Horizon Weights sum to 1.0
    if schema.mandate_hard_constraints and schema.mandate_hard_constraints.horizon_allocation:
        allocs = schema.mandate_hard_constraints.horizon_allocation
        total_weight = sum([h.capital_weight for h in allocs if h.capital_weight is not None])
        if total_weight > 0 and abs(total_weight - 1.0) > 0.01:
            hard_errors.append(f"Horizon allocation weights must sum to 1.0, got {total_weight:.2f}")

    # 401k account type with non-ETF assets
    if schema.mandate_hard_constraints and schema.mandate_hard_constraints.account_type and "401k" in schema.mandate_hard_constraints.account_type.lower():
        if schema.mandate_hard_constraints.universe_hard_filters and schema.mandate_hard_constraints.universe_hard_filters.asset_classes_permitted:
            assets = [a.lower() for a in schema.mandate_hard_constraints.universe_hard_filters.asset_classes_permitted]
            if any("etf" not in a and "mutual_fund" not in a for a in assets):
                hard_errors.append("Account type 401k specified but non-ETF/Mutual Fund asset classes are permitted.")

    # Implied Sharpe ratio contradiction
    if schema.performance_targets and schema.performance_targets.target_annual_return_pct and schema.mandate_hard_constraints and schema.mandate_hard_constraints.max_portfolio_drawdown_pct:
        target_return = schema.performance_targets.target_annual_return_pct
        max_dd = schema.mandate_hard_constraints.max_portfolio_drawdown_pct
        if max_dd > 0 and (target_return / max_dd) > 2.0:
            hard_errors.append(f"Target return of {target_return*100:.1f}% with max drawdown of {max_dd*100:.1f}% implies an unrealistic Sharpe ratio.")

    # 2. LLM Cross-Section Synthesis Call
    schema_dump = schema.model_dump(exclude_none=True)
    messages = [
        {"role": "system", "content": CONFIRM_SYNTHESIS_PROMPT},
        {"role": "user", "content": f"Full Schema:\n{schema_dump}\n\nRespond with ONLY valid JSON."}
    ]

    try:
        adapter_res = llm_adapter.invoke(
            messages=messages,
            role="structured_extraction",
            workflow_id="intake_confirmation",
            node_id="confirm_synthesis"
        )
        content = adapter_res.content
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        response_data = json.loads(content)
    except Exception as e:
        response_data = {
            "regime_universe_pairs": [],
            "macro_views": [],
            "filing_notes_contradictions": [f"LLM Synthesis Error: {str(e)}"]
        }

    # Update Schema with synthesized fields
    if not schema.strategy_intent:
        schema.strategy_intent = {}
    schema.strategy_intent.regime_universe_pairs = response_data.get("regime_universe_pairs", [])
    
    if not schema.market_context:
        schema.market_context = {}
    schema.market_context.macro_views = response_data.get("macro_views", [])
    
    cross_section_contradictions = response_data.get("filing_notes_contradictions", [])
    if cross_section_contradictions:
        if not schema.filing_notes:
            schema.filing_notes = {}
        if not schema.filing_notes.contradictions:
            schema.filing_notes.contradictions = []
        schema.filing_notes.contradictions.extend(cross_section_contradictions)

    return ReviewResponse(
        schema_updated=schema,
        hard_errors=hard_errors,
        cross_section_contradictions=cross_section_contradictions,
        is_valid=len(hard_errors) == 0
    )
