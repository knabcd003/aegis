# AEGIS AI — FORM-BASED LLM INTAKE SYSTEM
## Behavioral Specification for Aegis-Native Mandate Building

**Version:** v9.0
**Document purpose:** This document defines the Form-based Intake architecture, replacing the deprecated conversational intake. It outlines the hybrid approach where explicit Tier 1 hard constraints are captured deterministically, and the LLM acts as a bounded validator and prose synthesizer for Tier 2 context.

---

## PART I: PHILOSOPHY AND DESIGN PRINCIPLES

### The Hallucination Problem
Conversational intake relies on the LLM to extract fields from natural language. When a user says "I'm conservative", inferring a `max_portfolio_drawdown_pct` of 10% is a hallucination. The LLM chose the number, not the user. Tier 1 hard constraints should never involve inference.

### The Hybrid Form Solution
The intake process is a 7-section form that maps directly to the logical groupings of the `V9IntakeSchema`.
Each section contains:
1. **Structured Fields**: Explicit inputs (dropdowns, number inputs, multi-select, toggles) that map 1:1 to Tier 1 constraints and structured Tier 2 fields. What the user types is what gets stored.
2. **Detail Box**: A free-text area where the user provides nuance, context, history, and reasoning. The LLM reads this to populate the Tier 2 prose fields.
3. **Validate Button**: Submits the structured fields and the detail box to a stateless backend endpoint for LLM validation and enrichment.

### What the LLM Actually Does
The LLM's role is strictly bounded to four functions:
1. **Detail Box → Prose Translation**: Deterministically maps the user's free-text to the corresponding Tier 2 prose fields applying `[EXPLICIT]`/`[INFERRED]` tagging.
2. **Gap Detection**: Identifies missing context that would improve strategy generation and returns targeted questions.
3. **Contradiction Detection**: Cross-references structured inputs against the detail box content and flags conflicts.
4. **Cross-Section Synthesis**: At final confirmation, it runs a synthesis pass across all sections to construct `regime_universe_pairs`, `macro_views`, and `filing_notes.contradictions`.

---

## PART II: SECTION BREAKDOWN

### Section 1 — Foundation
**Structured:** investable capital (number), account type (dropdown), existing holdings (ticker input), holdings to never touch (ticker input).
**Detail box:** "Tell us about your existing portfolio and what role you want Aegis to play."
**LLM populates:** `investor_profile.portfolio_context`, `portfolio_scope.ambition_description`, `portfolio_scope.portfolio_beta_existing`.

### Section 2 — Risk
**Structured:** max portfolio drawdown % (number slider), max concurrent strategies (number), leverage permitted (toggle).
**Detail box:** "How do you think about risk? Describe your tolerance for volatility, overnight gaps, concentration, and any past experiences that shaped your thinking."
**LLM populates:** all `risk_profile` prose sub-fields, `risk_profile.loss_aversion_context`.

### Section 3 — Performance Targets
**Structured:** primary objective (dropdown), target annual return % (number), benchmark (dropdown + custom), target return horizon in months (number).
**Detail box:** "What does success look like? What would make you pull the plug on this?"
**LLM populates:** `performance_targets.target_annual_return_context`, `return_character`, `success_definition`, `failure_definition`.

### Section 4 — Universe
**Structured:** asset classes (multi-select), sectors of interest (multi-select), sectors to avoid (multi-select), market cap range (dual slider), min daily volume (number), price range (dual input), geographies (multi-select), specific tickers to focus (ticker), tickers to exclude (ticker).
**Detail box:** "What do you want to trade and why? Include any fundamental requirements and what you know about these markets."
**LLM populates:** `universe_mandate.universe_description`, `sector_reasoning`, `equity_character`, `fundamental_screens`, `asset_class_preferences`.

### Section 5 — Strategy Intent
**Structured:** catalyst types (multi-select), strategy types to avoid (multi-select), options permitted (toggle), short selling permitted (toggle).
**Detail box:** "How do you think about entering and exiting trades? Describe the kinds of setups you're looking for, what you've tried before, and what you want the system to prioritize."
**LLM populates:** `strategy_intent.regime_preferences`, `entry_philosophy`, `exit_philosophy`, `holding_philosophy`, `catalyst_preferences`, `complexity_preference`.

### Section 6 — Execution
**Structured:** account type (carried forward), brokerage (text input), pre/post market capable (toggle), order type preference (dropdown).
**Detail box:** "When can you realistically act on a trade signal? Describe your available windows and any execution constraints."
**LLM populates:** `execution_profile.available_windows`, `execution_latency_context`, `brokerage_constraints`.

### Section 7 — Priorities
**Structured:** drag-to-rank list of dimensions. Per-dimension flexibility rating (dropdown).
**Detail box (Trade-off philosophy):** "In your own words, when the system has to sacrifice one thing to get another, what should guide that decision?"
**LLM populates:** `mandate_priority_hierarchy.ordered_priorities`, `preference_flexibility`, `trade_off_philosophy`. (LLM writes rationale from context).

---

## PART III: ARCHITECTURE

- **Frontend (`IntakePage.tsx`)**: Manages the 7 sections, storing draft state in `localStorage` with auto-save. Implements upstream lock invalidation (if Section 1 is edited, Section 2-7 locks are invalidated).
- **Validation Endpoint (`intake_validate.py`)**: Stateless. Returns populated prose fields, gap questions, and contradictions for the requested section.
- **Confirm Endpoint (`intake_confirm.py`)**: Runs deterministic cross-section validation (e.g. return target vs drawdown Sharpe check) and invokes LLM for full schema synthesis prior to lock.

---
*Aegis AI v9.0 — Form-Based Intake System Specification*
