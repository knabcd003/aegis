# Phase 3 — Custom Engine SDK

> **Status:** ⬜ Not started — blocked on Phase 2
> **Primary blueprint reference:** §5 (entire section)
> **Prerequisite:** All Phase 2 done conditions met.

---

## What This Phase Builds

The formal SDK that allows users to integrate their own models, data sources, and signal logic as first-class engines. Custom engines participate in Glass Box logging, health monitoring, and MLflow attribution identically to built-in engines.

---

## Build Order

### Step 16 — BaseEngine Abstract Class
**File:** `engines/sdk/base_engine.py`

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime

@dataclass
class EngineInput:
    tickers: List[str]
    as_of_date: datetime
    data_snapshot: Dict[str, Any]   # point-in-time enforced externally
    config: Dict[str, Any]
    prior_outputs: Dict[str, Any]

@dataclass
class EngineOutput:
    signals: Dict[str, Any]         # {ticker: value}
    signal_type: str                # "conviction" | "boolean" | "context" | "veto"
    reasoning: Dict[str, Any]       # logged verbatim to Glass Box
    metadata: Dict[str, Any]        # engine_id, version, duration_ms, model_hash

@dataclass
class EngineHealth:
    last_successful_run_ts: datetime
    last_error: Optional[str]
    avg_run_duration_ms: float
    custom_status: Optional[str]

class BaseEngine(ABC):
    engine_id: str      # required class attribute
    engine_name: str    # required class attribute
    version: str        # required class attribute
    role: str           # DATA_SOURCE | SIGNAL_GENERATOR | GATE_CONDITION | CONTEXT_MODIFIER | RISK_OVERRIDE

    @abstractmethod
    def describe(self) -> str: ...      # plain-language description for Glass Box

    @abstractmethod
    def run(self, input: EngineInput) -> EngineOutput: ...

    @abstractmethod
    def health(self) -> EngineHealth: ...
```

Five valid roles and how the pipeline treats each:
- `DATA_SOURCE` — provides additional snapshot data, cannot gate
- `SIGNAL_GENERATOR` — conviction score 0–1, can be added as gate condition
- `GATE_CONDITION` — boolean pass/fail, directly participates in signal gate
- `CONTEXT_MODIFIER` — advisory context to Analyst Engine, cannot gate
- `RISK_OVERRIDE` — hard veto authority identical to Risk Agent. **Requires explicit user confirmation at wizard step.**

### Step 17 — Custom Engine Registry
**File:** `engines/sdk/registry.py`
- Load registered engines from config directory
- Validate each engine via the registration sequence (Step 18)
- Make registered engines available to simulation loop and health monitor
- Engine appears in Engine Library under `/engines/custom` after successful registration

### Step 18 — Registration + Validation Sequence
**CLI command:** `aegis engine register ./my_engine.py --validate`

Validation sequence — all must pass:
1. Import and instantiate wrapper (catch dependency errors)
2. `engine.describe()` returns non-empty string
3. `engine.health()` returns valid `EngineHealth` object
4. Single Quick Iteration backtest (90-day, 1 ticker) — `EngineOutput` produced without exceptions
5. If all pass: engine registered. If any fail: registration blocked with specific error.

### Step 19 — Execution Sandbox (Security)

**Why this is non-optional:** Without isolation, a custom `.py` file runs in the same process as the application that holds all API keys. A malicious or compromised engine can read `.env`, make outbound calls, and exfiltrate credentials. The user believes they're running a backtest.

**Phase 3 — Subprocess enforcement (ship with Phase 3):**
**File:** `engines/sdk/sandbox_wrapper.py`

Every `run()` call executes in a restricted subprocess:
- Import allowlist: `numpy`, `pandas`, `scikit-learn`, `torch` (CPU-only), `scipy`
- No network access blocked at subprocess level
- `sys.path` restricted to venv — no access to application modules or `.env`
- Any import outside the allowlist raises `ImportRestrictionError` — run aborts, user notified
- `datetime.now()` calls intercepted and blocked (lookahead prevention)
- Violation raises `LookaheadViolation` exception

**Phase 3b — Docker isolation (production target, follow-up):**

```bash
docker run \
  --network none \
  --read-only \
  --memory 512m \
  --cpus 1.0 \
  --env-file /dev/null \
  aegis-engine-runner
  # EngineInput serialized via stdin → EngineOutput returned via stdout
```

- `--network none` — no outbound or inbound connections
- Read-only filesystem + no host env vars = no key access
- Resource caps prevent runaway engine from consuming host
- ~200ms startup overhead acceptable for daily-bar backtests
- Day Trader template: pre-warm container, keep alive across ticks

Phase 3b is not shipped simultaneously with Phase 3. Ship Phase 3 (subprocess), then upgrade to Docker once the subprocess enforcement is validated.

### Step 20 — Glass Box Custom Engine Rendering
- Every `EngineOutput.reasoning` dict logged verbatim to MLflow alongside built-in agent traces
- Glass Box view: each custom engine renders as collapsible section with `describe()` as header tooltip
- Visual format matches built-in agent sections — no distinction in the audit trail

### Custom Engine Health Monitor Integration
- Health check coroutine calls `engine.health()` on same schedule as connectors (every 4 hours)
- If `last_successful_run_ts` exceeds staleness threshold: Sentinel → `DEGRADED`
- Consistent failures: Sentinel → `OFFLINE`, signal generation suspended
- Custom engines define their own staleness thresholds via `BaseConnector` (if acting as data source)

---

## Reference Implementation
**File:** `engines/sdk/examples/momentum_engine.py`

A complete working example of a custom engine implementing all four methods. Used in the registration validation Quick Run to confirm the SDK works end-to-end.

---

## Done Conditions for Phase 3

- [ ] `BaseEngine`, `EngineInput`, `EngineOutput`, `EngineHealth` importable from `aegis.sdk`
- [ ] Registration CLI works: `aegis engine register ./my_engine.py --validate`
- [ ] All 4 validation steps run in sequence — specific error on any failure
- [ ] **Subprocess sandbox** blocks imports outside allowlist (`ImportRestrictionError` raised)
- [ ] **Subprocess sandbox** blocks `datetime.now()` calls (`LookaheadViolation` raised)
- [ ] `sys.path` restriction confirmed — engine cannot import app modules or read `.env`
- [ ] `RISK_OVERRIDE` role requires explicit confirmation — wizard blocks without it
- [ ] Custom engine `reasoning` dict appears in MLflow trace verbatim
- [ ] Glass Box renders custom engine section with `describe()` tooltip
- [ ] Health monitor calls `engine.health()` on schedule — `DEGRADED`/`OFFLINE` propagated
- [ ] Reference momentum engine passes full registration validation sequence
- [ ] Phase 3b Docker spec documented and ticketed for follow-up upgrade
