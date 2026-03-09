# Phase 1 — Mathematical Foundation

> **Status:** 🔨 Current build phase
> **Primary blueprint reference:** §4.2, §3.3, §4.3, §6.3, §6.4, §6.5, §7
> **Dependency:** Everything in Phases 2–5 is built on top of this. Get it right before moving on.

---

## What This Phase Builds

The complete mathematical layer of Aegis — no LLM calls, no agent reasoning. Just correct data, correct configuration, a vectorized simulation loop, and honest performance metrics logged to MLflow.

When this phase is done you can run a full backtest over 2 years of real data on 5 tickers, get performance metrics you trust, and see them logged in MLflow. That's the bar.

---

## What Already Exists (Inherited)

The following connectors exist in `engines/data_ingestion/connectors/` and are usable **but need to be audited and patched**:

| Connector | File | Gap vs. v6 Requirement |
|---|---|---|
| YFinance | `yfinance_connector.py` | Missing `public_disclosure_ts`. Fetches live data — no immutable local cache. |
| FRED | `fred_connector.py` | Needs `release_ts` field. FRED is exempt from immutable ledger (ALFRED vintage data). |
| SEC EDGAR | `sec_edgar_connector.py` | Needs `edgar_accession_ts`. Must store by accession number, never overwrite. |
| Finnhub | `finnhub_connector.py` | Needs `published_ts`. |
| Congressional | Missing | Does not exist yet. Must enforce `disclosure_filing_ts`, never `trade_date`. |
| FinBERT | `finbert_connector.py` | Inherits timestamp from source — verify this is enforced. |

**The `SandboxOrchestrator` in `engines/sandbox/orchestrator.py` is deprecated** — it uses mock data, VPIN-first logic, and Optuna sweeps over a hardcoded NVDA scenario. It is pre-v6 architecture. Do not extend it. It will be replaced by the new simulation loop built in this phase.

**The quant models** (`hmm_model.py`, `vpin_calculator.py`, `portfolio_optimizer.py`, `chronos_forecaster.py`) are Plugin Layer components per v6 — they are off by default and not part of Phase 1. Leave them in place for Phase 2+.

---

## Build Order

Work through these in order. Do not start step N+1 until step N passes its done condition.

---

### Step 1 — `public_disclosure_ts` Enforcement

**What:** Patch every existing connector to attach `public_disclosure_ts` to every returned record. Add the immutable local cache for SEC EDGAR and YFinance fundamentals.

**Files to modify:**
- `engines/data_ingestion/connectors/yfinance_connector.py`
- `engines/data_ingestion/connectors/fred_connector.py`
- `engines/data_ingestion/connectors/sec_edgar_connector.py`
- `engines/data_ingestion/connectors/finnhub_connector.py`
- `engines/data_ingestion/connectors/finbert_connector.py`

**Files to create:**
- `engines/data_ingestion/connectors/congressional_connector.py` — STOCK Act disclosures. `disclosure_filing_ts` only. Never `trade_date`.
- `engines/data_ingestion/base_connector.py` — Add `public_disclosure_ts: datetime` as a required field on the return contract.
- `data/ledger/` directory structure:
  ```
  data/ledger/
  ├── sec_filings/{ticker}/{accession_number}.json   ← immutable; never overwritten
  ├── prices/{ticker}_{start}_{end}.parquet          ← cached at download time
  └── macro/FRED_{series}_{downloaded_at}.parquet    ← FRED snapshot
  ```

**Key rules:**
- YFinance price data: cache at download time. Simulation queries hit local cache, not live API.
- SEC EDGAR: store by accession number with `edgar_accession_ts`. New restated filing = new accession number = new file. Old files never touched.
- FRED: ALFRED vintage data is trustworthy. No immutable cache required. Query live during simulation.
- Congressional: `disclosure_filing_ts` = the STOCK Act filing date (up to 45 days after trade). The 45-day delay is a feature. Use it.

**NLI Model Startup:** The `cross-encoder/nli-deberta-v3-large` model (~183MB) used in Trap 1 / segment obfuscation detection is loaded **once at application startup as a singleton**. Do not reload per filing or per query. Load it in the SEC EDGAR connector's `__init__` and hold it in memory. Startup cost: ~2-3 seconds. Per-call cost: ~1ms on CPU.

```python
from sentence_transformers import CrossEncoder
_nli_model = CrossEncoder("cross-encoder/nli-deberta-v3-large")  # singleton
```

**Done when:** Every connector method returns a dict or DataFrame where every row has `public_disclosure_ts` populated. Unit tests confirm no record with `public_disclosure_ts > simulation_date` can be returned when queried with `as_of_date`. `_nli_model` loads once and is reused across all filing ingest calls.

