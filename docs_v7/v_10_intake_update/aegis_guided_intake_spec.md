# AEGIS — GUIDED INTAKE SPECIFICATION
## Version 10.0 — Implementation Spec for Coding Agent

**Scope:** Guided intake only (Path A). Submission/validation is a shared spec
handled separately. Builder handoff is out of scope.

---

## PART 1: OVERVIEW

The guided intake is a 10-section sequential form with a live AI agent panel.
The agent behaves like a knowledgeable human sitting with the user at a bank —
an expert on the form who watches what's being filled in, reacts to it,
asks questions, surfaces contradictions in real time, and can write directly
to form fields where permitted. It is not a passive chatbot. It is an active
participant in the intake process.

The agent panel is persistent across all sections. The form advances
sequentially — sections unlock only when the previous section is validated
and locked. The user cannot skip ahead.

Both the form and the agent write to the same underlying schema state. The
schema is the single source of truth. The agent reads live schema state on
every call.

---

## PART 2: PAGE ARCHITECTURE

### Route
`/intake` — protected route, requires auth

### Layout
```
┌─────────────────────────────────────────────────────────┐
│  IntakePage                                              │
│  ┌──────────────────────┐  ┌─────────────────────────┐  │
│  │  SectionNav          │  │  AgentPanel             │  │
│  │  (left sidebar)      │  │  (right panel, fixed)   │  │
│  ├──────────────────────┤  │                         │  │
│  │  SectionForm         │  │  AgentMessages          │  │
│  │  (main content)      │  │  AgentInput             │  │
│  │                      │  │  AgentStatus            │  │
│  └──────────────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Component Tree
```
IntakePage
├── SectionNav
│   └── SectionNavItem × 10 (locked / active / complete states)
├── SectionForm
│   ├── Section1_MandateCapital
│   ├── Section2_Risk
│   ├── Section3_Performance
│   ├── Section4_Universe
│   ├── Section5_Strategy
│   ├── Section6_Operations
│   ├── Section7_Behavioral
│   ├── Section8_Tax
│   ├── Section9_Macro
│   └── Section10_Governance
│       (only one rendered at a time based on currentSection)
└── AgentPanel
    ├── AgentHeader (name, status indicator)
    ├── AgentMessages (ScrollArea)
    │   └── AgentMessage × n (agent | user type)
    ├── AgentTypingIndicator (shown when isThinking)
    └── AgentInput (textarea + send button)
```

---

## PART 3: ZUSTAND STORE

```typescript
// store/intakeStore.ts

interface SectionState {
  locked: boolean;
  validated: boolean;
  validatedAt: string | null;
  checksum: string | null; // SHA-256 of section's Tier 1 field values
                           // used for lock invalidation
}

interface AgentMessage {
  id: string;
  role: 'agent' | 'user';
  content: string;
  timestamp: string;
  section: number; // which section this message belongs to
  fieldUpdates?: FieldUpdate[]; // if agent proposed field changes
  contradictions?: Contradiction[];
  requiresAction?: boolean; // blocks section lock until addressed
}

interface FieldUpdate {
  path: string;          // dot-notation schema path e.g. "risk_mandate.tier_1_risk_constraints.max_portfolio_drawdown_pct"
  value: any;
  tier: 1 | 2;
  requiresConfirmation: boolean; // always true for Tier 1
  confirmed: boolean;
  label: string;         // human-readable field name for confirmation UI
}

interface Contradiction {
  field_a: string;
  field_b: string;
  description: string;
  severity: 'blocking' | 'warning' | 'advisory';
  user_message: string;
  resolved: boolean;
}

interface IntakeStore {
  // Navigation
  currentSection: number; // 1-10
  setCurrentSection: (n: number) => void;

  // Section states
  sections: Record<number, SectionState>;
  lockSection: (n: number) => void;
  unlockSection: (n: number) => void;
  invalidateDownstream: (fromSection: number) => void;

  // Schema — the live v10 schema object
  schema: IntakeSchemaV10;
  updateField: (path: string, value: any) => void;
  applyFieldUpdate: (update: FieldUpdate) => void;

  // Agent
  messages: AgentMessage[];
  isThinking: boolean;
  pendingUpdates: FieldUpdate[];
  addMessage: (msg: AgentMessage) => void;
  setThinking: (v: boolean) => void;
  confirmFieldUpdate: (updateId: string) => void;
  dismissFieldUpdate: (updateId: string) => void;

  // Persistence
  lastSavedAt: string | null;
  mirrorToBackend: () => Promise<void>;

  // Reset
  reset: () => void;
}
```

---

## PART 4: AGENT ARCHITECTURE

### Persona
The agent is named **Aria**. It speaks like a senior analyst who has done
thousands of these intake sessions — precise, efficient, human. Not
clinical, not sycophantic. It gets straight to the point.

It opens each section with a brief orientation: what the section covers and
what it needs from the user. It does not say "Great question!" or "I'd be
happy to help!" It just responds.

### Agent Output Format

Every agent API call returns structured JSON. The frontend parses this and
renders the conversational content while processing any field updates,
contradictions, or questions separately.

```typescript
interface AgentAPIResponse {
  message: string;           // conversational text rendered in chat
  field_updates?: {
    path: string;
    value: any;
    tier: 1 | 2;
    requires_confirmation: boolean;
    label: string;
  }[];
  questions?: string[];      // follow-up questions agent is asking
  contradictions?: {
    field_a: string;
    field_b: string;
    description: string;
    severity: 'blocking' | 'warning' | 'advisory';
    user_message: string;
  }[];
  gap_flags?: string[];      // missing context the agent flagged
  section_ready?: boolean;   // agent signals section is ready to lock
}
```

The `message` field is always present. All other fields are optional.

**Critical rule on field_updates:**
- Tier 2 fields: agent can propose updates directly, no confirmation needed
  before applying (but user can dismiss)
- Tier 1 fields: agent can SUGGEST a value but `requires_confirmation: true`
  always. A confirmation card appears in the chat. The user must explicitly
  click "Apply" before the field updates. The agent never silently writes
  a Tier 1 field.

### Agent Triggers

The agent fires on five trigger types. Each constructs a different prompt.

```
TRIGGER_SECTION_ENTER
  When: user navigates to a new section
  Agent does: introduces the section, explains what's needed, asks the
              first question if the section has required fields empty
  Tone: brief, orienting

