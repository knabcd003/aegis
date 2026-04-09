# AEGIS AI v7.0
## Comprehensive System Blueprint

---

> **One-line thesis:** A fully autonomous AI trading pipeline where the human captures their mandate once, a transparent multi-agent system builds and validates strategies entirely on free-tier infrastructure, and the human makes a single binary decision before any real money moves.

---

## PART I: THE PIVOT FROM v6

### The Core Shift

v6 was a tool for sophisticated users who wanted to build their own AI-powered trading strategies. The human was the architect — designing strategies through a wizard, reviewing AI improvement proposals, approving promotions.

v7 makes one fundamental shift: **the human no longer builds anything.**

Hybrid human-AI trading workflows consistently underperform either pure-human or pure-AI systems. A retail investor reviewing a Signal Card faces a no-win situation. Always accepting makes the human step theater. Always declining based on gut overrides a calibrated system. Sometimes agreeing based on feel introduces random noise into a system that was optimized without that variance.

The correct role for a retail investor is mandate-setting and final execution consent. Everything between — strategy generation, backtesting, adversarial auditing, promotion, live monitoring — runs autonomously.

### What Carries Forward Unchanged from v6.1

- **Point-in-time data discipline** — `public_disclosure_ts` enforcement, immutable filing ledger, FRED vintage data via ALFRED API
- **Held-out partition** — 20% sealed at run initiation, hashed against `run_id`, never exposed to the optimization loop, `held_out_degradation_max: 0.35` non-configurable
- **MLflow tiered logging** — `quick_iteration` / `production` / `debug` depth tiers, artifact tiering, full reasoning traces written once at promotion
- **Five execution traps and fixes** — Segment Obfuscation NLI, deterministic scenario library, overfitting holdout, connector health silent failure, regulatory framing drift
- **Custom Engine SDK** — `BaseEngine` abstract class, five signal roles, Docker sandbox enforcement, `health()` method contract
- **Connector Health Monitor** — MONITORING / DEGRADED / OFFLINE states, asymmetry rule, signal suspension on OFFLINE
- **DeBERTa two-stage NLI** — singleton loading at startup, segment obfuscation detection before any data enters the pipeline
- **EntryStateSnapshot** — captured at position open, stored with trade record and MLflow artifact, required for Fundamental Shift exit type
- **Pre-flight Health Check** — memory sentinel, latency calibration, connector health validation before any pipeline run
- **Proving Ground criteria** — `proving_ground_criteria` block with explicit pass/fail thresholds, `require_explicit_sign_off: true`

### What Changes in v7

| Area | v6.1 | v7.0 |
|------|------|------|
| User entry point | 6-step Strategy Wizard | Two-path intake system |
| Strategy authorship | Human-designed, AI-refined | AI-generated from mandate + desire |
| Audit mechanism | Human reviews proposals | FinDebate with evidentiary rubric |
| Scenario testing | Curated historical date ranges | Block bootstrap generator |
| Model routing | Static 5-factor scorer | Static assignment table (RouteLLM Phase 6) |
| Model pool | Qwen3:8b + Claude | Six-provider free tier + Claude as emergency |
| Tool architecture | Custom wrappers per agent | VCL + MCP + Token Messenger Pattern |
| Sequencing enforcement | LangGraph edges (behavioral) | Token Messenger cryptographic chaining |
| Primary interface | Control panel + Glass Box | Visual Pipeline Map + Glass Box as product |
| Human role | Wizard + proposals + Signal Cards | Intake + Signal Cards only |
| Claude budget | Regular escalation tool | Emergency backstop — ~3–5 calls/month |
| Diversity mechanism | Measured after generation | Driven before generation via ArchetypePool |
| Degraded sessions | Not addressed | Held pending re-evaluation, flagged in Glass Box |
| Signal Card freshness | Not addressed | Live price validator, ACCEPT disabled if stale |
| Bear debate quality | Capability-driven | Evidentiary rubric, win rate monitoring |

---

## PART II: INTAKE SYSTEM

### Philosophy

The intake is the only moment the human shapes what the system builds. Two paths. Same output. Same pipeline.

Some users want to be running in two minutes. Others already have a sophisticated investment view developed through weeks of AI conversations and want to import that context precisely. Both are valid. The system meets users where they are.

### Honest Product Boundary

Aegis is not designed to compete with high-frequency trading algorithms or expert network traders on information speed. It does not capture the first 15 minutes after an FDA ruling or earnings release. That window belongs to institutional players with co-located servers and proprietary data feeds.

What Aegis captures: durable signal in the days and weeks following catalysts, where retail investors can realistically act. Post-announcement momentum, multi-day technical setups, fundamental shifts that play out over weeks. This boundary is stated explicitly during intake confirmation so users do not develop false expectations about what the system can deliver.

For users who select catalyst-driven desires like "FDA plays" or "earnings momentum," the confirmation screen includes: *"Aegis captures post-catalyst signal — momentum and positioning in the days after events, not pre-announcement alpha. The system will not outrace institutional traders to the first tick."*

### Path A — Simple Setup (Default)

No AI involved anywhere in the intake. Four direct inputs. Direct mapping — no parsing, no inference, no LLM call.

```
┌──────────────────────────────────────────────────────────────┐
│  What do you want to trade? (optional — skip to go generic)  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ e.g. "risky small biotech" or "boring dividend stocks" │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  How much can you lose before it stops being okay?           │
│  ○ A little (5–10%)  ● Some (10–20%)  ○ A lot (20–40%)      │
│                                                              │
│  How long do you hold positions?                             │
│  ○ Hours (day)  ● Days to weeks (swing)  ○ Weeks+ (position) │
│                                                              │
│  How much capital? (optional)                                │
│  $___________                                                │
│                                                              │
│               [ Build my pipeline → ]                        │
└──────────────────────────────────────────────────────────────┘
```

If the desire field is blank, the Builder explores freely within the risk parameters. The three structured inputs map deterministically to hard constraints — no model call involved.

### Path B — Comprehensive Schema Import (Power Users)

For users who already have rich investment context from conversations with Claude, ChatGPT, Gemini, or any other AI. They download two files:

1. **`aegis_intake_schema.json`** — every field Aegis can use, annotated for the filling LLM
2. **`aegis_llm_intake.md`** — standalone document explaining Aegis fully and instructing the external LLM exactly how to populate the schema

The user gives both to their AI of choice and pastes the populated schema into Aegis. The system validates it, translates to plain language, and shows hard constraints for explicit confirmation before anything freezes.

The schema alone is insufficient instruction for a filling LLM. The intake document explains the critical distinction between hard constraints and soft preferences, and the conservative rule for risk fields. Without it, an external LLM will fill risk fields aggressively based on personality inference rather than stated preferences.

### The Intake Schema

```json
{
  "_schema_version": "v7.0",
  "_path": "B",
  "_for_llm": "See aegis_llm_intake.md before filling this schema.",

  "required": {
    "risk_tolerance": null,
    "max_drawdown_pct": null,
    "time_horizon": null,
    "raw_desire": null
  },

  "portfolio": {
    "investable_capital": null,
    "existing_holdings": [],
    "holdings_to_never_touch": [],
    "account_type": null
  },

  "universe": {
    "asset_classes": [],
    "market_cap_range": null,
    "sectors_of_interest": [],
    "sectors_to_avoid": [],
    "geographies": [],
    "specific_tickers": [],
    "exclude_tickers": []
  },

  "strategy_character": {
    "preferred_regimes": [],
    "catalyst_types": [],
    "signal_type_preference": [],
    "holding_period_days": null,
    "preferred_complexity": null
  },

  "macro_views": [],

  "constraints": {
    "esg_exclusions": [],
    "max_sector_concentration_pct": null,
    "max_single_position_pct": null,
    "leverage": false
  },

  "notes": null
}
```

### Confirmation Step (Both Paths)

Mandatory before anything freezes. Shows hard constraints in plain language with an explicit product boundary note where relevant.

```
Here's what we're building:

  You want to trade risky small-cap biotech stocks —
  speculative, catalyst-driven, accepting high volatility.

  ℹ  Aegis captures post-catalyst signal — momentum and
     positioning in the days after FDA events and earnings,
     not pre-announcement alpha. The system will not outrace
     institutional traders to the first tick.

  These limits are hard — the system will never exceed them:
  ┌───────────────────────────────────────────────────────┐
  │  Max portfolio drawdown:  15%                         │
  │  Max position size:       2.5% per trade              │
  │  Stop-loss range:         1% – 3% per trade           │
  │  Holding period:          3 – 21 days                 │
  └───────────────────────────────────────────────────────┘

  ⚠  Small biotech is genuinely volatile. Your 15% drawdown
     limit may reduce signal frequency. Raise it if you want
     more activity.

  [ These look right — build it ]    [ Let me adjust ]
```

