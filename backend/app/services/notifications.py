import asyncio
import json
import logging
import uuid
from datetime import datetime
from fastapi import WebSocket
from sqlalchemy import select

from app.services.email import send_incident_email
from app.models.user import User
from app.models.zone import Zone
from app.models.camera import Camera
from app.database import AsyncSessionLocal

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
            logger.info(f"📢 [Yaqidh Notification] No users to notify for {incident_type} (all in cooldown)")
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
        
        # Fetch zone name for email
        async with AsyncSessionLocal() as db:
            zone_result = await db.execute(
                select(Zone)
                .join(Camera)
                .where(Camera.camera_id == camera_id)
            )
            zone = zone_result.scalar_one_or_none()
            zone_name = zone.zone_name if zone else "Unknown Zone"
        
        # Fetch camera name for email
        async with AsyncSessionLocal() as db:
            camera_result = await db.execute(
                select(Camera)
                .where(Camera.camera_id == camera_id)
            )
            camera = camera_result.scalar_one_or_none()
            camera_name = camera.camera_name if camera else None
        
        # Safely fetch users and extract data without consuming the stream twice
        async with AsyncSessionLocal() as db:
            users_result = await db.execute(
                select(User).where(User.user_id.in_(users_to_notify))
            )
            all_fetched_users = users_result.scalars().all()
            
            # Map values correctly
            users = {str(u.user_id): u.email for u in all_fetched_users}
            users_roles = {str(u.user_id): u.role_name for u in all_fetched_users}

        zone_id = str(zone.zone_id) if zone else "Unknown"
        
        # Build tasks for WebSocket and Email sends in parallel
        tasks = []
        
        # WebSocket broadcast for all users
        message = json.dumps(payload)
        for uid in users_to_notify:
            key = str(uid)
            for ws in self._connections.get(key, []):
                tasks.append(self._safe_send(ws, message))
        
        # Email send for each user
        email_count = 0
        for uid in users_to_notify:
            uid_str = str(uid)
            if uid_str in users:
                email_count += 1
                logger.info(f"📧 Queueing email for user {uid}")
                logger.info(f"📧 [Yaqidh Notification] Preparing email task for: {users[uid_str]} (Role: {users_roles.get(uid_str, 'User')})")
                tasks.append(
                    send_incident_email(
                        user_email=users[uid_str],
                        incident_type=incident_type,
                        zone_id=zone_id,
                        zone_name=zone_name,
                        camera_id=str(camera_id),
                        camera_name=camera_name,
                        timestamp=timestamp,
                        confidence=confidence,
                        incident_clip_url=incident_clip,
                        user_role=users_roles.get(uid_str, "User")
                    )
                )
        
        logger.info(f"🚀 [Yaqidh Notification] Dispatching {len(tasks)} parallel tasks ({email_count} Emails, {len(tasks) - email_count} WebSockets)...")
        
        # Execute all tasks in parallel (WebSocket + Email)
        if tasks:
            logger.info(f"⏳ Executing {len(tasks)} tasks (WebSocket + Email)")
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info("✅ [Yaqidh Notification] All dispatched notification tasks completed execution.")

    async def _safe_send(self, websocket: WebSocket, message: str):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.warning(f"Failed to send WebSocket message: {e}")

    @property
    def active_count(self) -> int:
        return sum(len(v) for v in self._connections.values())


manager = ConnectionManager()