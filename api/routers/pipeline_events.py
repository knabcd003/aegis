from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import logging

logger = logging.getLogger("aegis.ws.pipeline")

router = APIRouter()

class PipelineBroadcaster:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcasts a CanvasEvent dict to all connected clients.
        Import `broadcaster` and call `await broadcaster.broadcast(event)` to push events.
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