### The Two Core Objects

**`MandateProfile` — frozen hard constraints**

```python
@dataclass(frozen=True)
class MandateProfile:
    risk_tolerance:          str
    max_drawdown_target:     float
    max_position_pct:        float
    max_account_risk_pct:    float
    stop_loss_range:         tuple
    holding_period_range:    tuple
    allowed_asset_classes:   list[str]
    leverage_permitted:      bool
    mandate_profile_id:      str
    created_at:              datetime
    schema_version:          str
```

**`UserIntent` — soft preferences, guides generation**

```python
@dataclass
class UserIntent:
    raw_desire:              str        # preserved verbatim always
    has_preference:          bool
    universe_tags:           list[str]
    strategy_character:      str
    sectors_of_interest:     list[str]
    sectors_to_avoid:        list[str]
    market_cap_range:        Optional[tuple]
    catalyst_types:          list[str]
    macro_views:             list[MacroView]
    exclusions:              list[str]
    notes:                   Optional[str]
    intake_path:             str        # "A" | "B"
    intake_schema_version:   str
```

### Builder Context Assembly

Every Builder call receives four objects:

```
MandateProfile         → what cannot be violated
UserIntent             → what to explore and why
StrategyArchetypePool  → what already exists (drive diversity before generation)
FailureContext         → what failed last iteration (if any)
```

The `StrategyArchetypePool` prompt injection is what causes diversity during generation — not the `max_correlation_existing: 0.60` gate, which only catches duplicates after the fact.

> *"Existing promoted strategies: [momentum-small-cap-biotech-fda-catalyst]. Generate a strategy in a meaningfully different regime or sub-sector. Underrepresented: mean-reversion, earnings-driven setups, PDUFA plays."*

### Contradiction Detection

- Conservative drawdown + desire implying aggressive risk → flag
- "Never lose money" + day trading → flag
- Ticker exclusion conflicts with stated sector interest → flag

Contradictions are warnings, not hard blocks. User resolves before confirming.

---

## PART III: COMPUTE ARCHITECTURE

### The Core Principle: Stateless by Design

Every model in the pipeline is stateless. This was already true for local Qwen3:8b — Ollama calls are independent, no memory between calls. Switching to cloud free tiers changes nothing. Pipeline continuity comes from `AegisState` and MLflow artifacts, not model memory.

### The Six-Provider Pool

**Tier 0 — Zero Latency (Local)**
```
Model:   Qwen3:8b via Ollama
Cost:    Zero variable cost
Quota:   Unlimited
Latency: ~22–30 seconds (no network)

Roles:   Schema routing, JSON parsing, NLI pre-filter,
         connector health polling, plain verdict generation,
         FinDebate Bull agent

Why keep: Only tier guaranteed available regardless of network
          or rate limits. Terminal fallback for entire system.
```

**Tier 1 — Fast Structured (Groq)**
```
Model:   meta-llama/llama-4-scout-17b-16e-instruct
RPM: 30  RPD: 1,000  TPM: 30K  TPD: 500K

Roles:   Semantic validation, quick classification, structured
         data extraction, FinDebate round compression
```

**Tier 2 — Strong Reasoning (Groq)**
```
Model:   qwen/qwen3-32b
RPM: 60  RPD: 1,000  TPM: 6K  TPD: 500K

Roles:   Strategy generation, Improvement Analyzer,
         FinDebate Bear agent, complex structured reasoning
Note:    60 RPM — highest in pool
```

**Tier 3 — Adversarial / Agentic (Groq)**
```
Model:   moonshotai/kimi-k2-instruct
RPM: 60  RPD: 1,000  TPM: 10K  TPD: 300K

Roles:   FinDebate Bear (alternate), Auditor Agent,
         adversarial multi-step reasoning
```

**Tier 4 — Frontier Quality (Groq)**
```
Model:   openai/gpt-oss-120b
RPM: 30  RPD: 1,000  TPM: 8K  TPD: 200K

Roles:   FinDebate Moderator, final audit scoring
Note:    Near-frontier quality, Apache 2.0, free
```

**Tier 5 — Massive Context (Google AI Studio)**
```
Model:   gemini-2.5-flash
Mac:     250 RPD (direct API, separate Google project)
Linux:   250 RPD (OpenClaw device, separate project)
Total:   500 RPD — independent quotas, not shared
Context: 1M tokens

Roles:   10-K ingestion, news synthesis, tasks > 50K tokens,
         OpenClaw world event analysis
```

**Tier 6 — Overflow (OpenRouter)**
```
Models:  qwen3-235b:free, llama-4-maverick:free
RPM: 20  RPD: 200 SHARED across all free models

Roles:   When any Groq model exhausts 1K RPD daily quota

EXCLUDE: All DeepSeek — Chinese servers, no training opt-out,
         government data cooperation requirements.
         Unacceptable for financial data.
```

**Tier 7 — Emergency (Anthropic)**
```
Model:   Claude Sonnet 4.6
Budget:  $20 total (~950 calls at ~$0.021/call)

Roles:   Multi-model contradiction resolution, first live
         deployment sign-off per new strategy, ≥2 free models
         produce conflicting verdicts on irreversible decision

Target:  3–5 calls/month → $20 lasts ~15–20 years
```

### Degraded Session Handling

This is a load-bearing safety feature, not a nice-to-have.

When primary provider quotas exhaust and the pipeline falls back to lower-tier models for critical roles, the quality of reasoning degrades significantly. A strategy approved by local Qwen3:8b filling the Moderator role is not the same product as one approved by GPT-OSS-120B. The pipeline must handle this explicitly rather than silently proceeding.

**Critical roles** — roles where model quality is directly load-bearing on the correctness of the result:
- `debate_moderator`
- `strategy_generation`
- `final_audit_score`
- `improvement_analyzer`

**Non-critical roles** — roles where degradation has limited downstream impact:
- `schema_routing`, `json_parsing`, `nli_prefilter`, `connector_health`, `plain_verdict`

Every `AuditEvent` records whether the assigned model was the primary assignment or a fallback:

```python
@dataclass
class AuditEvent:
    ...
    model_provider:        str
    model_name:            str
    role:                  str
    was_primary_model:     bool       # False if fallback triggered
    fallback_reason:       Optional[str]  # "quota_exhausted" | "provider_error"
    session_quality:       str        # "nominal" | "degraded" | "severely_degraded"
```

**Session quality classification:**
```python
def classify_session_quality(audit_events: list[AuditEvent]) -> str:
    critical_events = [e for e in audit_events if e.role in CRITICAL_ROLES]
    fallback_critical = [e for e in critical_events if not e.was_primary_model]

    if not fallback_critical:
        return "nominal"

    # Check how far down the fallback chain we went
    worst = max(fallback_critical, key=lambda e: FALLBACK_DEPTH[e.model_name])
    if FALLBACK_DEPTH[worst.model_name] >= 3:  # reached local Qwen3:8b
        return "severely_degraded"
    return "degraded"
```

**What happens with degraded sessions:**

*Degraded (fallback to mid-tier free model):*
- Strategy is flagged in MLflow with `session_quality: "degraded"`
- Promotion Gate holds the strategy — does not promote
- Strategy is queued for re-evaluation when primary providers reset (midnight UTC)
- Glass Box shows a yellow "DEGRADED SESSION" badge on the run

*Severely degraded (fallback reached local Qwen3:8b for a critical role):*
- Strategy is flagged `session_quality: "severely_degraded"`
- Promotion Gate rejects outright — does not queue for re-evaluation
- Builder re-runs the strategy from scratch when quotas reset
- Glass Box shows a red "SEVERELY DEGRADED — NOT VALID" badge

**Signal Cards from degraded sessions:**
A Signal Card generated from a degraded session displays a prominent warning and the ACCEPT button is disabled until the strategy has been re-evaluated under nominal conditions. The user sees: *"This signal was generated during a degraded session. It will be re-evaluated when full reasoning capacity is available. ACCEPT will be enabled after re-evaluation."*

The user should never be in a position to trust a midnight-run degraded signal without knowing it was degraded. The Glass Box audit trail shows exactly which roles were served by fallback models and how far down the chain the fallback went.

### Groq-Less Degradation Mode

If Groq eliminates or significantly reduces free tier access:

