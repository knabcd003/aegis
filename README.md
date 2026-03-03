# Aegis AI — Autonomous Multi-Agent Trading System

> An autonomous trading prototype powered by a multi-agent architecture using **LangGraph**, **Claude 3.5 Sonnet**, and **Alpaca Paper Trading**. Features a real-time React dashboard with WebSocket telemetry, natural language strategy configuration, and actionable AI-driven trade alerts.

⚠️ **This system operates exclusively in Alpaca's Paper Trading environment. No real money is ever at risk.**

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Agent Breakdown](#agent-breakdown)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Frontend Dashboard](#frontend-dashboard)
- [Configuration](#configuration)
- [Testing](#testing)

---

## Overview

Aegis is an end-to-end autonomous trading system that researches stocks, calculates optimal position sizes using the **Kelly Criterion**, generates structured investment theses via an LLM, and executes paper trades — all orchestrated through a directed acyclic graph (DAG) of specialized AI agents.

The system is designed with a **human-in-the-loop** approval step: the AI agents research and recommend, but the user clicks **"Approve & Execute"** to confirm any trade.

### Key Features

- **Multi-Agent Pipeline** — Researcher → Quant → Analyst, orchestrated via LangGraph
- **Fractional Kelly Criterion** — Pure mathematical position sizing (no LLM hallucinations for risk math)
- **LLM-Powered Thesis Generation** — Claude 3.5 Sonnet writes structured investment theses with built-in constraint enforcement (P/E caps, philosophical alignment)
- **Sentinel Monitor** — Passive agent that watches open positions and auto-exits on broken theses or ATR stop-losses
- **Dual Memory** — SQLite for trade execution logs + ChromaDB for semantic investment thesis retrieval
- **Natural Language Configuration** — Describe your strategy in plain English; the AI parses it into strict systemic constraints
- **Real-Time Dashboard** — React + TypeScript frontend with WebSocket-powered live agent telemetry
- **Actionable Alerts** — AI-generated BUY/SELL signals surfaced directly in the dashboard

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Dashboard (Vite)                │
│  TopBar │ Dashboard │ Strategy Config │ Asset Terminal   │
│         │ + Alerts  │ (Manual / NLP)  │ (Approve/Exec)  │
└────────────────────────┬────────────────────────────────┘
                         │ REST + WebSocket
                         ▼
┌─────────────────────────────────────────────────────────┐
│                 FastAPI Gateway (api.py)                 │
│  /portfolio  /alerts  /run-analysis  /update-philosophy │
│  /execute-approved-trade    /stream-logs (WS)           │
└────────────────────────┬────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
   ┌────────────┐ ┌───────────┐ ┌────────────┐
   │ Researcher │→│   Quant   │→│  Analyst   │
   │  (Data)    │ │  (Math)   │ │  (LLM)     │
   └────────────┘ └───────────┘ └────────────┘
          │              │              │
          ▼              ▼              ▼
   ┌──────────┐   ┌───────────┐  ┌──────────┐
   │ Alpaca   │   │  Kelly    │  │ Claude   │
   │ FMP APIs │   │  Criterion│  │ 3.5      │
   └──────────┘   └───────────┘  └──────────┘
                                       │
                         ┌─────────────┼──────────┐
                         ▼             ▼          ▼
                   ┌──────────┐ ┌──────────┐ ┌────────┐
                   │ ChromaDB │ │  SQLite  │ │ Alpaca │
                   │ (Theses) │ │ (Trades) │ │ (Exec) │
                   └──────────┘ └──────────┘ └────────┘

   ┌─────────────────────────────────────────────┐
   │          Sentinel Agent (Cron)               │
   │  Monitors positions → LLM thesis validation │
   │  ATR-based stops → Auto-exits if broken     │
   └─────────────────────────────────────────────┘
```

---

## Agent Breakdown

| Agent | Role | LLM? | Description |
|-------|------|------|-------------|
| **Researcher** | Data Collection | No | Pulls 30-day price history from Alpaca, fundamental metrics (P/E, market cap) and earnings transcripts from FMP, and calculates SMA(50). |
| **Quant** | Position Sizing | No | Pure math engine. Calculates fractional Kelly Criterion allocation, clamps to user-defined max position size. Zero LLM dependency. |
| **Analyst** | Thesis & Execution | Yes | Claude 3.5 Sonnet ingests technicals + fundamentals, writes a 2-paragraph investment thesis, enforces philosophical constraints (e.g. value investing, P/E caps), stores thesis in ChromaDB, and triggers paper trades via Alpaca. |
| **Sentinel** | Portfolio Monitor | Yes | Runs on a cron schedule. Reviews open positions against original theses using LLM semantic evaluation. Executes SELL orders on ATR stop-loss hits or broken fundamental narratives. |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Orchestration | LangGraph (StateGraph with conditional routing) |
| LLM | Claude 3.5 Sonnet (via LangChain Anthropic) |
| Market Data | Alpaca Trade API, Financial Modeling Prep (FMP) |
| Trade Execution | Alpaca Paper Trading API |
| Vector Memory | ChromaDB (cosine similarity, persistent storage) |
| Relational Memory | SQLite (trade execution logs) |
| Backend API | FastAPI + Uvicorn (REST + WebSocket) |
| Frontend | React + TypeScript (Vite), Recharts |
| Configuration | JSON state file with NLP parsing via Claude |

---

## Project Structure

```
Aegis_AI/
├── agents/                  # AI agent implementations
│   ├── researcher.py        # Market data collection agent
│   ├── quant.py             # Kelly Criterion position sizing
│   ├── analyst.py           # LLM thesis generation + trade execution
│   └── sentinel.py          # Portfolio monitoring agent
├── config/
│   ├── manager.py           # ConfigManager (load/save JSON state)
│   └── user_preferences.json# User-defined strategy constraints
├── frontend/                # React + TypeScript dashboard
│   ├── src/
│   │   ├── App.tsx          # Main router (Dashboard, Config, etc.)
│   │   └── components/
│   │       ├── Dashboard.tsx      # Main view with chart + alerts + holdings
│   │       ├── TopBar.tsx         # Portfolio metrics + "Run Market Scan"
│   │       ├── Holdings.tsx       # Open positions table
│   │       ├── TerminalStream.tsx # WebSocket-powered live agent logs
│   │       ├── AssetTerminal.tsx  # Deep-dive thesis + quant view
│   │       ├── StrategyConfig.tsx # Manual + AI config form
│   │       ├── Sidebar.tsx        # Navigation sidebar
│   │       ├── ApiManagement.tsx  # API key management view
│   │       └── Performance.tsx    # Performance analytics view
│   └── package.json
├── graph/
│   └── workflow.py          # LangGraph DAG definition (Researcher→Quant→Analyst)
├── memory/
│   ├── db_helpers.py        # MemoryManager (SQLite + ChromaDB)
│   └── vector_store/        # ChromaDB persistent storage
├── tools/
│   ├── calculators.py       # Kelly Criterion, SMA, ATR stop-loss math
│   └── market_api.py        # AlpacaClient + FMPClient wrappers
├── tests/
│   └── test_calculators.py  # Unit tests for math functions
├── api.py                   # FastAPI gateway (REST + WebSocket endpoints)
├── main.py                  # CLI entrypoint (trade / monitor commands)
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable template
└── .gitignore
```

---

## Setup & Installation

### Prerequisites

- Python 3.11+
- Node.js 18+
- An [Alpaca](https://alpaca.markets/) Paper Trading account
- An [Anthropic](https://console.anthropic.com/) API key
- A [Financial Modeling Prep](https://financialmodelingprep.com/) API key

### 1. Clone the Repository

```bash
git clone https://github.com/knabcd003/aegis.git
cd aegis
```

### 2. Backend Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install fastapi uvicorn
```

### 3. Environment Variables

Copy the example file and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
ANTHROPIC_API_KEY=sk-ant-...
ALPACA_API_KEY=PK...
ALPACA_SECRET_KEY=...
ALPACA_BASE_URL=https://paper-api.alpaca.markets
FMP_API_KEY=...
```

### 4. Frontend Setup

```bash
cd frontend
npm install
```

### 5. Start the Application

Open two terminal windows:

**Terminal 1 — Backend API:**
```bash
source venv/bin/activate
python api.py
# → Runs on http://localhost:8000
```

**Terminal 2 — Frontend Dashboard:**
```bash
cd frontend
npm run dev
# → Runs on http://localhost:5173
```

---

## Usage

### Web Dashboard (Recommended)

1. **Open** `http://localhost:5173` in your browser
2. **Configure** your strategy via the **Strategy Config** tab:
   - **Manual Entry**: Select philosophy (Value/Growth/Momentum/Contrarian), set P/E caps, approved sectors, risk tolerance, max position size, and deployment amount
   - **AI Assistant**: Describe your strategy in plain English (e.g., *"I have $50,000 to deploy. Focus on undervalued tech stocks with a P/E under 20. Moderate risk."*) — the AI parses this into strict constraints
3. **Click "Save & Deploy"** to sync constraints to the backend
4. **Click "RUN MARKET SCAN"** in the top bar to trigger the full Researcher → Quant → Analyst pipeline
5. **Watch the Terminal** panel for real-time agent output streamed via WebSocket
6. **Review Alerts** — the Dashboard surfaces actionable AI-generated BUY/SELL signals
7. **Click into a holding** to open the Asset Terminal deep-dive view
8. **Click "Approve & Execute"** to confirm and execute the paper trade

### CLI (Advanced)

```bash
# Run the full pipeline for a specific ticker
python main.py trade --ticker AAPL

# Run the Sentinel portfolio monitor
python main.py monitor
```

### Sentinel Cron Job (Automated Monitoring)

To run the Sentinel agent automatically during market hours, add this to your crontab (`crontab -e`):

```bash
0 15 * * 1-5 cd /path/to/Aegis_AI && /path/to/venv/bin/python main.py monitor
```

This sweeps all open positions at 3:00 PM EST every weekday.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/portfolio/metrics` | Live portfolio value, daily P&L, cash balance |
| `GET` | `/api/portfolio/holdings` | Current open positions from Alpaca |
| `GET` | `/api/agents/status` | Current status of all agents |
| `GET` | `/api/alerts` | Actionable AI buy/sell alerts |
| `POST` | `/api/update-philosophy` | Update strategy config (structured JSON) |
| `POST` | `/api/update-philosophy-nl` | Update strategy config (natural language → AI parsing) |
| `POST` | `/api/run-analysis` | Trigger LangGraph pipeline for a ticker |
| `POST` | `/api/execute-approved-trade` | Execute an approved paper trade |
| `WS` | `/api/stream-logs` | Real-time agent telemetry stream |

---

## Frontend Dashboard

The dashboard features a dark, terminal-inspired aesthetic:

- **Top Bar** — Live portfolio metrics (total value, daily P&L, cash) + "RUN MARKET SCAN" trigger
- **Chart Panel** — Approximated candlestick chart with moving average overlay
- **Actionable Alerts** — Color-coded BUY (green) / SELL (red) recommendations with confidence scores
- **Holdings Table** — Interactive table of open positions; click any row to deep-dive
- **Terminal Stream** — Real-time WebSocket feed of agent execution logs
- **Asset Terminal** — Full thesis view + quant optimization data + "Approve & Execute" button
- **Strategy Config** — Dual-mode (Manual / AI Assistant) configuration form

---

## Configuration

Strategy constraints are stored in `config/user_preferences.json`:

```json
{
  "philosophy": "value",
  "max_pe_ratio": 15,
  "sectors": ["tech", "healthcare"],
  "risk_tolerance": "moderate",
  "max_position_size_pct": 0.10,
  "deployment_amount": 50000
}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `philosophy` | `string` | `value`, `growth`, `momentum`, or `contrarian` |
| `max_pe_ratio` | `float` | Hard cap on forward P/E ratio; stocks above this are rejected |
| `sectors` | `string[]` | Approved sectors for investment |
| `risk_tolerance` | `string` | `conservative`, `moderate`, or `aggressive` (affects stop-loss width) |
| `max_position_size_pct` | `float` | Max % of portfolio for a single position (decimal, e.g. `0.10` = 10%) |
| `deployment_amount` | `float` | Total capital in USD available for deployment |

These constraints are enforced at multiple levels:
- **Quant Agent** clamps Kelly Criterion output to `max_position_size_pct`
- **Analyst Agent** LLM prompt includes philosophy and P/E constraints; will output `REJECTED` for violations
- **Sentinel Agent** validates existing positions against the original thesis

---

## Testing

```bash
# Run unit tests
pytest tests/ -v
```

Current test coverage includes the `TradingCalculators` module (Kelly Criterion, SMA, ATR stop-loss/take-profit calculations).

---

## License

This project is for educational and demonstration purposes only. Not financial advice.