TRIGGER_FIELD_CHANGE
  When: a structured field value settles after 800ms debounce
  Agent does: reacts if the value is noteworthy, contradicts something
              already set, or needs context. Silent if the change is routine.
  Tone: reactive, specific

TRIGGER_DETAIL_BOX_SUBMIT
  When: user submits the detail box text
  Agent does: full processing — extracts Tier 2 prose fields, asks gap
              questions, proposes field_updates for Tier 2 fields it can
              populate, flags contradictions
  Tone: thorough

TRIGGER_VALIDATE
  When: user clicks "Validate Section"
  Agent does: full section validation — cross-references all structured
              fields against detail box, runs applicable contradiction rules,
              checks completeness, signals section_ready if clean
  Tone: decisive

TRIGGER_USER_MESSAGE
  When: user sends a message in the agent chat
  Agent does: responds to the question or comment in context
  Tone: conversational
```

### Agent System Prompt Structure

The system prompt is assembled fresh on every API call. It has five parts:

```
[PART 1 — IDENTITY AND RULES]
Static. Who Aria is, what the intake is for, the Tier 1 / Tier 2 rules,
what she can and cannot write to, the output format spec.

[PART 2 — FULL SCHEMA REFERENCE]
Static per session. The complete field spec from 1_llm_guide.md — all
sections, all fields, all enforcement mechanisms, all contradiction rules.
This is the agent's training on the form.

[PART 3 — CURRENT SCHEMA STATE]
Dynamic. The live JSON schema with every field populated so far. Agent
reads this to know what's already been captured and detect cross-section
contradictions.

[PART 4 — CURRENT SECTION CONTEXT]
Dynamic. The spec for the active section only — which fields are in it,
their types, their Tier classification, and any section-specific rules.

[PART 5 — TRIGGER CONTEXT]
Dynamic. What triggered this call — which trigger type, the specific field
that changed or the user message received. Tells the agent what to respond to.
```

### Model Routing for Agent

Different triggers have different complexity requirements:

```
TRIGGER_FIELD_CHANGE    → Llama 4 Scout (Groq)
  Fast, low latency. Simple reactive comment. No heavy schema processing.

TRIGGER_SECTION_ENTER   → Llama 4 Scout (Groq)
  Fast intro. Reads current section spec only.

TRIGGER_USER_MESSAGE    → Qwen3 32B (Groq)
  General questions need more capability. Context-aware responses.

TRIGGER_DETAIL_BOX_SUBMIT → Cerebras Qwen3 235B
  Heavy processing. Extracts multiple Tier 2 fields, detects contradictions,
  proposes updates. Needs the most capable available free-tier model.

TRIGGER_VALIDATE        → Cerebras Qwen3 235B
  Full section validation. Same reasoning as above.
  Fallback: Claude Sonnet 4.6 if Cerebras unavailable.
```

### Agent API Endpoint

`POST /api/intake/agent`

```typescript
// Request
{
  trigger: 'section_enter' | 'field_change' | 'detail_box_submit' |
           'validate' | 'user_message';
  section: number;
  schema_state: IntakeSchemaV10;     // full current schema
  trigger_context: {
    field_path?: string;             // for field_change
    field_value?: any;               // for field_change
    detail_box_text?: string;        // for detail_box_submit
    user_message?: string;           // for user_message
  };
  message_history: {                 // last 10 messages for context
    role: 'agent' | 'user';
    content: string;
  }[];
}

// Response
AgentAPIResponse  // see interface above
```

---

## PART 5: SECTION-BY-SECTION FORM SPEC

Each section has:
- A set of structured field components
- A detail box (free text, maps to Tier 2 prose fields)
- A Validate button
- A lock state

### Shared Section Shell

```tsx
<SectionShell
  sectionNumber={n}
  title="..."
  description="..."
  locked={sections[n].locked}
>
  {/* structured fields */}
  <DetailBox
    placeholder="..."
    onSubmit={handleDetailBoxSubmit}
  />
  <ValidateButton
    onClick={handleValidate}
    disabled={!hasRequiredFields || isThinking}
  />
</SectionShell>
```

---

### SECTION 1 — Mandate & Capital
**Schema sections:** A (mandate_identification) + B (capital_structure)

**Structured fields:**

```
investor_sophistication
  Component: SegmentedControl (4 options)
  Options: Retail (New) | Retail (Experienced) | Semi-Professional | Professional
  Schema path: mandate_identification.investor_sophistication
  Tier: 2
  Required: true — renders first, gates field visibility in subsequent sections

account_type
  Component: Dropdown
  Options: Individual Taxable | Joint Taxable | Traditional IRA | Roth IRA |
           Solo 401(k) | Trust | Corporate | SEP IRA | Other
  Schema path: mandate_identification.account_type
  Tier: 1
  Required: true

mandate_role
  Component: Dropdown
  Options: Entire Portfolio | Growth Sleeve | Satellite/Speculative |
           Income Sleeve | Other
  Schema path: mandate_identification.mandate_role
  Tier: 2

