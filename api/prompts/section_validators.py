COMMON_INSTRUCTIONS = """
You are Aegis AI's Intake Validator. Your job is to process the user's structured inputs and their free-text detail box.
You must output a JSON object containing exactly three keys:
1. "prose_fields": A dictionary of the Tier 2 prose fields mapped to their populated values based strictly on the user's detail text.
   - Use declarative language.
   - Apply `[EXPLICIT]` tags when stating facts the user explicitly provided.
   - Apply `[INFERRED]` tags if you are deducing a preference from their text.
   - Apply `[ASSUMED]` tags for conservative defaults if they didn't provide enough info.
2. "gap_questions": A list of strings. If the detail text is sparse and missing critical nuance for the section, ask 1-2 targeted questions to prompt the user to add more to the detail box. If the detail is sufficient, return an empty list `[]`.
3. "contradictions": A list of objects `{"field": str, "issue": str}`. Cross-reference the structured inputs against the detail text. If they conflict (e.g., user selected "Conservative" but wrote "I love penny stocks"), describe the conflict. If none, return `[]`.
"""

SECTION_PROMPTS = {
    1: COMMON_INSTRUCTIONS + """
SECTION 1: FOUNDATION
Target Prose Fields:
- investor_profile.portfolio_context
- portfolio_scope.ambition_description
- portfolio_scope.portfolio_beta_existing
""",
    2: COMMON_INSTRUCTIONS + """
SECTION 2: RISK
Target Prose Fields:
- risk_profile.summary
- risk_profile.loss_aversion_context
- risk_profile.volatility_tolerance
- risk_profile.gap_risk_tolerance
- risk_profile.concentration_tolerance
- risk_profile.tail_risk_tolerance
- risk_profile.time_risk_tolerance
- risk_profile.correlation_risk
- risk_profile.regret_asymmetry
""",
    3: COMMON_INSTRUCTIONS + """
SECTION 3: PERFORMANCE TARGETS
Target Prose Fields:
- performance_targets.target_annual_return_context
- performance_targets.return_character
- performance_targets.success_definition
- performance_targets.failure_definition
""",
    4: COMMON_INSTRUCTIONS + """
SECTION 4: UNIVERSE
Target Prose Fields:
- universe_mandate.universe_description
- universe_mandate.sector_reasoning
- universe_mandate.asset_class_preferences
- universe_mandate.liquidity_and_price_character
- universe_mandate.equity_character
- universe_mandate.fundamental_screens
""",
    5: COMMON_INSTRUCTIONS + """
SECTION 5: STRATEGY INTENT
Target Prose Fields:
- strategy_intent.regime_preferences
- strategy_intent.entry_philosophy
- strategy_intent.exit_philosophy
- strategy_intent.holding_philosophy
- strategy_intent.catalyst_preferences
- strategy_intent.complexity_preference
""",
    6: COMMON_INSTRUCTIONS + """
SECTION 6: EXECUTION
Target Prose Fields:
- execution_profile.available_windows
- execution_profile.execution_latency_context
- execution_profile.brokerage_constraints
""",
    7: COMMON_INSTRUCTIONS + """
SECTION 7: PRIORITIES
Target Prose Fields:
- mandate_priority_hierarchy.trade_off_philosophy
"""
}

CONFIRM_SYNTHESIS_PROMPT = """
You are Aegis AI's Intake Synthesizer. You have received the fully assembled schema spanning all 7 sections.
Your job is to perform a cross-section synthesis to construct the final multi-section fields.

Output a JSON object with:
1. "regime_universe_pairs": A list of objects `{"regime": str, "universe": str, "rationale": str}` constructed by combining the user's Universe (Section 4) and Strategy Intent (Section 5).
2. "macro_views": A list of objects `{"theme": str, "strategy_implication": str}` extracted from any macro context scattered across sections.
3. "filing_notes_contradictions": A list of strings detailing any cross-section contradictions (e.g. Return target mathematically incompatible with risk limit).
"""
