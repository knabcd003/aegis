# AEGIS AI — INTAKE LAYER v10.0
## Complete Implementation Specification

**Document purpose:** Self-contained implementation spec for the Aegis intake layer redesign. Covers both intake paths (form-based and LLM conversational), the complete field schema, all validation architecture, contradiction detection rules, behavioral enforcement mechanisms, and LLM prompt specifications. The Builder and all downstream pipeline components receive the same JSON schema regardless of which intake path was used.

**Scope:** Intake layer only. Builder handoff and downstream pipeline changes are out of scope for this document.

---

## PART 1: ARCHITECTURE OVERVIEW

### 1.1 Two Intake Paths, One Schema

There are two ways a user can produce an Aegis mandate schema:

**Path A — Form-Based Intake (`IntakePage.tsx`)**
A 10-section hybrid form. Tier 1 hard constraints are captured via structured UI controls (number inputs, dropdowns, multi-select, toggles, sliders) that map 1:1 to schema fields. No inference. The LLM acts as a bounded validator and prose synthesizer — it reads the user's free-text detail boxes and populates Tier 2 prose fields. At confirmation, a two-pass LLM call runs contradiction detection and cross-section synthesis.

**Path B — LLM Conversational Intake (`/intake/chat`)**
A structured conversational flow in which the LLM guides the user through all 13 schema sections via natural language. The LLM extracts structured field values AND prose context, applies `[EXPLICIT]`/`[INFERRED]` tagging to every populated field, runs inline contradiction detection, and produces the same JSON schema as Path A.

The Builder receives only the final JSON. It cannot distinguish which path was used. The schema must be path-agnostic.

### 1.2 What the LLM Does and Does Not Do

**The LLM DOES:**
- Translate free-text detail box content into Tier 2 prose fields
- Tag every populated field as `[EXPLICIT]` (user stated directly) or `[INFERRED]` (LLM derived from context)
- Detect gaps in context and return targeted questions
- Detect contradictions within and across sections
- Synthesize cross-section fields (`regime_universe_pairs`, `macro_views`, `ordered_priorities` rationale, `realistic_performance_range`)
- Run the Sharpe feasibility check and generate `filing_notes`

**The LLM NEVER:**
- Populates Tier 1 fields from inference. If the user says "I'm conservative," `max_portfolio_drawdown_pct` is NOT set to 10% by the LLM. Tier 1 fields are set exclusively by explicit user input via structured form controls (Path A) or explicit numerical statements (Path B).
- Overrides a Tier 1 field that has been set
- Generates `regime_universe_pairs` from implied preferences — only from explicitly linked user statements

### 1.3 Tier Framework

**Tier 1 — Mandate Hard Constraints**
Mechanically enforced by pipeline code. No AI agent can override. Populated only from explicit user input, never inferred. A field is Tier 1 if and only if: (a) its value directly drives a mathematical calculation in position sizing, risk management, or universe filtering, AND (b) violating it exposes the user to capital risk they did not explicitly consent to.

**Tier 2 — Investment Policy Context**
Read by the Builder as a portfolio manager reads a client brief. Informs strategy selection, exit rule design, regime preferences, and generation priorities. LLM populates prose fields from user's free-text. Structured Tier 2 fields are set deterministically.

**Tier 2-Hard — Immovable Policy Constraints**
Tier 2 fields tagged "immovable" in `mandate_priority_hierarchy.preference_flexibility`. Applied within the already-constructed universe (post Tier 1 filtering). Builder treats as inviolable within scope. Must NOT be collapsed into Tier 1 — they apply at a different pipeline stage. Example: "immovable" aversion to shorting biotech allows long biotech but blocks short biotech. A Tier 1 sector exclusion blocks all biotech. These are different constraints applied at different stages.

---

## PART 2: COMPLETE SCHEMA REFERENCE

All fields are documented here with: tier, type, builder note, enforcement mechanism (where applicable), and any implementation notes from the feedback review.

### SCHEMA SECTION A — MANDATE IDENTIFICATION

**Purpose:** Establishes mandate context. The most important contextual field is `aegis_capital_as_pct_of_total_liquid_net_worth` — a 10% max single position means fundamentally different things at 5% vs 90% of net worth. Read before interpreting any other section.

```
mandate_identification:
  account_type                              [TIER 1] enum
    options: individual_taxable | joint_taxable | traditional_ira | roth_ira |
             401k_solo | trust | corporate_taxable | sep_ira | other
    drives: tax section defaults, PDT rule enforcement, margin availability,
            ERISA applicability

  account_identifier                        [TIER 2] string
    purpose: multi-account disambiguation

  investor_sophistication                   [TIER 2] enum
    options: retail_novice | retail_experienced | semi_professional | professional
    IMPORTANT: Set in Section A before any other section renders.
    Drives conditional form complexity throughout all subsequent sections.
    retail_novice → simplified field sets, more explanatory copy, hide advanced fields
    professional → full field set, technical language, no explanations
    Builder use: calibrates explanation depth and default conservatism in strategy output

  mandate_role                              [TIER 2] enum
    options: entire_liquid_portfolio | growth_sleeve | satellite_speculative |
             income_sleeve | other

  aegis_capital_as_pct_of_total_liquid_net_worth  [TIER 2] number
    Builder use: concentration decisions; a 10% max_single_position_pct at 90%
    of net worth = 9% of total wealth per trade vs 0.5% at 5% of net worth

  total_liquid_net_worth_estimate_usd       [TIER 2] number

  existing_non_aegis_portfolio_description  [TIER 2] prose
    Builder use: total portfolio correlation context

  portfolio_beta_existing                   [TIER 2] number
    Builder use: interacts with target_portfolio_beta in risk section to define
    what Aegis should add to the total portfolio

  mandate_inception_reason                  [TIER 2] prose

  investment_experience                     [TIER 2] prose

  behavioral_history                        [TIER 2] prose
    Builder use: past financial trauma or overconfidence shapes risk defaults
```

### SCHEMA SECTION B — CAPITAL STRUCTURE

**Implementation note on `existing_holdings`:** Field is `[string]` ticker list only. No quantity, no cost basis, no account. Rationale: cost_basis and quantity are portfolio management fields that belong to a live positions tracker, not an intake schema — Aegis didn't enter those positions. Ticker list is retained for portfolio-level correlation awareness: if user already holds 35% of net worth in Healthcare outside Aegis, sector concentration limits within Aegis alone are insufficient context. `tickers_never_touch` handles explicit exclusions regardless.

```
capital_structure:
  investable_capital_usd                    [TIER 1] number
    drives: absolute dollar scalar for all position sizing

  reserved_cash_pct                         [TIER 1] number
    default: 10
    drives: system never deploys more than (100 - reserved_cash_pct)% of capital
    purpose: protects against margin calls, unsettled trade complications,
             unexpected liquidity needs

  max_deployed_pct                          [TIER 1] number
    default: 80
    drives: maximum % of investable_capital in live positions simultaneously
    note: distinct from reserved_cash_pct — accounts for pending orders,
          unsettled trades, and positions-in-flight

  leverage_permitted                        [TIER 1] boolean default: false

  max_leverage_ratio                        [TIER 1] number
    active: only if leverage_permitted = true
    excluded from enforcement: if leverage_permitted = false
    drives: gross exposure / capital ceiling

  margin_account                            [TIER 1] boolean default: false
    drives: PDT rule enforcement, intraday strategy eligibility

  options_permitted                         [TIER 1] boolean default: false

  short_selling_permitted                   [TIER 1] boolean default: false

  leverage_context                          [TIER 2] prose

  existing_holdings                         [TIER 2] [string]
    type: array of ticker strings only — no quantity, no cost basis
    purpose: portfolio-level correlation awareness
    example: ["AAPL", "MSFT", "JNJ"]
    Builder use: flag if new strategy positions create total-portfolio
                 concentration beyond what Aegis's own sector limits capture

  tickers_never_touch                       [TIER 1] [string]
    type: array of ticker strings
    enforcement: absolute unconditional exclusion before any other logic
```

### SCHEMA SECTION C — RISK MANDATE

**The seven-field Tier 1 minimum.** Each addresses a distinct failure mode. None are redundant with each other.

**Implementation note on `max_daily_loss_pct`:** Reference point is **portfolio value at market open for that trading day**. Not investable_capital_usd (static), not current portfolio value (moving target mid-day). Starting-of-day NAV is the standard reference in systematic trading and must be the implementation reference. Document this in code comments.

**Implementation note on `drawdown_breach_protocol`:** This field is required. The mandate cannot lock (confirm step blocked) if this field is null. The form must enforce this before proceeding to confirmation.

