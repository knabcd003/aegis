# Aegis AI Global Changelog

This document tracks major version shifts, architectural changes, and documentation archives across the entire Aegis AI platform.

---

## [v9.1] - 2026-05-06

### Form-Based Intake Shift
Replaced the LLM conversational flow entirely with a **7-stage deterministic hybrid form** (`aegis_form_intake_v9.md`). Hard constraints are mapped 1:1 via structured fields to eliminate hallucinations, while LLMs are strictly relegated to stateless validation of user-provided prose.

**Documents Referenced & Archived:**
*   **New Specs:** `docs_v7/updated_intake/aegis_form_intake_v9.md`
*   **Archived Specs:** `docs_v7/updated_intake/archive_aegis_conversational_intake_v9.md`

---

## [v9.0] - 2026-05-04

### Intake Schema Architecture Overhaul
The intake schema and parsing architecture were completely overhauled. The fundamental problem with v7 was that the schema lacked a mechanism for resolving conflicts between preferences, and collapsed multi-dimensional inputs (like risk and time horizon) into reductive labels. The v9 schema replaces the basic `MandateProfile` and `UserIntent` binary with a multi-tiered context object designed specifically to drive the downstream Builder and provide explanation context for Glass Box, Arena, and Debates.

### Key Changes
1. **Introduction of the Priority System (The ConflictResolutionProfile)**
   *   **v7:** No structured conflict resolution. The Builder guessed when preferences clashed.
   *   **v9:** Added `mandate_priority_hierarchy` with `ordered_priorities`, `preference_flexibility`, and `trade_off_philosophy`.
2. **Multi-Dimensional Risk Profile**
   *   **v7:** Single `risk_tolerance` string.
   *   **v9:** 6 separate dimensions allowing the Builder to calibrate different risk settings for different strategy types.
3. **Horizon Allocation**
   *   **v7:** Single string (`time_horizon`).
   *   **v9:** `horizon_allocation` list of weighted time buckets.
4. **Regime Universe Pairs**
   *   **v7:** Loose tags (`preferred_regimes`, `catalyst_types`).
   *   **v9:** `regime_universe_pairs` explicitly links a desired regime with a specific sector/catalyst.
5. **Explicit, Inferred, and Assumed Tagging**
   *   **v9:** Enforces strict tagging (`[EXPLICIT]`, `[INFERRED]`, `[ASSUMED]`) across all prose fields.
6. **Fundamental Screens**
   *   **v9:** Added `fundamental_screens` to `universe_mandate`.

**Documents Referenced & Archived:**
*   **Previous Version (v7):** `docs_v7/archive/v7_original/aegis_v7_final_blueprint.md`, `docs_v7/archive/v7_original/v7_intake_summary.md`
*   **New Version (v9):** `docs_v7/aegis_v7_final_blueprint.md`, `docs_v7/updated_intake/aegis_llm_intake_v9.md`, `docs_v7/updated_intake/aegis_intake_schema_v9_blank.json`
*   **Archived LLM Spec:** `docs_v7/archive/aegis_llm_intake_v7.md`

---

## [v7.0] - Previous Stable Build

### Transition from V6
The Aegis architecture was rebuilt to eliminate the "agentic analyst loop" model (v6) which suffered from catastrophic cost overruns and latency. v7 introduces a deterministic, multi-stage pipeline (Intake -> Simulation -> Debate -> Sentinel) powered by a verified component library.

**Documents Referenced & Archived:**
*   **Archived Code:** Root directory `_v6_archive/` contains old v6 analyst code.
*   **Current Architecture:** `docs_v7/aegis_v7_final_blueprint.md`
