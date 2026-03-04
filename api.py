from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from graph.workflow import build_trading_graph
from memory.db_helpers import MemoryManager
from tools.market_api import AlpacaClient
from config.manager import ConfigManager
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from typing import List
import json
from langchain_core.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic
from backtesting.runner import BacktestRunner
from backtesting.data_store import HistoricalDataStore
from backtesting.analytics import BacktestAnalytics

app = FastAPI(title="Aegis AI Trading API")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

# Setup CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = MemoryManager()
alpaca = AlpacaClient()

class TradeRequest(BaseModel):
    ticker: str

class ConfigPayload(BaseModel):
    philosophy: str
    max_pe_ratio: float
    sectors: List[str]
    risk_tolerance: str
    max_position_size_pct: float
    deployment_amount: float

class NLConfigPayload(BaseModel):
    prompt: str

class BacktestPayload(BaseModel):
    tickers: List[str]
    start_date: str
    end_date: str
    strategy: dict = {}
    use_llm: bool = False
    eval_frequency_days: int = 5

class DataDownloadPayload(BaseModel):
    tickers: List[str]
    start_date: str
    end_date: str

bt_runner = BacktestRunner()
data_store = HistoricalDataStore()

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "Aegis API is running"}

@app.get("/api/portfolio/metrics")
def get_portfolio_metrics():
    """Returns live portfolio metrics from Alpaca."""
    return alpaca.get_portfolio_metrics()

@app.get("/api/portfolio/holdings")
def get_holdings():
    """Retrieves current open positions from Alpaca Paper Trading."""
    positions = alpaca.get_open_positions()
    
    # Map from Alpaca return format to UI format
    return [
        {
            "ticker": p["symbol"],
            "alloc": (p["market_value"] / max(alpaca.get_portfolio_metrics()["total_value"], 1)) * 100,
            "entry": p["avg_entry_price"],
            "price": p["current_price"]
        }
        for p in positions
    ]

@app.get("/api/agents/status")
def get_agent_status():
    return [
        {"name": "Researcher", "status": "IDLE"},
        {"name": "Quant Engine", "status": "ACTIVE"},
        {"name": "Risk Analyst", "status": "SCANNING"},
        {"name": "Sentinel", "status": "WATCHING"}
    ]

@app.post("/api/update-philosophy")
def update_philosophy(payload: ConfigPayload):
    ConfigManager.save_config(payload.model_dump())
    return {"status": "success", "message": "Philosophy updated"}

@app.post("/api/update-philosophy-nl")
def update_philosophy_nl(payload: NLConfigPayload):
    llm = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0)
    prompt = PromptTemplate.from_template(
        "You are an expert algorithmic trading config parser. Extract the following from the user "
        "prompt into a valid JSON object ONLY. Do not write markdown blocks or any other surrounding text.\n\n"
        "Keys to extract:\n"
        "- philosophy (string: value, growth, momentum, contrarian)\n"
        "- max_pe_ratio (float)\n"
        "- sectors (list of strings)\n"
        "- risk_tolerance (string: conservative, moderate, aggressive)\n"
        "- max_position_size_pct (float, decimal representation of max percentage)\n"
        "- deployment_amount (float, total cash in USD)\n\n"
        "User Prompt: {input}\n\nJSON Output:"
    )
    try:
        res = llm.invoke(prompt.format(input=payload.prompt))
        # Strip potential markdown formatting just in case
        clean_json = res.content.replace("```json", "").replace("```", "").strip()
        config_dict = json.loads(clean_json)
        ConfigManager.save_config(config_dict)
        return {"status": "success", "config": config_dict}
    except Exception as e:
        print(f"Error parsing NLP Config: {e}")
        raise HTTPException(status_code=400, detail="Failed to parse natural language config.")

@app.get("/api/alerts")
def get_alerts():
    """Returns a list of actionable alerts generated by the Sentinel and Analyst agents."""
    return [
        {
            "id": 1,
            "type": "OPEN",
            "ticker": "NVDA",
            "message": "Analyst Agent identified strong fundamental breakout. Target deployment: 10%.",
            "confidence": 88
        },
        {
            "id": 2,
            "type": "CLOSE",
            "ticker": "TSLA",
            "message": "Sentinel Agent detected breaking thesis (Delivery Miss). Recommend immediate exit.",
            "confidence": 95
        }
    ]