aegis_capital_as_pct_of_total_liquid_net_worth
  Component: NumberInput (% suffix)
  Range: 1-100
  Schema path: mandate_identification.aegis_capital_as_pct_of_total_liquid_net_worth
  Tier: 2

investable_capital_usd
  Component: NumberInput ($ prefix, formatted)
  Schema path: capital_structure.investable_capital_usd
  Tier: 1
  Required: true

reserved_cash_pct
  Component: Slider (5-30%, step 1%, default 10%)
  Schema path: capital_structure.reserved_cash_pct
  Tier: 1

max_deployed_pct
  Component: Slider (50-100%, step 5%, default 80%)
  Schema path: capital_structure.max_deployed_pct
  Tier: 1

leverage_permitted
  Component: Toggle (default off)
  Schema path: capital_structure.leverage_permitted
  Tier: 1

max_leverage_ratio
  Component: NumberInput (step 0.1, min 1.0, max 4.0)
  Schema path: capital_structure.max_leverage_ratio
  Tier: 1
  Visible: only when leverage_permitted = true

margin_account
  Component: Toggle (default off)
  Schema path: capital_structure.margin_account
  Tier: 1

options_permitted
  Component: Toggle (default off)
  Schema path: capital_structure.options_permitted
  Tier: 1

short_selling_permitted
  Component: Toggle (default off)
  Schema path: capital_structure.short_selling_permitted
  Tier: 1

existing_holdings
  Component: TickerInput (typeahead, multi-value, stores as string[])
  Schema path: capital_structure.existing_holdings
  Tier: 2
  Label: "Tickers you already hold (for portfolio context only)"
  Subtext: "Tickers only — we don't need quantities or cost basis"

tickers_never_touch
  Component: TickerInput (typeahead, multi-value, stores as string[])
  Schema path: capital_structure.tickers_never_touch
  Tier: 1
  Label: "Tickers Aegis should never trade under any circumstances"
```

**Detail box prompt:**
"Tell us about your existing portfolio and what role you want Aegis to play.
What are you trying to accomplish? What's the rest of your portfolio doing?"

**Agent populates from detail box:**
mandate_identification.existing_non_aegis_portfolio_description,
mandate_identification.portfolio_beta_existing,
mandate_identification.mandate_inception_reason,
mandate_identification.investment_experience,
mandate_identification.behavioral_history,
capital_structure.leverage_context

**Validation rules for this section:**
- investable_capital_usd must be set
- account_type must be set
- If leverage_permitted = true, max_leverage_ratio must be set
- investor_sophistication must be set (gates all subsequent sections)

---

### SECTION 2 — Risk
**Schema sections:** C (risk_mandate)

**Structured fields:**

```
max_portfolio_drawdown_pct
  Component: Slider (5-50%, step 1%)
  Schema path: risk_mandate.tier_1_risk_constraints.max_portfolio_drawdown_pct
  Tier: 1
  Required: true
  Helper: "Maximum total loss from peak before the system stops.
           This is the most important number in your mandate."

max_daily_loss_pct
  Component: Slider (1-10%, step 0.5%)
  Schema path: risk_mandate.tier_1_risk_constraints.max_daily_loss_pct
  Tier: 1
  Required: true
  Helper: "Maximum loss in a single trading day before new position-building
           halts. Reference: your portfolio value at market open that day."

drawdown_breach_protocol
  Component: RadioGroup (4 options with plain-language descriptions)
  Schema path: risk_mandate.tier_1_risk_constraints.drawdown_breach_protocol
  Tier: 1
  Required: true — section cannot validate without this
  Options:
    pause_all_notify_user    → "Stop everything and notify me — I'll restart manually"
    reduce_position_sizes_50pct → "Cut all positions in half and keep running"
    manual_restart_required  → "Full stop — I review and manually restart"
    reduce_and_notify        → "Cut positions in half and alert me"

max_single_position_pct
  Component: Slider (2-25%, step 1%)
  Schema path: risk_mandate.tier_1_risk_constraints.max_single_position_pct
  Tier: 1
  Required: true

max_single_position_usd
  Component: NumberInput ($ prefix, formatted)
  Schema path: risk_mandate.tier_1_risk_constraints.max_single_position_usd
  Tier: 1
  Required: true
  Helper: "Both the % and $ limits apply — whichever is more restrictive wins"

max_sector_concentration_pct
  Component: Slider (10-60%, step 5%)
  Schema path: risk_mandate.tier_1_risk_constraints.max_sector_concentration_pct
  Tier: 1
  Required: true

max_concurrent_live_strategies
  Component: Stepper (1-20)
  Schema path: risk_mandate.tier_1_risk_constraints.max_concurrent_live_strategies
  Tier: 1
  Required: true

max_position_as_pct_of_adv
  Component: Slider (1-10%, step 0.5%, default 3%)
  Schema path: risk_mandate.tier_1_risk_constraints.max_position_as_pct_of_adv
  Tier: 1
  Visible: investor_sophistication in [retail_experienced, semi_professional, professional]

regret_asymmetry.type
  Component: SegmentedControl (3 options)
  Options:
    loss_regret_dominant → "Holding losers too long bothers me more"
    miss_regret_dominant → "Selling winners too early bothers me more"
    balanced             → "Both bother me equally"
  Schema path: risk_mandate.tier_2_risk_context.regret_asymmetry.type
  Tier: 2
  Required: true

regret_asymmetry.magnitude
  Component: SegmentedControl (3 options)
  Options: Mildly | Moderately | Strongly
  Schema path: risk_mandate.tier_2_risk_context.regret_asymmetry.magnitude
  Tier: 2
  Visible: after regret_asymmetry.type is set