```
risk_mandate:

  [TIER 1 FIELDS]

  max_portfolio_drawdown_pct                [TIER 1] number
    THE foundational risk input. Builder derives portfolio volatility target
    via risk-constrained Kelly logic. Derivation assumes conservative baseline
    Sharpe of 0.4-0.6 for pre-deployment strategies. Updated as live
    performance data accumulates. Derivation documented transparently in
    filing_notes.volatility_target_derivation.

  max_daily_loss_pct                        [TIER 1] number
    reference point: portfolio value at market open for that trading day
    enforcement: if intraday P&L falls below (-1 * max_daily_loss_pct)% of
                 starting-of-day NAV, halt all new position-building for the
                 remainder of that trading day. Existing positions continue
                 their normal exit logic. Resets at next market open.
    distinct from: max_portfolio_drawdown_pct (cumulative; kills strategies)
                   vs max_daily_loss_pct (daily; halts new entries that day)

  drawdown_breach_protocol                  [TIER 1] enum REQUIRED
    options: pause_all_notify_user | reduce_position_sizes_50pct |
             manual_restart_required | reduce_and_notify
    mandate cannot lock if null
    enforcement: executed immediately when max_portfolio_drawdown_pct is hit

  max_single_position_pct                   [TIER 1] number
    enforcement: percentage ceiling per name
    binding rule: both max_single_position_pct and max_single_position_usd
                  are enforced simultaneously; the more restrictive applies

  max_single_position_usd                   [TIER 1] number
    enforcement: absolute dollar ceiling per name
    rationale: percentage alone fails for large accounts — 5% of $2M in a
               $1M ADV stock = $100K position = 10% market impact, eroding
               the edge the strategy is designed to capture
    binding rule: see max_single_position_pct above

  max_sector_concentration_pct              [TIER 1] number
    enforcement: maximum capital weight in any single GICS sector
                 simultaneously across all live positions
    rationale: post-catalyst strategies generate correlated sector signals
               during earnings seasons and FDA decision weeks

  max_concurrent_live_strategies            [TIER 1] integer
    enforcement: hard ceiling on simultaneous open strategy positions
    rationale: (1) operational safeguard; (2) stress-scenario protection —
               covariance matrix manages correlation under normal conditions
               but underestimates stress-period correlation spikes (→1.0);
               this field provides structural protection. NOT redundant with
               the covariance matrix — complementary.

  max_position_as_pct_of_adv               [TIER 1] number default: 3
    enforcement: maximum position size as % of the asset's 20-day avg
                 daily volume. Prevents market impact erosion of theoretical
                 edge. Critical for small-cap post-catalyst strategies.
    empirical basis: 1-5% of ADV is the validated threshold range

  [TIER 2 FIELDS]

  volatility_tolerance                      [TIER 2] prose
  gap_risk_tolerance                        [TIER 2] prose
  concentration_tolerance                   [TIER 2] prose
  tail_risk_tolerance                       [TIER 2] prose
  time_risk_tolerance                       [TIER 2] prose

  regret_asymmetry                          [TIER 2] structured + prose
    type: loss_regret_dominant | miss_regret_dominant | balanced
    magnitude: mild | moderate | severe
    context: prose

    BUILDER ENFORCEMENT — HIGHEST IMPACT FIELD IN THIS SECTION:
    loss_regret_dominant → enforce strict time-based exits; auto-liquidate
      position on Day N regardless of P&L (N derived from horizon_allocation
      midpoint for that strategy bucket)
    miss_regret_dominant → use trailing volatility stops; no time-based exit
      override; allow momentum to run for full anomaly window
    balanced → hybrid: time-based floor (auto-exit at Day N) with trailing
      stop that can extend if momentum is sustained above threshold

  loss_aversion_context                     [TIER 2] prose
  correlation_risk_context                  [TIER 2] prose

  target_portfolio_beta                     [TIER 2] number
    Builder use: interacts with mandate_identification.portfolio_beta_existing
    to define what Aegis should add to the total portfolio
    0 = market neutral intent; 1 = market-matching; >1 = high-beta mandate

  stress_scenario_constraints               [TIER 2] array
    schema: [{scenario_name: string, max_acceptable_loss_pct: number}]
    Builder use: validate strategy robustness against named historical scenarios
    example: [{scenario_name: "covid_march_2020", max_acceptable_loss_pct: 25}]
```

### SCHEMA SECTION D — RETURN MANDATE

**All fields Tier 2. Returns are outputs, not constraints.**

**Eliminated from v9:** `target_win_rate_pct` is removed entirely as an input. Win rate is an output of the strategy's edge distribution. For momentum strategies, empirical win rates are 45–55%. Constraining the optimizer to 70%+ forces premature winner liquidation, converts positive skew to negative skew. Retained as an informational output field in performance reporting only — never as an intake input.

```
return_mandate:

  primary_objective                         [TIER 2] enum
    options: capital_growth | income_generation | capital_preservation |
             beat_benchmark | absolute_return
    Builder use: anchor for all other fields in this section

  target_annual_return_pct                  [TIER 2] number
    ADVISORY ONLY — explicitly labeled in UI and schema
    Builder use: calibrate aggressiveness of signal selection
    NOT a hard optimization target. Sharpe feasibility check at confirmation
    flags if this implies Sharpe > 1.5 (warning) or > 2.0 (blocking)

  target_annual_return_context              [TIER 2] prose

  benchmark                                 [TIER 2] enum
    options: sp500 | nasdaq100 | russell_2000 | custom_ticker |
             absolute_return_hurdle

  benchmark_context                         [TIER 2] prose

  return_character                          [TIER 2] structured
    smoothness_preference: smooth_and_consistent | lumpy_and_high
    income_vs_appreciation: income | appreciation | balanced
    UI NOTE: These are technical labels requiring plain-language explanations
    in the form. Suggested copy:
      smooth_and_consistent — "Smaller, more frequent gains. Lower month-to-month
        volatility. Fewer large wins."
      lumpy_and_high — "Larger, less frequent gains. Some months will be flat or
        negative. Wins are larger when they come."

  target_monthly_income_usd                 [TIER 2] number
    active: only if primary_objective = income_generation

  min_acceptable_sharpe                     [TIER 2] number advisory

  target_return_horizon_months              [TIER 2] number
    operational implication: strategies must demonstrate success/failure
    within this window

  success_definition                        [TIER 2] prose
  failure_definition                        [TIER 2] prose

  expectation_calibration_acknowledged      [TIER 2] boolean default: false
    Set to true only after user has reviewed and acknowledged
    filing_notes.realistic_performance_range at confirmation step.
    Mandate cannot lock if false.
```

### SCHEMA SECTION E — UNIVERSE MANDATE

**Implementation note on `fundamental_screens`:** The `applies_to_catalyst_types` field on each screen is critical. It allows users to apply profitability screens to PEAD earnings trades while leaving the biotech FDA universe unfiltered. Without it, the user must choose between fundamental screens and biotech exposure. The system generates `fundamental_screen_compatibility_warnings` automatically at the section validation step based on selected catalyst types in Section F.

```
universe_mandate:

  [TIER 1 — HARD FILTERS]
  Applied as database query parameters before signal generation.

  asset_classes_permitted                   [TIER 1] [enum]
    options: us_equities | canadian_equities | etfs | equity_options | us_adrs

  geographies_permitted                     [TIER 1] [enum]
    options: us | canada | uk | eu | asia_pacific

  market_cap_min_usd                        [TIER 1] number

  market_cap_max_usd                        [TIER 1] number nullable
    null = no upper cap

  min_avg_daily_volume_usd                  [TIER 1] number
    recommended floor: 1000000
    empirical basis: validated threshold for baseline tradeability in
    momentum strategies (research report, Section 5)

  price_min_usd                             [TIER 1] number
    recommended: 1.00
    purpose: market manipulation and spread quality gate, not a liquidity proxy
    rationale: sub-$1.00 stocks disproportionately subject to pump-and-dump
    dynamics that contaminate momentum signals

  restrict_to_sectors_of_interest          [TIER 1] boolean default: false
    if true: sectors_of_interest is enforced as a hard filter
    if false: sectors_of_interest is a Tier 2 preference weight

  sectors_of_interest                       [TIER 1 if restrict=true, else TIER 2] [enum]
    options: technology | healthcare | financials | consumer_discretionary |
             consumer_staples | industrials | energy | materials |
             real_estate | utilities | communication_services | biotech

  sectors_excluded                          [TIER 1] [enum]
    enforcement: absolute exclusion before any other logic

  specific_tickers_focus                    [TIER 1] [string]
    if populated: universe narrows to these names (plus sector constraints)

  specific_tickers_exclude                  [TIER 1] [string]
    enforcement: never trade, no override

  esg_hard_exclusions                       [TIER 1] [enum]
    options: weapons | tobacco | gambling | adult_content | cannabis |
             fossil_fuels | other

  [TIER 2 — UNIVERSE CONTEXT]

  universe_description                      [TIER 2] prose
  sector_reasoning                          [TIER 2] prose
    Builder use: sub-sector prioritization, adjacent sector signal handling,
    regime-dependent weighting. NOT decorative despite not changing the
    database WHERE clause — informs decisions within the universe.
  equity_character                          [TIER 2] prose
  liquidity_and_price_character             [TIER 2] prose
  options_context                           [TIER 2] prose
  etf_preferences                           [TIER 2] prose
  asset_class_preferences                   [TIER 2] prose

  [FUNDAMENTAL SCREENS]

  fundamental_screens_enabled               [TIER 2] boolean default: false
    if false: entire fundamental_screens sub-section is skipped

  fundamental_screens                       [TIER 2] array
    schema per screen:
      screen_type: profitability_required | revenue_positive | positive_fcf |
                   max_debt_to_equity | max_pe_ratio | max_pb_ratio |
                   min_revenue_growth_pct | min_market_cap_separate | custom
      threshold: number (where applicable)
      flexibility: hard_filter | soft_preference | advisory_only
      applies_to_catalyst_types: "all" | "pead_only" | "non_biotech_only" |
                                  [array of specific catalyst_type values]
      custom_description: string (if screen_type = custom)

  fundamental_screen_compatibility_warnings [SYSTEM-GENERATED] array
    Generated at section validation step — not user input.
    Cross-references fundamental_screens against catalyst_types in Section F.
    Example: "profitability_required applies to all catalyst types but
    fda_pdufa_biotech is selected. 94%+ of PDUFA candidates are pre-revenue.
    This screen will return an empty biotech universe. Recommend setting
    applies_to_catalyst_types to 'non_biotech_only'."
```

### SCHEMA SECTION F — STRATEGY MANDATE

**Critical change from v9:** Catalyst types are structured explicit opt-in with per-type risk acknowledgments. Not a prose field. Not LLM-interpreted. The user must explicitly enable each catalyst type and acknowledge the specific risks associated with it. This is the most consequential single user decision in the system.

