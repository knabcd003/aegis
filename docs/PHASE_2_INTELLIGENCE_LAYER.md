# Phase 2 — Intelligence Layer

> **Status:** ⬜ Not started — blocked on Phase 1
> **Primary blueprint reference:** §4.5, §6.2, §6.7, §10
> **Prerequisite:** All Phase 1 done conditions met.

---

## What This Phase Builds

The LangGraph reasoning layer wired into the simulation loop. Signal gate events that passed in Phase 1's vectorized run now invoke the Analyst Engine. The Model Routing Layer controls whether each Supervisor call goes to Claude or Qwen — all development in Build Mode so Claude spend is $0.

---

## Build Order

### Step 7 — Signal Gate Finalization
- Wire signal gate output from Phase 1 into the Phase 2 event queue
- Every gate-passing event in the Phase 1 simulation now queues a LangGraph invocation for Phase 2
- Gate rate (% of days that pass) logged to MLflow as `signal_gate_rate`

### Step 8 — Model Routing Layer
**File:** `engines/routing/router.py`
- Three modes: `build` (Qwen always, $0), `validate` (budget-aware), `production` (Claude always)
- Mode is explicit in config: `routing.mode`
- Current routing mode always visible — log it to MLflow at run start
- **Default for all development: Build Mode**

```python
def route_supervisor(u_score: float, config: dict, budget_tracker) -> str:
    if config["routing"]["mode"] == "build":
        return "qwen2.5:8b"
    if config["routing"]["mode"] == "production":
        return "claude-sonnet-4-6"
    # validate mode: budget-aware
    if u_score >= config["validation"]["min_uncertainty_threshold"] and budget_tracker.remaining > 0:
        budget_tracker.reserve(ESTIMATED_CLAUDE_COST_PER_CALL)
        return "claude-sonnet-4-6"
    return "qwen2.5:8b"
```

### Step 9 — Uncertainty Scorer
**File:** `engines/routing/uncertainty_scorer.py`
- Five-factor score (0.0–1.0): signal gate margin, sub-agent disagreement, episodic memory precedent, position size materiality, macro regime novelty
- **These weights are starting priors — not calibrated.** See §10.3.1 for calibration process.
- Pure math — no LLM call
- Score logged to MLflow per gated event

### Step 10 — Budget Allocator + Cost Tracker
**File:** `engines/routing/budget_tracker.py`
- Per-run declared budget from config (`validation.claude_budget_usd`)
- `budget_exhausted_behavior`: `fallback` (default), `pause`, `stop`
- Real-time remaining balance available to the routing layer
- Cost attribution logged per call: `{event_id, uncertainty_score, supervisor_model, supervisor_cost}`

### Step 11 — LangGraph Integration (Analyst Engine)
**Files:**
- `engines/analyst/agents/research_agent.py` — ChromaDB query + 10-Q synthesis
- `engines/analyst/agents/sentiment_agent.py` — FinBERT scores + news narrative
- `engines/analyst/agents/risk_agent.py` — position constraints, drawdown budget, macro check. **Veto is hard — overrides all other agents.**
- `engines/analyst/agents/context_ceiling_node.py` — **no LLM** — runs before Supervisor, counts tokens, truncates if > 3,500 using `trim_messages(strategy="last")`
- `engines/analyst/supervisor.py` — routes to Claude or Qwen per routing decision. Produces BUY/CLOSE + position spec + reasoning chain.
- `engines/analyst/episodic_memory.py` — rolling record of past signals and outcomes for Supervisor self-calibration

**Simulation loop change:** Phase 1 loop extended — on gate-passing events, invoke Analyst Engine instead of logging gate pass only.

All sub-agents use local model only (`qwen2.5:8b`). Only the Supervisor uses the routing decision.

**Three context window management requirements (non-optional):**

1. **ChromaDB retrieval cap: 3 chunks maximum.** One-line config change in the Research Agent. The 4th and 5th chunks are noise that inflate the KV cache without changing Supervisor conclusions.

2. **Context ceiling node before every Supervisor call.** Add a `context_ceiling_node` to the LangGraph graph that runs between the sub-agents and the Supervisor. Count tokens in accumulated state. If > 3,500 tokens: drop oldest sub-agent outputs using `LangChain.trim_messages(strategy="last", max_tokens=3500)`. Supervisor always receives the most recent sub-agent conclusions, never a truncated partial output.

3. **Sub-agents return structured JSON to Supervisor context. Full prose goes to MLflow only.** The Supervisor context receives compact structured summaries (~50 tokens). The full reasoning prose is logged verbatim to MLflow as a separate artifact. This distinction must be explicit in every agent's prompt design and output schema.

   Example Risk Agent Supervisor output:
   ```json
   {"approved": true, "position_within_limits": true, "drawdown_budget_remaining_pct": 0.67, "veto": false}
   ```

   Example Risk Agent MLflow artifact (full prose, not in Supervisor context):
   ```
   "The proposed position in MSFT at $412.50 representing 8.3% of declared capital is within the
    configured 15% maximum. Current portfolio drawdown is 2.1% against a 7% budget ceiling,
    leaving 4.9% remaining. The Risk Agent approves this position."
   ```

