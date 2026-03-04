# Aegis AI — Codebase Summary

## What This Is

An AI-powered autonomous trading system built on **LangGraph**. Four specialized agents work in sequence to research, size, analyze, and monitor stock positions — all connected to **Alpaca Paper Trading** for risk-free execution. A React dashboard provides real-time visibility and control.

---

## Architecture

```
User ──→ React Dashboard ──→ FastAPI Backend ──→ LangGraph Pipeline
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         ▼                          ▼                          ▼
   Alpaca API              Claude 3.5 Sonnet            FMP API
 (prices, trades)         (thesis generation)       (fundamentals)
```

**Data flow:** Researcher → Quant → Analyst → (optional) Sentinel monitoring

---

## Project Structure

```
Aegis_AI/
├── api.py                    # FastAPI server — all backend endpoints
├── main.py                   # CLI entry point for pipeline + sentinel
├── requirements.txt          # Python dependencies
├── .env / .env.example       # API keys (Alpaca, Anthropic, FMP)
│
├── agents/                   # LangGraph agent nodes
│   ├── researcher.py         # Data gathering (Alpaca + FMP)
│   ├── quant.py              # Position sizing (Kelly + SMA)
│   ├── analyst.py            # Thesis generation + trade execution
│   └── sentinel.py           # Portfolio monitoring + exit logic
│
├── graph/
│   └── workflow.py           # LangGraph state machine definition
│
├── tools/
│   ├── market_api.py         # AlpacaClient + FMPClient API wrappers
│   └── calculators.py        # Pure math: Kelly, SMA, ATR stops
│
├── memory/
│   ├── db_helpers.py         # SQLite (trade log) + ChromaDB (theses)
│   └── trade_history.db      # SQLite database file
│
├── config/
│   ├── manager.py            # ConfigManager — loads/saves user prefs
│   └── user_preferences.json # Current strategy configuration
│
├── tests/
│   └── test_calculators.py   # Unit tests for calculators.py
├── test_alpaca.py            # Standalone Alpaca connection test
│
└── frontend/                 # React + TypeScript + Vite
    └── src/
        ├── App.tsx           # Root component + routing
        ├── index.css         # Design system (dark theme, CSS vars)
        └── components/
            ├── Dashboard.tsx      # Main view: chart, alerts, holdings
            ├── Sidebar.tsx        # Navigation + agent status lights
            ├── TopBar.tsx         # Portfolio metrics header
            ├── Holdings.tsx       # Positions table
            ├── TerminalStream.tsx # Live WebSocket log viewer
            ├── AssetTerminal.tsx  # Per-ticker deep dive + trade approval
            ├── StrategyConfig.tsx # Manual + NLP config form
            ├── ApiManagement.tsx  # API key management UI
            └── Performance.tsx    # Performance analytics (placeholder)
```

---

## System-by-System Breakdown

### 1. Agents (`agents/`)

| Agent | File | What It Does | External Dependencies |
|-------|------|-------------|----------------------|
| **Researcher** | `researcher.py` | Fetches 30-day price history from Alpaca, fundamental metrics + earnings transcripts from FMP. Compiles into `research_data` dict. | Alpaca API, FMP API |
| **Quant** | `quant.py` | Calculates 20-day SMA crossover signal, Kelly Criterion position sizing, caps allocation at user's `max_position_size_pct`. Outputs PROCEED/SKIP decision. | None (pure math) |
| **Analyst** | `analyst.py` | Uses Claude 3.5 Sonnet to generate an investment thesis from research data. Enforces P/E constraints. If thesis is valid, executes a buy order via Alpaca and logs to SQLite + ChromaDB. | Anthropic API, Alpaca API |
| **Sentinel** | `sentinel.py` | Monitors open positions against their original theses. Uses ATR-based stop-loss/take-profit levels. Sells positions that breach limits. | Anthropic API, Alpaca API |

