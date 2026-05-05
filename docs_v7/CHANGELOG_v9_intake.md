# Aegis AI Intake Schema Changelog

**Date:** May 4, 2026
**Version Update:** v7.0 -> v9.0

## Documents Referenced
*   **Previous Version (v7):** `docs_v7/archive/v7_original/aegis_v7_final_blueprint.md`, `docs_v7/archive/v7_original/aegis_llm_intake_v7.md`, `docs_v7/archive/v7_original/v7_intake_summary.md`
*   **New Version (v9):** `docs_v7/aegis_v7_final_blueprint.md`, `docs_v7/updated_intake/aegis_conversational_intake_v9.md`, `docs_v7/updated_intake/aegis_llm_intake_v9.md`, `docs_v7/updated_intake/aegis_intake_schema_v9_blank.json`

## Overview of Changes

The intake schema and parsing architecture have been completely overhauled. The fundamental problem with v7 was that the schema lacked a mechanism for resolving conflicts between preferences, and collapsed multi-dimensional inputs (like risk and time horizon) into reductive labels. 

The v9 schema replaces the basic `MandateProfile` and `UserIntent` binary with a multi-tiered context object designed specifically to drive the downstream Builder and provide explanation context for Glass Box, Arena, and Debates.

### 1. Introduction of the Priority System (The ConflictResolutionProfile)
*   **v7:** No structured conflict resolution. The Builder guessed when preferences clashed.
*   **v9:** Added `mandate_priority_hierarchy`.
    *   `ordered_priorities`: Explicit ranking of core dimensions (e.g. `risk_control` > `universe_specificity`).
    *   `preference_flexibility`: Tags applied to all preferences (`immovable`, `high_priority`, `medium_priority`, `low_priority`).
    *   `trade_off_philosophy`: Prose explaining how the user wants tradeoffs handled.

### 2. Multi-Dimensional Risk Profile
*   **v7:** Single `risk_tolerance` string.
*   **v9:** 6 separate dimensions: `volatility_tolerance`, `gap_risk_tolerance`, `concentration_tolerance`, `tail_risk_tolerance`, `time_risk_tolerance`, and `regret_asymmetry`. This allows the Builder to calibrate different risk settings for different strategy types.

### 3. Horizon Allocation
*   **v7:** Single string (`time_horizon`).
*   **v9:** `horizon_allocation` list of weighted time buckets. Enables building a portfolio of strategies across different timeframes based on proportional capital weights.

### 4. Regime Universe Pairs
*   **v7:** Loose tags (`preferred_regimes`, `catalyst_types`).
*   **v9:** `regime_universe_pairs` explicitly links a desired regime (e.g., momentum) with a specific sector/catalyst, giving the Builder clear, thesis-backed direction instead of mixing mismatched regimes and universes.

### 5. Explicit, Inferred, and Assumed Tagging
*   **v7:** Relied on raw LLM summarization.
*   **v9:** Enforces strict tagging (`[EXPLICIT]`, `[INFERRED]`, `[ASSUMED]`) across all prose fields. The Builder treats constraints differently based on how directly the user stated them.

### 6. Conversational Intake Spec (Path A)
*   **v7:** A 4-question wizard.
*   **v9:** A detailed 7-stage conversational behavioral specification (`aegis_conversational_intake_v9.md`) designed to elicit high-signal responses for the complex schema without overwhelming the user.

### 7. Fundamental Screens
*   **v7:** Not explicitly handled outside of `exclude_tickers`.
*   **v9:** Added `fundamental_screens` to `universe_mandate` to capture financial characteristic requirements (e.g. profitability).