```
Primary reasoner: Qwen3:8b local
Large context:    Gemini 2.5 Flash (500 RPD combined)
Overflow:         OpenRouter :free (200 RPD shared)
Emergency:        Claude Sonnet 4.6

FinDebate degraded:
  Bull:       Qwen3:8b local
  Bear:       Qwen3:8b local (persona differentiation only)
  Moderator:  Gemini 2.5 Flash

Impact: Measurably worse reasoning quality. All sessions
        classified as "degraded" until Groq is restored.
        Pipeline functional — not stopped.
```

This is a documented first-class operating mode, not an edge case.

### Static Routing Table (Phase 5)

RouteLLM's classifier requires labeled preference data for financial tasks. You have none yet. The complexity thresholds would be arbitrary priors. Phase 5 uses a static assignment table. After 3–6 months of logged MLflow runs with outcome data, RouteLLM can be calibrated empirically and introduced in Phase 6.

```
Role                          Primary                  Fallback
─────────────────────────────────────────────────────────────────
schema_routing                local/qwen3:8b           —
json_parsing                  local/qwen3:8b           —
nli_prefilter                 local/qwen3:8b           —
connector_health              local/qwen3:8b           —
plain_verdict                 local/qwen3:8b           —
debate_bull                   local/qwen3:8b           groq/llama-4-scout

semantic_validation           groq/llama-4-scout       local/qwen3:8b
structured_extraction         groq/llama-4-scout       local/qwen3:8b
debate_compression            groq/llama-4-scout       local/qwen3:8b

strategy_generation  [C]      groq/qwen3-32b           groq/kimi-k2
improvement_analyzer [C]      groq/qwen3-32b           groq/kimi-k2
debate_bear                   groq/qwen3-32b           groq/kimi-k2

auditor_agent                 groq/kimi-k2             groq/qwen3-32b
adversarial_reasoning         groq/kimi-k2             groq/gpt-oss-120b

debate_moderator     [C]      groq/gpt-oss-120b        groq/kimi-k2
final_audit_score    [C]      groq/gpt-oss-120b        groq/kimi-k2

research_small                groq/qwen3-32b           groq/gpt-oss-120b
research_large                gemini-2.5-flash         groq/qwen3-32b
10k_ingestion                 gemini-2.5-flash         —
news_synthesis                gemini-2.5-flash         groq/qwen3-32b

overflow                      openrouter/:free         local/qwen3:8b
emergency                     claude-sonnet-4-6        —

[C] = Critical role — fallback triggers degraded session flag
```

### Provider Failover

```python
class ProviderRouter:
    def route(self, role: str, estimated_tokens: int) -> RoutingDecision:
        # Context size overrides role assignment
        if estimated_tokens > 50_000:
            if not self.quota.is_exhausted("gemini-2.5-flash"):
                return RoutingDecision(
                    provider="gemini-2.5-flash",
                    was_primary=True,
                    is_critical_role=role in CRITICAL_ROLES
                )

        preferred = STATIC_ROUTING_TABLE[role]
        provider, was_primary = self._first_available(preferred)

        return RoutingDecision(
            provider=provider,
            was_primary=was_primary,
            is_critical_role=role in CRITICAL_ROLES,
            fallback_reason=None if was_primary else "quota_exhausted"
        )

    def _first_available(self, preferred: str) -> tuple[str, bool]:
        if not self.quota.is_exhausted(preferred):
            return preferred, True
        chain = FALLBACK_CHAINS.get(preferred, []) + ["local/qwen3:8b"]
        for provider in chain:
            if not self.quota.is_exhausted(provider):
                return provider, False
        return "local/qwen3:8b", False
```

### Budget and Quota Tracking

```python
@dataclass
class ModelCallRecord:
    timestamp:            datetime
    provider:             str
    model:                str
    role:                 str
    tokens_in:            int
    tokens_out:           int
    estimated_cost:       float
    run_id:               str
    was_primary_model:    bool
    fallback_reason:      Optional[str]
    session_quality:      str
    quota_at_call:        dict
```

Glass Box Budget Dashboard: daily quota per Groq model, Gemini RPD across both devices, OpenRouter shared RPD, Claude total spend vs $20, routing distribution, and session quality distribution (what % of runs were nominal vs degraded).

### Context Management

Three rules for every agent call:

**Rule 1 — State object is the memory.** Every agent reads from `AegisState`, writes structured results back. No conversational history relied upon.

**Rule 2 — Compress before handoff.**

```python
def compress_to_schema(full_output: str, schema: Type[BaseModel]) -> BaseModel:
    result = fast_extractor.parse(full_output, schema)
    mlflow.log_artifact(full_output, artifact_path="agent_reasoning")
    return result
```

Without compression: 40 debate rounds × ~15K tokens = 600K tokens against Kimi K2's 300K TPD. With compression: ~80–120K tokens. This is load-bearing, not optional.

**Rule 3 — Inject only what the agent needs.** Task, relevant `AegisState` slice, last 2–3 decision log entries, current strategy. Not full pipeline history.

---

## PART IV: DETERMINISTIC STATE MACHINE

### AegisState

```python
class AegisState(TypedDict):
    mandate_profile:         MandateProfile
    user_intent:             UserIntent
    run_id:                  str
    created_at:              datetime

    # Flow control — framework only, never agents
    iteration_count:         int
    max_iterations:          int          # default 5, ceiling 7
    retry_count:             int          # per-node, max 3
    exit_reason:             Optional[str]

    # Strategy lifecycle
    current_config:          Optional[StrategyConfig]
    backtest_result:         Optional[BacktestResult]
    audit_result:            Optional[AuditResult]
    debate_verdict:          Optional[DebateVerdict]
    scenario_results:        Optional[ScenarioBatteryResult]
    promotion_decision:      Optional[PromotionDecision]

    # Token chain
    active_tokens:           dict[str, TokenRecord]

    # Provider state
    quota_state:             dict[str, QuotaDailyRecord]
    claude_budget_spent:     float
    session_quality:         str          # "nominal" | "degraded" | "severely_degraded"

    # Context continuity
    decision_log:            list[DecisionEntry]
    failure_context:         Optional[list[str]]

    # Audit
    audit_events:            list[AuditEvent]
    schema_version:          str
```

### Hard Exit Conditions

```python
def check_exit_conditions(state: AegisState) -> Optional[str]:
    if state["iteration_count"] >= state["max_iterations"]:
        return "max_iterations_reached"
    if state["iteration_count"] >= 2:
        if compute_improvement_delta(state) < 0.01:
            return "diminishing_returns"
    if count_promoted_strategies() >= 3:
        return "sufficient_strategies_promoted"
    if not state_changed_this_iteration(state):
        return "no_progress_detected"
    if state["claude_budget_spent"] > CLAUDE_BUDGET_SOFT_CEILING:
        tighten_routing_threshold(state)
    return None
```

### Backtest Runtime Model

**Quick Iteration Run** — pure NumPy/Pandas, no LLM calls, 2–10 minutes. Used for 80% of iterations. No FinDebate, no scenario battery. Explores the parameter space efficiently.

**Full Production Backtest** — 4–15 hours. Runs only at promotion boundaries. Includes full walk-forward validation, FinDebate, scenario battery, held-out evaluation.

A pipeline run from mandate to promoted Sentinel: 6–12 hours total across all iterations, dominated by 1–2 full production backtests.

**Operational requirements:** Run `caffeinate -i -s` before any production backtest. The pipeline writes MLflow checkpoints after every node. Interrupted runs resume from the last checkpoint — they do not restart.

### Pipeline Graph

```
START
  │
  ▼
[Supervisor]
  Reads MandateProfile + UserIntent
  Queries StrategyArchetypePool for exclusion context
  Model: Qwen3-32B (Groq)
  │
  ▼
[Builder]
  Assembles StrategyConfig from VCL components only
  Cannot write logic inline
  Model: Qwen3-32B → Kimi K2 fallback
  │
  ▼
[Schema Validator]
  Layer 1: Pydantic (milliseconds, no LLM)
  Layer 2: Semantic — Llama-4-Scout
  FAIL → retry++ → [Builder] (max 3)
  │ PASS
  ▼
[Quick Iteration Backtest]
  Pure math, no LLM
  FAIL → iteration++ → [Builder] with failure context
  PASS but not at threshold → loop to [Builder]
  PASS at threshold → continue
  │
  ▼
[Full Production Backtest]
  Generates backtest_token on success
  │
  ▼
[FinDebate Orchestrator]
  See Part IX for full spec including evidentiary rubric
  │
  ▼
[Bootstrap Scenario Battery]
  Pass rate ≥ 70% required
  FAIL → failing scenarios fed to Builder
  │ PASS
  ▼
[Promotion Gate]
  Deterministic math. No LLM.
  Holds strategy if session_quality != "nominal"
  FAIL → iteration++ → [Builder]
  │ PASS + promotion_token
  ▼
[MLflow Registry]
  Config versioned, StrategyArchetypePool updated
  │
  ▼
[Sentinel Deployment]
  Requires valid promotion_token
  │
  ▼
[Signal Card Queue]
  Freshness Validator active (see Part XII)
```

