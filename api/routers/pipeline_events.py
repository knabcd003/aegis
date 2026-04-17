import logging
import asyncio
import os
import time
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import List, Dict, Any

logger = logging.getLogger("aegis.ws.pipeline")

router = APIRouter()

class PipelineBroadcaster:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def _broadcast_async(self, message: Dict[str, Any]):
        """
        Internal async broadcast.
        """
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to client: {e}")
                disconnected.append(connection)
        
        # Clean up dead connections
        for conn in disconnected:
            self.disconnect(conn)

    def broadcast_sync(self, message: Dict[str, Any]):
        """
        Safely broadcast from synchronous backend engine threads.
        """
        if self._loop is None or not self._loop.is_running():
            return
            
        asyncio.run_coroutine_threadsafe(
            self._broadcast_async(message),
            self._loop
        )

    # Maintain async compatibility if needed by router
    async def broadcast(self, message: Dict[str, Any]):
        await self._broadcast_async(message)

# Singleton global instance for backend engines to import
broadcaster = PipelineBroadcaster()

@router.websocket("/pipeline")
async def websocket_pipeline_endpoint(websocket: WebSocket):
    await broadcaster.connect(websocket)
    try:
        while True:
            # Maintain the connection. The client doesn't send events to this endpoint.
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        broadcaster.disconnect(websocket)

async def broadcast_mock_sequence(workflow_id: str):
    """Fires a sequence of mock events with realistic delays for UI testing."""
    stages = [
        ("intake", "Human mandate locked"),
        ("builder", "Strategy generation complete"),
        ("simulation", "Backtest metrics computed"),
        ("audit", "Adversarial audit finished"),
        ("promotion", "Promotion gate passed"),
        ("sentinel", "Sentinel deployed in Proving Ground")
    ]
    
    for node_id, summary in stages:
        # Node Start
        await broadcaster.broadcast({
            "event_id": f"mock_start_{node_id}_{int(time.time()*1000)}",
            "workflow_id": workflow_id,
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "node_start",
            "node_id": node_id,
            "session_quality": "nominal",
            "payload": {"message": f"Starting {node_id}..."}
        })
        
        await asyncio.sleep(1)
        
        # Node Complete
        await broadcaster.broadcast({
            "event_id": f"mock_end_{node_id}_{int(time.time()*1000)}",
            "workflow_id": workflow_id,
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "node_complete",
            "node_id": node_id,
            "session_quality": "nominal",
            "payload": {"message": summary, "status": "success"}
        })
        
        await asyncio.sleep(1)

@router.post("/trigger-mock")
async def trigger_mock_pipeline(body: dict):
    """Diagnostic route for testing visual telemetry flow."""
    if not os.getenv("DEBUG", "false").lower() == "true":
        raise HTTPException(status_code=404, detail="Debug mode not enabled")
    
    workflow_id = body.get("workflow_id", f"mock_test_{int(time.time())}")
    # Fire a sequence of mock events with realistic delays
    asyncio.create_task(broadcast_mock_sequence(workflow_id))
    return {"workflow_id": workflow_id, "status": "started"}

from datetime import datetime # added here or near top