```
strategy_mandate:

  [TIER 1]

  catalyst_types                            [TIER 1] array
    MUST be explicit structured opt-in. Never inferred from prose.
    Schema per entry:
      catalyst_type: enum (see options below)
      permitted: boolean
      risk_acknowledgments:
        iv_crush_risk_acknowledged: boolean
          required for: options + binary events (fda_pdufa_biotech,
          clinical_trial_readout_phase3, clinical_trial_readout_phase2)
        gap_risk_acknowledged: boolean
          required for: all overnight-hold catalyst types
        binary_event_risk_acknowledged: boolean
          required for: fda_pdufa_biotech, clinical_trial_readout_phase3,
          clinical_trial_readout_phase2
        information_leakage_risk_acknowledged: boolean
          required for: fda_pdufa_biotech, clinical_trial_readout_phase3
        pre_revenue_universe_acknowledged: boolean
          required for: fda_pdufa_biotech, clinical_trial_readout_phase3,
          clinical_trial_readout_phase2

    catalyst_type options:
      pead_earnings_momentum
        description: Post-earnings announcement drift. 21-63 day hold window.
        typical acknowledgments: gap_risk_acknowledged
      fda_pdufa_biotech
        description: FDA target action dates.
        typical acknowledgments: all five
      clinical_trial_readout_phase3
        description: Phase III readouts. Highest binary risk.
        typical acknowledgments: all five
      clinical_trial_readout_phase2
        description: Phase II readouts. Smaller drift, higher failure rate.
        typical acknowledgments: all five
      ma_announcement
        description: M&A catalyst momentum. Deal spread dynamics.
        typical acknowledgments: gap_risk_acknowledged, binary_event_risk_acknowledged
      index_reconstitution
        description: Russell/S&P add/delete events. Predictable calendar.
        typical acknowledgments: gap_risk_acknowledged
      management_change
        description: CEO/CFO changes. Event-driven momentum.
        typical acknowledgments: gap_risk_acknowledged
      secondary_offering
        description: Post-secondary momentum reversal strategies.
        typical acknowledgments: gap_risk_acknowledged
      short_squeeze_setup
        description: High short-interest catalysts.
        typical acknowledgments: gap_risk_acknowledged, binary_event_risk_acknowledged
        compatibility check: requires short_selling_permitted = true OR
        strategy is long-only squeeze momentum (flag ambiguity)
      macro_data_surprise
        description: Economic data surprise momentum. Lower idiosyncratic risk.
        typical acknowledgments: gap_risk_acknowledged

  horizon_allocation                        [TIER 1] array
    Schema per bucket:
      label: string
      min_days: integer
      max_days: integer
      capital_weight: number (0.0 to 1.0)
    validation: capital_weight values must sum to 1.0
    drives: Builder selection of drift windows and exit trigger optimization

  strategy_types_excluded                   [TIER 1] [string]
    Builder never generates these strategy types.

  [TIER 2]

  regime_preferences                        [TIER 2] prose

  regime_universe_pairs                     [TIER 2] array
    Schema: [{regime, universe, strategy_type, rationale}]
    CREATION RULE: Generate ONLY from explicitly linked user preferences.
    Never infer. If the user links a specific market condition to a specific
    asset class and strategy type, create the pair. Otherwise leave empty.

  entry_philosophy                          [TIER 2] prose
    Builder use: respect strong user views over system defaults

  exit_philosophy                           [TIER 2] prose
    Builder use: respect strong user views; interacts with regret_asymmetry

  holding_philosophy                        [TIER 2] prose

  complexity_preference                     [TIER 2] enum
    options: simple_rules | moderate_complexity | maximum_sophistication

  signal_type_preferences                   [TIER 2] prose
```

### SCHEMA SECTION G — OPERATIONAL MANDATE

**Critical change from v9:** `available_windows` is Tier 1. It was Tier 2 in v9. This is a hard operational filter on strategy types — a strategy requiring execution outside the user's windows will never be acted on and must never be generated.

```
operational_mandate:

  [TIER 1]

  available_windows                         [TIER 1] array
    Schema per window:
      days: [monday | tuesday | wednesday | thursday | friday]
      start_time_et: HH:MM string
      end_time_et: HH:MM string
    enforcement: Builder hard-excludes any strategy type requiring execution
                 outside these windows. Not a soft preference.
    example: [{days: ["monday","tuesday","wednesday","thursday","friday"],
               start_time_et: "09:30", end_time_et: "11:30"}]

  pre_post_market_capable                   [TIER 1] boolean default: false

  max_execution_latency_minutes             [TIER 1] integer
    enforcement: at >= 120, strategies requiring tight entry windows are
                 hard-excluded. Directly determines entry range width
                 in generated strategies.
    example: a user with 30-min latency can execute PEAD morning breakouts;
             120-min latency requires multi-day drift strategies only

  automation_level                          [TIER 1] enum
    options: semi_automated_confirmation_required | fully_manual
    IMPLEMENTATION NOTE: fully_automated is NOT a valid option if the
    pipeline requires manual Signal Card confirmation before execution.
    If the pipeline is updated to support full automation (no confirmation
    step), add fully_automated to the enum. Do not add it until the
    pipeline capability exists. Default: semi_automated_confirmation_required.
    Builder use: fully_manual → wider entry windows, simpler signal
    structures, tolerance for discretionary timing variation

  [TIER 2]

  brokerage                                 [TIER 2] string
  order_type_philosophy                     [TIER 2] enum
    options: market_orders_acceptable | limit_orders_preferred |
             stop_limit_preferred
  brokerage_constraints                     [TIER 2] prose
  execution_friction_context                [TIER 2] prose
```

### SCHEMA SECTION H — BEHAVIORAL PROFILE

**Critical requirement:** Every behavioral field must have a specific, parametric enforcement mechanism documented. Fields without defined enforcement are decorative, which is the same failure the research report diagnosed in v9. See the enforcement mechanism section (Part 7 of this document) for the full parametric mappings.

```
behavioral_profile:
  (All fields Tier 2)

  regret_asymmetry                          [TIER 2] structured + prose
    type: loss_regret_dominant | miss_regret_dominant | balanced
    magnitude: mild | moderate | severe
    context: prose
    BUILDER ENFORCEMENT: See Part 7.1

  disposition_effect_tendency               [TIER 2] structured + prose
    self_assessed: strong | moderate | mild | none
    context: prose
    BUILDER ENFORCEMENT: See Part 7.2

  loss_aversion_coefficient                 [TIER 2] enum
    options: standard_2to1 | elevated_3to1 | severe_4plus_to_1
    BUILDER ENFORCEMENT: See Part 7.3

  overtrading_tendency                      [TIER 2] structured + prose
    self_assessed: frequent | occasional | rare | none
    context: prose
    BUILDER ENFORCEMENT: See Part 7.4

  behavioral_constraints_during_drawdown    [TIER 2] prose
    purpose: explicit commitment the user makes at intake
    note: system cannot verify compliance — this is a user-facing
    commitment document, not a system-enforced constraint

  cooling_off_requirements                  [TIER 2] structured
    trigger: drawdown_breach | consecutive_loss_threshold | major_adverse_event
    cooling_off_days: integer
    required_actions_before_restart: prose
    BUILDER ENFORCEMENT: See Part 7.5
    note: required_actions_before_restart is a human checklist — the system
    cannot verify completion. Document this explicitly in user-facing copy.

  signal_override_policy                    [TIER 2] structured
    can_user_override: boolean
    override_conditions: prose
    override_documentation_required: boolean
    note: ad hoc overrides are the most common source of systematic
    strategy performance degradation. This policy must be stated
    explicitly at intake to set expectations.

  max_consecutive_losses_review_trigger     [TIER 2] integer
    GOVERNANCE TRIGGER ONLY — not an optimization constraint.
    N consecutive losses activates mandate review and cooling_off_requirements.
    Does NOT constrain the Builder's optimization engine.
```

### SCHEMA SECTION I — TAX & LEGAL

**Implementation note on `legal_trading_restrictions`:** Full compliance enforcement (specific blackout dates, dynamic restricted securities lists, pre-clearance workflows) is OUT OF SCOPE for v10. This is a documentation-only field. Half-implementing it would create false confidence. The field captures disclosure for Builder awareness only. Full compliance module is scoped to a future release. This must be stated explicitly in user-facing copy adjacent to this field.

```
tax_and_legal:

  account_tax_status                        [TIER 1] enum
    options: fully_taxable | tax_deferred_traditional | tax_exempt_roth |
             partially_sheltered
    drives: strategy design at the generation level — different strategies
    for IRA vs taxable account

  estimated_marginal_tax_rate_pct           [TIER 2] number
    Builder use: weight after-tax returns in strategy evaluation

  short_term_gains_tolerance                [TIER 2] structured + prose
    level: strongly_prefer_to_avoid | prefer_to_avoid | neutral |
           acceptable | indifferent
    context: prose
    contradiction rule: see Part 8, Rule 10 and Rule 10b

  long_term_holding_preference_pct          [TIER 2] number advisory
    Builder use: weight exit timing decisions toward LTCG-eligible holds

  tax_loss_harvesting_directive             [TIER 2] enum
    options: active | passive_opportunistic | none

  wash_sale_awareness_required              [TIER 2] boolean default: false

  specific_tax_lot_method                   [TIER 2] enum
    options: fifo | lifo | hifo | specific_identification

  legal_trading_restrictions_disclosure     [TIER 2] prose
    DOCUMENTATION ONLY — NOT ENFORCED BY PIPELINE
    User-facing copy must state: "This field is for disclosure purposes
    only. The Aegis pipeline does not enforce blackout periods, restricted
    securities lists, or pre-clearance requirements. Users with legal trading
    restrictions must independently verify compliance with their applicable
    policies before acting on any signal. Full compliance enforcement is
    planned for a future release."
    Builder use: awareness only; flag in filing_notes if populated

  regulatory_constraints                    [TIER 2] prose
  jurisdiction                              [TIER 2] enum
    options: us | canada | uk | eu_member | other
  erisa_applicable                          [TIER 2] boolean default: false
```

### SCHEMA SECTION J — PORTFOLIO SCOPE & MACRO

```
portfolio_scope_and_macro:
  (All fields Tier 2)

  ambition_description                      [TIER 2] prose
  diversification_intent                    [TIER 2] prose
  correlation_intent                        [TIER 2] prose
  market_beta_intent                        [TIER 2] number
  pipeline_growth_intent                    [TIER 2] prose

  macro_views                               [TIER 2] array
    schema: [{view: prose, conviction: high|medium|low,
              time_horizon_months: number, strategy_implication: prose}]
    Builder use: strategy_implication is Builder-actionable language —
    use it directly. Not just informational.

  current_regime_beliefs                    [TIER 2] prose
  regime_adaptivity_intent                  [TIER 2] enum
    options: adaptive_to_regime | strategy_consistent_regardless_of_regime
  sectors_with_tailwinds                    [TIER 2] [string]
  sectors_with_headwinds                    [TIER 2] [string]
```

### SCHEMA SECTION K — GOVERNANCE & REVIEW

**New section in v10. Not present in v9. Standard in all institutional IPS documents.**

```
governance_and_review:
  (All fields Tier 2)

  mandate_review_frequency                  [TIER 2] enum
    options: monthly | quarterly | semi_annually | annually | event_driven_only

  review_trigger_conditions                 [TIER 2] structured
    drawdown_pct_of_max_triggers_review: number
      note: percentage of max_portfolio_drawdown_pct, not absolute
      example: 75 means review triggers when drawdown reaches 75% of the limit
    consecutive_losses_triggers_review: number
    calendar_interval_months: number
    regime_change_triggers_review: boolean
    capital_change_pct_triggers_review: number
    custom_trigger: prose

  strategy_pause_conditions                 [TIER 2] structured
    auto_pause_on_drawdown_breach: boolean default: true
      links to: risk_mandate.drawdown_breach_protocol
    auto_pause_on_market_circuit_breaker: boolean
    manual_pause_conditions: prose

  performance_reporting_frequency           [TIER 2] enum
    options: daily | weekly | monthly

  performance_attribution_framework        [TIER 2] structured
    by_catalyst_type: boolean
    by_sector: boolean
    by_strategy_type: boolean
    by_holding_period: boolean
    benchmark_for_attribution: string

  mandate_amendment_policy                  [TIER 2] prose
```