target_portfolio_beta
  Component: Slider (-1.0 to 2.0, step 0.1)
  Schema path: risk_mandate.tier_2_risk_context.target_portfolio_beta
  Tier: 2
  Visible: investor_sophistication in [semi_professional, professional]
```

**Detail box prompt:**
"How do you think about risk? Describe your tolerance for volatility,
overnight gaps, and large losses. Include any past experiences — trades
that hurt, drawdowns you struggled through, or times you acted against
your plan."

**Agent populates from detail box:**
risk_mandate.tier_2_risk_context.volatility_tolerance,
gap_risk_tolerance, concentration_tolerance, tail_risk_tolerance,
time_risk_tolerance, correlation_risk_context, loss_aversion_context,
regret_asymmetry.context

**Contradiction rules active in this section:** Rules 01, 08, 13

---

### SECTION 3 — Performance Targets
**Schema sections:** D (return_mandate)

**Structured fields:**

```
primary_objective
  Component: Dropdown
  Options: Capital Growth | Income Generation | Capital Preservation |
           Beat Benchmark | Absolute Return
  Schema path: return_mandate.primary_objective
  Tier: 2
  Required: true

target_annual_return_pct
  Component: NumberInput (% suffix)
  Schema path: return_mandate.target_annual_return_pct
  Tier: 2
  Label: "Target annual return — advisory, not a guarantee"
  Helper: "This calibrates the system's aggressiveness. It is not a
           commitment the system can mathematically guarantee."

benchmark
  Component: Dropdown + conditional text input
  Options: S&P 500 | Nasdaq 100 | Russell 2000 | Absolute Return | Custom
  Schema path: return_mandate.benchmark
  Tier: 2

return_character.smoothness_preference
  Component: BinaryToggle with descriptions
  Options:
    smooth_and_consistent → "Smaller, more frequent gains. Lower
                             month-to-month volatility. Fewer large wins."
    lumpy_and_high        → "Larger, less frequent gains. Some months
                             may be flat or negative. Wins are larger."
  Schema path: return_mandate.return_character.smoothness_preference
  Tier: 2

return_character.income_vs_appreciation
  Component: SegmentedControl
  Options: Income | Appreciation | Balanced
  Schema path: return_mandate.return_character.income_vs_appreciation
  Tier: 2

target_monthly_income_usd
  Component: NumberInput ($ prefix)
  Schema path: return_mandate.target_monthly_income_usd
  Tier: 2
  Visible: primary_objective = income_generation

min_acceptable_sharpe
  Component: NumberInput (step 0.1)
  Schema path: return_mandate.min_acceptable_sharpe
  Tier: 2
  Visible: investor_sophistication in [semi_professional, professional]

target_return_horizon_months
  Component: Stepper (3-60 months)
  Schema path: return_mandate.target_return_horizon_months
  Tier: 2
```

**Detail box prompt:**
"What does success look like for this system? And what would make you
pull the plug — either it's working too well (feels risky), not well
enough, or behaving in a way you didn't expect?"

**Agent populates from detail box:**
return_mandate.target_annual_return_context, benchmark_context,
success_definition, failure_definition

**Contradiction rules active:** Rule 01 (preliminary Sharpe check)
Agent surfaces early warning if implied Sharpe > 1.5 when both
target_annual_return_pct and max_portfolio_drawdown_pct are set.

---

### SECTION 4 — Universe
**Schema sections:** E (universe_mandate)

**Structured fields:**

```
asset_classes_permitted
  Component: MultiSelectCheckboxes
  Options: US Equities | ETFs | Equity Options | US ADRs | Canadian Equities
  Schema path: universe_mandate.tier_1_hard_filters.asset_classes_permitted
  Tier: 1
  Required: true

geographies_permitted
  Component: MultiSelectCheckboxes
  Options: United States | Canada | United Kingdom | European Union | Asia Pacific
  Schema path: universe_mandate.tier_1_hard_filters.geographies_permitted
  Tier: 1
  Required: true

market_cap_min_usd
  Component: SegmentedControl + custom input
  Options: $50M+ | $300M+ | $2B+ | $10B+ | Custom
  Schema path: universe_mandate.tier_1_hard_filters.market_cap_min_usd
  Tier: 1
  Required: true

market_cap_max_usd
  Component: SegmentedControl + custom input (optional)
  Options: $2B | $10B | $50B | No cap | Custom
  Schema path: universe_mandate.tier_1_hard_filters.market_cap_max_usd
  Tier: 1

min_avg_daily_volume_usd
  Component: Dropdown
  Options: $500K | $1M (recommended) | $2M | $5M | $10M | Custom
  Schema path: universe_mandate.tier_1_hard_filters.min_avg_daily_volume_usd
  Tier: 1
  Required: true
  Default: 1000000

price_min_usd
  Component: NumberInput ($ prefix, default 1.00)
  Schema path: universe_mandate.tier_1_hard_filters.price_min_usd
  Tier: 1

restrict_to_sectors_of_interest
  Component: Toggle (default off)
  Schema path: universe_mandate.tier_1_hard_filters.restrict_to_sectors_of_interest
  Tier: 1
  Label: "Restrict universe ONLY to selected sectors"
  Helper: "Off = can trade any sector. On = limited to sectors below."

sectors_of_interest
  Component: MultiSelectChips (sector list)
  Schema path: universe_mandate.tier_1_hard_filters.sectors_of_interest
  Tier: 1 if restrict_to_sectors_of_interest = true, else Tier 2

