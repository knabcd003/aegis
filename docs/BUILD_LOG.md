# Aegis AI — Build Log

> Comprehensive record of every build phase, what was built, and key decisions made.

---

## Phase 0: Original Prototype (Complete — Archived)
**Date:** Feb 2026
**Status:** ⚠️ Nuked — replaced by v2 architecture

Built a basic LangGraph trading system with 4 agents (Researcher, Quant, Analyst, Sentinel), hardcoded to Alpaca + FMP APIs, and a React dashboard. Served as proof-of-concept but was too rigid and limited for production use.

**What existed:**
- `agents/` — 4 Python agent files (researcher, quant, analyst, sentinel)
- `tools/` — AlpacaClient + FMPClient + TradingCalculators
- `memory/` — SQLite trade log + ChromaDB thesis store
- `graph/` — LangGraph workflow (linear chain)
- `api.py` — FastAPI with 10 endpoints (several returned mock data)
- `frontend/` — React dashboard with 9 components

**Why nuked:** Architecture wasn't designed for the scope we're building. Hardcoded to two paid APIs, no NLP pipeline, no regime detection, no pluggable data sources, half the API returned mock data. Research report defined a fundamentally different system.

**What survived:** `index.css` (design system), `config/` (user prefs), `.env`, `.gitignore`, Vite project scaffolding.

---

## Phase 1: Data Ingestion Engine (Completed)
**Date:** Mar 3, 2026
**Status:** ✅ Complete

### Completed
- **`base_connector.py`** — Abstract connector interface.
- **`yfinance_connector.py`** — Prices, fundamentals, news, financial statements, options chains, insider activity.
- **`data_engine.py`** — Central registry + fallback routing + Parquet/JSON cache + DuckDB SQL query layer.
- **`fred_connector.py`** — Macro indicators (Fed funds, CPI, GDP, unemployment, yield spread). 
- **`finbert_connector.py`** — Local CPU NLP sentiment scoring (Hugging Face ProsusAI/finbert).
- **`sec_edgar_connector.py`** — CIK lookup, 10-K/10-Q filing lists, full text + section extraction. No API key needed.
- **`finnhub_connector.py`** — Earnings transcripts, real-time news, calendar events (requires key).
- **`alpaca_connector.py`** — Backup prices + paper trade execution (requires key).

### Key Decisions
- **yfinance over FMP** — Covers fundamentals + prices + news in one free library. Eliminated FMP dependency entirely.
- **Pluggable connector pattern** — Each data source is one file implementing `BaseConnector`. Adding a source = adding one file, nothing else changes.
- **Parquet + DuckDB for storage** — Columnar files + in-process SQL. No server needed.

---

## Future Phases (Planned)

---

## Phase 2: Intelligence Layer & Orchestration (Completed)
**Date:** Mar 10, 2026
**Status:** ✅ Complete

### Completed
- **`health.py`** — High-fidelity infrastructure audit (Memory + 2-stage inference latency).
- **`AgenticSupervisor` (Dynamic Mesh)** — Decoupled orchestrator that builds LangGraph DAGs from JSON strategy manifests.
- **Node Registry** — Flexible mapping of strings to agent classes.
- **Connectivity Check** — Post-compilation DFS verification to prevent dangling nodes and runtime hangs.
- **`qwen3:8b` Support** — Validated local LLM inference via Ollama.

### Key Decisions
- **Manifest-Based DAG vs Hardcoded Graph** — Decoupling logic from code allows users to reconfigure agent sequences (e.g., adding/removing a Risk Manager) without a single line of Python change.
- **Pre-Flight Health Audit** — Catching memory/latency issues *before* backtests start prevents hours of wasted compute on a failing system.
- **DFS Connectivity Verification** — Essential for a dynamic DAG where a user-defined JSON could easily result in infinite loops or dangling states.

---

## Phase 3: Improvement Analyzer (Completed)
**Status:** ✅ Complete

### Completed
- **`glass_box.py` & `improvement_agent.py`** — Analyzes MLflow traces and generates targeted one-parameter scalar mutations (e.g. SL from 0.05 -> 0.02) to optimize strategy performance.
- Evaluates `held_out_degradation` vs in-sample Sharpe ratio to prevent structural overfitting.
- Backtracks when degrading boundaries are crossed.

---

## Phase 4: Sentinel Engine & VCL Wrappers (Completed)
**Status:** ✅ Complete

### Completed
- **Core Sentinel Components**: `CloseSignalGenerator`, `PromotionGate`, `MirrorPortfolio` (Counterfactual Tracker), `SentinelStateManager`.
- **Pre-Flight Health Checks**: `ConnectorHealthMonitor`, `SegmentClassifier`.
- **VCL Wrapper Implementation**: All 6 Phase 4 evaluation actors wrapped using the Vectorized Component Library (VCL) SDK, strictly exposing `input_schema` and `output_schema` Pydantic contracts.

---

## Phase 5: Production Architecture (In Progress)
**Status:** 🔨 Building

### Phase 5.1: Intake System (Complete)
- **`MandateProfile` & `UserIntent`** — Risk/Stop-Loss tier constraints properly validated & coerced.
- **Contradiction Detection** — Explicit rules block unaligned requests.
- **`StrategyArchetypePool`** — Persisted JSON diversity tracker measuring cosine-similarity distance against active strategies. Injected into Supervisor to force diverse strategy generation.

### Phase 5.2: Multi-Provider Router (Complete)
- **`ProviderRouter` & `QuotaTracker`** — YAML-defined model fallbacks separating semantic generation, compression, and mathematical roles to exact LLMs (`claude`, `qwen3:8b`, `qwen3-32b`, `gpt-oss-120b`, `llama-4-scout`). Guaranteed unlimited local fallback terminals.

### Phase 5.3: VCL Registry & Pydantic Payloads (Complete)
- Built the `VCLRegistry` to automatically compile `model_json_schema()`. 
- Implemented payload instantiation (`_generate_minimal_valid_dict`) generating schema-native objects (like strictly bounded floats and lists) to automatically run Contract AND Canary component tests without failure. Fixed `test_components.py` dependencies. Supported Fingerprint verification over JSON serialization.

### Phase 5.4: Token Messenger Pattern (Complete)
- **Ephemeral State**: `WorkflowToken` is a cryptographically secured (SHA256 config hashing), 1-hour TTL, single-use `consumed` credential.
- **Cryptographic Sequencing**: `BACKTEST -> AUDIT -> PROMOTION -> DEPLOYMENT` enforces strict state progression. Impossible to skip stages, replay old tokens, or drift configurations across boundaries (`SequenceViolationError`).

### Phase 5.5: FinDebate Protocol (Complete)
- **Evidentiary Rubric**: `DebateArgumentScore` automatically enforces fixed weights (e.g., `BACKTEST_DATA = 1.0`, `ASSERTION_ONLY = 0.0`) globally on the server side via `@model_validator(mode="after")`.
- **Token Compression**: `compress_to_schema()` strips massive semantic agent responses down into strict `schema` dictionaries (budgeted < 3K tokens) routed explicitly via `groq/llama-4-scout`.
- **Anti-Rubber-Stamp**: `ModeratorAgent` prompt flag (`COMPROMISED`) integrated. `FinDebateOrchestrator` consumes `BACKTEST` and issues `AUDIT` safely.
- **Glass Box Win Rate**: Rolling 30-day `BearWinRateMonitor` implemented to scan `mlflow.search_runs()` triggering alerts over 75%.
