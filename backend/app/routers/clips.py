"""
app/routers/clips.py
--------------------
Serves incident video clips with full authentication and authorization.
Supports HTTP Range requests (206 Partial Content) for seamless browser streaming.
"""

import os
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from fastapi.responses import StreamingResponse
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


def send_bytes_range_requests(file_path: Path, range_header: str):
    """
    Generator that parses the Range header and streams specific byte ranges
    to allow the browser to buffer, scrub, and seek video timelines cleanly.
    """
    file_size = file_path.stat().st_size
    start, end = 0, file_size - 1

    # Parse Range Header: "bytes=start-end"
    range_str = range_header.replace("bytes=", "").strip()
    range_parts = range_str.split("-")
    
    if range_parts[0]:
        start = int(range_parts[0])
    if len(range_parts) > 1 and range_parts[1]:
        end = int(range_parts[1])

    # Ensure boundaries are secure
    start = max(0, min(start, file_size - 1))
    end = max(start, min(end, file_size - 1))
    chunk_size = (end - start) + 1

    with open(file_path, "rb") as f:
        f.seek(start)
        bytes_to_read = chunk_size
        while bytes_to_read > 0:
            chunk = f.read(min(bytes_to_read, 8192))
            if not chunk:
                break
            bytes_to_read -= len(chunk)
            yield chunk


@router.get("/{incident_id}")
async def get_incident_clip(
    incident_id: uuid.UUID,
    request: Request,
    range: str = Header(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Stream the video clip for a specific incident with support for 206 Partial Content.
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

    # ── Check clip field exists in DB ─────────────────────────────────────────
    if not incident.incident_clip:
        raise HTTPException(status_code=404, detail="No clip available for this incident")

    # ── Corrected File Path Resolution ────────────────────────────────────────
    # Path(__file__).resolve().parents[2] navigates to the 'Backend' root directory.
    # From there, we go directly into 'incident_clips'.
    base_backend_dir = Path(__file__).resolve().parents[2]
    filename = Path(incident.incident_clip).name
    clip_path = base_backend_dir / "incident_clips" / filename

    # ── Terminal Debug Log ────────────────────────────────────────────────────
    print("\n" + "="*80)
    print(f"🔍 YAQIDH CLIP DEBUG CONSOLE (UPDATED)")
    print(f"   • Incident ID:  {incident_id}")
    print(f"   • Checking Path: {clip_path.resolve()}")
    print(f"   • File Found?:  {clip_path.exists()}")
    print("="*80 + "\n")
    # ──────────────────────────────────────────────────────────────────────────

    if not clip_path.exists():
        raise HTTPException(
            status_code=404, 
            detail=f"Clip file not found on disk at location: {clip_path.name}"
        )

    file_size = clip_path.stat().st_size

    # If browser sends a Range header, handle partial content streaming
    if range:
        range_str = range.replace("bytes=", "").strip()
        range_parts = range_str.split("-")
        start = int(range_parts[0]) if range_parts[0] else 0
        end = int(range_parts[1]) if (len(range_parts) > 1 and range_parts[1]) else file_size - 1
        
        start = max(0, min(start, file_size - 1))
        end = max(start, min(end, file_size - 1))
        content_length = (end - start) + 1

        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(content_length),
            "Content-Disposition": f'inline; filename="{clip_path.name}"',
        }
        
        return StreamingResponse(
            send_bytes_range_requests(clip_path, range),
            status_code=206,
            media_type="video/mp4",
            headers=headers
        )

    # Fallback response if no Range header is sent
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(file_size),
        "Content-Disposition": f'attachment; filename="{clip_path.name}"',
    }
    
    def full_file_generator():
        with open(clip_path, "rb") as f:
            while chunk := f.read(8192):
                yield chunk

    return StreamingResponse(full_file_generator(), status_code=200, media_type="video/mp4", headers=headers)