sectors_excluded
  Component: MultiSelectChips (sector list)
  Schema path: universe_mandate.tier_1_hard_filters.sectors_excluded
  Tier: 1
  Note: cannot overlap with sectors_of_interest — frontend enforces

specific_tickers_focus
  Component: TickerInput (typeahead, multi-value)
  Schema path: universe_mandate.tier_1_hard_filters.specific_tickers_focus
  Tier: 1

specific_tickers_exclude
  Component: TickerInput (typeahead, multi-value)
  Schema path: universe_mandate.tier_1_hard_filters.specific_tickers_exclude
  Tier: 1

esg_hard_exclusions
  Component: MultiSelectCheckboxes
  Options: Weapons | Tobacco | Gambling | Adult Content | Cannabis |
           Fossil Fuels | Other
  Schema path: universe_mandate.tier_1_hard_filters.esg_hard_exclusions
  Tier: 1

fundamental_screens_enabled
  Component: Toggle (default off)
  Schema path: universe_mandate.fundamental_screens.fundamental_screens_enabled
  Tier: 2

[if fundamental_screens_enabled = true]
fundamental_screens (per-screen builder)
  Component: DynamicScreenBuilder
  Each screen row: screen_type dropdown + threshold input +
                   flexibility dropdown + applies_to_catalyst_types selector
  Schema path: universe_mandate.fundamental_screens.screens
  Tier: 2
  Note: applies_to_catalyst_types options populated from Section 5 catalyst
        selections. If Section 5 not yet complete, show all options.
        Compatibility warnings generated by agent on TRIGGER_VALIDATE.
```

**Detail box prompt:**
"What do you want to trade and why? Include what you know about these
markets, any financial characteristics you care about, and what makes a
stock appealing or unappealing to you."

**Agent populates from detail box:**
universe_mandate.tier_2_context.universe_description, sector_reasoning,
equity_character, liquidity_and_price_character

**Contradiction rules active:** Rules 02, 03, 07, 11
Fundamental screen compatibility warnings generated at validate step.

---

### SECTION 5 — Strategy & Catalysts
**Schema sections:** F (strategy_mandate)

**Structured fields:**

```
catalyst_types
  Component: CatalystCardGrid
  One card per catalyst type (10 total). Each card:
    - Catalyst name + plain-language description
    - Toggle: permitted (default off)
    - [if permitted = true]: RiskAcknowledgments sub-section
      Each acknowledgment: labeled checkbox + explanation text
  Schema path: strategy_mandate.catalyst_types
  Tier: 1
  Required: at least one permitted = true
  Note: required acknowledgments per catalyst type are defined in schema spec.
        Frontend enforces — cannot toggle permitted = true without completing
        required acknowledgments for that type.

horizon_allocation
  Component: HorizonAllocationBuilder
  User adds buckets: label input + min_days stepper + max_days stepper +
                     capital_weight slider
  Schema path: strategy_mandate.horizon_allocation
  Tier: 1
  Required: true
  Validation: weights must sum to 1.0 — show running total, block validate
              if not exactly 1.0

strategy_types_excluded
  Component: MultiSelectChips
  Options: Market Neutral | Long/Short | Intraday Scalping | Options Only |
           Pairs Trading | Other
  Schema path: strategy_mandate.strategy_types_excluded
  Tier: 1

complexity_preference
  Component: SegmentedControl
  Options: Simple Rules | Moderate Complexity | Maximum Sophistication
  Schema path: strategy_mandate.tier_2_strategy_context.complexity_preference
  Tier: 2
```

**Detail box prompt:**
"How do you think about entering and exiting trades? Describe the kinds
of setups you're looking for, any approaches you've tried, and what you
want the system to prioritize when it has to make trade-offs."

**Agent populates from detail box:**
strategy_mandate.tier_2_strategy_context.regime_preferences,
entry_philosophy, exit_philosophy, holding_philosophy,
signal_type_preferences

**Contradiction rules active:** Rules 02, 03, 05, 06, 08, 12

**Cross-section trigger:** When catalyst_types changes, agent runs
backward compatibility check against Section 4's fundamental_screens.
If conflict detected, surfaces immediately.

---

### SECTION 6 — Operations & Execution
**Schema sections:** G (operational_mandate)

**Structured fields:**

```
available_windows
  Component: WeeklyCalendarGrid (custom — see Part 6)
  Schema path: operational_mandate.tier_1_operational_constraints.available_windows
  Tier: 1
  Required: true — at least one window must be defined
  Stores as: [{days: string[], start_time_et: string, end_time_et: string}]

pre_post_market_capable
  Component: Toggle (default off)
  Schema path: operational_mandate.tier_1_operational_constraints.pre_post_market_capable
  Tier: 1

max_execution_latency_minutes
  Component: SegmentedControl
  Options: Under 15 min | 15–30 min | 30–60 min | 1–2 hours | Over 2 hours
  Maps to integers: 10 | 22 | 45 | 90 | 150
  Schema path: operational_mandate.tier_1_operational_constraints.max_execution_latency_minutes
  Tier: 1
  Required: true

automation_level
  Component: SegmentedControl (2 options only)
  Options:
    semi_automated_confirmation_required → "I confirm each trade before it executes"
    fully_manual                        → "I execute manually from signals"
  Schema path: operational_mandate.tier_1_operational_constraints.automation_level
  Tier: 1
  Required: true
  Note: fully_automated is NOT a valid option — do not include it

brokerage
  Component: TextInput with common broker suggestions
  Schema path: operational_mandate.tier_2_execution_context.brokerage
  Tier: 2

