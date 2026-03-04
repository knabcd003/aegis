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

## Phase 1: Data Ingestion Engine (In Progress)
**Date:** Mar 3, 2026
**Status:** 🔨 Building

### Completed
- **`engines/data_ingestion/base_connector.py`** — Abstract connector interface. Defines standard methods: `get_prices()`, `get_fundamentals()`, `get_news()`, `health_check()`. All connectors implement this so the rest of the system never touches external APIs directly.
- **`engines/data_ingestion/connectors/yfinance_connector.py`** — Primary data source. Prices, fundamentals (P/E, market cap, EPS, sector, analyst rating), and news headlines. No API key required. Tested and verified with real AAPL + NVDA data.
- **Installed `yfinance` package**

### In Progress
- `data_engine.py` — Registry + Parquet cache layer

### Pending
- Expand yfinance connector: financial statements, options chains, insider activity, short interest
- `fred_connector.py` — Macro indicators (free API key)
- `finbert_connector.py` — NLP sentiment scoring (local CPU model)
- `alpaca_connector.py` — Backup prices + paper trade execution
- `sec_edgar_connector.py` — 10-K/10-Q filing text
- `finnhub_connector.py` — Earnings transcripts

### Key Decisions
- **yfinance over FMP** — Covers fundamentals + prices + news in one free library. Eliminated FMP dependency entirely.
- **Pluggable connector pattern** — Each data source is one file implementing `BaseConnector`. Adding a source = adding one file, nothing else changes.
- **Parquet + DuckDB for storage** — Columnar files + in-process SQL. No server needed.

---

## Future Phases (Planned)

### Phase 2: Quant Engine
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
