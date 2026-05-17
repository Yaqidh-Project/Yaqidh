import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.camera import Camera
from app.models.zone import Zone
from app.models.user import User
from app.schemas.camera import CameraCreate, CameraUpdate, CameraOut
from app.auth.dependencies import get_current_user, require_roles, require_phone_verified

router = APIRouter(
    prefix="/cameras",
    tags=["cameras"],
    dependencies=[Depends(require_phone_verified)],
)


async def _user_can_access_camera(user: User, camera: Camera, db: AsyncSession) -> bool:
    if user.role_name == "Manager":
        return True
    result = await db.execute(
        select(Zone)
        .join(Zone.users)
        .where(Zone.zone_id == camera.zone_id, User.user_id == user.user_id)
    )
    return result.scalar_one_or_none() is not None


@router.post("", response_model=CameraOut, status_code=status.HTTP_201_CREATED)
async def create_camera(
    payload: CameraCreate,
    current_user: User = Depends(require_roles("Manager")),
    db: AsyncSession = Depends(get_db),
):
    zone_result = await db.execute(select(Zone).where(Zone.zone_id == payload.zone_id))
    if not zone_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Zone not found")

    camera = Camera(**payload.model_dump())
    db.add(camera)
    await db.flush()
    await db.refresh(camera)
    return camera


@router.get("", response_model=list[CameraOut])
async def list_cameras(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role_name == "Manager":
        result = await db.execute(select(Camera).offset(skip).limit(limit))
        return result.scalars().all()

    result = await db.execute(
        select(Camera)
        .join(Camera.zone)
        .join(Zone.users)
        .where(User.user_id == current_user.user_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{camera_id}", response_model=CameraOut)
async def get_camera(
    camera_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Camera).where(Camera.camera_id == camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    if not await _user_can_access_camera(current_user, camera, db):
        raise HTTPException(status_code=403, detail="Access denied to this camera")
    return camera


@router.patch("/{camera_id}", response_model=CameraOut)
async def update_camera(
    camera_id: uuid.UUID,
    payload: CameraUpdate,
    current_user: User = Depends(require_roles("Manager")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Camera).where(Camera.camera_id == camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(camera, field, value)
    await db.flush()
    await db.refresh(camera)
    return camera


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(
    camera_id: uuid.UUID,
    current_user: User = Depends(require_roles("Manager")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Camera).where(Camera.camera_id == camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    await db.delete(camera)
