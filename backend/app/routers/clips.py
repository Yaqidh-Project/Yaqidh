"""
app/routers/clips.py
--------------------
Serves incident video clips with full authentication and authorization.

Endpoint: GET /clips/{incident_id}

Security:
  - User must be authenticated
  - User must be assigned to the camera's zone (or be a Manager)
  - Clip file must exist on disk
  - No public access — every request goes through auth + authz checks
"""

import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.incident import Incident
from app.models.camera import Camera
from app.models.zone import Zone
from app.models.user import User
from app.auth.dependencies import get_current_user, require_phone_verified
from app.config import get_settings

router = APIRouter(
    prefix="/clips",
    tags=["clips"],
    dependencies=[Depends(require_phone_verified)],
)

settings = get_settings()


async def _get_zone_user_ids(camera_id: uuid.UUID, db: AsyncSession) -> list[uuid.UUID]:
    result = await db.execute(
        select(User.user_id)
        .join(Zone.users)
        .join(Zone.cameras)
        .where(Camera.camera_id == camera_id)
    )
    return [row[0] for row in result.all()]


@router.get("/{incident_id}")
async def get_incident_clip(
    incident_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Stream the video clip for a specific incident.

    Authorization rules:
      - Manager: can access any clip
      - Teacher/Parent: can only access clips from cameras in their assigned zones
    """

    # ── Fetch incident ────────────────────────────────────────────────────────
    result = await db.execute(
        select(Incident).where(Incident.incident_id == incident_id)
    )
    incident = result.scalar_one_or_none()

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # ── Authorization ─────────────────────────────────────────────────────────
    if current_user.role_name != "Manager":
        if not incident.camera_id:
            raise HTTPException(status_code=403, detail="Access denied")

        zone_user_ids = await _get_zone_user_ids(incident.camera_id, db)
        if current_user.user_id not in zone_user_ids:
            raise HTTPException(
                status_code=403,
                detail="Access denied: you are not assigned to this camera's zone",
            )

    # ── Check clip exists ─────────────────────────────────────────────────────
    if not incident.incident_clip:
        raise HTTPException(status_code=404, detail="No clip available for this incident")

    # incident_clip stores relative URL: /incident_clips/filename.mp4
    # Convert to actual file path on disk
    clip_relative = incident.incident_clip.lstrip("/")   # remove leading slash
    clip_path = Path(settings.CLIPS_DIR).parent / clip_relative

    if not clip_path.exists():
        raise HTTPException(status_code=404, detail="Clip file not found on disk")

    return FileResponse(
        path=str(clip_path),
        media_type="video/mp4",
        filename=clip_path.name,
    )