order_type_philosophy
  Component: Dropdown
  Options: Market Orders | Limit Orders (preferred) | Stop-Limit (preferred)
  Schema path: operational_mandate.tier_2_execution_context.order_type_philosophy
  Tier: 2
```

**Detail box prompt:**
"When can you realistically act on a trade? Describe your available
windows and any constraints — day job, travel schedule, time zones,
internet reliability."

**Agent populates from detail box:**
operational_mandate.tier_2_execution_context.brokerage_constraints,
execution_friction_context

**Contradiction rules active:** Rules 05, 06
When available_windows is set, agent cross-checks against permitted
catalyst types from Section 5 and fires Rule 06 if applicable.

---

### SECTION 7 — Behavioral Profile
**Schema sections:** H (behavioral_profile)

**Structured fields:**

```
disposition_effect_tendency.self_assessed
  Component: SegmentedControl
  Label: "How often do you sell winning positions too early?"
  Options: Often | Sometimes | Rarely | Never
  Schema path: behavioral_profile.disposition_effect_tendency.self_assessed
  Tier: 2

loss_aversion_coefficient
  Component: SegmentedControl
  Label: "When you lose $1,000, how does it feel vs. gaining $1,000?"
  Options:
    standard_2to1    → "About twice as bad"
    elevated_3to1    → "About 3x as bad"
    severe_4plus_to_1 → "4x or more as bad"
  Schema path: behavioral_profile.loss_aversion_coefficient
  Tier: 2

overtrading_tendency.self_assessed
  Component: SegmentedControl
  Label: "Do you have a tendency to overtrade or chase signals?"
  Options: Often | Sometimes | Rarely | Never
  Schema path: behavioral_profile.overtrading_tendency.self_assessed
  Tier: 2

max_consecutive_losses_review_trigger
  Component: Stepper (3-15)
  Label: "After how many consecutive losing trades should Aegis trigger a review?"
  Helper: "This triggers a review, not a shutdown."
  Schema path: behavioral_profile.max_consecutive_losses_review_trigger
  Tier: 2

cooling_off_requirements.trigger
  Component: MultiSelectChips
  Options: Drawdown Breach | Consecutive Loss Threshold | Major Adverse Event
  Schema path: behavioral_profile.cooling_off_requirements.trigger
  Tier: 2

cooling_off_requirements.cooling_off_days
  Component: Stepper (1-30)
  Schema path: behavioral_profile.cooling_off_requirements.cooling_off_days
  Tier: 2
  Visible: cooling_off_requirements.trigger is set

signal_override_policy.can_user_override
  Component: Toggle
  Label: "Can you manually reject a signal you disagree with?"
  Schema path: behavioral_profile.signal_override_policy.can_user_override
  Tier: 2

signal_override_policy.override_documentation_required
  Component: Toggle
  Label: "Require a written reason when overriding a signal?"
  Schema path: behavioral_profile.signal_override_policy.override_documentation_required
  Tier: 2
  Visible: signal_override_policy.can_user_override = true
```

**Note:** regret_asymmetry was captured in Section 2. It is displayed here
as a read-only summary card ("Based on Section 2, you're loss-regret
dominant at moderate intensity") — not re-captured.

**Detail box prompt:**
"Describe your psychological relationship with trading. What patterns
have you noticed in yourself — good and bad? When things go wrong, how
do you typically respond? What commitments do you want to make about
how you'll behave during drawdowns?"

**Agent populates from detail box:**
behavioral_profile.behavioral_constraints_during_drawdown,
disposition_effect_tendency.context,
overtrading_tendency.context,
cooling_off_requirements.required_actions_before_restart,
signal_override_policy.override_conditions

---

### SECTION 8 — Tax & Legal
**Schema sections:** I (tax_and_legal)

**Structured fields:**

```
account_tax_status
  Component: Dropdown (pre-filled suggestion from account_type in Section 1)
  Options: Fully Taxable | Tax-Deferred (Traditional IRA/401k) |
           Tax-Exempt (Roth) | Partially Sheltered
  Schema path: tax_and_legal.account_tax_status
  Tier: 1
  Required: true

estimated_marginal_tax_rate_pct
  Component: SegmentedControl
  Options: 10% | 12% | 22% | 24% | 32% | 35% | 37%
  Schema path: tax_and_legal.estimated_marginal_tax_rate_pct
  Tier: 2
  Visible: account_tax_status = fully_taxable

short_term_gains_tolerance.level
  Component: RadioGroup (5 options with descriptions)
  Schema path: tax_and_legal.short_term_gains_tolerance.level
  Tier: 2
  Visible: account_tax_status = fully_taxable

long_term_holding_preference_pct
  Component: Slider (0-100%)
  Schema path: tax_and_legal.long_term_holding_preference_pct
  Tier: 2

tax_loss_harvesting_directive
  Component: Dropdown
  Options: Active | Opportunistic | None
  Schema path: tax_and_legal.tax_loss_harvesting_directive
  Tier: 2

wash_sale_awareness_required
  Component: Toggle
  Schema path: tax_and_legal.wash_sale_awareness_required
  Tier: 2

specific_tax_lot_method
  Component: Dropdown
  Options: FIFO | LIFO | HIFO | Specific Identification
  Schema path: tax_and_legal.specific_tax_lot_method
  Tier: 2
  Visible: account_tax_status = fully_taxable

jurisdiction
  Component: Dropdown
  Schema path: tax_and_legal.jurisdiction
  Tier: 2

erisa_applicable
  Component: Toggle
  Schema path: tax_and_legal.erisa_applicable
  Tier: 2
  Visible: account_type in [traditional_ira, 401k_solo, sep_ira]

