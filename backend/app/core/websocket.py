import asyncio
from typing import List
from fastapi import WebSocket
import logging

logger = logging.getLogger("powercortex.websocket")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Start a background task for heartbeat/ping
        asyncio.create_task(self._ping_loop(websocket))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def _ping_loop(self, websocket: WebSocket):
        try:
            while websocket in self.active_connections:
                await asyncio.sleep(30)
                await websocket.send_json({"type": "ping"})
        except Exception:
            self.disconnect(websocket)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: dict):
        stale_connections = []
        for connection in self.active_connections[:]:  # iterate over a copy
            try:
                await connection.send_json(message)
            except Exception as e:
                # Connection might have closed without triggering disconnect
                logger.warning(f"Failed to send broadcast message: {e}. Removing connection.")
                stale_connections.append(connection)
        for conn in stale_connections:
            self.disconnect(conn)

manager = ConnectionManager()
