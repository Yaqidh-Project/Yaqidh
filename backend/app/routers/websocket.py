from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.auth.jwt import verify_token
from app.services.notifications import manager
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


@router.websocket("/ws/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
):
    payload = verify_token(token, token_type="access")
    if not payload:
        await websocket.close(code=4001)
        return

    user_id_str = payload.get("sub")
    if not user_id_str:
        await websocket.close(code=4001)
        return

    user_id = uuid.UUID(user_id_str)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            await websocket.close(code=4001)
            return

    await manager.connect(user_id, websocket)
    try:
        await websocket.send_json({"event": "connected", "user_id": str(user_id)})
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"event": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
        logger.info(f"WebSocket client {user_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(user_id, websocket)
