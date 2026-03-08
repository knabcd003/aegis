from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any, List
import asyncio
import json
import logging

logger = logging.getLogger("aegis.ws")
router = APIRouter()

class ConnectionManager:
    """Manages active WebSocket connections for agent thought streaming."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WS Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WS Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """Push an intermediate LangGraph state update to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to WS Client: {e}")
                disconnected.append(connection)
                
        # Clean up dead connections
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

@router.websocket("/agent_thoughts")
async def websocket_agent_thoughts(websocket: WebSocket):
    """
    WebSocket endpoint for the React frontend to listen to the LangGraph Analyst Engine.
    As the Supervisor routes tasks to Qwen, this streams the internal state live.
    """
    await manager.connect(websocket)
    try:
        # Acknowledge connection
        await websocket.send_json({
            "type": "system",
            "message": "Connected to Aegis AI Analyst Stream. Awaiting jobs..."
        })
        
        while True:
            # We don't actually expect the client to send us data here (mostly 1-way streaming),
            # but we keep the loop open to listen for disconnects or control pings.
            data = await websocket.receive_text()
            
            try:
                payload = json.loads(data)
                if payload.get("action") == "ping":
                    await websocket.send_json({"type": "system", "message": "pong"})
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket Error: {e}")
        manager.disconnect(websocket)