### SCHEMA SECTION L — PRIORITY HIERARCHY

**Updated dimension set from v9.** v9 dimensions `universe_specificity` and `strategy_type_adherence` are replaced by `catalyst_type_adherence` and `sector_focus`. The drag-to-rank UI component from v9 must be updated to reflect this new dimension set.

```
mandate_priority_hierarchy:
  (All fields Tier 2)

  ordered_priorities                        [TIER 2] array
    schema: [{rank: integer, dimension: enum, rationale: prose}]
    dimension options:
      capital_preservation | return_maximization | consistency |
      tax_efficiency | catalyst_type_adherence | sector_focus |
      execution_simplicity | income_generation
    LLM generates rationale from context

  preference_flexibility                    [TIER 2] array
    schema: [{preference: string, flexibility: enum, rationale: prose}]
    flexibility options: immovable | strong | moderate | flexible
    immovable → activates Tier 2-Hard status for that preference
    Builder must treat immovable preferences as inviolable within
    their pipeline stage (post-Tier-1-filtering)
    CRITICAL: Do NOT collapse immovable preferences into Tier 1 hard filters.
    Different pipeline stages. Different semantics.

  trade_off_philosophy                      [TIER 2] prose
  conflict_notes                            [TIER 2] [string] system-generated
```

### SCHEMA SECTION M — FILING NOTES

**System-generated entirely. No user input. Read last.**

```
filing_notes:
  (All fields system-generated)

  explicit_vs_inferred_summary              prose
  contradictions                            array
    schema: [{field_a, field_b, description, severity, user_message}]
    severity: blocking | warning | advisory
    blocking: mandate cannot lock until resolved
    warning: can proceed; output will be degraded
    advisory: surfaced for user awareness

  expectation_corrections                   array
    schema: [{field, user_stated, realistic_range, explanation}]

  sharpe_feasibility_check                  structured
    implied_sharpe_required: number
    feasibility: achievable | difficult | implausible
    explanation: prose

  volatility_target_derivation              structured
    assumed_sharpe: number (0.4-0.6 for pre-deployment)
    derived_volatility_pct: number
    confidence: pre_deployment_estimate | early_live_data | established_track_record
    note: prose explaining derivation and update cadence

  open_questions                            [string]
  realistic_performance_range               structured
    return_pct: {low, mid, high}
    sharpe: {low, mid, high}
    max_drawdown_pct: {low, mid, high}
    assumptions: prose

  legal_restrictions_disclosure_flag        boolean
    true if legal_trading_restrictions_disclosure is populated
    Builder: flag in strategy generation output when true

  conversation_quality_note                 prose
  expectation_calibration_presented_at      ISO timestamp
```

---

## PART 3: FORM-BASED INTAKE SPECIFICATION

### 3.1 Form Architecture

**Frontend component:** `IntakePage.tsx`
**State management:** Draft state in localStorage with auto-save (structure: `aegis_intake_draft_v10`)
**Section count:** 10 form sections mapping to 13 schema sections

Sections F and G (Strategy + Operations) are combined into one form section. Sections K and L (Governance + Priorities) are combined into one form section. All other schema sections map 1:1 to form sections.

| Form Section | Schema Sections | Title |
|---|---|---|
| 1 | A + B | Mandate & Capital |
| 2 | C | Risk |
| 3 | D | Performance Targets |
| 4 | E | Universe |
| 5 | F | Strategy & Catalysts |
| 6 | G | Operations & Execution |
| 7 | H | Behavioral Profile |
| 8 | I | Tax & Legal |
| 9 | J | Portfolio Scope & Macro |
| 10 | K + L | Governance & Priorities |

### 3.2 Investor Sophistication Gating

`investor_sophistication` is the **first field rendered** in Form Section 1. It must be set before any other section renders. It drives conditional field visibility throughout the entire form.

**Implementation:** On selection, store value in component state AND localStorage. Pass as context prop to all subsequent section components.

| Field Category | retail_novice | retail_experienced | semi_professional | professional |
|---|---|---|---|---|
| Risk sub-fields (gap, tail, correlation) | 2 shown (volatility, loss_aversion) | 4 shown | All shown | All shown + advanced |
| Stress scenario constraints | Hidden | Show 1 | Show all | Show all |
| Fundamental screens | Hidden | Simplified | Full | Full |
| Sharpe, Kelly references | Hidden | Advisory | Standard | Technical |
| Macro views | Hidden | Simplified | Standard | Full |
| Governance section | Simplified | Standard | Full | Full |
| Technical field labels | Plain language only | Plain + technical | Technical | Technical |

### 3.3 Section-by-Section Form Specification

Each section spec covers: structured fields (UI type), detail box prompt text, LLM population targets, and validate endpoint behavior.

---

#### FORM SECTION 1 — Mandate & Capital

**Structured fields:**

```
investor_sophistication
  UI: segmented control (4 options)
  required: true
  renders first, gates all subsequent sections

account_type
  UI: dropdown
  required: true

mandate_role
  UI: dropdown

investable_capital_usd
  UI: number input with currency formatting
  required: true

reserved_cash_pct
  UI: slider 5-30%, default 10%

max_deployed_pct
  UI: slider 50-100%, default 80%

leverage_permitted
  UI: toggle, default off

max_leverage_ratio
  UI: number input (1.0-4.0)
  visible: only if leverage_permitted = true

margin_account
  UI: toggle, default off

options_permitted
  UI: toggle, default off

short_selling_permitted
  UI: toggle, default off

existing_holdings
  UI: ticker input with typeahead, multi-value
  label: "Tickers you already hold (for portfolio context)"
  note: "We track these for correlation awareness only, not portfolio management."

tickers_never_touch
  UI: ticker input with typeahead, multi-value
  label: "Tickers Aegis should never trade, no exceptions"
```

**Detail box prompt:**
"Tell us about your existing portfolio and what role you want Aegis to play. What are you trying to accomplish? What's the rest of your portfolio doing?"

**LLM populates:** `mandate_identification.existing_non_aegis_portfolio_description`, `mandate_identification.portfolio_beta_existing`, `mandate_identification.mandate_inception_reason`, `mandate_identification.investment_experience`, `mandate_identification.behavioral_history`, `capital_structure.leverage_context`

**Validate endpoint behavior:** Translate detail box → prose fields. Flag if investable_capital_usd is not set (blocking gap). Flag if leverage_permitted = true but max_leverage_ratio is null (blocking gap). Apply [EXPLICIT]/[INFERRED] tags.

---

#### FORM SECTION 2 — Risk

**Structured fields:**

```
max_portfolio_drawdown_pct
  UI: slider 5-50% in 1% increments
  required: true
  helper text: "Maximum total loss from peak before the system stops.
               This is the most important number you'll set."

max_daily_loss_pct
  UI: slider 1-10% in 0.5% increments
  required: true
  helper text: "Maximum loss in a single trading day before new position
               building stops for that day. Resets at next market open.
               Reference: your portfolio value at market open that day."

drawdown_breach_protocol
  UI: radio buttons (4 options with plain-language descriptions)
  required: true — form blocks progression if null
  option descriptions:
    pause_all_notify_user → "Stop everything, send me an alert, wait for me"
    reduce_position_sizes_50pct → "Cut all positions by half, keep running"
    manual_restart_required → "Full stop — I have to manually restart"
    reduce_and_notify → "Cut positions by half and send me an alert"

max_single_position_pct
  UI: slider 2-25%
  required: true

max_single_position_usd
  UI: number input
  required: true
  helper text: "Absolute dollar cap per position — works alongside the
               percentage cap. Whichever is lower applies."

max_sector_concentration_pct
  UI: slider 10-60%
  required: true

max_concurrent_live_strategies
  UI: stepper 1-20
  required: true

max_position_as_pct_of_adv
  UI: slider 1-10%, default 3%
  visible: retail_experienced and above
  helper text: "Max position as % of that stock's average daily trading
               volume. Prevents you from moving the market."

target_portfolio_beta
  UI: slider -1.0 to 2.0, step 0.1
  visible: semi_professional and above

regret_asymmetry.type
  UI: 3-option segmented control
  label: "When a trade goes wrong, which bothers you more?"
  options:
    loss_regret_dominant → "Holding a loser too long"
    miss_regret_dominant → "Selling a winner too early"
    balanced → "Both bother me equally"
  required: true

regret_asymmetry.magnitude
  UI: 3-option segmented control
  label: "How strongly do you feel this?"
  options: Mildly | Moderately | Strongly
```

**Detail box prompt:**
"How do you think about risk? Describe your tolerance for volatility, overnight gaps, and large losses. Include any past experiences — trades that hurt, drawdowns you struggled through, or situations where you acted against your plan."

**LLM populates:** `risk_mandate.tier_2_risk_context.volatility_tolerance`, `gap_risk_tolerance`, `concentration_tolerance`, `tail_risk_tolerance`, `time_risk_tolerance`, `loss_aversion_context`, `correlation_risk_context`, `regret_asymmetry.context`

**Validate endpoint behavior:** Check consistency between drawdown limit and regret_asymmetry (if loss_regret_dominant + high drawdown limit → flag for clarification). Cross-reference with investable_capital_usd to check if max_single_position_usd > (investable_capital_usd * max_single_position_pct / 100) — if so, percentage is the binding limit and flag this for clarity. Apply [EXPLICIT]/[INFERRED] tags.

---

#### FORM SECTION 3 — Performance Targets

**Structured fields:**

```
primary_objective
  UI: dropdown
  required: true

target_annual_return_pct
  UI: number input with % suffix
  label: "Target annual return (advisory — not a guaranteed target)"
  helper text shown prominently: "This is a planning input, not a guarantee.
    The system will aim toward this but cannot mathematically commit to it."

benchmark
  UI: dropdown + custom text input if "custom_ticker" selected

return_character.smoothness_preference
  UI: binary toggle with descriptions (see Part 2 UI NOTE)

return_character.income_vs_appreciation
  UI: 3-option segmented control

target_monthly_income_usd
  UI: number input
  visible: only if primary_objective = income_generation

min_acceptable_sharpe
  UI: number input, step 0.1
  visible: retail_experienced and above

target_return_horizon_months
  UI: stepper or number input

expectation_calibration_acknowledged
  UI: NOT shown here — shown at confirmation step only after
      filing_notes.realistic_performance_range is generated
```

