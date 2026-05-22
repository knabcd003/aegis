import logging
import json
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from engines.system.llm_adapter import LLMAdapter

logger = logging.getLogger("aegis.api.aria")

router = APIRouter()
llm_adapter = LLMAdapter()

# ── Pydantic Request/Response Models ──────────────────────────────────────────

class MessageEntry(BaseModel):
    role: str # "aria" | "user"
    content: str

class AriaContextRequest(BaseModel):
    trigger: str # "section_enter" | "field_focus" | "field_change" | "user_message" | "validation_result"
    section: int
    active_field_path: Optional[str] = None
    active_field_value: Optional[Any] = None
    user_message: Optional[str] = None
    validation_errors: Optional[List[str]] = None
    validation_warnings: Optional[List[str]] = None
    schema_state: Dict[str, Any]
    message_history: List[MessageEntry]

class FieldUpdate(BaseModel):
    path: str
    value: Any
    tier: int # 1 | 2
    plain_label: str
    plain_value: str
    auto_apply: bool
    auto_apply_delay_ms: Optional[int] = 3000

class ConflictEntry(BaseModel):
    description: str
    severity: str # "blocking" | "warning" | "advisory"
    fields_involved: List[str]
    suggested_resolution: str

class AriaResponse(BaseModel):
    message: str
    field_updates: Optional[List[FieldUpdate]] = None
    questions: Optional[List[str]] = None
    conflicts: Optional[List[ConflictEntry]] = None
    section_context_complete: Optional[bool] = None

# ── Field Knowledge Map ───────────────────────────────────────────────────────

FIELD_KNOWLEDGE_MAP = """
FIELD: mandate_identification.investor_sophistication
plain_language: "The user's self-assessed level of trading sophistication (retail_novice, retail_experienced, semi_professional, professional)"
typical_range: "retail_novice to professional"
aria_can_extract: true
extraction_cue: "user describes their experience, how long they have traded, or their familiarity with market terms"

FIELD: capital_structure.investable_capital_usd
plain_language: "The total investable capital allocated to Aegis in USD"
typical_range: "$10,000 to $10,000,000"
aria_can_extract: true
extraction_cue: "user mentions an amount of money, budget, portfolio size, or capital constraint"

FIELD: risk_mandate.tier_1_risk_constraints.max_portfolio_drawdown_pct
plain_language: "The maximum cumulative loss from portfolio peak before system halts (drawdown limit)"
typical_range: "10-25%"
aria_can_extract: true
extraction_cue: "user mentions percentage loss tolerance, pain threshold, or maximum drawdowns they can bear"

FIELD: risk_mandate.tier_1_risk_constraints.max_daily_loss_pct
plain_language: "Daily circuit breaker limit. Halts new position entry if intraday loss exceeds this percentage of starting-of-day NAV"
typical_range: "1-5%"
aria_can_extract: true

FIELD: risk_mandate.tier_1_risk_constraints.drawdown_breach_protocol
plain_language: "Protocol to execute immediately upon drawdown breach (pause_all_notify_user, reduce_position_sizes_50pct, manual_restart_required, reduce_and_notify)"
aria_can_extract: true

FIELD: risk_mandate.tier_1_risk_constraints.max_single_position_pct
plain_language: "Maximum capital exposure in any single position as a percentage of portfolio"
typical_range: "2-10%"

FIELD: risk_mandate.tier_1_risk_constraints.max_single_position_usd
plain_language: "Maximum capital exposure in any single position in absolute USD"

FIELD: risk_mandate.tier_1_risk_constraints.max_sector_concentration_pct
plain_language: "Maximum cumulative exposure in any single GICS sector"
typical_range: "15-30%"

FIELD: risk_mandate.tier_1_risk_constraints.max_concurrent_live_strategies
plain_language: "Maximum number of distinct strategies allowed to be active concurrently"
typical_range: "3-15"

FIELD: return_mandate.primary_objective
plain_language: "The primary objective of the portfolio (capital_growth, income_generation, capital_preservation, beat_benchmark, absolute_return)"

FIELD: universe_mandate.tier_1_hard_filters.min_avg_daily_volume_usd
plain_language: "Minimum 20-day average daily dollar volume for permitted assets"
typical_range: ">= $1,000,000"

FIELD: strategy_mandate.catalyst_types
plain_language: "List of opted-in catalyst event types (pead_earnings_momentum, fda_pdufa_biotech, clinical_trial_readout_phase3, clinical_trial_readout_phase2, ma_announcement, index_reconstitution, management_change, secondary_offering, short_squeeze_setup, macro_data_surprise)"
aria_can_extract: true

FIELD: operational_mandate.tier_1_operational_constraints.max_execution_latency_minutes
plain_language: "Maximum allowable delay between signal and execution in minutes"

FIELD: operational_mandate.tier_1_operational_constraints.automation_level
plain_language: "Level of trade execution automation (semi_automated_confirmation_required, fully_manual)"

FIELD: behavioral_profile.loss_aversion_coefficient
plain_language: "Tolerance for losses relative to gains (standard_2to1, elevated_3to1, severe_4plus_to_1)"

FIELD: tax_and_legal.account_tax_status
plain_language: "Account tax classification (fully_taxable, tax_deferred_traditional, tax_exempt_roth, partially_sheltered)"

FIELD: portfolio_scope_and_macro.regime_adaptivity_intent
plain_language: "Whether strategies should adapt to current regimes or remain consistent (adaptive_to_regime, strategy_consistent_regardless_of_regime)"

FIELD: governance_and_review.mandate_review_frequency
plain_language: "Frequency of formal mandate review sessions (monthly, quarterly, semi_annually, annually, event_driven_only)"
"""

