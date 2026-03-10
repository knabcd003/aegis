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

## Phase 3: Improvement Analyzer (In Progress)
**Date:** Mar 10, 2026
**Status:** 🔨 Building

Next focus is on the self-correcting loop: analyze MLflow traces and generate one-parameter mutations to optimize strategy performance.

---

## Future Phases (Planned)

### Phase 4: Sentinel Engine
Real-time monitoring: price + VPIN + news-driven exits.

### Phase 5: API Layer
FastAPI endpoints for each engine.

### Phase 6: Frontend v2
New component architecture built around actual engine outputs.
