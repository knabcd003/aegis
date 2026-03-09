# Phase 4 — Sentinel Layer

> **Status:** ⬜ Not started — blocked on Phase 3
> **Primary blueprint reference:** §4.2.1, §8 (entire section), §7.4
> **Prerequisite:** All Phase 3 done conditions met.

---

## What This Phase Builds

The live deployment layer. A promoted Sentinel manages a real paper portfolio against live market data, generates Signal Cards, tracks accept/decline decisions, and maintains the Mirror Portfolio counterfactual. The Proving Ground enables live paper trading before promotion.

---

## Build Order

### Step 21 — Connector Health Monitor
**File:** `engines/monitoring/connector_health.py`
- `last_successful_fetch_ts` on every connector (already required in Phase 1 — verify in place)
- Health check coroutine running every 4 hours (daily connectors) / 30 minutes (real-time)
- Three states: `MONITORING`, `DEGRADED`, `OFFLINE`
- **Asymmetry rule:** when ambiguous, downgrade. False `DEGRADED` = annoying notification. Silent stale data = product integrity failure.
- `OFFLINE` suspends Signal Card generation **immediately** — not just flagged

### Step 22 — Segment Obfuscation NLI Check
**File:** `engines/fundamental/segment_anchor.py`

Two-stage process at each new 10-Q ingest:

**Stage 1 — DeBERTa-v3-large cross-encoder (runs on every filing):**
```python
from sentence_transformers import CrossEncoder
_nli_model = CrossEncoder("cross-encoder/nli-deberta-v3-large")  # singleton, loaded at startup

result = classify_segment_change(historical_label, candidate_text)
# returns: 'ENTAILMENT' | 'NEUTRAL' | 'CONTRADICTION'
```

| Result | Action |
|---|---|
| `ENTAILMENT` | Extract normally. Qwen not invoked. |
| `NEUTRAL` | Wake Qwen 8B for constrained JSON confirmation. |
| `CONTRADICTION` | Wake Qwen 8B for full extraction. Queue re-anchoring alert. Suspend monitoring. |

**Stage 2 — Qwen 8B (only on NEUTRAL or CONTRADICTION):**
Constrained JSON output: `{equivalent_metric_found, proposed_replacement, change_type: "cosmetic"|"structural", confidence}`

**Stage 3 — Human re-anchoring:** Suspend monitoring, surface Re-Anchoring Alert. Monitoring resumes only on explicit user confirmation, logged to MLflow.

**The `_nli_model` singleton must already be loaded** — initialized in Phase 1 at SEC EDGAR connector startup.

### Step 23 — Sentinel State Manager
**File:** `engines/sentinel/state_manager.py`
- Tracks all deployed Sentinels with locked config version
- Runs complete signal pipeline against live data continuously
- Queues Signal Cards for user review
- Manages paper portfolio NAV in real time
- Any config modification → new version required → must pass Full Production Backtest before new version can be promoted

### Step 24 — Mirror Portfolio Tracker
**File:** `engines/sentinel/mirror_portfolio.py`
- Paper account initialized at user-declared capital at promotion time
- Tracks every position, every Signal Card accept/decline
- Counterfactual P&L tracked for every declined signal:
  - BUY declined → paper opens hypothetically, tracks outcome, real unchanged
  - CLOSE declined → paper closes, real holds past exit, cost tracked
- Gap analysis report: paper NAV vs. real account NAV + where the gap came from

### Step 25 — Close Signal Generator (all 5 exit types)
**File:** `engines/sentinel/close_signal_generator.py`
Five exit condition types — all must work:
1. **Target approached** — price reached configured target
2. **Stop triggered** — price hit configured stop-loss
3. **Hold duration** — position exceeded max configured hold
4. **Fundamental shift** — requires `EntryStateSnapshot` from Step 26
5. **Risk budget** — maintaining position would exceed drawdown budget

**EntryStateSnapshot** stored at position open (see §8.4.1 for full spec):
```python
@dataclass
class EntryStateSnapshot:
    position_id: str
    ticker: str
    opened_at: datetime
    earnings_revision: float
    insider_activity: str
    finbert_score: float
    gate_conditions_met: Dict[str, Any]   # conditions that passed at entry
    custom_engine_states: Dict[str, Any]  # custom engine outputs at entry
    thresholds: Dict[str, float]          # divergence thresholds from config
```

Continuous comparison on each live day: if any gate condition diverges beyond its threshold → Fundamental Shift close signal.

### Step 26 — Promotion Gate Evaluator
**File:** `engines/sentinel/promotion_gate.py`
- Runs current configuration against the sealed held-out window for the first time
- Shows both windows side by side before user confirms
- If `held_out_degradation > held_out_degradation_max (0.35 Sharpe)`: promotion blocked. **Not configurable.**
- `held_out_sharpe_min (0.85)` also non-configurable
- Promotion logs the held-out result to MLflow

**Promotion version lock:** `write_full_promotion_artifact()` is associated with the **specific MLflow Run ID** that passed the promotion gate. If the user re-runs the same config later, a new artifact is NOT generated — the promotion artifact belongs to the run that was actually promoted. The Glass Box always reads from the run ID recorded at promotion time.

**Proving Ground criteria** (enforced before promotion option shown):
```json
{
  "min_observation_days": 30,
  "min_signals_generated": 5,
  "max_win_rate_degradation": 0.15,
  "max_drawdown_vs_backtest": 0.05,
  "max_signal_frequency_ratio": 3.0,
  "require_explicit_sign_off": true
}
```
Shortfalls require explicit acknowledgment (logged to MLflow) — they do not block promotion.

### Step 27 — Plugin Layer
**File:** `engines/plugins/__init__.py` + wiring
- HMM, VPIN, Chronos, Alpaca — all pre-exist in `engines/quant/`
- Wire them into simulation loop as optional context contributors
- All OFF by default — require explicit `enabled: true` in config
- Context-only in signal output: never displayed as raw scores, always plain-language in Signal Card expanded section
- Tier 2+ required for HMM, VPIN; Tier 3 only for Day Trader/Alpaca template

---

## Done Conditions for Phase 4

- [ ] Connector Health Monitor transitions `DEGRADED`/`OFFLINE` correctly with asymmetry rule
- [ ] `OFFLINE` suspends Signal Card generation — verified with test that forces connector failure
- [ ] **DeBERTa NLI Stage 1** returns ENTAILMENT/NEUTRAL/CONTRADICTION correctly on test cases
- [ ] **Qwen Stage 2 only invoked** on NEUTRAL or CONTRADICTION — not on ENTAILMENT
- [ ] Re-anchoring alert surfaced on CONTRADICTION + structural NEUTRAL
- [ ] Human re-anchoring required before monitoring resumes — confirmed with test that skips acknowledgment
- [ ] All 5 Close Signal types trigger correctly in test scenarios
- [ ] `EntryStateSnapshot` stored at position open and used in Fundamental Shift comparison
- [ ] Mirror Portfolio: accept/decline recording works, counterfactual P&L tracked
- [ ] Gap analysis: paper vs. real NAV breakdown shows where gap originated
- [ ] Promotion Gate blocks on `held_out_degradation > 0.35` — confirmed non-configurable
- [ ] **Promotion version lock:** `full_reasoning_trace.jsonl` associated with promoted Run ID only — not regenerated on re-run
- [ ] Proving Ground sign-off logged to MLflow with acknowledgment timestamp
- [ ] All plugins remain OFF by default — verified by checking default config templates
