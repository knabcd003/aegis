import logging
import json
from typing import Dict, Any, List, Optional
from fastapi import APIRouter
from pydantic import BaseModel
from engines.system.llm_adapter import LLMAdapter

logger = logging.getLogger("aegis.api.aria")

router = APIRouter()
llm_adapter = LLMAdapter()

# ── Request / Response Models ─────────────────────────────────────────────────

class MessageEntry(BaseModel):
    role: str  # "aria" | "user"
    content: str

class AriaContextRequest(BaseModel):
    trigger: str  # "section_enter" | "field_focus" | "field_change" | "user_message" | "validation_result"
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
    tier: int  # 1 = requires confirmation | 2 = auto-apply
    plain_label: str
    plain_value: str
    auto_apply: bool
    auto_apply_delay_ms: Optional[int] = 3000

class ConflictEntry(BaseModel):
    description: str
    severity: str  # "blocking" | "warning" | "advisory"
    fields_involved: List[str]
    suggested_resolution: str

class AriaResponse(BaseModel):
    message: str
    field_updates: Optional[List[FieldUpdate]] = None
    questions: Optional[List[str]] = None
    conflicts: Optional[List[ConflictEntry]] = None
    section_context_complete: Optional[bool] = None

# ── Section Metadata ──────────────────────────────────────────────────────────

SECTION_META = {
    1: {
        "name": "Mandate & Capital",
        "goal": "Establish who you are as an investor, how much Aegis will manage, and the absolute global boundaries.",
        "critical_field": "investable_capital_usd — every position size, drawdown dollar, and exposure limit derives from this number.",
        "schema_keys": ["mandate_identification", "capital_structure"],
    },
    2: {
        "name": "Risk Mandate",
        "goal": "Set the hard stops. These are the gates that protect you when things go wrong.",
        "critical_field": "max_portfolio_drawdown_pct — this is the single number that determines when Aegis stops trading entirely.",
        "schema_keys": ["risk_mandate"],
    },
    3: {
        "name": "Performance Targets",
        "goal": "Define what success looks like and what failure is unacceptable.",
        "critical_field": "primary_objective — everything else in this section flows from whether you want growth, income, or capital preservation.",
        "schema_keys": ["return_mandate"],
    },
    4: {
        "name": "Universe & Asset Class",
        "goal": "Define the playing field — what Aegis is allowed to trade and what it must avoid.",
        "critical_field": "asset_classes_permitted + min_avg_daily_volume_usd — illiquid assets blow up position sizing.",
        "schema_keys": ["universe_mandate"],
    },
    5: {
        "name": "Strategy & Catalysts",
        "goal": "Choose which market events Aegis hunts for and how capital is split across time horizons.",
        "critical_field": "catalyst_types — each event type has different risk acknowledgment requirements. Biotech in particular conflicts with sector exclusions.",
        "schema_keys": ["strategy_mandate"],
    },
    6: {
        "name": "Operational Mandate",
        "goal": "Configure execution timing, latency constraints, and automation level.",
        "critical_field": "automation_level — this determines whether Aegis executes automatically or waits for your approval on each trade.",
        "schema_keys": ["operational_mandate"],
    },
    7: {
        "name": "Behavioral Profile",
        "goal": "Build in psychological guardrails — rules that protect you from your own worst trading instincts.",
        "critical_field": "cooling_off_requirements — the most underestimated field. Overtrading after a loss is the #1 reason mandates fail.",
        "schema_keys": ["behavioral_profile"],
    },
    8: {
        "name": "Tax & Legal",
        "goal": "Align the mandate with your tax situation and any regulatory constraints.",
        "critical_field": "account_tax_status — determines whether wash sale rules apply and how gains should be timed.",
        "schema_keys": ["tax_and_legal"],
    },
    9: {
        "name": "Portfolio Scope & Macro",
        "goal": "Set how Aegis interacts with your existing portfolio and how it responds to macro regimes.",
        "critical_field": "regime_adaptivity_intent — whether Aegis pivots strategy during bear markets or holds its approach regardless.",
        "schema_keys": ["portfolio_scope_and_macro"],
    },
    10: {
        "name": "Governance & Attestation",
        "goal": "Define the review cadence and attest to your compliance awareness.",
        "critical_field": "mandate_review_frequency — how often you commit to revisiting and potentially updating this document.",
        "schema_keys": ["governance_and_review", "mandate_priority_hierarchy"],
    },
}