legal_trading_restrictions_disclosure
  Component: Textarea
  Schema path: tax_and_legal.legal_trading_restrictions_disclosure
  Tier: 2
  Label: "Legal trading restrictions (disclosure only)"
  Warning banner shown: "This field is for disclosure only. Aegis does
    not enforce blackout periods or restricted securities lists. You are
    responsible for compliance with your applicable trading policies."
```

**Detail box prompt:**
"Any additional tax context or legal constraints? Include anything
relevant to how gains and losses should be handled."

**Agent populates from detail box:**
tax_and_legal.short_term_gains_tolerance.context,
regulatory_constraints

**Contradiction rules active:** Rules 09, 10

---

### SECTION 9 — Portfolio Scope & Macro
**Schema sections:** J (portfolio_scope_and_macro)

**Structured fields:**

```
market_beta_intent
  Component: Slider (-1.0 to 2.0, step 0.1)
  Schema path: portfolio_scope_and_macro.market_beta_intent
  Tier: 2
  Visible: investor_sophistication in [semi_professional, professional]

regime_adaptivity_intent
  Component: BinaryToggle
  Options:
    adaptive_to_regime                    → "Adapt strategy selection to market conditions"
    strategy_consistent_regardless_of_regime → "Stay consistent regardless of regime"
  Schema path: portfolio_scope_and_macro.regime_adaptivity_intent
  Tier: 2

sectors_with_tailwinds
  Component: MultiSelectChips (sector list)
  Schema path: portfolio_scope_and_macro.sectors_with_tailwinds
  Tier: 2

sectors_with_headwinds
  Component: MultiSelectChips (sector list)
  Schema path: portfolio_scope_and_macro.sectors_with_headwinds
  Tier: 2
  Note: agent fires contradiction if a sector appears in both lists
```

**Detail box prompt:**
"What's your macro view? What do you think is happening in the market
right now, what's coming, and how should Aegis position in response?
Include any views on sectors, rates, inflation, or regime."

**Agent populates from detail box:**
portfolio_scope_and_macro.ambition_description, diversification_intent,
correlation_intent, pipeline_growth_intent, macro_views,
current_regime_beliefs

---

### SECTION 10 — Governance & Priorities
**Schema sections:** K (governance_and_review) + L (mandate_priority_hierarchy)

**Structured fields:**

```
mandate_review_frequency
  Component: Dropdown
  Options: Monthly | Quarterly | Semi-Annually | Annually | Event-Driven Only
  Schema path: governance_and_review.mandate_review_frequency
  Tier: 2

review_trigger_conditions.drawdown_pct_of_max_triggers_review
  Component: Slider (50-100%)
  Label: "Trigger review when drawdown reaches ___% of your maximum"
  Schema path: governance_and_review.review_trigger_conditions.drawdown_pct_of_max_triggers_review
  Tier: 2

review_trigger_conditions.consecutive_losses_triggers_review
  Component: Stepper
  Schema path: governance_and_review.review_trigger_conditions.consecutive_losses_triggers_review
  Tier: 2

performance_reporting_frequency
  Component: SegmentedControl
  Options: Daily | Weekly | Monthly
  Schema path: governance_and_review.performance_reporting_frequency
  Tier: 2

performance_attribution_framework
  Component: CheckboxGroup
  Options: By Catalyst Type | By Sector | By Strategy Type | By Holding Period
  Schema path: governance_and_review.performance_attribution_framework
  Tier: 2

ordered_priorities
  Component: DragToRankList (custom — see Part 6)
  Dimensions: Capital Preservation | Return Maximization | Consistency |
              Tax Efficiency | Catalyst Type Adherence | Sector Focus |
              Execution Simplicity | Income Generation
  Schema path: mandate_priority_hierarchy.ordered_priorities
  Tier: 2
  Per-dimension: flexibility dropdown (Immovable | Strong | Moderate | Flexible)
                 stored in preference_flexibility[]
```

**Detail box (two boxes):**

Trade-off philosophy:
"In your own words — when the system has to sacrifice one thing to get
another, what should guide that decision?"

Governance:
"Under what conditions would you amend or shut down this mandate?"

**Agent populates from detail boxes:**
mandate_priority_hierarchy.trade_off_philosophy,
governance_and_review.mandate_amendment_policy,
all ordered_priorities[].rationale fields (LLM-generated from context)

---

## PART 6: CUSTOM COMPONENTS

### WeeklyCalendarGrid

**Purpose:** Capture available_windows as structured time blocks.

**Behavior:**
- 5-column grid (Mon-Fri)
- Rows represent 30-minute time slots from 9:00 AM to 4:30 PM ET
- User clicks a cell to toggle it, or click-drags to select a range
- Adjacent selected cells in the same column auto-merge into one window
- Deselecting breaks a merged window at that point
- Selected cells styled with Sage (#ACCEC5) fill
- Unselected cells styled with glass-panel background

**Output format:**
```typescript
// Each contiguous block per day becomes one entry
[
  {
    days: ["monday", "tuesday", "wednesday", "thursday", "friday"],
    start_time_et: "09:30",
    end_time_et: "11:30"
  },
  {
    days: ["monday", "tuesday", "wednesday", "thursday", "friday"],
    start_time_et: "15:30",
    end_time_et: "16:00"
  }
]
```

**Smart merge logic:**
If the same time block is selected for multiple days, merge into one entry
with multiple days in the array. If days differ, create separate entries.

**Agent integration:**
When the grid is committed (user clicks away or section validates), agent
cross-checks windows against permitted catalyst types from Section 5
and fires Rule 06 if applicable.

---

### DragToRankList

**Purpose:** Capture ordered_priorities and preference_flexibility.

**Behavior:**
- Vertical list of dimension cards
- Each card is draggable — drag handle on left, dimension label, flexibility
  dropdown on right
- Rank number shown on left (updates as order changes)
- Flexibility dropdown: Immovable | Strong | Moderate | Flexible
  Immovable items show a lock icon and subtle Terracotta (#FFB59E) accent
- User can remove dimensions they don't want to rank (collapses to unranked
  pool below)
- Unranked pool shows dimensions not yet added to the ranking

**Output:**
```typescript
// ordered_priorities
[
  { rank: 1, dimension: "capital_preservation", rationale: null },
  { rank: 2, dimension: "catalyst_type_adherence", rationale: null }
]

