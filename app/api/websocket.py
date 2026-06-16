import asyncio
import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from app.core.context import DataContext
from app.api.routes import get_system


router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_message(self, client_id: str, message: Dict[str, Any]):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections.values():
            await connection.send_json(message)


manager = ConnectionManager()


@router.websocket("/analyze/{client_id}")
async def websocket_analyze(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            request = json.loads(data)
            query = request.get("query", "")

            await manager.send_message(client_id, {
                "type": "status",
                "message": "Starting analysis...",
            })

            try:
                coordinator, orchestrator = get_system()
                context = DataContext()

                await manager.send_message(client_id, {
                    "type": "status",
                    "message": "Planning tasks...",
                })

                result = await orchestrator.run(
                    user_request=query,
                    context=context,
                    coordinator=coordinator,
                )

                await manager.send_message(client_id, {
                    "type": "result",
                    "data": {
                        "status": result.get("status", "success"),
                        "report": result.get("report", ""),
                        "review": result.get("review", ""),
                        "charts": result.get("charts", []),
                        "artifacts": result.get("artifacts", []),
                        "errors": result.get("errors", {}),
                        "execution": result.get("execution", {}),
                    },
                })

            except Exception as e:
                await manager.send_message(client_id, {
                    "type": "error",
                    "message": str(e),
                })

    except WebSocketDisconnect:
        manager.disconnect(client_id)


@router.websocket("/progress/{client_id}")
async def websocket_progress(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_message(client_id, {
                "type": "ping",
                "message": "connected",
            })
    except WebSocketDisconnect:
        manager.disconnect(client_id)