# ── Per-field Advisor Guidance ────────────────────────────────────────────────
# Injected only when the user focuses that specific field.
# Plain English — never expose schema path names in responses.

FIELD_GUIDANCE: Dict[str, Dict] = {
    "mandate_identification.investor_sophistication": {
        "label": "Investor Sophistication",
        "guide": (
            "This controls which fields and warnings Aegis surfaces throughout the intake. "
            "Retail Novice gets simplified terminology and more guard-rails. Professional unlocks "
            "institutional metrics like Sortino ratio targets and custom VaR limits. "
            "Be honest — choosing Professional when you're not skips important safeguards."
        ),
        "chips": ["I'm new to active trading", "I've traded for several years", "I manage this professionally"],
    },
    "mandate_identification.account_type": {
        "label": "Account Type",
        "guide": (
            "This affects wash sale rule enforcement, options eligibility, and tax treatment. "
            "401k / IRA accounts restrict short selling and some options strategies. "
            "Margin accounts unlock leverage but require the leverage_permitted flag to be set."
        ),
        "chips": ["It's a taxable brokerage", "It's an IRA", "It's a 401k"],
    },
    "capital_structure.investable_capital_usd": {
        "label": "Investable Capital",
        "guide": (
            "This is the single most important number in the form. Every position size, "
            "dollar-based exposure limit, and risk budget is derived from it. "
            "Use the amount currently allocated — not your total net worth. "
            "If you plan to add capital over time, use your starting allocation."
        ),
        "chips": ["Under $50k", "$50k–$250k", "$250k–$1M", "Over $1M"],
    },
    "capital_structure.leverage_permitted": {
        "label": "Leverage Permitted",
        "guide": (
            "Enabling this allows Aegis to use margin. It does NOT automatically apply leverage — "
            "it just removes the hard block. You can still set a max_leverage_ratio separately. "
            "If your account is an IRA or 401k, keep this false — margin is not permitted in retirement accounts."
        ),
        "chips": ["No leverage — protect my capital", "Yes, I have margin enabled"],
    },
    "capital_structure.reserved_cash_pct": {
        "label": "Reserved Cash Buffer",
        "guide": (
            "Percentage of portfolio always held in cash — never deployed into positions. "
            "This is your emergency liquidity. Typical range is 5–15%. "
            "If your drawdown limit is tight, a larger cash buffer helps you recover without forced selling."
        ),
    },
    "capital_structure.max_deployed_pct": {
        "label": "Max Capital Deployed",
        "guide": (
            "The ceiling on how much of the investable capital can be in live positions at any time. "
            "Setting this to 80% means Aegis will always keep at least 20% undeployed. "
            "Useful for accounts where you want to keep dry powder for manual trades alongside Aegis."
        ),
    },
    "risk_mandate.tier_1_risk_constraints.max_portfolio_drawdown_pct": {
        "label": "Maximum Portfolio Drawdown Limit",
        "guide": (
            "When cumulative portfolio losses from the recent peak hit this percentage, "
            "Aegis halts ALL new position entry. Existing positions keep running — this is not a stop-loss. "
            "Too tight (under 8%) causes frequent false halts during normal volatility on concentrated books. "
            "Too loose (over 35%) suggests the user hasn't modeled a real bear scenario. "
            "Start at 2–3× your daily loss limit. If your target return is 20%+, a 10% drawdown cap is probably too restrictive."
        ),
        "chips": ["Conservative (10–15%)", "Moderate (15–20%)", "Aggressive (20–25%)"],
    },
    "risk_mandate.tier_1_risk_constraints.max_daily_loss_pct": {
        "label": "Daily Loss Circuit Breaker",
        "guide": (
            "If intraday losses exceed this percentage of start-of-day NAV, Aegis stops opening new positions for the rest of that session. "
            "This prevents a bad morning from becoming a catastrophic day. "
            "Typical: 1–3% for conservative, 3–5% for aggressive. "
            "Should be roughly 1/5 to 1/3 of your drawdown limit."
        ),
        "chips": ["1% daily limit", "2% daily limit", "3% daily limit", "5% daily limit"],
    },
    "risk_mandate.tier_1_risk_constraints.drawdown_breach_protocol": {
        "label": "Drawdown Breach Protocol",
        "guide": (
            "What happens the moment the drawdown limit is hit. "
            "'Pause and notify' is the safest — nothing happens until you manually restart. "
            "'Reduce positions 50%' lets Aegis partially de-risk automatically. "
            "'Manual restart required' means you have to explicitly log in and re-enable trading — good if you want to be in the loop."
        ),
        "chips": ["Pause all — I want to manually restart", "Reduce positions 50% automatically", "Notify me and wait"],
    },
    "risk_mandate.tier_1_risk_constraints.max_single_position_pct": {
        "label": "Max Position Size (% of Portfolio)",
        "guide": (
            "Hard cap on any single position as a percentage of total portfolio value. "
            "This prevents concentration risk from a single trade. "
            "Typical: 2–5% for diversified, 5–10% for focused/concentrated. "
            "If you're running a high-conviction concentrated book, you might go to 15%, but that requires strong conviction."
        ),
    },
    "risk_mandate.tier_1_risk_constraints.max_single_position_usd": {
        "label": "Max Position Size (Dollar Cap)",
        "guide": (
            "Absolute dollar ceiling per position, regardless of portfolio percentage. "
            "This protects against leverage scenarios where the pct limit would allow a huge dollar amount. "
            "Set this to: max_portfolio_drawdown_pct × investable_capital ÷ max_positions_you'd_want_to_lose."
        ),
    },
    "risk_mandate.tier_1_risk_constraints.max_sector_concentration_pct": {
        "label": "Max Sector Concentration",
        "guide": (
            "No single GICS sector can exceed this percentage of total exposure. "
            "Tech-heavy portfolios often need to explicitly set this higher (30–40%) to give Aegis room. "
            "If your catalyst list includes biotech events, make sure healthcare isn't capped too low."
        ),
    },
    "risk_mandate.tier_1_risk_constraints.max_concurrent_live_strategies": {
        "label": "Max Concurrent Active Strategies",
        "guide": (
            "How many distinct strategies Aegis can run simultaneously. "
            "More is not always better — each strategy competes for the same capital. "
            "For smaller accounts (under $100k), 3–5 concurrent strategies is usually optimal. "
            "Larger accounts can support 8–15 without diluting each strategy's capital."
        ),
    },
    "return_mandate.primary_objective": {
        "label": "Primary Objective",
        "guide": (
            "This is the north star for every trade decision. "
            "Capital growth → Aegis optimizes for total return, accepting volatility. "
            "Income generation → Aegis prioritizes dividend yield and premium collection. "
            "Capital preservation → Aegis avoids volatility, accepts lower returns. "
            "Beat benchmark → Aegis explicitly tracks and tries to outperform your benchmark. "
            "Choose the one that matches why you're trading, not what you wish for."
        ),
        "chips": ["Capital growth", "Income generation", "Capital preservation", "Beat a benchmark"],
    },
    "return_mandate.target_annual_return_pct": {
        "label": "Target Annual Return",
        "guide": (
            "This is advisory — Aegis uses it as a calibration signal, not a hard target. "
            "It cross-checks against your drawdown limit: return/drawdown > 2.0 flags as unrealistic. "
            "If you want 25% annual returns but your drawdown limit is 10%, Aegis will flag that as a contradiction. "
            "Enter 0 if you'd rather not set a specific number."
        ),
    },
    "universe_mandate.tier_1_hard_filters.asset_classes_permitted": {
        "label": "Permitted Asset Classes",
        "guide": (
            "The whitelist. Aegis will only trade instruments in these classes. "
            "US Equities + ETFs is the most common starting point. "
            "Adding Options unlocks premium collection strategies but requires options-specific risk acknowledgments. "
            "Adding Crypto requires separate exchange connectors."
        ),
        "chips": ["US Equities only", "Equities + ETFs", "Equities + ETFs + Options"],
    },
    "universe_mandate.tier_1_hard_filters.min_avg_daily_volume_usd": {
        "label": "Minimum Liquidity Floor",
        "guide": (
            "Aegis will not enter any position in a stock with a 20-day average daily dollar volume below this. "
            "This prevents getting stuck in illiquid names where slippage destroys the edge. "
            "Minimum $500k for small accounts, $1M+ for accounts over $100k, $5M+ for accounts over $500k."
        ),
        "chips": ["$500k minimum", "$1M minimum", "$5M minimum"],
    },
    "strategy_mandate.catalyst_types": {
        "label": "Catalyst Event Types",
        "guide": (
            "These are the market events Aegis actively hunts for. "
            "Each catalyst type has different holding periods, volatility profiles, and risk characteristics. "
            "Earnings momentum is the most common and best-tested. "
            "Biotech FDA events have binary outcomes — high reward, high risk. "
            "M&A and index reconstitution are lower-frequency but more predictable."
        ),
    },
    "operational_mandate.tier_1_operational_constraints.automation_level": {
        "label": "Automation Level",
        "guide": (
            "Fully automated means Aegis executes trades without asking you. "
            "Confirmation required means every trade waits for your approval — useful if you want to stay in control. "
            "Semi-automated with confirmation is recommended for new users until you trust the system."
        ),
        "chips": ["I want to approve each trade", "Fully automatic — Aegis decides"],
    },
    "behavioral_profile.loss_aversion_coefficient": {
        "label": "Loss Aversion Level",
        "guide": (
            "This calibrates how Aegis weights potential losses vs. potential gains when sizing trades. "
            "Standard (2:1) is the behavioral economics baseline — most people feel losses twice as acutely as gains. "
            "Elevated (3:1) means you need larger expected gains before taking a position. "
            "Setting this too high biases Aegis toward inaction, which has its own cost."
        ),
    },
    "tax_and_legal.account_tax_status": {
        "label": "Account Tax Status",
        "guide": (
            "This determines whether Aegis applies wash sale rules, optimizes for long-term vs. short-term gains, "
            "and how it handles year-end tax loss harvesting. "
            "Taxable: full wash sale enforcement, short-term gains taxed as income. "
            "Tax-deferred (Traditional IRA): no wash sale concern, but RMDs apply later. "
            "Tax-exempt (Roth): no tax on gains at all — Aegis can be more aggressive here."
        ),
        "chips": ["Taxable brokerage", "Traditional IRA", "Roth IRA"],
    },
    "portfolio_scope_and_macro.regime_adaptivity_intent": {
        "label": "Regime Adaptivity",
        "guide": (
            "When the market shifts from bull to bear (or vice versa), should Aegis change its strategy mix? "
            "Adaptive means Aegis can shift toward defensive positions in bear regimes. "
            "Consistent means Aegis runs the same strategy regardless of the macro environment — "
            "useful if your strategies are already designed to be regime-agnostic."
        ),
        "chips": ["Adapt to market regimes", "Stay consistent regardless of macro"],
    },
    "governance_and_review.mandate_review_frequency": {
        "label": "Mandate Review Frequency",
        "guide": (
            "How often you commit to revisiting this mandate document. "
            "Markets change, your situation changes, and mandates that aren't reviewed drift out of alignment. "
            "Quarterly is the most common cadence for active investors. "
            "Event-driven only is appropriate if your mandate is very long-term and market-condition-independent."
        ),
        "chips": ["Monthly", "Quarterly", "Semi-annually", "Only when triggered by events"],
    },
}

