# Aegis AI — Testing Tracker

> **Legend:** `[ ]` Not tested · `[/]` Partially tested · `[x]` Fully verified

---

## 1. Environment & Setup
- [ ] Python venv activates and all `requirements.txt` packages install cleanly
- [ ] `.env` file loads correctly (API keys are valid)
- [ ] Backend starts with `python api.py` (no import errors, server binds to :8000)
- [ ] Frontend starts with `npm run dev` (no build errors, serves on :5173)

## 2. External API Connections
- [ ] Alpaca API key authenticates successfully
- [ ] Alpaca returns historical price data for a test ticker
- [ ] Alpaca returns account balance / portfolio metrics
- [ ] Alpaca can list open positions (even if empty)
- [ ] FMP API key authenticates successfully
- [ ] FMP returns company metrics for a test ticker
- [ ] Anthropic API key authenticates (Claude responds to a test prompt)

## 3. Tools Layer (`tools/`)
- [ ] `calculators.py` — `calculate_sma` returns correct SMA
- [ ] `calculators.py` — `calculate_kelly_criterion` returns correct Kelly %
- [ ] `calculators.py` — `calculate_position_size_usd` returns correct USD allocation
- [ ] `calculators.py` — `calculate_stop_loss_price` / `calculate_take_profit_price` correct
- [ ] `market_api.py` — `AlpacaClient.get_historical_prices()` returns data
- [ ] `market_api.py` — `AlpacaClient.get_portfolio_metrics()` returns valid dict
- [ ] `market_api.py` — `AlpacaClient.get_open_positions()` returns list
- [ ] `market_api.py` — `AlpacaClient.execute_trade()` places a paper order
- [ ] `market_api.py` — `FMPClient.get_company_metrics()` returns data
- [ ] `market_api.py` — `FMPClient.get_technical_indicators()` returns data

## 4. Memory Layer (`memory/`)
- [ ] `MemoryManager.log_trade()` writes a row to SQLite
- [ ] `MemoryManager.get_trade_history()` reads trades back correctly
- [ ] `MemoryManager.store_thesis()` writes to ChromaDB
- [ ] `MemoryManager.query_similar_theses()` retrieves relevant results

## 5. Config Layer (`config/`)
- [ ] `ConfigManager.load_config()` returns defaults when no file exists
- [ ] `ConfigManager.load_config()` reads `user_preferences.json` correctly
- [ ] `ConfigManager.save_config()` writes valid JSON

## 6. Agents (`agents/`)

### Researcher
- [ ] Returns `research_data` dict with keys: `metrics`, `technicals`, `transcripts`
- [ ] Returns `prices` list with close prices
- [ ] Handles missing ticker gracefully (no crash)

### Quant
- [ ] Correctly identifies BULLISH/BEARISH/NEUTRAL signal from SMA
- [ ] Kelly + position size calculation produces reasonable output
- [ ] SKIP decision when signal is bearish
- [ ] PROCEED decision with correct shares when signal is bullish

### Analyst
- [ ] Generates a thesis from Claude given research data
- [ ] Respects P/E cap from config (rejects high-P/E stocks)
- [ ] Executes a paper trade via Alpaca on thesis approval
- [ ] Logs trade to SQLite + thesis to ChromaDB

### Sentinel
- [ ] Loads open positions from Alpaca
- [ ] Calculates ATR-based stop/take-profit levels
- [ ] Triggers sell when position breaches stop-loss
- [ ] Triggers sell when position reaches take-profit
- [ ] Validates thesis is still intact via LLM

## 7. Graph / Pipeline (`graph/`)
- [ ] `build_trading_graph()` compiles without error
- [ ] Full pipeline (Researcher → Quant → Analyst) runs for a real ticker
- [ ] Pipeline correctly routes to END when Quant says SKIP
- [ ] Pipeline handles API errors gracefully (no unhandled exceptions)

## 8. API Endpoints (`api.py`)

| Endpoint | Tested | Notes |
|----------|--------|-------|
| `GET /api/health` | [ ] | |
| `GET /api/portfolio/metrics` | [ ] | Requires valid Alpaca keys |
| `GET /api/portfolio/holdings` | [ ] | Requires valid Alpaca keys |
| `GET /api/agents/status` | [ ] | Returns hardcoded data |
| `POST /api/update-philosophy` | [ ] | Saves to user_preferences.json |
| `POST /api/update-philosophy-nl` | [ ] | Requires Anthropic key |
| `GET /api/alerts` | [ ] | Returns mock data |
| `WS /api/stream-logs` | [ ] | WebSocket connection |
| `POST /api/run-analysis` | [ ] | Triggers full pipeline |
| `POST /api/execute-approved-trade` | [ ] | Places Alpaca paper trade |

## 9. Frontend (`frontend/`)
- [ ] App loads at `localhost:5173` with no console errors
- [ ] Sidebar renders with agent status indicators
- [ ] TopBar displays portfolio metrics from API
- [ ] Dashboard view renders chart placeholder and holdings table
- [ ] Alerts feed fetches and displays from `/api/alerts`
- [ ] TerminalStream connects to WebSocket and shows live logs
- [ ] AssetTerminal loads ticker detail and "Approve & Execute" works
- [ ] StrategyConfig manual mode saves config via API
- [ ] StrategyConfig NLP mode parses prompt and updates form
- [ ] Navigation between all views works (sidebar clicks)

## 10. Integration Tests
- [ ] Backend + Frontend communicate correctly (CORS, API calls)
- [ ] Full user flow: open dashboard → run analysis → see terminal output → approve trade
- [ ] Config change propagates: update config → run pipeline → agent uses new config
- [ ] Sentinel can run independently and monitor live positions