---

## PART V: VERIFIED COMPONENT LIBRARY (VCL)

### Core Principle

Agents can only use components that have passed import verification. They cannot write logic inline, call external APIs directly, or generate implementations from scratch. This eliminates the "faking it" failure mode — where an LLM writes plausible-looking but incorrect code inline because no real tool exists.

### Standard Interface

```python
class VCLComponent(ABC):
    component_id:      str
    version:           str
    role:              ComponentRole
    input_schema:      Type[BaseModel]
    output_schema:     Type[BaseModel]

    @abstractmethod
    def execute(self, input: BaseModel) -> BaseModel: ...

    @abstractmethod
    def health(self) -> HealthStatus:
        """Must complete within 5 seconds."""

    @property
    def compatibility_fingerprint(self) -> str:
        return sha256(
            str(self.input_schema.model_json_schema()) +
            str(self.output_schema.model_json_schema())
        ).hexdigest()[:16]

    def describe(self) -> str:
        """What it does, what it cannot do, known failure modes."""
```

### Five-Gate Import Verification

**Gate 1** — Schema compilation: valid Pydantic `BaseModel` subclasses
**Gate 2** — Health check: completes within 5 seconds, returns valid `HealthStatus`
**Gate 3** — Contract tests: 5 standard cases pass, 2 adversarial cases fail gracefully
**Gate 4** — Security scan: SCA, dependency vulnerabilities, secrets detection
**Gate 5** — Canary test: malformed input produces clean error, not crash

On pass: semantic version + SHA-256 hash assigned, registered in VCL manifest.
On fail: rejection report to Glass Box. Component cannot be used.

### Component Roles

```
DATA_SOURCE        — provides data
SIGNAL_GENERATOR   — conviction scores 0–1
GATE_CONDITION     — boolean pass/fail
CONTEXT_MODIFIER   — advisory only
RISK_OVERRIDE      — hard veto (requires human sign-off)
AUDITOR            — evaluates other components
SCENARIO_GENERATOR — generates synthetic scenarios
EXECUTOR           — external system interaction (requires human sign-off)
```

---

## PART VI: TOKEN MESSENGER PATTERN

### The Problem

LangGraph conditional edges are behavioral constraints — they live in the agent's action space and can be bypassed by a sufficiently confused model. The Token Messenger Pattern makes sequencing **structural** — a tool cannot execute without a cryptographically valid token generated by the preceding tool.

### Implementation

```python
@mcp.tool()
def run_backtest(config: BacktestConfig) -> BacktestResult:
    result = execute_backtest_deterministic(config)
    if result.passed_all_gates:
        token = secrets.token_urlsafe(32)
        _workflow_store["backtest_token"] = {
            "value":       token,
            "config_hash": sha256(config.json().encode()).hexdigest(),
            "issued_at":   time.time(),
            "expires_at":  time.time() + 3600,
            "consumed":    False
        }
        return BacktestResult(success=True, token=token, metrics=result.metrics)
    return BacktestResult(success=False, reason=result.failure_reason)


@mcp.tool()
def run_audit(config: BacktestConfig, backtest_token: str) -> AuditResult:
    stored = _workflow_store.get("backtest_token")
    if not stored:
        raise SequenceViolationError("No backtest_token")
    if stored["consumed"]:
        raise SequenceViolationError("Already consumed — single use only")
    if stored["value"] != backtest_token:
        raise SequenceViolationError("Token value mismatch")
    if sha256(config.json().encode()).hexdigest() != stored["config_hash"]:
        raise SequenceViolationError("Config modified — chain broken")
    if time.time() > stored["expires_at"]:
        raise SequenceViolationError("Token expired")

    stored["consumed"] = True
    result = execute_audit(config)
    if result.passed:
        audit_token = secrets.token_urlsafe(32)
        _workflow_store["audit_token"] = {
            "value": audit_token, "consumed": False,
            "config_hash": stored["config_hash"],
            "expires_at": time.time() + 3600
        }
        return AuditResult(success=True, token=audit_token, findings=result.findings)
    return AuditResult(success=False, findings=result.findings)

# evaluate_promotion requires audit_token → generates promotion_token
# deploy_sentinel requires promotion_token — terminal link
```

---

## PART VII: LAYERED I/O CONTRACTS

### Layer 1 — Structural Validation (Pydantic)

Milliseconds, zero cost. Catches type errors, missing fields, out-of-range values, mandate violations.

```python
class StrategyConfig(BaseModel):
    model_config = ConfigDict(strict=True)
    schema_version:     Literal["v7.0"]
    strategy_id:        str = Field(pattern=r"^strat_[a-z0-9]{8}$")
    mandate_profile_id: str
    asset_universe:     list[str] = Field(min_length=1, max_length=50)
    signal_gate:        SignalGateConfig
    position_sizing:    PositionSizingConfig
    exit_conditions:    ExitConditionConfig
    agent_pipeline:     list[str]

    @field_validator("asset_universe")
    @classmethod
    def validate_tickers_exist(cls, tickers):
        invalid = [t for t in tickers if not vcl_registry.ticker_exists(t)]
        if invalid:
            raise ValueError(f"Unknown tickers — cannot fake data: {invalid}")
        return tickers

    @model_validator(mode="after")
    def validate_against_mandate(self):
        mandate = MandateProfile.load(self.mandate_profile_id)
        if self.position_sizing.max_position_pct > mandate.max_position_pct:
            raise ValueError(
                f"Position sizing {self.position_sizing.max_position_pct:.1%} "
                f"exceeds mandate ceiling {mandate.max_position_pct:.1%}"
            )
        return self
```

**Schema versioning:** Every schema carries `schema_version: Literal["v7.0"]`. Migration functions keep historical audit logs readable across schema changes.

### Layer 2 — Semantic Validation (LLM-as-Judge)

Catches logically valid but financially impossible outputs.

```python
class SemanticValidationResult(BaseModel):
    is_valid:    bool
    confidence:  float = Field(ge=0.0, le=1.0)
    violations:  list[str]
    reasoning:   str    # always required

def validate_strategy_semantics(config: StrategyConfig) -> SemanticValidationResult:
    prompt = f"""
    Evaluate whether this strategy is logically coherent and financially sound.

    Strategy: {config.model_dump_json()}
    Mandate: {MandateProfile.load(config.mandate_profile_id)}
    User desire: {UserIntent.load(config.mandate_profile_id).raw_desire}

    REQUIRED: Identify at least one potential issue or limitation.
    "No issues found" is not acceptable.
    """
    return provider_router.call(
        role="semantic_validation",
        prompt=prompt,
        response_model=SemanticValidationResult
    )
```

---

## PART VIII: DATA INTEGRITY FOUNDATION

### Point-in-Time Discipline

Every record carries `event_ts` (when it happened) and `public_disclosure_ts` (when it became publicly available). Simulation uses only `public_disclosure_ts`. ChromaDB queries enforce: `public_disclosure_ts <= simulation_date`.

**The YFinance silent-restatement problem:** Standard APIs overwrite historical statements on restatement. The immutable filing ledger:

```
data/ledger/
├── sec_filings/{ticker}/
│   └── {edgar_accession_number}.json   ← NEVER overwritten
├── prices/
│   └── {ticker}_{date_range}.parquet   ← cached at download time
└── macro/
    └── FRED_{series}_{downloaded_at}.parquet
```

**On alpha decay and information speed:** Point-in-time discipline prevents look-ahead bias in backtesting — it ensures the simulation only uses information actually available at the simulated trade time. It does not address alpha decay in live trading. These are different problems. Aegis captures post-catalyst signal (momentum and positioning in the days after events), not pre-announcement alpha. The system will not outrace institutional traders with co-located servers to the first tick after an FDA ruling. This boundary is stated at intake and visible in the Glass Box on every Signal Card.

### Data Source Registry

```
Connector           Point-in-Time Field          Tier
────────────────────────────────────────────────────────
YFinance            market_close_ts              Core
FRED (ALFRED)       release_ts (vintage)         Core
SEC EDGAR           edgar_accession_ts           Core
Finnhub             published_ts                 Core
Congressional       disclosure_filing_ts         Core
FinBERT             Inherits from source         Core
Alpaca              bar_ts                       Plugin
OpenClaw            event_ts (live only)         World Monitor
Custom VCL          Required at import           SDK
```

