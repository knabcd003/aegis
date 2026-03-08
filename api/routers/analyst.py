from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from api.main import state
from engines.analyst.episodic_memory import EpisodicMemory

router = APIRouter()

# Lazy-loaded components
_memory_bank: Optional[EpisodicMemory] = None

def get_memory() -> EpisodicMemory:
    global _memory_bank
    if _memory_bank is None:
        _memory_bank = EpisodicMemory(persist_directory="./chroma_db")
    return _memory_bank

class ThesisRequest(BaseModel):
    ticker: str
    force_refresh: bool = False

@router.get("/memory")
async def get_episodic_memory(
    ticker: Optional[str] = Query(None, description="Filter memories by ticker"),
    outcome: Optional[str] = Query(None, description="Filter by outcome (e.g., 'Loss', 'Win')"),
    limit: int = Query(10, description="Max memories to return")
) -> Dict[str, Any]:
    """Retrieve episodic memories (past generated theses and post-mortem logs) from ChromaDB."""
    memory = get_memory()
    
    # Simple query wrapper since EpisodicMemory uses vector search under the hood.
    # We pass a generic query and use the filters.
    where_filter = {}
    if ticker:
        where_filter["ticker"] = ticker
    if outcome:
        where_filter["outcome"] = outcome
        
    try:
        # Pass an empty query text to just use metadata filtering if supported,
        # otherwise provide a generic query string
        results = memory.retrieve("trade thesis", k=limit, where_filter=where_filter if where_filter else None)
        
        return {
            "status": "success",
            "count": len(results),
            "memories": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/thesis/async")
async def generate_thesis_async(
    request: ThesisRequest, 
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Kicks off a background task to generate a thesis.
    Because the LangGraph Supervisor can take multiple minutes, we don't await it here.
    (In a real production app, we'd use Celery/Redis for this, but for local sandbox BackgroundTasks suffices).
    """
    if not state.data_engine:
        raise HTTPException(status_code=503, detail="Data Engine is offline")
        
    # Mocking the background job payload for now until we build the main orchestrator script hook
    job_id = f"job_thesis_{request.ticker}_{int(datetime.now().timestamp())}"
    
    def background_run_graph(ticker: str):
        # We will import the supervisor here later and run the graph
        pass
        
    background_tasks.add_task(background_run_graph, request.ticker)
    
    return {
        "status": "accepted",
        "job_id": job_id,
        "message": f"Thesis generation for {request.ticker} started in the background. Connect to the WebSocket stream to watch agent thoughts."
    }