SECTION_PROMPTS = {
    1: "Section 1: Mandate Identification. Help the user establish their profile, account type, experience level, and overall capital allocation context.",
    2: "Section 2: Risk Mandate. Help the user set drawdown limits, position ceilings, and sector concentration limits. Focus heavily on drawdown limits.",
    3: "Section 3: Return Mandate. Discuss performance expectations. Validate if targets are realistic compared to drawdown parameters.",
    4: "Section 4: Universe Mandate. Define acceptable sectors, liquidity floors (volume, price), and tickers to focus on or avoid.",
    5: "Section 5: Strategy Mandate. Capture which catalyst events to trade (earnings, FDA biotech trials) and horizon drift weights.",
    6: "Section 6: Operational Mandate. Configure execution latency windows, market timing capabilities, and automation preferences.",
    7: "Section 7: Behavioral Profile. Understand the user's emotional responses to trading stress, overtrading tendencies, and cooling-off triggers.",
    8: "Section 8: Tax and Legal. Deal with marginal tax rates, tax status constraints, wash sale concerns, and regulatory compliance.",
    9: "Section 9: Portfolio Scope and Macro. Establish regime views, correlation limits, existing portfolio beta, and macro concerns.",
    10: "Section 10: Governance and Review. Set review frequencies, pause thresholds, attribution choices, and amendment policies."
}

# ── Endpoint Implementation ───────────────────────────────────────────────────