---

## PART IX: FINDEBATE — ADVERSARIAL AUDITING

### The Bear Bias Problem and the Evidentiary Rubric

The Bear agent uses a significantly stronger model (Qwen3-32B, 32B parameters) than the Bull agent (Qwen3:8b, 8B parameters). This is intentional — conservative bias in strategy selection has asymmetric value in trading, where a bad trade loses real money and a missed trade loses only opportunity.

However, "more sophisticated" does not mean "more accurate." A 32B model is better at constructing fluent, complex-sounding arguments regardless of their validity. Without constraints, the Bear will win debates not because it is right but because it is more articulate. The Moderator, faced with a sophisticated Bear argument and a less articulate Bull argument, may consistently side with the Bear on rhetorical grounds rather than evidentiary ones.

The fix is constraining what counts as a valid argument. The Moderator evaluates arguments on an **evidentiary rubric**, not on argumentative quality:

```python
class DebateArgumentScore(BaseModel):
    argument_id:         str
    agent:               str   # "bull" | "bear"
    claim:               str
    evidence_type:       str   # "backtest_data" | "historical_analogy" |
                               # "cited_scenario" | "assertion_only"
    evidence_specific:   bool  # True if specific numbers/dates cited
    falsifiable:         bool  # True if the claim could in principle be wrong
    evidentiary_weight:  float # 0.0–1.0, set by rubric, not by quality
```

**Evidentiary weight by evidence type:**
```
backtest_data (specific numbers from this run):  1.0
historical_analogy (specific dates/periods):     0.8
cited_scenario (from scenario battery):          0.7
general_principle (no specific data):            0.3
assertion_only (no evidence):                    0.0
```

The Moderator is explicitly instructed: *"Score arguments by evidentiary weight, not by sophistication or fluency. A well-written assertion with no data is worth less than a clumsy citation of a specific backtest metric. A Bear argument that says 'liquidity sweeps are likely' without citing a specific historical instance from the backtest data scores 0.0 on evidentiary weight regardless of how convincingly it is argued."*

### Bear Win Rate Monitoring

Track Bear verdict rate over time in MLflow. If the Bear wins more than 70–75% of debates across a rolling 30-day window, the system is likely miscalibrated — either the evidentiary rubric is not being applied correctly or the debate structure is systematically biased. Surface this metric in the Glass Box and alert the user if the Bear win rate exceeds threshold for more than 7 consecutive days.

This is not a reason to automatically adjust the debate parameters. It is a signal for the user to review a sample of debate transcripts in the Debate Theater and determine whether the system is correctly rejecting bad strategies or incorrectly rejecting good ones.

```python
class DebateHealthMetrics(BaseModel):
    window_days:          int    # rolling window (default 30)
    total_debates:        int
    bear_wins:            int
    bull_wins:            int
    bear_win_rate:        float
    alert_threshold:      float  # default 0.75
    alert_triggered:      bool
    consecutive_days_over: int
```

### The Three Agents

**Bull Agent — Qwen3:8b local, thinking OFF, temp 0.7**

Zero network latency. Constructs the optimistic scenario.

Persona constraint: *"You are a long-only fund manager. You MUST find at least 3 compelling reasons this strategy succeeds. Every claim must cite specific data from the backtest results — round number, date range, or metric. Unanchored assertions will score zero. You are prohibited from dwelling on risks."*

**Bear Agent — Qwen3-32B (Groq), thinking ON, temp 0.9**

Adversarial pressure. Stronger model, intentional conservative bias.

Persona constraint: *"You are a short-seller who survived three market crashes. You are prohibited from saying anything positive. Find every way this strategy fails. REQUIRED: specific numerical evidence for every critique — a historical date range, a specific scenario from the battery, a specific metric from the backtest. 'This could fail' without data scores zero on the evidentiary rubric and will not influence the verdict."*

**Moderator — GPT-OSS-120B (Groq), temp 0.3**

Applies evidentiary rubric. Does not reward fluency.

```python
class DebateVerdict(BaseModel):
    confidence_score:         int = Field(ge=0, le=100)
    verdict:                  Literal["APPROVE", "REJECT", "REVISE"]
    bull_strongest_point:     str
    bear_strongest_point:     str
    deciding_factor:          str
    required_revisions:       list[str]
    debate_integrity:         Literal["CLEAN", "COMPROMISED"]
    bull_evidentiary_score:   float    # average weight across Bull's arguments
    bear_evidentiary_score:   float    # average weight across Bear's arguments
    moderator_model:          str
```

### Debate Structure and Context Compression

```
Round 1: Bull opens (250 token max, structured JSON with evidence citations)
         → compress_to_schema(DebateRound) → full reasoning to MLflow

Round 2: Bear responds, adds critiques with evidence
         → compress_to_schema(DebateRound) → full reasoning to MLflow

Round 3: Bull rebuts Bear's specific claims with counter-evidence
         → compress_to_schema(DebateRound) → full reasoning to MLflow

Round 4: Bear final argument
         → compress_to_schema(DebateRound) → full reasoning to MLflow

Moderator: Receives 4 compressed DebateRound objects
           Applies evidentiary rubric to each argument
           Produces DebateVerdict with evidentiary scores
```

**Anti-rubber-stamp enforcement:** If both agents argue the same position by Round 4, Moderator flags `debate_integrity: "COMPROMISED"` and issues `verdict: "REVISE"`. Both `bull_evidentiary_score` and `bear_evidentiary_score` are stored — if one is consistently near zero, the system is not getting productive debate from that agent.

---

## PART X: BOOTSTRAP SCENARIO GENERATOR

### Why Not WGAN-GP in Phase 5

WGAN-GP for financial time series requires: stable GAN architecture for temporal data, training data curation with macroeconomic covariates, a validation framework for "statistically plausible but distinct" scenarios, and a retraining schedule. On a 16GB Mac with no GPU, training is slow and hard to validate. WGAN-GP is Phase 6+.

Phase 5 uses **historical block bootstrap** — buildable in a week, produces adversarial scenarios by construction, uses the same `ScenarioBatteryResult` schema. When WGAN-GP is ready in Phase 6, it replaces this component behind the same VCL interface. No other code changes.

### Implementation

```python
class BlockBootstrapGenerator(VCLComponent):
    """
    Resamples non-overlapping blocks of historical returns.
    Preserves short-run autocorrelation within blocks.
    Disrupts long-run regime dependencies across blocks.
    Produces scenarios the backtest has not optimized against.
    """
    role = ComponentRole.SCENARIO_GENERATOR

    def execute(self, request: ScenarioRequest) -> ScenarioBattery:
        scenarios = []
        for _ in range(request.num_scenarios):
            blocks = self._sample_blocks(
                returns=self.return_history,
                block_size=request.block_size_days,
                total_length=request.scenario_length_days
            )
            scenarios.append(self._assemble_scenario(blocks, request.tickers))
        return ScenarioBattery(scenarios=scenarios)
```

```python
class ScenarioBatteryResult(BaseModel):
    scenarios_run:         int
    scenarios_passed:      int
    pass_rate:             float
    worst_case_drawdown:   float
    expected_shortfall_95: float
    battery_passed:        bool      # True iff pass_rate >= 0.70
    failing_scenarios:     list[ScenarioSummary]
    generator_type:        str       # "block_bootstrap" | "wgan_gp"
```

Failing scenarios inject context into the Builder for next iteration.

---

## PART XI: PROMOTION GATE

Standalone Python module. No LLM. No agent modifies thresholds. Reads from MLflow. Applies hard rules.

**Additional gate condition:** `session_quality == "nominal"`. Degraded sessions do not promote — they queue for re-evaluation when primary providers reset.

### Stage 1 — Backtest → Proving Ground

```python
BACKTEST_GATE = {
    "min_oos_sharpe":               1.0,
    "max_drawdown":                 0.15,
    "min_trades":                   100,
    "min_profit_factor":            1.3,
    "min_walk_forward_efficiency":  0.50,
    "max_correlation_existing":     0.60,
    "max_pvalue":                   0.05,
    "min_scenario_pass_rate":       0.70,
    "min_debate_confidence":        65,
    "required_session_quality":     "nominal",
}
```

### Stage 2 — Proving Ground → Live (small, max 10% allocation)

```python
PROVING_GROUND_GATE = {
    "min_observation_days":         30,
    "min_signals_generated":        5,
    "max_win_rate_degradation":     0.15,
    "max_drawdown_vs_backtest":     0.05,
    "max_signal_frequency_ratio":   3.0,
    "require_explicit_sign_off":    True,
}
```