@app.websocket("/api/stream-logs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/api/run-analysis")
async def run_analysis(req: TradeRequest, background_tasks: BackgroundTasks):
    """
    Triggers the LangGraph pipeline for a specific ticker and broadcasts via Websocket.
    """
    async def run_graph(ticker: str):
        await manager.broadcast(f"[System] Waking components to scan market for {ticker}...")
        graph = build_trading_graph()
        
        # In a real async setup we would yield from stream, 
        # but for this prototype we can mock the streaming output
        await asyncio.sleep(1)
        await manager.broadcast(f"[Researcher] Pulling 30-day tape for {ticker}...")
        
        try:
            # Run the synchronous graph in thread (or via stream wrapper)
            state = {"ticker": ticker}
            for step in graph.stream(state):
                node_name = list(step.keys())[0]
                await manager.broadcast(f"[{node_name.capitalize()}] Output completed.")
                await asyncio.sleep(0.5)
                
            await manager.broadcast(f"[System] Complete. Check Terminal output for final thesis.")
            
        except Exception as e:
            await manager.broadcast(f"[Error] Pipeline failed: {e}")

    background_tasks.add_task(run_graph, req.ticker)
    return {"status": "Analysis triggered", "ticker": req.ticker}

@app.post("/api/execute-approved-trade")
def execute_approved_trade(req: TradeRequest):
    """
    Called when the user clicks 'Approve & Execute' on the frontend terminal.
    Executes the trade via Alpaca and logs it to the database.
    """
    # For prototype, we mock the qty/thesis parameters that the agent would have stored in memory.
    qty = 10.0
    order = alpaca.execute_trade(symbol=req.ticker, qty=qty, side="buy")
    if order:
        db.log_trade(trade_data=order, exit_reason="USER_APPROVED_INITIAL_ENTRY")
        return {"status": "success", "order": order}
    else:
        raise HTTPException(status_code=500, detail="Failed to execute trade.")

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)

# ── Backtesting Endpoints ───────────────────────────────────────────────

@app.post("/api/backtest/run")
def run_backtest(payload: BacktestPayload, background_tasks: BackgroundTasks):
    """Launch a backtest with the given configuration. Returns run_id immediately."""
    config = {
        "tickers": payload.tickers,
        "start_date": payload.start_date,
        "end_date": payload.end_date,
        "strategy": payload.strategy or ConfigManager.load_config(),
        "use_llm": payload.use_llm,
        "eval_frequency_days": payload.eval_frequency_days,
    }
    # Run synchronously for now (could move to background_tasks for large runs)
    run_id = bt_runner.run_backtest(config)
    return {"status": "completed", "run_id": run_id}

@app.get("/api/backtest/results")
def list_backtest_results():
    """List all completed backtest runs."""
    return bt_runner.list_runs()

@app.get("/api/backtest/results/{run_id}")
def get_backtest_result(run_id: int):
    """Retrieve detailed results for a specific backtest run."""
    result = bt_runner.get_run_results(run_id)
    if not result:
        raise HTTPException(status_code=404, detail="Run not found")
    return result

@app.get("/api/backtest/compare")
def compare_backtests(ids: str):
    """Compare two backtest runs side-by-side. Query: ?ids=1,2"""
    try:
        id_list = [int(x.strip()) for x in ids.split(",")]
        if len(id_list) != 2:
            raise HTTPException(status_code=400, detail="Provide exactly 2 run IDs")
        run_a = bt_runner.get_run_results(id_list[0])
        run_b = bt_runner.get_run_results(id_list[1])
        if not run_a or not run_b:
            raise HTTPException(status_code=404, detail="One or both runs not found")
        return BacktestAnalytics.compare_runs(run_a, run_b)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run IDs")

@app.post("/api/backtest/download-data")
def download_data(payload: DataDownloadPayload):
    """Download historical data for the given tickers and date range."""
    results = data_store.download_historical_data(
        payload.tickers, payload.start_date, payload.end_date
    )
    return {"status": "completed", "results": results}
