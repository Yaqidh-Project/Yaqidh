import asyncio
import json
import logging
import uuid
from datetime import datetime
from fastapi import WebSocket

logger = logging.getLogger(__name__)

# Per-user, per-incident-type cooldowns (in seconds)
INCIDENT_COOLDOWNS = {
    "fall": 10,
    "violence": 20,
}

# Cooldown tracking: {(user_id, camera_id, incident_type): last_notification_time}
_user_incident_cooldowns: dict[tuple[str, str, str], float] = {}


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

    async def notify_incident(
        self,
        user_ids: list[uuid.UUID],
        incident_id: uuid.UUID,
        incident_type: str,
        danger_category: str,
        camera_id: uuid.UUID,
        confidence: float,
        timestamp: datetime,
        incident_clip: str = None,
        stub: bool = False,
    ):
        """
        Notify users about an incident with per-user, per-incident-type cooldown.
        
        Cooldowns are enforced per user/camera/incident_type combination to avoid
        spamming the same user with multiple notifications of the same type.
        - Fall detection: 10 second cooldown
        - Violence detection: 20 second cooldown
        """
        cooldown_seconds = INCIDENT_COOLDOWNS.get(incident_type, 10)
        now = datetime.now().timestamp()
        
        # Filter users who are not in cooldown
        users_to_notify = []
        for user_id in user_ids:
            cooldown_key = (str(user_id), str(camera_id), incident_type)
            last_notification_time = _user_incident_cooldowns.get(cooldown_key, 0)
            
            if now - last_notification_time >= cooldown_seconds:
                users_to_notify.append(user_id)
                _user_incident_cooldowns[cooldown_key] = now
        
        if not users_to_notify:
            logger.debug(f"No users to notify for {incident_type} incident (all in cooldown)")
            return
        
        # Build notification payload
        payload = {
            "event": "incident_detected",
            "incident_id": str(incident_id),
            "danger_category": danger_category,
            "incident_type": incident_type,
            "camera_id": str(camera_id),
            "confidence": confidence,
            "timestamp": timestamp.isoformat(),
            "incident_clip": incident_clip,
            "stub": stub,
        }
        
        # Broadcast to users not in cooldown
        await self.broadcast_to_users(users_to_notify, payload)

    async def _safe_send(self, websocket: WebSocket, message: str):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.warning(f"Failed to send WebSocket message: {e}")

    @property
    def active_count(self) -> int:
        return sum(len(v) for v in self._connections.values())


manager = ConnectionManager()