### Stage 3 — Live (small) → Live (full)

```python
LIVE_EXPANSION_GATE = {
    "min_live_days":                60,
    "min_live_sharpe":              0.5,
    "max_circuit_breaker_triggers": 0,
    "min_positive_months":          2,
}
```

### Non-Configurable Invariants

- `held_out_degradation_max: 0.35` — permanent
- `max_circuit_breaker_triggers: 0` — one trigger = permanent disqualification
- Human must approve first live trade for every new strategy

---

## PART XII: SENTINEL LAYER AND SIGNAL CARDS

### Signal Types

**BUY Signal:** Full position spec — shares, dollar value, portfolio %, hold duration, price target, stop-loss. FinDebate confidence score, evidentiary scores for Bull and Bear, verdict. Scenario battery pass rate and worst-case drawdown. Model attribution including session quality. Track record anchored to held-out window only.

**CLOSE Signal — Five Exit Types:**
1. **Target Approached** — price within configured % of target
2. **Stop Triggered** — price crossed stop-loss
3. **Hold Duration** — exceeded maximum holding period
4. **Fundamental Shift** — requires EntryStateSnapshot comparison
5. **Risk Budget** — maintaining position would exceed remaining drawdown budget

### Signal Card Freshness Validator

A stale Signal Card for a volatile stock is a real harm. The Freshness Validator runs continuously while a Signal Card is displayed.

**On card display:** The validator pings a free price API (Finnhub or Alpaca free tier) and checks whether current mid-price is within the freshness threshold of the intended entry price.

**Freshness thresholds by volatility:**
```python
FRESHNESS_THRESHOLDS = {
    "low_volatility":    0.015,   # 1.5% — bonds, large-cap defensives
    "medium_volatility": 0.010,   # 1.0% — large-cap equities, ETFs
    "high_volatility":   0.007,   # 0.7% — mid-cap equities
    "speculative":       0.005,   # 0.5% — small-cap, biotech, crypto-adjacent
}
```

Volatility bucket is assigned at Sentinel deployment based on historical ATR.

**Validator behavior:**
```python
class SignalFreshnessState(BaseModel):
    is_fresh:              bool
    current_price:         float
    intended_entry:        float
    price_deviation_pct:   float
    freshness_threshold:   float
    last_checked_at:       datetime
    reeval_triggered:      bool

def validate_signal_freshness(signal: SignalCard) -> SignalFreshnessState:
    current = price_feed.get_mid_price(signal.ticker)
    deviation = abs(current - signal.intended_entry) / signal.intended_entry

    return SignalFreshnessState(
        is_fresh=(deviation <= signal.freshness_threshold),
        current_price=current,
        intended_entry=signal.intended_entry,
        price_deviation_pct=deviation,
        freshness_threshold=signal.freshness_threshold,
        last_checked_at=datetime.utcnow(),
        reeval_triggered=(deviation > signal.freshness_threshold * 2)
    )
```

**ACCEPT button states:**
- **Active (green):** Current price within freshness threshold. User can accept.
- **Stale (amber):** Price moved beyond threshold. ACCEPT disabled. Card shows: *"Price moved [X]% from intended entry. Re-evaluating entry parameters."* System re-runs signal generation using current price. If the trade still makes sense at the new price, ACCEPT re-enables with updated parameters.
- **Invalid (red):** Price moved beyond 2× threshold. ACCEPT disabled permanently for this card. System evaluates whether to generate a new Signal Card at current price.

The check runs every 30 seconds while the card is displayed. For speculative names (small-cap biotech), the check runs every 15 seconds.

**For degraded session cards:** ACCEPT remains disabled regardless of freshness until the strategy has been re-evaluated under nominal conditions. Freshness validation and session quality validation are independent — both must pass.

### Signal Card UI

```
┌───────────────────────────────────────────────────────────────┐
│  SENTINEL: [name]       [timestamp]      [session: NOMINAL]   │
├───────────────────────────────────────────────────────────────┤
│  📈  BUY — [TICKER]                                           │
│                                                               │
│  [X shares] @ ~$[price] = $[value]  ([Y%] of portfolio)      │
│  Hold: [range]    Target: $[T]    Stop: $[S]                 │
│                                                               │
│  ─── Price Freshness ───────────────────────────────────────│
│  Current: $[live_price]   Entry: $[intended]   ✓ Fresh       │
│  Last checked: [N] seconds ago                               │
│                                                               │
│  ─── FinDebate ─────────────────────────────────────────────│
│  Confidence: [N]/100   Verdict: APPROVED                     │
│  Bull score: [X]/1.0 evidentiary   Bear score: [Y]/1.0       │
│  Bull: [strongest evidenced point]                           │
│  Bear: [strongest evidenced point]                           │
│  Decided by: [deciding factor]                               │
│                                                               │
│  ─── Scenario Battery ──────────────────────────────────────│
│  Passed: [X]/[total]   Worst case: -[Y]%   ES95: -[Z]%      │
│                                                               │
│  ─── Track Record (held-out window only) ───────────────────│
│  Sentinel: [X]/[Y] profitable ([Z]% win rate)               │
│  Backtest held-out: [A]% win rate, avg [B]% per trade        │
│                                                               │
│  ─── Execution ─────────────────────────────────────────────│
│  ℹ Aegis captures post-catalyst signal, not pre-announcement │
│  Copy to your brokerage:                                      │
│  Qty: [X shares]   Limit: ~$[price]   Stop: $[S]            │
│  Take-profit: $[T] (set as separate order if available)      │
│                                                               │
│  ⚠ AI-generated signal. Not financial advice.               │
│                                                               │
│             [ ACCEPT ]           [ DECLINE ]                 │
└───────────────────────────────────────────────────────────────┘
```

If session quality was degraded, the card instead shows:

```
│  ⚠ DEGRADED SESSION — ACCEPT DISABLED                       │
│  This signal was generated when primary reasoning models     │
│  were unavailable. Re-evaluating under normal conditions.    │
│  ACCEPT will be enabled after re-evaluation.                 │
```

### On Manual Execution

The system does not connect to any brokerage API. Automated order placement at the direction of an AI system creates regulatory and liability exposure. The human manually executes in their own brokerage account. This is a deliberate product boundary.

The most error-prone step — order entry — remains human. To reduce transcription errors, Signal Cards present a formatted execution block with exact values in copy-friendly format. Stop-loss and target are displayed as separate brokerage order parameters. Future versions may offer a screenshot-optimized order summary the user can reference while placing the trade.

### ACCEPT/DECLINE Flow

- **ACCEPT:** Paper portfolio executes at next available price. Human replicates in brokerage.
- **DECLINE:** Paper portfolio executes hypothetically. Counterfactual P&L tracked permanently.

After 5 consecutive ACCEPTs without reviewing debate details, a nudge: *"You've accepted 5 in a row. Want to review the reasoning on this one?"* Not a block.

---

## PART XIII: OPENCLAW WORLD MONITOR

### Architecture

Dedicated Linux box. Systemd daemon. Gemini 2.5 Flash (250 RPD, separate Google project). Full internet access. No Aegis processes on this device.

### Authenticated Communication

An unauthenticated POST endpoint that can trigger Tier 3 escalations and Close Signal evaluation is unacceptable from a device with full internet access. Shared secret Bearer token authentication on both endpoints:

```python
OPENCLAW_API_SECRET = os.environ["OPENCLAW_API_SECRET"]

@app.get("/api/sentinel/known_universe/{sentinel_id}")
async def get_known_universe(
    sentinel_id: str,
    authorization: str = Header(None)
):
    if authorization != f"Bearer {OPENCLAW_API_SECRET}":
        raise HTTPException(status_code=401)
    return sentinel_state_manager.get_known_universe(sentinel_id)

@app.post("/api/sentinel/event_card")
async def receive_event_card(
    event: EventCard,
    authorization: str = Header(None)
):
    if authorization != f"Bearer {OPENCLAW_API_SECRET}":
        raise HTTPException(status_code=401)
    return event_card_handler.process(event)
```

Secret set as environment variable on both devices at deployment. Never in source code. Never transmitted over the internet. Communication is over the local network between devices only.

### Known Universe