### 2. Graph (`graph/workflow.py`)

LangGraph state machine with conditional routing:
- `researcher` → `quant` → `route_after_quant` → either `analyst` (if PROCEED) or `END` (if SKIP)
- Error handling edges route to END on failures

### 3. Tools (`tools/`)

| File | Classes/Functions | Purpose |
|------|-------------------|---------|
| `market_api.py` | `AlpacaClient` | Historical prices, account info, position listing, trade execution via Alpaca Paper Trading |
| | `FMPClient` | Company metrics, technical indicators, earnings transcripts via Financial Modeling Prep |
| `calculators.py` | `TradingCalculators` | Pure math utilities: `calculate_kelly_criterion`, `calculate_position_size_usd`, `calculate_sma`, `calculate_stop_loss_price`, `calculate_take_profit_price` |

### 4. Memory (`memory/db_helpers.py`)

| Store | Technology | What It Holds |
|-------|-----------|---------------|
| Trade log | SQLite (`trade_history.db`) | Every executed trade: symbol, qty, price, side, exit reason, timestamp |
| Thesis store | ChromaDB (vector DB) | Investment theses with semantic search capability for future RAG |

### 5. Config (`config/manager.py`)

Reads/writes `user_preferences.json`:
```json
{
  "philosophy": "value",
  "max_pe_ratio": 25,
  "sectors": ["tech", "healthcare"],
  "risk_tolerance": "moderate",
  "max_position_size_pct": 0.10,
  "deployment_amount": 50000
}
```

### 6. API (`api.py`)

| Endpoint | Method | What It Does |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/portfolio/metrics` | GET | Live portfolio value from Alpaca |
| `/api/portfolio/holdings` | GET | Current open positions |
| `/api/agents/status` | GET | Agent status indicators (currently hardcoded) |
| `/api/update-philosophy` | POST | Save manual config |
| `/api/update-philosophy-nl` | POST | Parse natural language config via Claude |
| `/api/alerts` | GET | Actionable trading alerts (currently mock data) |
| `/api/stream-logs` | WebSocket | Real-time agent execution log streaming |
| `/api/run-analysis` | POST | Trigger full LangGraph pipeline for a ticker |
| `/api/execute-approved-trade` | POST | Execute a user-approved trade via Alpaca |

### 7. Frontend (`frontend/`)

React + TypeScript + Vite. Key views:

| Component | Purpose |
|-----------|---------|
| `Dashboard.tsx` | Main view — alerts feed, asset chart, holdings table, terminal stream |
| `StrategyConfig.tsx` | Two modes: manual form or NLP text prompt for strategy configuration |
| `AssetTerminal.tsx` | Per-ticker deep dive with agent output and "Approve & Execute" button |
| `TerminalStream.tsx` | WebSocket-connected live log viewer |
| `TopBar.tsx` | Portfolio value, daily P&L, available cash display |

---

## Environment Variables (`.env`)

| Variable | Source | Purpose |
|----------|--------|---------|
| `ALPACA_API_KEY` | Alpaca | Paper trading account access |
| `ALPACA_SECRET_KEY` | Alpaca | Paper trading auth |
| `ALPACA_BASE_URL` | Alpaca | `https://paper-api.alpaca.markets` |
| `ANTHROPIC_API_KEY` | Anthropic | Claude 3.5 Sonnet for thesis generation |
| `FMP_API_KEY` | FMP | Financial Modeling Prep fundamentals data |

---

## Known Limitations & Incomplete Items

1. **`/api/agents/status`** — returns hardcoded statuses, not actual agent state
2. **`/api/alerts`** — returns mock data, not connected to Sentinel/Analyst output
3. **`Performance.tsx`** — placeholder component, no real analytics yet
4. **`execute_approved_trade`** — uses hardcoded `qty=10`, doesn't use the Quant agent's recommendation
5. **Sentinel** — designed for cron execution, not wired into the API server's lifecycle
