import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.incident import Incident
from app.models.camera import Camera
from app.models.zone import Zone
from app.models.user import User
from app.schemas.incident import IncidentCreate, IncidentUpdate, IncidentOut
from app.auth.dependencies import get_current_user, require_roles, require_phone_verified
from app.services.notifications import manager as ws_manager

router = APIRouter(
    prefix="/incidents",
    tags=["incidents"],
    dependencies=[Depends(require_phone_verified)],
)


def _normalize_incident_clip(value: str | None) -> str | None:
    """
    Normalizes the incident video clip file path.
    """
    if value is None:
        return None
    return f"/incident_clips/{Path(value).name}"


async def _get_zone_users(camera_id: uuid.UUID, db: AsyncSession) -> list[uuid.UUID]:
    """
    Fetches all user IDs mapped to the zone where the specific camera belongs.
    """
    result = await db.execute(
        select(User.user_id)
        .join(Zone.users)
        .join(Zone.cameras)
        .where(Camera.camera_id == camera_id)
    )
    return [row[0] for row in result.all()]


async def _assert_camera_access(user: User, camera_id: uuid.UUID, db: AsyncSession) -> None:
    """
    Enforces data isolation by verifying if the user has access to the specified camera's zone.
    """
    result = await db.execute(
        select(Camera)
        .join(Camera.zone)
        .join(Zone.users)
        .where(Camera.camera_id == camera_id, User.user_id == user.user_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you are not assigned to this camera's zone",
        )


async def _assert_incident_access(user: User, incident: Incident, db: AsyncSession) -> None:
    """
    Internal helper to validate write/update permissions on an incident.
    Ensures that a user cannot access/modify an incident unless they own the corresponding zone context.
    """
    if not incident.camera_id:
        raise HTTPException(status_code=403, detail="Access denied to this incident")
        
    user_ids = await _get_zone_users(incident.camera_id, db)
    if user.user_id not in user_ids:
        raise HTTPException(status_code=403, detail="Access denied to this incident")


@router.post("", response_model=IncidentOut, status_code=status.HTTP_201_CREATED)
async def create_incident(
    payload: IncidentCreate,
    current_user: User = Depends(require_roles("Manager", "Teacher")),  
    db: AsyncSession = Depends(get_db),
):
    """
    Creates a new security/safety incident record and triggers real-time WebSocket notifications.
    """
    cam_result = await db.execute(select(Camera).where(Camera.camera_id == payload.camera_id))
    if not cam_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Camera not found")

    await _assert_camera_access(current_user, payload.camera_id, db)

    incident_data = payload.model_dump()
    incident_data["incident_clip"] = _normalize_incident_clip(incident_data.get("incident_clip"))
    incident = Incident(**incident_data)
    db.add(incident)
    await db.flush()
    await db.commit()  # Explicit commit added to persist incident record permanently
    await db.refresh(incident)

    user_ids = await _get_zone_users(payload.camera_id, db)
    await ws_manager.broadcast_to_users(
        user_ids,
        {
            "event": "incident_created",
            "incident_id": str(incident.incident_id),
            "danger_category": incident.danger_category,
            "incident_type": incident.incident_type,
            "camera_id": str(incident.camera_id),
            "timestamp": incident.timestamp.isoformat(),
        },
    )
    return incident


@router.get("", response_model=list[IncidentOut])
async def list_incidents(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_roles("Manager", "Parent")),  #  Restricted to Manager & Parent only
    db: AsyncSession = Depends(get_db),
):
    """
    Lists incidents filtered strictly by the current user's assigned zones.
    """
    result = await db.execute(
        select(Incident)
        .join(Incident.camera)
        .join(Camera.zone)
        .join(Zone.users)
        .where(User.user_id == current_user.user_id)
        .order_by(Incident.timestamp.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{incident_id}", response_model=IncidentOut)
async def get_incident(
    incident_id: uuid.UUID,
    current_user: User = Depends(require_roles("Manager", "Parent")),  # Restricted to Manager & Parent only
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves a single incident by its ID enforcing clear security boundaries.
    """
    result = await db.execute(select(Incident).where(Incident.incident_id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    await _assert_incident_access(current_user, incident, db)
    return incident


@router.patch("/{incident_id}", response_model=IncidentOut)
async def update_incident(
    incident_id: uuid.UUID,
    payload: IncidentUpdate,
    current_user: User = Depends(require_roles("Manager", "Teacher")),
    db: AsyncSession = Depends(get_db),
):
    """
    Updates the fields of an incident record after enforcing data access restrictions.
    """
    result = await db.execute(select(Incident).where(Incident.incident_id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if current_user.role_name == "Teacher":
        await _assert_incident_access(current_user, incident, db)

    incident_data = payload.model_dump(exclude_none=True)
    
    if "status" in incident_data:
        new_status = str(incident_data["status"]).lower()
        current_status = str(incident.status).lower()
        
        if new_status == "resolved" and current_status != "resolved":
            incident.resolved_at = func.now()
            incident.resolved_by_id = current_user.user_id
        elif new_status == "open":
            incident.resolved_at = None
            incident.resolved_by_id = None

    for field, value in incident_data.items():
        if field == "incident_clip":
            value = _normalize_incident_clip(value)
        setattr(incident, field, value)
        
    await db.flush()
    await db.commit()
    await db.refresh(incident)
    
    return incident


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_incident(
    incident_id: uuid.UUID,
    current_user: User = Depends(require_roles("Manager", "Parent")),  # Opened for Parent as well
    db: AsyncSession = Depends(get_db),
):
    """
    Deletes an incident record from the database context permanently.
    """
    result = await db.execute(select(Incident).where(Incident.incident_id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    await _assert_incident_access(current_user, incident, db)  # Secure validation layer
        
    await db.delete(incident)
    await db.commit()