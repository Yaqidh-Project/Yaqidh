import asyncio
import json
import logging
import uuid
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, user_id: uuid.UUID, websocket: WebSocket):
        await websocket.accept()
        key = str(user_id)
        if key not in self._connections:
            self._connections[key] = []
        self._connections[key].append(websocket)
        logger.info(f"WebSocket connected for user {user_id}")

    def disconnect(self, user_id: uuid.UUID, websocket: WebSocket):
        key = str(user_id)
        if key in self._connections:
            self._connections[key] = [
                ws for ws in self._connections[key] if ws is not websocket
            ]
            if not self._connections[key]:
                del self._connections[key]
        logger.info(f"WebSocket disconnected for user {user_id}")

    async def broadcast_to_users(self, user_ids: list[uuid.UUID], payload: dict):
        message = json.dumps(payload)
        tasks = []
        for uid in user_ids:
            key = str(uid)
            for ws in self._connections.get(key, []):
                tasks.append(self._safe_send(ws, message))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_send(self, websocket: WebSocket, message: str):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.warning(f"Failed to send WebSocket message: {e}")

    @property
    def active_count(self) -> int:
        return sum(len(v) for v in self._connections.values())


manager = ConnectionManager()