```json
{
  "sentinel_id": "string",
  "generated_at": "ISO8601",
  "holdings": [{
    "ticker": "string",
    "thesis": "string",
    "entry_price": 0.0,
    "entry_date": "ISO8601",
    "position_pct": 0.0,
    "dependency_map": {
      "commodity_inputs": [],
      "geographic_risk": [],
      "macro_sensitivities": [],
      "key_customers": [],
      "regulatory_exposure": []
    }
  }],
  "macro_watches": [],
  "upcoming_events": [{
    "event": "string",
    "datetime": "ISO8601",
    "importance": "critical|high|medium",
    "promote_to_active_hours_before": 24,
    "watch_after_hours": 2
  }],
  "prediction_markets": {
    "polymarket_api": "https://gamma-api.polymarket.com",
    "kalshi_api": "https://api.elections.kalshi.com/trade-api/v2",
    "alert_threshold": 0.07,
    "topics_to_watch": []
  }
}
```

### Security Configuration

- `sessionTarget: "isolated"` — clean session per run
- ClawHub blocked — only pre-audited local skills
- No raw credentials — all data via authenticated Mac endpoints
- No internal Aegis database access

### Heartbeat Protocol

```
Wake schedule:
  active   (7 min)  — event within 2 hours OR Tier 3 detected
  watching (20 min) — market hours, no imminent events
  idle     (2 hrs)  — after hours
  dormant  (4 hrs)  — overnight 8pm–4am ET, weekends

Pre-filter (free, before Gemini call):
  1. Price moves since last heartbeat (local calc)
  2. Economic calendar (cached, < 1 API call/day)
  3. Prediction market deltas vs memory (free API)
  Nothing flags → HEARTBEAT_OK, sleep. Zero Gemini cost.

Budget:
  Standard day:   ~35-50 calls
  FOMC day:       ~60-80 calls
  Earnings day:   ~50-70 calls
  Hard ceiling:   250 RPD
```

### Prediction Markets

**Polymarket:** `https://gamma-api.polymarket.com/markets?keywords=<topic>&active=true`
**Kalshi:** `https://api.elections.kalshi.com/trade-api/v2/markets?status=open&keyword=<topic>`

Both free, no authentication for read-only access. Local price memory tracks last-seen probabilities. Alert when market moves > `alert_threshold` since last check.

### Event Tiers

```
Tier 1 — Log only
  Routine notes, price moves < 2%, no direct holding impact
  Action: Local log only

Tier 2 — Event Card (user decides)
  Earnings within 24hrs, macro releases, prediction market
  moves > threshold, commodity moves > 5%
  Action: POST event_card with auth
  Options: IGNORE | FLAG | FULL ANALYSIS

Tier 3 — Immediate escalation
  CEO/CFO departure (held co.), regulatory action, earnings
  miss > 10%, trading halt, Taiwan escalation, fraud/DOJ
  Action: POST immediately with auth
          Sentinel enters REVIEW mode
          Close Signal evaluation triggered
```

---

## PART XIV: GLASS BOX — AUDIT TRAIL AS PRODUCT

The Glass Box is the primary interface. The human is not building anything — watching the AI work transparently is the product.

### Audit Event Schema

```python
class AuditEvent(BaseModel):
    event_id:             str
    trace_id:             str
    timestamp:            datetime
    event_type:           str
    agent_id:             str
    schema_version:       str
    action:               str
    reasoning:            str       # always required
    inputs:               dict
    outputs:              dict
    model_provider:       str
    model_name:           str
    role:                 str
    was_primary_model:    bool
    fallback_reason:      Optional[str]
    session_quality:      str
    tokens_in:            int
    tokens_out:           int
    estimated_cost:       float
    token_consumed:       Optional[str]
    token_generated:      Optional[str]
    validation_passed:    bool
    validation_errors:    list[str]
    confidence:           Optional[float]
    debate_scores:        Optional[DebateArgumentScore]
```

### Progressive Disclosure

**Level 0** — Single line: *"FinDebate approved Strategy #7 (confidence: 82, Bear evidentiary: 0.71)"*
**Level 1** — Three sentences. Key decision, evidence quality, outcome.
**Level 2** — Full debate transcript, evidentiary scores per argument, backtest charts, scenario results.
**Level 3** — Complete JSON, schema validation, token chain, all provider attribution including fallback decisions.

### Narrative Feed

Generated once at run completion. Stored as MLflow artifact. No LLM at render time. Includes session quality, evidentiary scores, and the product boundary note for catalyst-driven strategies.

### Key Glass Box Metrics

- **Bear Win Rate** — rolling 30-day, alert if > 75% for 7+ consecutive days
- **Session Quality Distribution** — % nominal vs degraded vs severely degraded
- **Evidentiary Score Distribution** — Bull and Bear average scores over time
- **Freshness Invalidation Rate** — % of Signal Cards that went stale before user action
- **Budget Dashboard** — quota utilization per provider, Claude total spend

---

## PART XV: FRONTEND — VISUAL PIPELINE INTERFACE

### Stack

React + Vite + TypeScript + TailwindCSS + React Flow (`@xyflow/react`) + Zustand + TanStack Virtual + Lightweight Charts + Three WebSocket channels

### Sidebar

```
AEGIS AI
├── OBSERVE
│   ├── Mission Control     Sentinels, Signal Cards, event feed
│   ├── Portfolio Tracker   mirror portfolio, counterfactuals
│   └── System Health       connectors, quotas, budgets
│
├── PIPELINE
│   ├── Visual Map          live canvas (Phase A — now)
│   ├── Component Library   VCL browser, import
│   └── Flow Editor         interactive editing (Phase B — Phase 6)
│
├── ANALYZE
│   ├── Glass Box           audit trail, narrative, graph
│   ├── Arena               MLflow runs, leaderboard
│   ├── Debate Theater      transcripts, evidentiary scores, replay
│   └── Budget Dashboard    quota, routing, spend, session quality
│
└── SETTINGS
    ├── Intake              view and update mandate
    ├── Connectors          API keys, health config
    └── World Monitor       OpenClaw status, subscriptions
```

### Phase A — Live Monitoring Map (Build Now)

Read-only. Observation only.

**Node types:** Component nodes (name, role, status, latency sparkline, provider badge), Data nodes (click for JSON inspector), Token nodes (gold chain, TTL countdown), Model nodes (provider badge, quota remaining, `was_primary_model` indicator).

**Live behaviors:** Blue pulse when executing, particle flow on active edges, red flash on validation failure, agent dialogue overlays, gold token chain propagation, amber/red provider badge when fallback triggers.

**Red flags:**
- Schema validation failure
- VCL component health failure
- Connector DEGRADED or OFFLINE
- FinDebate COMPROMISED
- Circuit breaker trigger
- Any Groq model > 90% daily quota
- Claude > 75% budget consumed
- Sequence violation attempt
- Session quality degraded (amber badge on run)
- Session quality severely degraded (red badge)
- Bear win rate alert

### Phase B — Interactive Flow Editor (Phase 6)

~6 weeks after Phase A is stable and VCL SDK proven. Drag-and-drop component swap with fingerprint compatibility enforcement, live wiring with schema validation, chat control with confirmation and versioned provenance.

---

## PART XVI: HARDWARE CONFIGURATION

### 16GB Mac (Aegis Core)

```
Local model:   qwen3:8b (~5.0 GB)
OLLAMA_MAX_LOADED_MODELS=1
Peak usage:    ~11–15 GB (comfortable)
```

**Quick iteration:** Safe anytime.
**Production backtest:** Close React dev server. Run `caffeinate -i -s`. 4–15 hours.
**Upgrade path:** 32GB → change `qwen3:8b` to `qwen3:14b` in one config line.

### Linux Box (OpenClaw)

OpenClaw systemd daemon only. Gemini 2.5 Flash (separate Google project, own 250 RPD). Full internet access. Isolated from Aegis network except two authenticated endpoints.

### Provider Routing Config

```json
{
  "routing": {
    "mode": "static_with_quota_aware_fallback",
    "context_size_threshold_tokens": 50000,
    "context_override_provider": "gemini-2.5-flash",
    "exclude_models": ["deepseek/*"],
    "critical_roles": [
      "strategy_generation", "debate_moderator",
      "final_audit_score", "improvement_analyzer"
    ],
    "roles": {
      "schema_routing":        "local/qwen3:8b",
      "json_parsing":          "local/qwen3:8b",
      "nli_prefilter":         "local/qwen3:8b",
      "connector_health":      "local/qwen3:8b",
      "plain_verdict":         "local/qwen3:8b",
      "debate_bull":           "local/qwen3:8b",
      "semantic_validation":   "groq/llama-4-scout",
      "structured_extraction": "groq/llama-4-scout",
      "debate_compression":    "groq/llama-4-scout",
      "strategy_generation":   "groq/qwen3-32b",
      "improvement_analyzer":  "groq/qwen3-32b",
      "debate_bear":           "groq/qwen3-32b",
      "auditor_agent":         "groq/kimi-k2",
      "debate_moderator":      "groq/gpt-oss-120b",
      "final_audit_score":     "groq/gpt-oss-120b",
      "10k_ingestion":         "gemini-2.5-flash",
      "news_synthesis":        "gemini-2.5-flash",
      "research_large":        "gemini-2.5-flash",
      "research_small":        "groq/qwen3-32b",
      "emergency":             "claude-sonnet-4-6"
    },
    "fallback_chains": {
      "groq/qwen3-32b":     ["groq/kimi-k2", "groq/gpt-oss-120b",
                             "openrouter/qwen3-235b:free", "local/qwen3:8b"],
      "groq/kimi-k2":       ["groq/qwen3-32b", "groq/gpt-oss-120b",
                             "openrouter/qwen3-235b:free", "local/qwen3:8b"],
      "groq/gpt-oss-120b":  ["groq/kimi-k2",
                             "openrouter/qwen3-235b:free", "local/qwen3:8b"],
      "groq/llama-4-scout": ["local/qwen3:8b"],
      "gemini-2.5-flash":   ["groq/qwen3-32b", "local/qwen3:8b"]
    }
  }
}
```

