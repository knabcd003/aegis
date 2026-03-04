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

## Phase 2: Quant Engine (In Progress)
**Date:** Mar 3, 2026
**Status:** 🔨 Building

HMM regime detection, Riskfolio-Lib portfolio optimization, VPIN order flow toxicity.

### Phase 3: Analyst Engine
FinBERT-scored signals → Claude thesis generation → ChromaDB storage.

### Phase 4: Sentinel Engine
Real-time monitoring: price + VPIN + news-driven exits.

### Phase 5: MLflow + Backtesting
Experiment tracking, model comparison, backtest runner.

### Phase 6: API Layer
FastAPI endpoints for each engine.

### Phase 7: Frontend v2
New component architecture built around actual engine outputs.