---

### Step 2 — Configuration Schema

**What:** The configuration is the atomic unit of the platform. Load, validate, and version it.

**File to create:** `config/schema.py`

```python
# Minimal required fields — see §3.3 of aegis_v6.md for full spec
REQUIRED_FIELDS = [
    "config_id", "version", "asset_universe.tickers", "asset_universe.benchmark",
    "fundamental_engine.earnings_revision.enabled",
    "fundamental_engine.insider_monitor.enabled",
    "position_sizing.capital", "position_sizing.max_position_pct",
    "sandbox.slippage_bps", "sandbox.promotion_criteria.held_out_sharpe_min",
    "sandbox.promotion_criteria.held_out_degradation_max",
    "routing.mode"
]
```

**File to create:** `config/manager.py` — loads JSON config, validates required fields, assigns a `config_fingerprint` (SHA256 hash of the config dict), manages version increments.

**Done when:** `ConfigManager.load("config/tech_breakout_v1.json")` returns a validated config object with `config_fingerprint`. Invalid configs raise `ConfigValidationError` with the specific missing field.

---

### Step 3 — Fundamental Engine

**What:** The primary signal generation layer. No LLM. Pure data processing.

**Files to create:**
- `engines/fundamental/earnings_revision_tracker.py`
- `engines/fundamental/insider_activity_monitor.py`
- `engines/fundamental/macro_overlay.py`
- `engines/fundamental/signal_gate.py`
- `engines/fundamental/__init__.py`

**Earnings Revision Tracker:**
- Input: Finnhub estimate revisions for a ticker, `as_of_date`
- Output: `{direction: "up"|"down"|"flat", magnitude: float, analyst_count: int, momentum: "accelerating"|"decelerating"|"stable"}`
- Point-in-time: only revisions with `published_ts <= as_of_date` are visible

**Insider Activity Monitor:**
- Input: SEC Form 4 + Congressional filings for a ticker, `as_of_date`, config window
- Output: `{insider_type: str, transaction: "BUY"|"SELL", cluster_buy: bool, cluster_size: int, cluster_window_days: int}`
- Point-in-time: `edgar_accession_ts <= as_of_date` for Form 4; `disclosure_filing_ts <= as_of_date` for Congressional

**Macro Overlay:**
- Input: FRED series (T10Y2Y, FEDFUNDS, credit spreads), `as_of_date`
- Output: `{macro_regime: "tightening"|"easing"|"stable", yield_curve: "inverted"|"flat"|"normal", credit_spread_trend: "widening"|"tightening"|"stable"}`
- This is context only — not a gate condition by itself

**Signal Gate:**
- Input: Fundamental Engine outputs + FinBERT score, gate config from `config.signal_gate`
- Output: `True` (gate passed — invoke LangGraph) or `False` (skip this ticker/day)
- Must support: `require_earnings_revision_direction`, `require_insider_activity`, `finbert_above`, arbitrary custom conditions (for Phase 2 custom engine extension)

**Done when:** `signal_gate.evaluate(signals, config.signal_gate)` returns correct boolean for all test cases in the unit test suite.

---

### Step 4 — Simulation Loop

**What:** The vectorized day-by-day backtest engine. Phase 1 only (no LLM).

**File to create:** `engines/simulation/loop.py`

Key implementation requirements:
1. **Held-out partition at run start** — 20% of trading days randomly partitioned and sealed before any processing begins. Seed = `run_id` for reproducibility. Logged to MLflow immediately.
2. **Point-in-time snapshot per day** — `data_engine.get_snapshot(tickers, as_of=date)` returns only records with `public_disclosure_ts <= date`.
3. **Signal gate before any agent call** — the signal gate is evaluated in Phase 1 (vectorized). Gate-passing events are logged but LangGraph is not called in Phase 1.
4. **Slippage injection on every trade:**
   - Bid-ask spread: 10 bps (half-spread per side)
   - Market impact: 5 bps per $10k notional
   - Execution latency: fill at next bar open, not current bar close
   - Partial fills: applied above 2% of daily volume
5. **Portfolio state tracking** — position ledger, NAV history, trade log.

```python
def run_phase1_backtest(config: dict, run_id: str) -> dict:
    """
    Phase 1: vectorized, no LLM. Returns metrics dict + trade log.
    Phase 2 (LangGraph) wires in on top of this in Phase 2 of the build.
    """
```

**Done when:** 2-year backtest on 5 tickers completes in under 60 seconds. NAV history, trade log, slippage drag all present in the output dict.