@router.post("", response_model=AriaResponse)
async def get_aria_guidance(req: AriaContextRequest):
    try:
        # Part 1: Identity & Rules
        system_prompt = (
            "You are Aria, an expert intake agent for the Aegis autonomous trading system. "
            "You are helping a user configure their investment mandate.\n\n"
            "SYSTEM RULES:\n"
            "1. You never set a Tier 1 field without explicit user confirmation. You may suggest a value, but set auto_apply: false for Tier 1 fields.\n"
            "2. You set Tier 2 prose fields automatically from conversation (auto_apply: true, no confirmation needed).\n"
            "3. You set Tier 2 structured fields with auto_apply: true and a 3-second auto_apply_delay_ms (default 3000).\n"
            "4. You never mention schema JSON paths or Pydantic field names directly. Translate to plain language (e.g., say 'drawdown limit' instead of 'max_portfolio_drawdown_pct').\n"
            "5. Keep messages short. 2-4 sentences max unless explaining a complex conflict. The user is filling a form, not reading an essay.\n"
            "6. When you detect a conflict, report it immediately in the `conflicts` array with plain-language details.\n"
            "7. When validation fails, explain each issue in plain language with the specific fix. Never say 'validation failed' generically.\n"
            "8. Respond with ONLY valid JSON matching the AriaResponse schema.\n"
            "9. If the user's response provides sufficient detail for the current section's qualitative context, set `section_context_complete`: true.\n\n"
        )

        # Part 2: Field Knowledge Map
        system_prompt += "FIELD KNOWLEDGE MAP:\n" + FIELD_KNOWLEDGE_MAP + "\n\n"

        # Part 3: Current Schema State
        system_prompt += f"CURRENT MANDATE STATE:\n{json.dumps(req.schema_state, indent=2)}\n\n"

        # Part 4: Trigger Context
        trigger_context = f"TRIGGER TYPE: {req.trigger}\n"
        trigger_context += f"ACTIVE SECTION: {req.section} — {SECTION_PROMPTS.get(req.section, 'Unknown Section')}\n"
        if req.active_field_path:
            trigger_context += f"ACTIVE FIELD PATH: {req.active_field_path}\n"
            trigger_context += f"ACTIVE FIELD VALUE: {req.active_field_value}\n"
        if req.validation_errors:
            trigger_context += f"VALIDATION ERRORS (blocking): {req.validation_errors}\n"
        if req.validation_warnings:
            trigger_context += f"VALIDATION WARNINGS: {req.validation_warnings}\n"
        if req.user_message:
            trigger_context += f"USER MESSAGE: \"{req.user_message}\"\n"

        system_prompt += "TRIGGER CONTEXT:\n" + trigger_context + "\n\n"

        # Part 5: Recent Message History
        history_str = "RECENT MESSAGE HISTORY:\n"
        for msg in req.message_history[-4:]:
            history_str += f"{msg.role.upper()}: {msg.content}\n"
        system_prompt += history_str + "\n\n"

        system_prompt += (
            "INSTRUCTIONS FOR RESPONSE FORMAT:\n"
            "Provide your response as a valid JSON object matching this TypeScript structure:\n"
            "{\n"
            "  \"message\": \"What you say to the user (plain text, no markdown code blocks, Newsreader style conversational content)\",\n"
            "  \"field_updates\": [\n"
            "    {\n"
            "      \"path\": \"dot.notation.path\",\n"
            "      \"value\": any,\n"
            "      \"tier\": 1 or 2,\n"
            "      \"plain_label\": \"Plain language field label\",\n"
            "      \"plain_value\": \"Plain language description of value\",\n"
            "      \"auto_apply\": boolean,\n"
            "      \"auto_apply_delay_ms\": 3000\n"
            "    }\n"
            "  ],\n"
            "  \"questions\": [\"suggestion chip 1\", \"suggestion chip 2\"],\n"
            "  \"conflicts\": [\n"
            "    {\n"
            "      \"description\": \"plain language conflict description\",\n"
            "      \"severity\": \"blocking\" | \"warning\" | \"advisory\",\n"
            "      \"fields_involved\": [\"Field A\", \"Field B\"],\n"
            "      \"suggested_resolution\": \"How to resolve the conflict\"\n"
            "    }\n"
            "  ],\n"
            "  \"section_context_complete\": boolean\n"
            "}\n"
            "Do NOT wrap the output in markdown code blocks like ```json ... ```. Just return raw JSON."
        )

        messages = [
            {"role": "system", "content": system_prompt}
        ]
        if req.user_message:
            messages.append({"role": "user", "content": req.user_message})
        else:
            messages.append({"role": "user", "content": f"Analyze the current trigger context ({req.trigger}) and produce the appropriate guide response."})

        # Model routing based on trigger
        if req.trigger in ("section_enter", "field_focus", "field_change"):
            role = "intake_advisor"
        else:
            role = "adversarial_reasoning"

        # Invoke LLM Adapter
        adapter_res = llm_adapter.invoke(
            messages=messages,
            role=role,
            workflow_id="aria_interactive",
            node_id=f"aria_{req.trigger}"
        )

        content = adapter_res.content.strip()
        
        # Clean markdown wrappers if any
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        data = json.loads(content)

        return AriaResponse(
            message=data.get("message", "I'm looking at your inputs. Let's proceed."),
            field_updates=data.get("field_updates"),
            questions=data.get("questions"),
            conflicts=data.get("conflicts"),
            section_context_complete=data.get("section_context_complete")
        )

    except Exception as e:
        logger.error(f"Error in Aria API endpoint: {str(e)}")
        # Safe fallback response
        return AriaResponse(
            message="Take your time — I'm here to help translate your goals into mandate logic when you're ready.",
            field_updates=[],
            questions=[],
            conflicts=[],
            section_context_complete=False
        )