**Memory math:** 3 chunks × 512 tokens = 1,536 tokens (Research Agent). Three sub-agents at ~50 tokens each = 150 tokens. Prompt instructions ~300 tokens. EntryStateSnapshot ~200 tokens. Total: ~2,186 tokens — well below the 3,500 ceiling with headroom for Supervisor output. KV cache: ~1.1GB. Fits comfortably in 16GB headroom.

### Step 12 — Improvement Analyzer
**File:** `engines/improvement/analyzer.py`
- Runs after every Full Production Backtest
- Receives: trade P&L log, signal gate events, sub-agent vote log, LLM alpha contribution
- Produces two proposal types:
  - **Parameter Proposal** — specific, testable, with `expected_delta`
  - **System Insight** — structural finding with evidence and options
- Constrained JSON output schemas — no free-form reasoning
- Every proposal logged to `proposal_decision_log.jsonl` with `{proposal_id, proposed_by, outcome, time_to_decision_seconds, user_value, user_notes}`
- **Sees optimization window only — never the held-out window**

### Step 13 — Scenario Library
**File:** `engines/simulation/scenario_library.py`
- Deterministic date-range mappings (never LLM-generated — see Trap 2 in blueprint)
- All scenario instances from §6.2 (`rising_rate_environment`, `market_crash`, `high_volatility`)
- Runs full pipeline over exact calendar dates using real data
- Post-scenario decomposition: Qwen 2.5 8B analyzes structured results with constrained prompt
- Show survival rates across all instances, not just most recent
- MLflow tag: `run_type=scenario`

### Step 14 — Quick Iteration Run Mode
- 90-day window, up to 3 tickers, Phase 1 only (no LangGraph)
- Completes in 2–10 minutes
- Claude never invoked (Build Mode behavior regardless of config)
- MLflow tag: `run_type=quick_iteration`
- This is the direction-validation tool before committing to a full 4–15 hour production run

### Step 15 — Pre-Run Cost Estimator
**File:** `engines/routing/cost_estimator.py`
- Before any Full Production Backtest: estimate gated events, high-uncertainty fraction, Claude spend
- Uses historical signal gate rates from prior MLflow runs for the config; uses template defaults for first run
- Display in Sandbox UI before user confirms launch (Phase 5 frontend)

### Step 6b — MLflow Tiered Logging Configuration
**File:** `engines/simulation/mlflow_logger.py` (update from Phase 1)

Add tiered trace depth and artifact tiering per `logging.depth` config field:

| Run Type | Trace Depth | Logged |
|---|---|---|
| `quick_iteration` | minimal | Config + metrics. No traces. |
| `production` / `scenario` | production | Config + metrics + top-level Supervisor output per event. |
| `debug` | full | Full autolog. Explicit opt-in. **Block if disk < 5GB.** |

Default for all runs: `production`. Never `debug` by default.

At promotion: `write_full_promotion_artifact()` generates `full_reasoning_trace.jsonl` for the promoted run's MLflow Run ID. This file is written once and permanently associated with that run ID. Never regenerated.

Artifact routing:
- Regular runs: `config.json`, `metrics.json`, `portfolio_nav.csv`, `plain_verdict.md`, `proposal_log.jsonl`, `cost_log.jsonl`, `recommendation_trace.jsonl` (top-level only)
- Promotion only: `full_reasoning_trace.jsonl` (complete sub-agent reasoning per gated event)

---

## Done Conditions for Phase 2

- [ ] Build Mode confirmed $0 Claude spend across 10 test runs
- [ ] Uncertainty Scorer returns scores 0.0–1.0 per the five-factor formula
- [ ] Budget tracker correctly halts Claude invocations when budget exhausted (`fallback` behavior)
- [ ] LangGraph produces BUY/CLOSE + full position spec on gated events
- [ ] Risk Agent veto correctly suppresses signal regardless of other agent votes
- [ ] Sub-agent model attribution (`model_used`) logged on every Supervisor output
- [ ] **Context ceiling node** truncates correctly at 3,500 tokens — verified with an oversized context test case
- [ ] **Sub-agent outputs to Supervisor are structured JSON** — prose only in MLflow artifact
- [ ] **ChromaDB returns max 3 chunks** — confirmed by retrieval test
- [ ] Improvement Analyzer generates both proposal types with constrained JSON schemas
- [ ] Proposal decision log schema is populated after each production backtest
- [ ] Scenario Library runs at least 3 scenario types against real historical data
- [ ] Quick Iteration Run logs config + metrics only (no traces)
- [ ] Production runs log top-level Supervisor output only (no sub-agent spans)
- [ ] Debug mode blocked if disk < 5GB
- [ ] `write_full_promotion_artifact()` generates full trace once at promotion, associated with that run's MLflow ID
- [ ] Cost estimator produces estimate before run — actual spend within 20% of estimate
