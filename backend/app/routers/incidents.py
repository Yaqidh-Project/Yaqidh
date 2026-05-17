import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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


async def _get_zone_users(camera_id: uuid.UUID, db: AsyncSession) -> list[uuid.UUID]:
    result = await db.execute(
        select(User.user_id)
        .join(Zone.users)
        .join(Zone.cameras)
        .where(Camera.camera_id == camera_id)
    )
    return [row[0] for row in result.all()]


async def _assert_camera_access(user: User, camera_id: uuid.UUID, db: AsyncSession) -> None:
    if user.role_name == "Manager":
        return
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


@router.post("", response_model=IncidentOut, status_code=status.HTTP_201_CREATED)
async def create_incident(
    payload: IncidentCreate,
    current_user: User = Depends(require_roles("Manager", "Teacher")),
    db: AsyncSession = Depends(get_db),
):
    cam_result = await db.execute(select(Camera).where(Camera.camera_id == payload.camera_id))
    if not cam_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Camera not found")

    await _assert_camera_access(current_user, payload.camera_id, db)

    incident = Incident(**payload.model_dump())
    db.add(incident)
    await db.flush()
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role_name == "Manager":
        result = await db.execute(
            select(Incident).order_by(Incident.timestamp.desc()).offset(skip).limit(limit)
        )
        return result.scalars().all()

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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Incident).where(Incident.incident_id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if current_user.role_name != "Manager":
        if not incident.camera_id:
            raise HTTPException(status_code=403, detail="Access denied to this incident")
        user_ids = await _get_zone_users(incident.camera_id, db)
        if current_user.user_id not in user_ids:
            raise HTTPException(status_code=403, detail="Access denied to this incident")

    return incident


@router.patch("/{incident_id}", response_model=IncidentOut)
async def update_incident(
    incident_id: uuid.UUID,
    payload: IncidentUpdate,
    current_user: User = Depends(require_roles("Manager")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Incident).where(Incident.incident_id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(incident, field, value)
    await db.flush()
    await db.refresh(incident)
    return incident


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_incident(
    incident_id: uuid.UUID,
    current_user: User = Depends(require_roles("Manager")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Incident).where(Incident.incident_id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    await db.delete(incident)