**Detail box prompt:**
"What does success look like for this system? And what would make you pull the plug — either because it's working too well (feels risky), not well enough, or in a way you didn't expect?"

**LLM populates:** `return_mandate.target_annual_return_context`, `benchmark_context`, `success_definition`, `failure_definition`

**Validate endpoint behavior:** Preliminary Sharpe feasibility check (if target_annual_return_pct and max_portfolio_drawdown_pct both set): compute implied_sharpe_required = target_annual_return_pct / (max_portfolio_drawdown_pct * 1.5). If > 1.5, surface early warning. Full check runs at confirmation.

---

#### FORM SECTION 4 — Universe

**Structured fields:**

```
asset_classes_permitted
  UI: multi-select checkboxes

geographies_permitted
  UI: multi-select checkboxes

market_cap_min_usd
  UI: segmented control with common ranges + custom
  options: $50M+ (Micro/Small) | $300M+ (Small/Mid) | $2B+ (Mid/Large) | Custom

market_cap_max_usd
  UI: same pattern, optional

min_avg_daily_volume_usd
  UI: dropdown with common values
  options: $500K | $1M (recommended) | $2M | $5M | $10M | Custom

price_min_usd
  UI: number input, default 1.00

restrict_to_sectors_of_interest
  UI: toggle
  label: "Restrict universe ONLY to sectors I select"
  helper: "Off = Aegis can trade anything; On = Aegis is limited to your
           selected sectors"

sectors_of_interest
  UI: multi-select chip selector

sectors_excluded
  UI: multi-select chip selector

specific_tickers_focus
  UI: ticker typeahead, multi-value

specific_tickers_exclude
  UI: ticker typeahead, multi-value

esg_hard_exclusions
  UI: multi-select checkboxes

fundamental_screens_enabled
  UI: toggle, default off
  label: "Apply fundamental quality screens to the universe"

[if fundamental_screens_enabled = true]
fundamental_screens
  UI: expandable per-screen builder
  Each screen: screen_type dropdown + threshold input (where applicable)
               + flexibility radio + applies_to_catalyst_types selector
  note: applies_to_catalyst_types options are dynamically populated
        from whatever catalyst types the user selected in Section 5
        (handle cross-section dependency — Section 5 must be partially
        completable before Section 4 validates fundamental screen
        compatibility, OR run compatibility check at confirmation only)
```

**Detail box prompt:**
"What do you want to trade and why? Include what you know about these markets, any fundamental characteristics you care about, and what makes a stock appealing or unappealing to you."

**LLM populates:** `universe_mandate.universe_description`, `sector_reasoning`, `equity_character`, `liquidity_and_price_character`, `options_context`, `etf_preferences`, `asset_class_preferences`

**Validate endpoint behavior:** Generate `fundamental_screen_compatibility_warnings` if Section 5 catalyst types are already set. If not yet set, defer to confirmation pass. Apply [EXPLICIT]/[INFERRED] tags.

---

#### FORM SECTION 5 — Strategy & Catalysts

**Structured fields:**

```
catalyst_types
  UI: expandable card per catalyst type
  Each card contains:
    - catalyst name + plain-language description
    - permitted: toggle (default off)
    - [if permitted = true]: risk acknowledgments section with required checkboxes
    - Each acknowledgment: labeled checkbox with explanation of the risk
  Required: at least one catalyst_type must be set to permitted = true

horizon_allocation
  UI: capital allocation builder
  User adds buckets with label, min/max days, and capital weight
  Validation: weights must sum to 100% before section can be validated
  Helper: suggest common splits based on selected catalyst types
    e.g., pead_earnings_momentum suggests: Swing 5-21d / Intermediate 21-63d

strategy_types_excluded
  UI: multi-select from common strategy types
  options: market_neutral | long_short | intraday_scalping |
           options_only | pairs_trading | other

complexity_preference
  UI: 3-option segmented control
  options: Simple rules | Moderate | Maximum sophistication
```

**Detail box prompt:**
"How do you think about entering and exiting trades? Describe the kinds of setups you're looking for, any approaches you've tried before, and what you want the system to prioritize when it has to make trade-offs."

**LLM populates:** `strategy_mandate.regime_preferences`, `entry_philosophy`, `exit_philosophy`, `holding_philosophy`, `signal_type_preferences`

**Validate endpoint behavior:** Cross-reference catalyst_types with short_selling_permitted from Section 1 (short_squeeze_setup requires clarification if short_selling_permitted = false). Cross-reference with sectors_excluded from Section 4. Generate fundamental_screen_compatibility_warnings if fundamental_screens are set. Apply [EXPLICIT]/[INFERRED] tags.

---

#### FORM SECTION 6 — Operations & Execution

**Structured fields:**

```
available_windows
  UI: weekly calendar grid
  User clicks/drags to mark available time blocks
  Stored as structured [{days, start_time_et, end_time_et}]
  Required: at least one window must be defined

pre_post_market_capable
  UI: toggle, default off

max_execution_latency_minutes
  UI: segmented control
  options: < 15 min | 15-30 min | 30-60 min | 1-2 hours | > 2 hours
  maps to: 10 | 22 | 45 | 90 | 150 (midpoint integers for schema)

automation_level
  UI: 2-option segmented control (NOT 3 — fully_automated excluded)
  options:
    semi_automated_confirmation_required → "I confirm before each trade"
    fully_manual → "I execute manually from signals"

brokerage
  UI: text input + common broker dropdown suggestions

order_type_philosophy
  UI: dropdown
```

**Detail box prompt:**
"When can you realistically act on a trade signal? Describe your available windows, how quickly you can execute, and any constraints — travel, day job, time zones, internet access."

**LLM populates:** `operational_mandate.brokerage_constraints`, `execution_friction_context`

**Validate endpoint behavior:** If available_windows covers < 30 minutes per day and pead_earnings_momentum is selected → surface warning. If max_execution_latency >= 120 AND any catalyst requiring morning execution is selected → surface constraint note. Apply [EXPLICIT]/[INFERRED] tags.

---

#### FORM SECTION 7 — Behavioral Profile

**Structured fields:**

```
disposition_effect_tendency.self_assessed
  UI: 4-option segmented control
  label: "How often do you sell winning positions too early?"
  options: Often | Sometimes | Rarely | Never

loss_aversion_coefficient
  UI: 3-option segmented control
  label: "When you lose $1,000, how does it feel compared to gaining $1,000?"
  options:
    standard_2to1 → "About twice as bad"
    elevated_3to1 → "About 3x as bad"
    severe_4plus_to_1 → "4x or more as bad"

overtrading_tendency.self_assessed
  UI: 4-option segmented control
  label: "Do you have a tendency to overtrade or chase signals?"
  options: Often | Sometimes | Rarely | Never

regret_asymmetry
  Note: captured in Section 2 (Risk). Not repeated here.
  Reference: Section 2 data feeds behavioral enforcement logic.

max_consecutive_losses_review_trigger
  UI: stepper 3-15
  label: "After how many consecutive losing trades should Aegis pause
          and ask you to review?"
  helper: "This triggers a review, not a shutdown."

cooling_off_requirements.trigger
  UI: dropdown (multi-select)

cooling_off_requirements.cooling_off_days
  UI: stepper 1-30

signal_override_policy.can_user_override
  UI: toggle
  label: "Can you manually reject a signal you disagree with?"

signal_override_policy.override_documentation_required
  UI: toggle (visible if can_user_override = true)
  label: "Require a written reason when overriding a signal?"
```

**Detail box prompt:**
"Describe your psychological relationship with trading. What patterns have you noticed in yourself — good and bad? When things go wrong, how do you typically respond? What commitments do you want to make about how you'll behave during drawdowns?"

**LLM populates:** `behavioral_profile.behavioral_constraints_during_drawdown`, `disposition_effect_tendency.context`, `overtrading_tendency.context`, `cooling_off_requirements.required_actions_before_restart`, `signal_override_policy.override_conditions`

**Validate endpoint behavior:** If disposition_effect_tendency.self_assessed = strong AND exit_philosophy (from Section 5) describes a preference for discretionary exits → surface conflict. If overtrading_tendency = frequent AND max_execution_latency < 30 → note that fast execution capability combined with overtrading tendency increases friction importance. Apply [EXPLICIT]/[INFERRED] tags.

---

#### FORM SECTION 8 — Tax & Legal

**Structured fields:**

```
account_tax_status
  UI: dropdown (carries forward account_type from Section 1 to pre-fill suggestion)
  required: true

estimated_marginal_tax_rate_pct
  UI: segmented control
  options: 10% | 12% | 22% | 24% | 32% | 35% | 37%
  visible: only if account_tax_status = fully_taxable

short_term_gains_tolerance.level
  UI: 5-option radio buttons with descriptions
  visible: only if account_tax_status = fully_taxable

long_term_holding_preference_pct
  UI: slider 0-100%

tax_loss_harvesting_directive
  UI: dropdown

wash_sale_awareness_required
  UI: toggle

specific_tax_lot_method
  UI: dropdown
  visible: account_tax_status = fully_taxable

jurisdiction
  UI: dropdown

erisa_applicable
  UI: toggle
  visible: account_type in [traditional_ira, 401k_solo, sep_ira]

legal_trading_restrictions_disclosure
  UI: textarea
  label: "Legal trading restrictions (disclosure only)"
  subtext shown prominently in red/orange: "Important: This field is for
    disclosure purposes only. Aegis does not enforce blackout periods or
    restricted securities lists. You are responsible for compliance with
    your applicable trading policies."
```

**Detail box prompt:**
"Any additional tax context, legal constraints, or special circumstances? Include anything relevant to how gains and losses should be handled."

**LLM populates:** `tax_and_legal.regulatory_constraints`

**Validate endpoint behavior:** If account_tax_status = fully_taxable AND estimated_marginal_tax_rate_pct is null → flag gap (advisory — not blocking). If erisa_applicable = true → flag for additional compliance consideration. Apply [EXPLICIT]/[INFERRED] tags.

---

#### FORM SECTION 9 — Portfolio Scope & Macro

**Structured fields:**

```
market_beta_intent
  UI: slider -1.0 to 2.0
  visible: semi_professional and above

regime_adaptivity_intent
  UI: binary segmented control

sectors_with_tailwinds
  UI: sector chip selector (multi-select from sector enum)

sectors_with_headwinds
  UI: sector chip selector (multi-select from sector enum)
```

