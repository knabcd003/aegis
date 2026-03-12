import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional

from engines.data_ingestion.data_engine import DataEngine
from engines.data_ingestion.connectors.yfinance_connector import YFinanceConnector
from engines.monitoring.connector_health import ConnectorHealthMonitor
from engines.sentinel.state_manager import SentinelStateManager

# Setup standard logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("aegis.api")

class AppState:
    """Singleton container holding instances of engine components so they don't reload on every request."""
    data_engine: Optional[DataEngine] = None
    health_monitor: Optional[ConnectorHealthMonitor] = None
    sentinel_mgr: Optional[SentinelStateManager] = None

state = AppState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan hook.
    Initializes heavyweight AI engines when the server boots up,
    and cleanly tears them down when the server shuts down.
    """
    logger.info("Initializing Aegis AI Engines...")
    
    # Initialize Data Engine
    state.data_engine = DataEngine(data_dir="./data")
    state.data_engine.register(YFinanceConnector(), priority=1)
    
    # Initialize Health Monitor
    state.health_monitor = ConnectorHealthMonitor(state.data_engine)
    
    # Initialize Sentinel State Manager
    state.sentinel_mgr = SentinelStateManager(
        data_engine=state.data_engine,
        health_monitor=state.health_monitor
    )
    
    logger.info("Aegis AI Engines are online and ready to accept requests.")
    yield # The server is now running and accepting connections
    
    logger.info("Shutting down Aegis AI. Cleaning up connections...")
    # Any teardown logic goes here


# Initialize the main FastAPI application
app = FastAPI(
    title="Aegis AI API",
    description="The core API Layer governing the multi-agent AI quantitative framework.",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS so the React frontend can talk to this API from a different port
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"], # Common React/Vite ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    """Sanity check endpoint to verify the API is running."""
    return {
        "status": "online",
        "engines": {
            "data": "healthy" if state.data_engine else "offline",
            "sentinel_mgr": "healthy" if state.sentinel_mgr else "offline"
        }
    }

from api.routers import quant, analyst, mlops, stream, systems, audit, health, improvements, portfolio

# ============================================================
# API Routers
# ============================================================
app.include_router(quant.router, prefix="/api/quant", tags=["Quant"])
app.include_router(analyst.router, prefix="/api/analyst", tags=["Analyst"])
app.include_router(stream.router, prefix="/api/ws", tags=["Streaming"])
app.include_router(mlops.router, prefix="/api/mlops", tags=["MLOps"])
app.include_router(systems.router, prefix="/api/systems", tags=["Systems"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit"])
app.include_router(health.router, prefix="/api/system-health", tags=["Health"])
app.include_router(improvements.router, prefix="/api/improvements", tags=["Improvements"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])
