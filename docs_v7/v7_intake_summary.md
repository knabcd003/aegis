# Aegis AI V7 LLM Intake Summary

The intake process is the only interaction the user has to steer Aegis before strategies are constructed. There are two paths to populate the `Aegis Intake Schema` (JSON):

1. **Path A (Form-Based Intake, Default)**: A deterministic 7-stage form that explicitly captures Tier 1 hard constraints while using an LLM to validate and enrich Tier 2 soft preferences from free-text detail boxes.
2. **Path B (Comprehensive/Power User)**: The user has an AI (Claude/ChatGPT/etc.) fill out an extensive JSON schema (`aegis_intake_schema_v9_blank.json`) based on their conversation history, guided by `aegis_llm_intake_v9.md`.

## Golden Rule of Intake interpretation
**Hard Constraints vs. Soft Preferences**

### 1. Hard Constraints (The `required` mapping)
These become the **`MandateProfile`**.
*   **Fields:** `risk_tolerance`, `max_drawdown_pct`, `time_horizon`, `raw_desire`
*   **Rule:** Interpret these with **EXTREME CONSERVATISM**.
*   Never infer a higher risk tolerance or max drawdown. If the user mentions "moderate risk" but wants "biotech plays," stick to the conservative bounds of moderate risk (e.g., `max_drawdown_pct: 15`).
*   Empty values are fine; Aegis will default strictly.
*   `raw_desire`: Must preserve the user's exact wording.

### 2. Soft Preferences (The `universe`, `character`, `macro` mappings)
These become the **`UserIntent`**.
*   **Rule:** Use reasonable inference based *only* on stated goals. Do not extrapolate.
*   If the user says "I like tech stocks", add `["Technology"]` to `sectors_of_interest`. Do not randomly assume they are bullish on "semiconductor capex cycles" for the `macro_views` section.
*   `leverage` defaults to `false`. Never enable unless explicitly requested.

## Hand-off and Safety
After the external LLM or path populates the JSON, the schema is parsed into the pipeline:
1. Contradictions (e.g., "Conservative Risk" vs. "Penny Stock Desire") are detected mathematically.
2. Aegis displays the parameters back to the user in **plain language**.
3. Aegis flags the contradictions to the user.
4. **The user must explicitly confirm** these bounds before the system freezes them and the V7 pipeline engages.