**Detail box prompt:**
"What's your macro view? What do you think is happening in the market right now, what's coming, and how should Aegis position in response? Include anything about sectors you see as strong or weak, and whether you want the system to adapt to changing conditions or stay consistent regardless."

**LLM populates:** `portfolio_scope_and_macro.ambition_description`, `diversification_intent`, `correlation_intent`, `pipeline_growth_intent`, `macro_views`, `current_regime_beliefs`

**Validate endpoint behavior:** Cross-reference sectors_with_tailwinds against sectors_excluded from Section 4 → flag if a sector is simultaneously a tailwind and excluded. Apply [EXPLICIT]/[INFERRED] tags.

---

#### FORM SECTION 10 — Governance & Priorities

**Structured fields:**

```
mandate_review_frequency
  UI: dropdown

review_trigger_conditions.drawdown_pct_of_max_triggers_review
  UI: slider 50-100%
  label: "Trigger a review when drawdown reaches ___% of your maximum"
  example display: "At your 15% max, this would trigger at 11.25%"

review_trigger_conditions.consecutive_losses_triggers_review
  UI: stepper

performance_reporting_frequency
  UI: segmented control: Daily | Weekly | Monthly

performance_attribution_framework
  UI: checkboxes for each attribution dimension

ordered_priorities
  UI: drag-to-rank component
  dimensions: capital_preservation | return_maximization | consistency |
              tax_efficiency | catalyst_type_adherence | sector_focus |
              execution_simplicity | income_generation
  note: v9 had universe_specificity and strategy_type_adherence —
        these are replaced by catalyst_type_adherence and sector_focus

preference_flexibility
  UI: per-dimension flexibility selector (appears below drag-to-rank)
  For each ranked dimension: dropdown (Flexible | Moderate | Strong | Immovable)
  immovable tooltip: "Aegis will never sacrifice this, even at significant
                     cost to other goals"
```

**Detail box prompt (two boxes):**

Trade-off philosophy: "In your own words — when the system has to sacrifice one thing to get another, what should guide that decision?"

Mandate governance: "Under what conditions would you amend or shut down this mandate? What would a full review look like for you?"

**LLM populates:** `mandate_priority_hierarchy.trade_off_philosophy`, `mandate_priority_hierarchy.conflict_notes` (initial), `governance_and_review.mandate_amendment_policy`, all `ordered_priorities.rationale` fields