---

### Step 5 — Performance Metrics

**What:** All metrics from §6.5 of aegis_v6.md.

**File to create:** `engines/simulation/metrics.py`

Must compute:
- Total Return, CAGR, Sharpe (annualized), Sortino, Max Drawdown
- Win Rate, Avg Win / Avg Loss, Alpha vs. Benchmark, Beta
- Avg Hold Duration, Signal Gate Rate, Slippage Drag
- **Optimization Window Sharpe** (80% window) and **Held-Out Sharpe** (20% window — computed separately)

**Done when:** All metrics match hand-calculated values on a 10-trade test portfolio. Held-out metrics computed correctly from the sealed partition.

---

### Step 6 — MLflow Extended Logging

**What:** Every production backtest run must be fully logged and reproducible.

**File to create:** `engines/simulation/mlflow_logger.py`

Must log:
- **Params:** `config_fingerprint`, full `config.json` as artifact, `holdout_dates` (sealed immediately at run start)
- **Metrics:** all from Step 5, both optimization window and held-out window
- **Artifacts:**
  - `portfolio_nav.csv` — daily NAV
  - `trade_log.jsonl` — trade-by-trade with slippage breakdown
  - `signal_gate_events.jsonl` — every gate pass/fail per ticker per day
  - `config.json` — exact config that produced this run
- **Proposal Decision Log** — empty at Phase 1, but the log schema must be set up from day one: `{proposal_id, proposed_by, target_param, proposed_value, outcome, user_value, time_to_decision_seconds, user_notes}`
- **Cost Attribution Log** — empty at Phase 1 (no LLM calls), but schema in place: `{event_id, uncertainty_score, supervisor_model, supervisor_cost, signal, confidence}`

**Done when:** After a Phase 1 backtest run, `mlflow ui` shows a complete run with all params, metrics, and artifacts. Running the same config twice produces identical results (reproducibility from `run_id` seed).

---

## Folder Structure After Phase 1

```
engines/
├── data_ingestion/
│   ├── base_connector.py          [PATCHED — public_disclosure_ts required]
│   └── connectors/
│       ├── yfinance_connector.py  [PATCHED — immutable cache]
│       ├── fred_connector.py      [PATCHED — release_ts]
│       ├── sec_edgar_connector.py [PATCHED — accession ledger]
│       ├── finnhub_connector.py   [PATCHED — published_ts]
│       ├── finbert_connector.py   [PATCHED — inherits source ts]
│       └── congressional_connector.py  [NEW]
├── fundamental/
│   ├── __init__.py                [NEW]
│   ├── earnings_revision_tracker.py  [NEW]
│   ├── insider_activity_monitor.py   [NEW]
│   ├── macro_overlay.py              [NEW]
│   └── signal_gate.py                [NEW]
├── simulation/
│   ├── __init__.py                [NEW]
│   ├── loop.py                    [NEW — Phase 1 vectorized backtest]
│   ├── metrics.py                 [NEW]
│   └── mlflow_logger.py           [NEW]
└── quant/                         [UNTOUCHED — Phase 2 Plugin Layer]
config/
├── schema.py                      [NEW]
├── manager.py                     [NEW]
└── templates/
    ├── tech_breakout_v1.json      [NEW — see §16 of blueprint]
    ├── insider_conviction_v1.json [NEW]
    └── conservative_etf_v1.json  [NEW]
data/
└── ledger/                        [NEW — immutable filing store]
    ├── sec_filings/
    ├── prices/
    └── macro/
```

---

## Done Conditions for Phase 1

All of these must be true before starting Phase 2:

- [ ] Every connector returns `public_disclosure_ts` on every record
- [ ] Querying any connector with `as_of_date` returns zero records with `public_disclosure_ts > as_of_date`
- [ ] SEC EDGAR filings stored by accession number — re-running the same backtest produces the same data
- [ ] Congressional connector enforces `disclosure_filing_ts`, tested with known STOCK Act filings
- [ ] `ConfigManager.load()` validates required fields and raises on missing ones
- [ ] `config_fingerprint` is logged to MLflow at run start
- [ ] Signal gate correctly passes/fails on all test cases
- [ ] 2-year Phase 1 backtest runs in under 60 seconds on 5 tickers
- [ ] Held-out partition is sealed at run start, logged to MLflow, and cannot be queried during simulation
- [ ] All 12 performance metrics compute correctly
- [ ] Slippage drag is always present in outputs — never shown without it
- [ ] MLflow run is fully reproducible from `config_fingerprint` + `run_id`
- [ ] Proposal decision log and cost attribution log schemas are in place (empty but structured)