---

## PART XVII: FAILURE MODES

### 1. Backtest Overfitting

Walk-forward validation (min 6 folds, efficiency ≥ 50%) + scenario battery (pass rate ≥ 70%) + held-out partition (20%, sealed, `held_out_degradation_max: 0.35`). All three required.

### 2. Knight Capital-Style Runaway

Circuit breakers in a **separate process** with read-only position access:
```
5%  drawdown → reduce all positions 50%
10% drawdown → close all positions
15% drawdown → kill switch
20% drawdown → system disabled, manual code-level restart required
```

### 3. Builder Gaming the Auditor

Randomize which Trading Constitution principles the Bear checks each cycle. Track audit pass rate — alarm if consistently > 80% without OOS improvement. Inject canary strategies to verify Auditor catches them. Track Bear win rate (alarm > 75% for 7+ consecutive days).

### 4. Model Collapse

Monitor cosine similarity of strategy feature vectors (alarm > 0.70). Monitor entropy of strategy types (alarm if declining). `StrategyArchetypePool` prompt injection drives exploration — `max_correlation_existing: 0.60` gate is the hard backstop.

### 5. Provider Cascade Failure

Fallback chain handles individual exhaustion. Degraded session handling prevents silent quality degradation. Groq-less degradation mode is documented. Terminal fallback to local Qwen3:8b means the pipeline never stops — it degrades.

### 6. Stale Signal Execution

Freshness Validator continuously checks price deviation while Signal Card is displayed. ACCEPT disabled if price moves beyond volatility-adjusted threshold. Strategy re-evaluated at new price if deviation exceeds 2× threshold.

### 7. Debate Bias Producing Bad Rejections

Bear Win Rate metric (rolling 30-day) surfaced in Glass Box. Alert if > 75% for 7+ consecutive days. Evidentiary rubric prevents rhetorical quality from overriding data quality in Moderator scoring.

---

## PART XVIII: INVARIANTS

- No AI agent modifies Promotion Gate thresholds
- No AI agent modifies its own iteration counter
- No AI agent disables or modifies circuit breakers
- No AI agent deploys to live trading without a valid promotion_token
- No AI agent executes a live trade — only the human executes in their brokerage
- The Builder never sees the held-out partition
- The Backtest Engine never accesses data beyond simulation date
- OpenClaw never connects to Aegis databases directly
- Both OpenClaw endpoints require Bearer token authentication
- The World Monitor never runs in backtesting mode
- No ClawHub skills without local pre-audit and VCL import verification
- No custom engine `run()` executes outside Docker sandbox
- No prompt patches applied silently
- FinDebate "no issues found" is not a valid result
- DeepSeek models never receive Aegis data
- MandateProfile is frozen at intake confirmation
- Degraded sessions never produce promoted strategies
- ACCEPT is disabled on degraded session Signal Cards until re-evaluation
- ACCEPT is disabled on stale Signal Cards until freshness restored

---

## PART XIX: BUILD ORDER

### Completed (Phases 1–3.5)
Point-in-time enforcement, Config Schema, Fundamental Engine, Simulation Loop, Metrics Calculator, MLflow logging, Signal Gate, LangGraph integration, Model Routing, Improvement Analyzer, Subprocess Sandbox, Holdout Partition, Semantic versioning, Lineage Ledger, Audit Chat, Session Logs

### In Progress (Phase 4)
Connector Health Monitor, DeBERTa NLI, Sentinel State Manager, Mirror Portfolio Tracker, Close Signal Generator, Promotion Gate, Plugin Layer, World Monitor wiring

### Phase 5 — v7 Pivot

**5.1 — Intake System**
Path A UI, Path B schema import + validation, Intent Parser, contradiction detection, MandateProfile + UserIntent, StrategyArchetypePool, intake product boundary messaging

**5.2 — VCL SDK**
`VCLComponent` abstract class, `compatibility_fingerprint`, `health()`, five-gate import pipeline, role system, VCL manifest

**5.3 — Multi-Provider Static Routing**
`ProviderRouter`, `QuotaTracker`, critical role classification, degraded session detection, `session_quality` tracking, fallback chain, `ModelCallRecord` logging

**5.4 — Token Messenger Pattern**
MCP server, `_workflow_store`, cryptographic tokens, consume-and-generate cycle, config hash validation

**5.5 — FinDebate with Evidentiary Rubric**
Bull/Bear/Moderator, `DebateArgumentScore`, evidentiary weight rubric, `compress_to_schema()`, Bear Win Rate metric, anti-rubber-stamp enforcement, `DebateVerdict` with `bull_evidentiary_score` and `bear_evidentiary_score`

**5.6 — Bootstrap Scenario Generator**
`BlockBootstrapGenerator` VCL component, scenario battery, failing scenario feedback loop

**5.7 — Signal Card Freshness Validator**
Price feed integration (Finnhub/Alpaca free tier), volatility-bucketed thresholds, ACCEPT button state machine, stale card re-evaluation flow, 15/30 second polling

**5.8 — Provider Integration**
Groq API client, Gemini API client (separate Mac/Linux projects), OpenRouter client (DeepSeek excluded), LiteLLM unified interface, OpenClaw endpoint authentication

### Phase 5A — Frontend
React Flow canvas, WebSocket integration, live node status, degraded session badges, Freshness Validator UI, Bear Win Rate alert, Budget Dashboard with session quality distribution

### Phase 6 — Future
Interactive Flow Editor, RouteLLM (after MLflow data accumulates), WGAN-GP (replaces block bootstrap behind same VCL interface)

---

## PART XX: CHANGELOG v6.1 → v7.0

| Decision | v6.1 | v7.0 | Reason |
|----------|------|------|--------|
| User entry | Strategy Wizard | Two-path intake | Meet users where they are |
| Input model | Thesis-first | Desire-first ("what do you want to trade") | Honest about retail psychology |
| Schema import | None | Path B with LLM intake doc | Captures existing AI conversation context |
| Strategy creation | Human-designed | AI-generated | Remove human bottleneck |
| Diversity | Gate only (post-hoc) | ArchetypePool prompt injection (pre-generation) | Gate catches; prompt causes |
| Model routing | Static 5-factor | Static table (RouteLLM Phase 6) | No training data yet |
| Model pool | Qwen3:8b + Claude | Six-provider free tier | $20 lasts ~15–20 years |
| Moderator | Claude | GPT-OSS-120B (free) | Frontier quality at zero cost |
| Bear agent | Symmetric capability | Stronger model, intentional | Conservative bias is a feature |
| Bear debate quality | Capability-driven | Evidentiary rubric + win rate monitoring | Prevents rhetorical bullying |
| Scenario testing | Curated date ranges | Block bootstrap (WGAN-GP Phase 6) | Buildable now, same interface |
| Sequencing | LangGraph edges | Token Messenger (cryptographic) | Cannot be bypassed |
| Degraded sessions | Not addressed | Held pending re-eval, flagged | Silent quality degradation is unacceptable |
| Signal freshness | Not addressed | Live validator, ACCEPT disabled if stale | Stale biotech card is a real harm |
| OpenClaw auth | Unauthenticated | Shared secret Bearer token | Prevents fake event card injection |
| Alpha speed | Implied | Explicitly bounded at intake | Honest about what Aegis captures |
| Context continuity | Conversation history | AegisState + MLflow | Was always stateless — now explicit |
| Manual execution | Signal Card only | Signal Card + formatted execution block | Reduce transcription error |

---

*Aegis AI v7.0 — The human captures the desire. The AI builds, audits, and deploys. The human executes the trade.*