// preference_flexibility (one entry per dimension in the ranked list)
[
  { preference: "capital_preservation", flexibility: "immovable", rationale: null },
  { preference: "catalyst_type_adherence", flexibility: "strong", rationale: null }
]
```

Rationale fields are populated by the agent from the detail box — not
user-typed.

---

## PART 7: SECTION VALIDATION FLOW

Per section:

```
1. User fills structured fields
2. User writes in detail box (optional but encouraged)
3. User clicks "Validate Section"
4. Frontend sends TRIGGER_VALIDATE to agent API
   Payload: full current schema state + current section spec
5. Agent (Cerebras Qwen3 235B) processes:
   - Translates detail box → Tier 2 prose fields (returns as field_updates)
   - Detects gaps (returns as gap_flags)
   - Detects contradictions for active rules (returns as contradictions)
   - Signals section_ready if clean
6. Frontend renders agent response:
   - Tier 2 field_updates applied immediately (no confirmation needed)
   - Tier 1 field_updates shown as confirmation cards in agent panel
   - Contradictions shown as inline alerts:
     blocking → red alert, blocks "Lock Section" button
     warning  → amber alert, requires acknowledge before lock
     advisory → blue info card, no block
   - gap_flags shown as follow-up questions in agent panel
7. User addresses any issues (edits fields, answers questions,
   acknowledges warnings)
8. User clicks "Lock Section"
   - Blocked if any blocking contradictions unresolved
   - Blocked if required Tier 1 fields are null
   - Blocked if drawdown_breach_protocol is null (Section 2)
9. Section locks
   - Checksum computed from Tier 1 fields in this section
   - SectionState.locked = true, validatedAt = now()
   - Schema mirrored to backend
10. Next section unlocks
```

---

## PART 8: LOCK INVALIDATION

When a user edits a locked section upstream:

```
Section 1 edited → invalidate all locks 2-10
Section 2 edited → invalidate all locks 3-10
Section 3 edited → rerun Sharpe check at confirmation only
Section 4 edited → invalidate Section 5 lock (compatibility check)
Section 5 edited → invalidate Section 4 lock (compatibility check)
                   rerun Rules 02, 03, 05, 06, 08, 12
Section 8 edited → rerun Rules 09, 10
```

Implementation: on any field change in a locked section, compute new
checksum of that section's Tier 1 fields. If different from stored
checksum, unlock that section and all downstream sections. Show banner:
"You've changed a field in Section {n}. Sections {n+1} through {m} need
to be re-validated."

---

## PART 9: STATE PERSISTENCE

**localStorage auto-save:**
```typescript
// Debounced 500ms after any schema field update
localStorage.setItem(
  'aegis_intake_draft_v10',
  JSON.stringify({
    schema: store.schema,
    sections: store.sections,
    currentSection: store.currentSection,
    messages: store.messages,
    savedAt: new Date().toISOString()
  })
)
```

**Backend mirror triggers:**
```
- Section locked → POST /api/intake/draft { schema, sections, event: 'section_lock' }
- All 10 sections locked → POST /api/intake/draft { schema, sections, event: 'complete' }
- Manual save (user action) → POST /api/intake/draft { schema, sections, event: 'manual' }
```

**Draft restore on page load:**
```typescript
// On IntakePage mount:
const draft = localStorage.getItem('aegis_intake_draft_v10')
if (draft) {
  const parsed = JSON.parse(draft)
  // validate schema version matches
  if (parsed.schema._schema_version === 'v10.0') {
    store.restoreFromDraft(parsed)
    // show "Resume from saved draft" banner
  }
}
```

---

## PART 10: API ENDPOINTS

```
POST /api/intake/agent
  Body: AgentAPIRequest (see Part 4)
  Returns: AgentAPIResponse
  Auth: required
  Notes: model selection handled server-side based on trigger type

POST /api/intake/draft
  Body: { schema, sections, event }
  Returns: { saved: true, session_id: string }
  Auth: required

GET /api/intake/draft
  Returns: latest saved draft for authenticated user
  Auth: required
```

---

## PART 11: COMPONENTS TO BUILD FROM SCRATCH

```
WeeklyCalendarGrid      — Section 6 execution windows
DragToRankList          — Section 10 priority hierarchy
CatalystCardGrid        — Section 5 catalyst type cards with acknowledgments
HorizonAllocationBuilder — Section 5 capital weight bucketing
DynamicScreenBuilder    — Section 4 fundamental screens per-screen builder
SegmentedControl        — reusable across all sections
AgentPanel              — persistent right panel with chat + typing indicator
AgentMessage            — agent and user message variants
FieldUpdateConfirmCard  — Tier 1 field update confirmation UI in agent panel
SectionShell            — shared section wrapper with lock state
SectionNav              — left sidebar with progress
```

---

*Aegis AI v10.0 — Guided Intake Implementation Specification*
*For: React 19 + TypeScript + Vite + Tailwind 3.4 + Radix UI + Zustand*
*Out of scope: submission validation, builder handoff*