**Validate endpoint behavior:** Cross-reference ordered_priorities against other sections for obvious conflicts (e.g., capital_preservation ranked #1 but fda_pdufa_biotech is selected → advisory flag). Apply [EXPLICIT]/[INFERRED] tags.

### 3.4 Lock Invalidation Rules

When a section is edited after being locked, downstream section locks are invalidated. The following dependencies must be enforced:

```
Section 1 (Mandate & Capital) edited →
  Invalidates: All sections 2-10

Section 2 (Risk) edited →
  Invalidates: Section 10 (priorities may need re-ranking)
  Re-runs: Sharpe feasibility check at confirmation

Section 3 (Performance) edited →
  Re-runs: Sharpe feasibility check at confirmation

Section 4 (Universe) edited →
  Invalidates: Section 5 (fundamental screen compatibility may change)

Section 5 (Strategy & Catalysts) edited →
  Invalidates: Section 4 (compatibility warnings regenerated)
  Re-runs: All contradiction detection rules at confirmation

Section 8 (Tax & Legal) edited →
  Re-runs: Rule 10 and Rule 10b contradiction checks
```

---

## PART 4: LLM CONVERSATIONAL INTAKE SPECIFICATION

### 4.1 Architecture

The conversational intake produces the same JSON schema as the form path. The LLM guides the user through all 13 schema sections via natural language questions, extracting structured values AND prose context simultaneously.

**System prompt architecture:** One persistent system prompt that defines the LLM's role, all 13 sections, field extraction rules, tagging requirements, contradiction rules, and the schema structure. The full schema blank is embedded in the system prompt.

**Session management:** Full conversation history is passed on every API call. The schema JSON is maintained as a live state object updated incrementally as fields are confirmed.

**Output format per turn:** The LLM returns:
1. A user-facing conversational response (asking the next question, confirming extraction, surfacing contradictions)
2. A machine-readable extraction block: `{ "schema_updates": {...}, "gaps": [...], "contradictions": [...], "pending_confirmations": [...] }`

### 4.2 Conversation Flow

The LLM follows this section sequence. It may skip or reorder sub-questions based on prior answers (e.g., if leverage_permitted = false, skip max_leverage_ratio).

```
Phase 1: Context Setting (Schema Section A)
  - Open question: mandate context, account type, role of Aegis
  - Extract: account_type, mandate_role, aegis_capital_as_pct_of_net_worth
  - Then: investor_sophistication (if not already clear from language register)
  - Then: total_liquid_net_worth_estimate_usd, portfolio_beta_existing

Phase 2: Capital Structure (Schema Section B)
  - investable_capital_usd (MUST be explicit number — never inferred)
  - Instrument permissions: leverage, options, short selling (explicit yes/no)
  - existing_holdings (tickers only), tickers_never_touch

Phase 3: Risk Mandate (Schema Section C)
  - max_portfolio_drawdown_pct (MUST be explicit number)
  - max_daily_loss_pct (MUST be explicit number)
  - drawdown_breach_protocol (present 4 options, get explicit selection)
  - max_single_position_pct (MUST be explicit number)
  - max_single_position_usd (MUST be explicit number)
  - max_sector_concentration_pct (MUST be explicit number)
  - max_concurrent_live_strategies (MUST be explicit number)
  - Risk character questions → extract prose fields
  - regret_asymmetry (explicit choice + context)

Phase 4: Return Mandate (Schema Section D)
  - primary_objective (explicit selection)
  - target_annual_return_pct (advisory, explicit number — clearly framed)
  - return_character, benchmark

Phase 5: Universe (Schema Section E)
  - asset_classes, geographies (explicit multi-select)
  - market_cap and volume floors (explicit numbers)
  - sector preferences and exclusions (explicit)
  - fundamental screens (if desired — explicit per-screen setup)

Phase 6: Strategy & Catalysts (Schema Section F)
  - Walk through each catalyst_type: present description, get explicit permit/deny
  - For each permitted: walk through required risk acknowledgments explicitly
  - horizon_allocation: get explicit bucket definitions and weights (must sum to 100%)

Phase 7: Operations (Schema Section G)
  - available_windows (get specific days + times in ET)
  - max_execution_latency (explicit estimate)
  - automation_level (2 options)

Phase 8: Behavioral Profile (Schema Section H)
  - Walk through behavioral tendency questions
  - Extract cooling_off_requirements, signal_override_policy

Phase 9: Tax & Legal (Schema Section I)
  - account_tax_status, jurisdiction
  - short_term_gains_tolerance (if taxable)
  - legal_restrictions_disclosure (with explicit non-enforcement disclosure)

Phase 10: Portfolio Scope & Macro (Schema Section J)
  - macro views and regime beliefs

Phase 11: Governance (Schema Section K)
  - Review frequency, trigger conditions, reporting preferences

Phase 12: Priority Hierarchy (Schema Section L)
  - Walk through dimension ranking
  - Capture trade_off_philosophy

Phase 13: Synthesis & Confirmation
  - LLM runs two-pass confirmation internally (see Part 5)
  - Present contradictions to user for resolution
  - Present realistic_performance_range
  - Confirm expectation_calibration_acknowledged
  - Lock schema
```

### 4.3 Field Extraction Rules

**Tier 1 fields — extraction requirements:**
- Must be stated explicitly by the user as a concrete value
- If a user says "I'm conservative," the LLM does NOT set max_portfolio_drawdown_pct
- LLM must ask: "What's the maximum percentage loss from peak that would cause you to want to stop? Give me a specific number."
- If user continues to resist giving a number after two attempts, flag as open_question and apply the most conservative default (5%)
- All Tier 1 fields populated from the conversational path are tagged [EXPLICIT]

**Tier 2 prose fields — extraction requirements:**
- Extracted from natural language; tagged [INFERRED] if derived from context
- Tagged [EXPLICIT] only if the user stated the specific content directly

**Tagging format:** Every populated field in the schema output must be tagged. The tag is stored as metadata, not embedded in the field value itself. Implementation: parallel `_tags` object in the schema output: `{ "field_path": "[EXPLICIT]" | "[INFERRED]" }`.

### 4.4 Contradiction Detection in Conversational Path

Run contradiction rules inline as fields are collected — don't wait for the end. When a contradiction is detected:
1. Surface it to the user immediately in conversational language
2. Ask which input they'd like to change
3. Update the schema accordingly
4. Log the original values and resolution in `filing_notes.contradictions`

---

## PART 5: VALIDATION ARCHITECTURE

### 5.1 Section-Level Validation Endpoint (Form Path)

**Endpoint:** `POST /intake/validate/section`

**Request body:**
```json
{
  "section_id": "section_2_risk",
  "structured_fields": { ... },
  "detail_box_text": "string",
  "schema_so_far": { ... },
  "investor_sophistication": "retail_experienced"
}
```

**Response body:**
```json
{
  "prose_fields_populated": { ... },
  "explicit_inferred_tags": { ... },
  "gap_questions": ["string"],
  "section_contradictions": [{"field_a": "...", "field_b": "...", "description": "...", "severity": "..."}],
  "cross_section_warnings": ["string"]
}
```

**LLM system prompt for section validators:**
```
You are the Aegis intake validator for {section_name}.

Your role has exactly four functions:
1. PROSE TRANSLATION: Read the user's detail box text. Populate the Tier 2 prose
   fields listed in your target fields below. Write as a portfolio manager
   documenting a client brief — precise, specific, actionable.
2. GAP DETECTION: Identify missing context that would improve strategy generation.
   Return as targeted questions, not generic prompts.
3. CONTRADICTION DETECTION: Cross-reference structured inputs against detail box
   content and the schema_so_far. Flag conflicts.
4. TAGGING: Tag every field you populate as [EXPLICIT] if the user stated it
   directly, or [INFERRED] if you derived it from context.

You NEVER:
- Populate Tier 1 fields from inference
- Set numerical Tier 1 values from qualitative descriptions
- Override structured field values that have been explicitly set

Schema section you are processing: {schema_section}
Tier 2 target fields for this section: {target_fields_list}
Full schema state so far: {schema_so_far}

Structured fields (already set by form — do not modify):
{structured_fields}

User detail box:
{detail_box_text}

Return a JSON object only. No prose outside the JSON.
```

### 5.2 Two-Pass Confirmation Architecture

**Endpoint:** `POST /intake/confirm`

The confirmation step runs two sequential LLM calls. Do not combine them into one call — they have different objectives, different failure modes, and different quality requirements. Running both in one call risks the LLM deprioritizing whichever task appears second in the prompt.

**Pass 1: Contradiction Detection & Feasibility**

**Request:** Complete schema JSON

**LLM task:** Run all 13 contradiction rules (see Part 6). Generate Sharpe feasibility check. Generate expectation_corrections. Generate volatility_target_derivation.

**LLM system prompt (Pass 1):**
```
You are the Aegis mandate validator running a contradiction detection pass.

You have the complete intake schema. Your task:

1. CONTRADICTION DETECTION: Evaluate each of the 13 contradiction rules below.
   For each triggered rule, generate a filing_notes.contradictions entry with:
   field_a, field_b, description, severity (blocking|warning|advisory),
   and user_message (plain language for display to the user).

2. SHARPE FEASIBILITY CHECK:
   implied_sharpe = target_annual_return_pct / (max_portfolio_drawdown_pct * 1.5)
   If implied_sharpe > 2.0: severity = blocking
   If implied_sharpe > 1.5: severity = warning
   If implied_sharpe <= 1.5: severity = achievable
   Generate explanation in plain language.

3. EXPECTATION CORRECTIONS:
   For any user-stated value that falls outside the empirically realistic
   range for post-catalyst momentum strategies, generate an expectation
   correction entry.

4. VOLATILITY TARGET DERIVATION:
   Assuming Sharpe = 0.5 (conservative baseline for pre-deployment strategies):
   derived_volatility_pct = max_portfolio_drawdown_pct / (2.5 * sqrt(time_horizon_years))
   where time_horizon_years = max(horizon_allocation[].max_days) / 252
   Document the assumption explicitly.

5. LEGAL RESTRICTIONS FLAG:
   If legal_trading_restrictions_disclosure is populated (not null),
   set filing_notes.legal_restrictions_disclosure_flag = true

Contradiction rules to evaluate: {RULES — see Part 6}

Complete schema:
{complete_schema_json}

Return JSON only. Structure:
{
  "filing_notes_updates": {
    "contradictions": [...],
    "expectation_corrections": [...],
    "sharpe_feasibility_check": {...},
    "volatility_target_derivation": {...},
    "legal_restrictions_disclosure_flag": boolean
  }
}
```

**Pass 2: Cross-Section Synthesis**

**Request:** Complete schema JSON + Pass 1 output

**LLM task:** Generate cross-section synthesis fields. This is where the mandate comes together as a coherent document.

**LLM system prompt (Pass 2):**
```
You are the Aegis mandate synthesizer. You have the complete intake schema
and the results of the contradiction detection pass.

Your task is to generate the cross-section synthesis fields that require
reading multiple sections together. These fields are the most important
context the Builder will use when generating strategies.

1. REGIME_UNIVERSE_PAIRS (strategy_mandate):
   Create ONLY from explicitly linked user preferences. If the user explicitly
   linked a market condition (from macro_views or current_regime_beliefs) to
   a specific asset class AND a strategy type, create a regime_universe_pair.
   If no explicit linkage exists, return an empty array.
   Schema: [{regime, universe, strategy_type, rationale}]

2. ORDERED_PRIORITIES RATIONALE:
   For each ranked dimension in mandate_priority_hierarchy.ordered_priorities,
   write a 1-2 sentence rationale grounded in what the user actually said
   across the full schema.

3. REALISTIC_PERFORMANCE_RANGE:
   Based on: selected catalyst types, horizon allocation, drawdown limit,
   universe constraints, and empirical data from the research basis.
   PEAD strategies: Sharpe 0.4-0.8, win rate 45-55%, drift 21-63 days
   Biotech binary: higher variance, asymmetric return distribution
   Generate low/mid/high ranges for: annual return %, Sharpe, max drawdown %
   State assumptions explicitly.

4. EXPLICIT_VS_INFERRED_SUMMARY:
   Brief summary of what was stated explicitly vs what the system inferred.
   Reference the [EXPLICIT]/[INFERRED] tags in the schema.

5. OPEN_QUESTIONS:
   Any material gaps where conservative defaults will be applied.
   Be specific — name the field and the default being applied.

6. CONVERSATION_QUALITY_NOTE:
   Brief assessment of how much weight to give the full context vs defaults.

Complete schema (with Pass 1 filing_notes updates applied):
{complete_schema_with_pass1}

Return JSON only. Structure:
{
  "strategy_mandate_updates": {
    "regime_universe_pairs": [...]
  },
  "mandate_priority_hierarchy_updates": {
    "ordered_priorities": [...with rationale populated...]
  },
  "filing_notes_updates": {
    "explicit_vs_inferred_summary": "...",
    "open_questions": [...],
    "realistic_performance_range": {...},
    "conversation_quality_note": "..."
  }
}
```

**After Pass 2:** Merge both pass outputs into the schema. Surface to user:
- All `blocking` contradictions (must be resolved before confirm button activates)
- All `warning` contradictions (user must acknowledge each)
- `realistic_performance_range` (user must check `expectation_calibration_acknowledged`)
- `expectation_corrections` (user must acknowledge)

**Confirm button activates only when:**
- Zero blocking contradictions remain
- All warnings have been acknowledged
- `expectation_calibration_acknowledged = true`
- `drawdown_breach_protocol` is not null

---

## PART 6: CONTRADICTION DETECTION RULES

Machine-readable rule definitions for implementation. Both the section validators and Pass 1 use these rules.

```
RULE 01 — SHARPE FEASIBILITY
  condition: target_annual_return_pct IS NOT NULL AND max_portfolio_drawdown_pct IS NOT NULL
  check: implied_sharpe = target_annual_return_pct / (max_portfolio_drawdown_pct * 1.5)
  severity:
    implied_sharpe > 2.0 → blocking
    implied_sharpe > 1.5 → warning
  field_a: return_mandate.target_annual_return_pct
  field_b: risk_mandate.tier_1_risk_constraints.max_portfolio_drawdown_pct
  user_message (warning): "Your return target of {X}% with a {Y}% drawdown limit implies
    a Sharpe ratio of {Z}, which exceeds what post-catalyst momentum strategies
    realistically achieve out-of-sample. Consider lowering your return target
    or raising your drawdown limit."
  user_message (blocking): "Your return target of {X}% with a {Y}% drawdown limit implies
    a Sharpe ratio of {Z}. This is not achievable with the strategies Aegis builds.
    You must adjust one of these values before proceeding."

RULE 02 — BIOTECH CATALYST + PROFITABILITY SCREEN
  condition: catalyst_types contains {catalyst_type: fda_pdufa_biotech, permitted: true}
             OR clinical_trial_readout_phase3 OR clinical_trial_readout_phase2
  AND: fundamental_screens contains {screen_type: profitability_required,
       applies_to_catalyst_types: "all"}
  severity: blocking
  field_a: strategy_mandate.catalyst_types
  field_b: universe_mandate.fundamental_screens
  user_message: "You've enabled biotech catalyst types (FDA/clinical readouts) and
    a profitability screen that applies to all catalyst types. 94%+ of biotech PDUFA
    candidates are pre-revenue. This combination will produce an empty universe.
    Change the screen's 'applies to' setting to exclude biotech, or disable the
    profitability screen for biotech catalyst types."

RULE 03 — SECTOR EXCLUSION + CATALYST TYPE CONFLICT
  condition: universe_mandate.sectors_excluded contains healthcare OR biotech
             AND strategy_mandate.catalyst_types contains any of
             [fda_pdufa_biotech, clinical_trial_readout_phase3,
             clinical_trial_readout_phase2] with permitted = true
  severity: blocking
  field_a: universe_mandate.sectors_excluded
  field_b: strategy_mandate.catalyst_types
  user_message: "Healthcare/biotech is excluded from your universe but you've enabled
    biotech catalyst types. These are mutually exclusive. Either remove healthcare
    from your exclusion list or disable the biotech catalyst types."

RULE 04 — LEVERAGE CONTRADICTION
  condition: capital_structure.leverage_permitted = false
             AND capital_structure.max_leverage_ratio IS NOT NULL AND > 1.0
  severity: blocking
  field_a: capital_structure.leverage_permitted
  field_b: capital_structure.max_leverage_ratio
  user_message: "You've disabled leverage but set a leverage ratio above 1.0.
    Set leverage ratio to 1.0 or enable leverage."

RULE 05 — SHORT SELLING CONTRADICTION
  condition: capital_structure.short_selling_permitted = false
             AND strategy_mandate.strategy_types_excluded does NOT include
             long_short and market_neutral
             AND regime_universe_pairs contains any entry with strategy_type
             implying short positions
  severity: warning
  field_a: capital_structure.short_selling_permitted
  field_b: strategy_mandate.regime_universe_pairs
  user_message: "Short selling is disabled but some of your strategy preferences
    imply short positions. Only long-side strategies will be generated."

RULE 06 — NARROW WINDOW + MORNING EXECUTION CATALYST
  condition: available_windows contains no window with start_time_et <= "10:30"
             AND strategy_mandate.catalyst_types contains pead_earnings_momentum
             with permitted = true
  severity: warning
  field_a: operational_mandate.available_windows
  field_b: strategy_mandate.catalyst_types
  user_message: "PEAD earnings momentum strategies achieve best entry quality
    in the first 60-90 minutes of market open (9:30-11:00 ET). Your available
    windows don't include this period. Strategy quality will be reduced —
    the system will use multi-day drift entries instead of breakout entries."

RULE 07 — ADV FLOOR + CAPITAL SIZE
  condition: universe_mandate.min_avg_daily_volume_usd < 500000
             AND capital_structure.investable_capital_usd > 500000
  severity: warning
  field_a: universe_mandate.min_avg_daily_volume_usd
  field_b: capital_structure.investable_capital_usd
  user_message: "Your minimum volume floor of ${X} may allow positions that
    exceed 5% of daily volume at your capital level, creating market impact
    that erodes strategy edge. Consider raising the volume floor to $1M+."

RULE 08 — LOW DRAWDOWN + BINARY CATALYST RISK
  condition: risk_mandate.tier_1_risk_constraints.max_portfolio_drawdown_pct < 5
             AND strategy_mandate.catalyst_types contains any of
             [fda_pdufa_biotech, clinical_trial_readout_phase3,
             clinical_trial_readout_phase2] with permitted = true
  severity: warning
  field_a: risk_mandate.tier_1_risk_constraints.max_portfolio_drawdown_pct
  field_b: strategy_mandate.catalyst_types
  user_message: "Your drawdown limit is {X}%. Binary biotech events (FDA decisions,
    clinical readouts) carry gap risk that can produce single-position losses of
    15-40% on the catalyst. Even with position size limits, a single adverse
    binary event could approach your total drawdown limit. Consider raising the
    drawdown limit or excluding binary catalyst types."

RULE 09 — SHORT TERM GAINS TOLERANCE + HORIZON (direct conflict)
  condition: tax_and_legal.short_term_gains_tolerance.level = strongly_prefer_to_avoid
             AND ALL horizon_allocation entries have max_days < 365
  severity: warning
  field_a: tax_and_legal.short_term_gains_tolerance
  field_b: strategy_mandate.horizon_allocation
  user_message: "You strongly prefer to avoid short-term gains, but all of your
    horizon allocation buckets have holding periods under 365 days. Every strategy
    generated will produce short-term capital gains. Either add a long-term bucket
    (max_days >= 365) or adjust your tax preference."

RULE 10 — SHORT TERM GAINS + HIGH TAX RATE (proactive connection)
  condition: tax_and_legal.estimated_marginal_tax_rate_pct >= 32
             AND ANY horizon_allocation entry has max_days < 365
             AND short_term_gains_tolerance.level IN [neutral, acceptable, indifferent]
  severity: advisory
  field_a: tax_and_legal.estimated_marginal_tax_rate_pct
  field_b: strategy_mandate.horizon_allocation
  user_message: "At your marginal tax rate of {X}%, short-term capital gains
    (holds under 12 months) will be taxed as ordinary income. Most of your
    horizon buckets are under 365 days. Your after-tax returns will be
    materially lower than gross returns — for example, a 15% gross annual
    return becomes ~{Y}% after tax. You selected 'neutral' on short-term gains
    tolerance — this is flagged so you can confirm that's intentional given
    your tax rate."

RULE 11 — CAP SIZE + PEAD ANOMALY STRENGTH
  condition: universe_mandate.market_cap_min_usd > 10000000000
             AND strategy_mandate.catalyst_types contains pead_earnings_momentum
             with permitted = true
  severity: advisory
  field_a: universe_mandate.market_cap_min_usd
  field_b: strategy_mandate.catalyst_types
  user_message: "PEAD drift is materially weaker in large-cap stocks (>$10B market
    cap). The anomaly is strongest in small and mid-cap where analyst coverage
    is lower and institutional arbitrage is more limited. At your market cap
    floor, expected PEAD alpha will be reduced. Adjust expectations accordingly."

RULE 12 — CAPITAL PRESERVATION + BINARY EVENTS
  condition: return_mandate.primary_objective = capital_preservation
             AND strategy_mandate.catalyst_types contains any of
             [fda_pdufa_biotech, clinical_trial_readout_phase3] with permitted = true
  severity: advisory
  field_a: return_mandate.primary_objective
  field_b: strategy_mandate.catalyst_types
  user_message: "Your primary objective is capital preservation, but you've
    enabled high-volatility binary catalyst types (FDA/Phase III). These
    are high-variance strategies by nature. Aegis will apply conservative
    position sizing, but there is inherent tension between capital preservation
    and binary event exposure. Confirm this is intentional."

RULE 13 — DRAWDOWN BREACH PROTOCOL MISSING
  condition: risk_mandate.tier_1_risk_constraints.drawdown_breach_protocol IS NULL
  severity: blocking
  field_a: risk_mandate.tier_1_risk_constraints.drawdown_breach_protocol
  field_b: null
  user_message: "You must select a drawdown breach protocol before your mandate
    can be finalized. This defines what Aegis does when your maximum drawdown
    limit is hit."
```

---

## PART 7: BEHAVIORAL FIELD ENFORCEMENT MECHANISMS

Every behavioral field must have a specific, parametric mapping to a Builder output. Fields without defined enforcement mechanisms are decorative. The research report diagnosed this failure in v9 — v10 must not repeat it.

### 7.1 `regret_asymmetry` → Exit Rule Design

```
loss_regret_dominant:
  mild → time-based exit at 80% of horizon_allocation midpoint for that bucket
          (example: for a 21-63 day bucket, auto-exit at day 34)
  moderate → time-based exit at 60% of horizon midpoint; no extension
  severe → time-based exit at 40% of horizon midpoint; hard cutoff regardless of
           momentum signal strength; trailing stop disabled for this user

miss_regret_dominant:
  mild → trailing volatility stop at 2.0x ATR; no time-based exit
  moderate → trailing stop at 1.5x ATR; position can ride for full anomaly window
  severe → trailing stop at 1.25x ATR; no time-based override; maximum
           continuation mode

balanced:
  time-based floor at horizon midpoint + trailing stop at 1.75x ATR
  whichever triggers first closes the position
```

### 7.2 `disposition_effect_tendency` → Minimum Hold Rules

```
strong:
  Enforce mandatory minimum holding period on profitable positions before
  any profit-taking exit signal is honored.
  Calculation: min_hold_days = round(horizon_allocation_bucket.min_days * 0.5)
  Example: for a 5-21 day bucket, min_hold = 3 days on a winning position
  Implementation: if position P&L > 0 AND days_held < min_hold_days,
    suppress profit-taking exit signals (stop-loss exits still active)
  Note: this applies to signal-generated exits, not user manual overrides
        (manual overrides governed by signal_override_policy)

moderate:
  min_hold_days = round(horizon_allocation_bucket.min_days * 0.25)

mild:
  No minimum hold enforcement — standard exit logic applies

none:
  No minimum hold enforcement
```

### 7.3 `loss_aversion_coefficient` → Stop Loss Calibration

```
standard_2to1:
  Stop loss distance = 2.0x annualized daily standard deviation of price changes
  (standard volatility-scaled stop)

elevated_3to1:
  Stop loss distance = 1.5x annualized daily standard deviation
  (tighter stop — user feels losses more acutely, reduces loss magnitude)
  Position size scaling: reduce position size by 15% to offset tighter stops

severe_4plus_to_1:
  Stop loss distance = 1.0x annualized daily standard deviation
  (very tight stop)
  Position size scaling: reduce position size by 25% to maintain equivalent
  risk per trade at tighter stop distance
  Signal threshold: elevate signal quality score requirement by 10 percentile
  points — only highest-conviction signals enter
```

### 7.4 `overtrading_tendency` → Signal Friction

```
frequent:
  Two enforcement mechanisms applied simultaneously:
  (1) Signal score threshold elevation: only signals in top 20th percentile
      of signal score distribution are surfaced (vs default top 40th percentile)
  (2) Mandatory minimum time between new position entries: 48-hour lockout
      after any new position entry before the next new entry is permitted
      (existing positions run normal exit logic; lockout applies to NEW entries)

occasional:
  Signal score threshold: top 30th percentile (mild tightening)
  No time lockout

rare | none:
  Standard thresholds apply
```

### 7.5 `cooling_off_requirements` → System Protocol

```
When trigger condition fires:

1. IMMEDIATE: Block all new strategy generation and new position entries
   Implementation: set system_status.cooling_off_active = true
                   set system_status.cooling_off_until = now() + cooling_off_days
   Existing live positions: continue running their normal exit logic
   No premature forced exits due to cooling off

2. DURING COOLING OFF: System generates no new signals
   Performance tracking continues
   Reporting continues per performance_reporting_frequency

3. RESTART:
   system_status.cooling_off_active reverts to false at cooling_off_until timestamp
   System presents required_actions_before_restart checklist to user
   User must acknowledge checklist (checkbox confirmation)
   Note: System cannot verify checklist completion — user acknowledgment only
   After acknowledgment: normal signal generation resumes

4. MANDATE REVIEW TRIGGER (distinct from cooling off):
   When max_consecutive_losses_review_trigger is hit:
   → Activate cooling_off_requirements (if defined)
   → Flag mandate for review per governance_and_review settings
   → Does NOT modify the optimization engine or signal quality thresholds
```

---

## PART 8: FRONTEND ARCHITECTURE NOTES

### 8.1 State Management

```
localStorage key: "aegis_intake_draft_v10"
Structure:
{
  investor_sophistication: string | null,
  section_states: {
    section_1: { locked: boolean, validated: boolean, data: {...} },
    section_2: { locked: boolean, validated: boolean, data: {...} },
    ... (sections 1-10)
  },
  schema_accumulation: {...}, // running merged schema JSON
  confirmation_state: {
    pass1_complete: boolean,
    pass2_complete: boolean,
    contradictions_acknowledged: [...],
    expectation_acknowledged: boolean
  }
}
```

### 8.2 Section Navigation Rules

- Sections are navigable in any order after Section 1 is completed
- Section 1 (investor_sophistication + account_type + investable_capital) must be completed first — it gates everything else
- Validated sections show a ✓ indicator
- Locked sections (validated + acknowledged) show a 🔒 indicator
- Confirm button is accessible from any section but runs the full schema before proceeding

### 8.3 Validate Button Behavior

Per section:
1. Collect structured fields + detail box text
2. POST to `/intake/validate/section`
3. Show loading state
4. On response: display populated prose fields for user review
5. Show gap questions (if any) as follow-up prompts
6. Show section-level contradictions as inline warnings
7. User can edit and re-validate before locking

### 8.4 Confirmation Flow

1. User clicks "Review & Confirm"
2. Run Pass 1 (POST to `/intake/confirm/pass1`)
   - Show loading: "Checking for conflicts..."
   - Display all contradictions grouped by severity
   - Blocking contradictions: shown as errors, confirm blocked
   - Warnings: shown with "Acknowledge" buttons
   - Advisory: shown as info
3. User resolves blocking contradictions (edit relevant sections)
4. User acknowledges all warnings
5. Run Pass 2 (POST to `/intake/confirm/pass2`)
   - Show loading: "Building your mandate..."
6. Display `realistic_performance_range` to user
7. User checks `expectation_calibration_acknowledged` checkbox
8. Confirm button activates
9. Final schema locked and passed to Builder handoff endpoint

---

*Aegis AI v10.0 — Intake Layer Complete Implementation Specification*
*Covers: Schema reference (13 sections), Form-based intake (10 form sections), LLM conversational intake, Validation architecture (two-pass confirmation), Contradiction detection rules (13 rules), Behavioral enforcement mechanisms, Frontend architecture.*
*Out of scope: Builder handoff, strategy generation, live pipeline changes.*