# ── Helper: Extract Minimal Section Context ───────────────────────────────────

def get_section_context(section: int, schema: Dict[str, Any]) -> Dict[str, Any]:
    """Return only the schema fields relevant to the current section."""
    meta = SECTION_META.get(section, {})
    keys = meta.get("schema_keys", [])
    return {k: schema.get(k, {}) for k in keys}


def get_cross_section_snapshot(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Key facts from other sections that Aria needs for cross-field reasoning."""
    cap = schema.get("capital_structure", {})
    ident = schema.get("mandate_identification", {})
    risk = schema.get("risk_mandate", {}).get("tier_1_risk_constraints", {})
    ret = schema.get("return_mandate", {})
    return {
        "investable_capital": cap.get("investable_capital_usd"),
        "account_type": ident.get("account_type"),
        "investor_sophistication": ident.get("investor_sophistication"),
        "leverage_permitted": cap.get("leverage_permitted"),
        "max_drawdown_pct": risk.get("max_portfolio_drawdown_pct"),
        "max_daily_loss_pct": risk.get("max_daily_loss_pct"),
        "primary_objective": ret.get("primary_objective"),
        "target_return_pct": ret.get("target_annual_return_pct"),
    }


# ── Trigger-Specific Instructions ─────────────────────────────────────────────

TRIGGER_INSTRUCTIONS = {
    "section_enter": (
        "The user just scrolled into this section for the first time (or returned to it).\n"
        "Write 2 sentences: (1) what this section accomplishes in the mandate, (2) the single most important thing to get right.\n"
        "End with ONE focused question that helps you understand their situation so you can give better advice as they fill it out.\n"
        "Do NOT explain what fields are — the user can see the labels. Explain WHY this section matters for THEIR trading."
    ),
    "field_focus": (
        "The user just clicked into a specific field (shown below).\n"
        "If the field already has a value: acknowledge it in one sentence, validate it against cross-section context, suggest a refinement only if warranted.\n"
        "If the field is empty: in ONE sentence explain what this field controls in the trading system (not the label — the effect). "
        "Then make a specific recommendation based on what you know about the user already, or ask ONE question to help you make one.\n"
        "Be direct. Do not repeat the field label back to them."
    ),
    "field_change": (
        "The user just updated a field value (shown below).\n"
        "In ONE sentence: either confirm the value makes sense given their other inputs, or flag a specific cross-field issue.\n"
        "If everything is fine, suggest the next most important empty field they should fill in this section.\n"
        "Do NOT explain what the field does — they just set it. Focus on whether the value is right."
    ),
    "user_message": (
        "The user sent a message. Respond conversationally.\n"
        "If they're describing their situation: extract field values from their words and propose them as field_updates.\n"
        "If they're asking a question: answer it directly and concisely (2-3 sentences max).\n"
        "If they're pushing back on a suggestion: acknowledge their perspective and adjust your recommendation.\n"
        "Always end with either a field_update suggestion or a follow-up question — keep the form moving forward."
    ),
    "validation_result": (
        "The section has validation errors (listed below). For EACH error:\n"
        "1. Name the field in plain English (no schema paths)\n"
        "2. Explain in one sentence WHY it's required and what bad things happen without it\n"
        "3. Suggest a specific value to fix it\n"
        "Keep the entire response to 3-4 sentences total. Be direct — the user needs to act, not read."
    ),
}

# ── Endpoint ──────────────────────────────────────────────────────────────────

ARIA_PERSONA = """You are Aria — a mandate specialist at Aegis AI. You know this form better than anyone alive.

YOUR RULES:
- You are a SPECIALIST, not a chatbot. Every response moves the user toward a complete, valid mandate.
- Keep responses SHORT. 2-4 sentences max unless explaining a conflict. The user is filling a form.
- NEVER use schema field names (say "drawdown limit", not "max_portfolio_drawdown_pct").
- NEVER explain what a field IS — the user can read. Explain the EFFECT and recommend a VALUE.
- Tier 1 fields (anything in tier_1_risk_constraints, capital amounts, account type) ALWAYS need user confirmation: set auto_apply: false.
- Tier 2 fields (context, descriptions, preferences) can be auto-applied: auto_apply: true.
- When you detect a cross-field conflict, report it in the conflicts array. Be specific about which values clash.
- You remember the whole conversation. Reference what the user told you earlier.
- Respond ONLY with valid JSON. No markdown wrappers."""


@router.post("", response_model=AriaResponse)
async def get_aria_guidance(req: AriaContextRequest):
    try:
        section_meta = SECTION_META.get(req.section, {})
        section_context = get_section_context(req.section, req.schema_state)
        cross_section = get_cross_section_snapshot(req.schema_state)

        # Resolve focused field label and guidance
        field_label = None
        field_guide_block = ""
        field_chips: List[str] = []
        if req.active_field_path and req.active_field_path in FIELD_GUIDANCE:
            fg = FIELD_GUIDANCE[req.active_field_path]
            field_label = fg["label"]
            field_guide_block = (
                f"\nFOCUSED FIELD: {field_label}\n"
                f"Current value: {req.active_field_value!r}\n"
                f"Advisor notes: {fg['guide']}\n"
            )
            field_chips = fg.get("chips", [])
        elif req.active_field_path:
            # Unknown field — just send path + value
            field_label = req.active_field_path.split(".")[-1].replace("_", " ").title()
            field_guide_block = (
                f"\nFOCUSED FIELD: {field_label} (path: {req.active_field_path})\n"
                f"Current value: {req.active_field_value!r}\n"
            )

        # Build the prompt
        trigger_instruction = TRIGGER_INSTRUCTIONS.get(req.trigger, TRIGGER_INSTRUCTIONS["user_message"])

        system_prompt = f"""{ARIA_PERSONA}

--- CURRENT SECTION: {req.section} — {section_meta.get('name', '')} ---
Goal of this section: {section_meta.get('goal', '')}
Most critical field here: {section_meta.get('critical_field', '')}

WHAT TO DO FOR THIS TRIGGER ({req.trigger.upper()}):
{trigger_instruction}

--- CROSS-SECTION CONTEXT (key facts about this user) ---
{json.dumps(cross_section, indent=2)}

--- CURRENT SECTION DATA (only what matters now) ---
{json.dumps(section_context, indent=2)}
{field_guide_block}"""

        if req.validation_errors:
            system_prompt += f"\n--- VALIDATION ERRORS ---\n{json.dumps(req.validation_errors)}\n"
        if req.validation_warnings:
            system_prompt += f"\n--- VALIDATION WARNINGS ---\n{json.dumps(req.validation_warnings)}\n"

        # Conversation history
        if req.message_history:
            history_lines = "\n".join(
                f"{m.role.upper()}: {m.content}"
                for m in req.message_history[-6:]
            )
            system_prompt += f"\n--- CONVERSATION SO FAR ---\n{history_lines}\n"

        system_prompt += """
--- RESPONSE FORMAT ---
Return ONLY valid JSON (no markdown, no code fences):
{
  "message": "What you say to the user — plain, direct, conversational. 2-4 sentences max.",
  "field_updates": [
    {
      "path": "exact.schema.path",
      "value": <the value>,
      "tier": 1 or 2,
      "plain_label": "Human-readable field name",
      "plain_value": "Human-readable description of the value",
      "auto_apply": false for tier 1, true for tier 2,
      "auto_apply_delay_ms": 3000
    }
  ],
  "questions": ["Chip 1 for user to click", "Chip 2"],
  "conflicts": [
    {
      "description": "Plain English conflict description",
      "severity": "blocking" | "warning" | "advisory",
      "fields_involved": ["Field A plain name", "Field B plain name"],
      "suggested_resolution": "Exactly what to change"
    }
  ],
  "section_context_complete": false
}
field_updates and questions and conflicts may be empty arrays []. Do not omit keys."""

        messages = [{"role": "system", "content": system_prompt}]
        if req.user_message:
            messages.append({"role": "user", "content": req.user_message})
        else:
            messages.append({
                "role": "user",
                "content": f"[{req.trigger}] Respond now."
            })

        # Fast model for passive triggers, stronger for conversation
        role = "adversarial_reasoning" if req.trigger in ("user_message", "validation_result") else "intake_advisor"

        adapter_res = llm_adapter.invoke(
            messages=messages,
            role=role,
            workflow_id="aria_interactive",
            node_id=f"aria_{req.trigger}",
        )

        content = adapter_res.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        data = json.loads(content)

        # Merge any field chips from guidance into questions
        suggested_questions = data.get("questions", [])
        if field_chips and not suggested_questions:
            suggested_questions = field_chips[:3]

        return AriaResponse(
            message=data.get("message", "I'm here — what would you like to tackle first?"),
            field_updates=data.get("field_updates") or [],
            questions=suggested_questions,
            conflicts=data.get("conflicts") or [],
            section_context_complete=data.get("section_context_complete", False),
        )

    except Exception as e:
        logger.error(f"Aria error: {e}", exc_info=True)
        return AriaResponse(
            message="I'm having trouble connecting right now. Keep filling in the form — I'll jump back in when I can.",
            field_updates=[],
            questions=[],
            conflicts=[],
            section_context_complete=False,
        )
