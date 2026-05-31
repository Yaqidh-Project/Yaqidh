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

# Strict global router security lock.
# Only Managers and Parents can interact with cameras. Teachers are completely blocked.
router = APIRouter(
    prefix="/cameras",
    tags=["cameras"],
    dependencies=[
        Depends(require_phone_verified),
        Depends(require_roles("Manager", "Parent"))
    ],
)


async def _user_can_access_camera(user: User, camera: Camera, db: AsyncSession) -> bool:
    """
    Validates if the requesting user (Manager or Parent) is explicitly assigned 
    to the specific zone monitoring this camera instance to preserve strict privacy.
    """
    result = await db.execute(
        select(Zone)
        .join(Zone.users)
        .where(Zone.zone_id == camera.zone_id, User.user_id == user.user_id)
    )
    return result.scalar_one_or_none() is not None


@router.post("", response_model=CameraOut, status_code=status.HTTP_201_CREATED)
async def create_camera(
    payload: CameraCreate,
    current_user: User = Depends(get_current_user),  # Role handled globally
    db: AsyncSession = Depends(get_db),
):
    """
    Provisions a new hardware camera record configuration.
    Enforces a strict constraint: A zone can only have ONE camera attached.
    """
    # 1. Verify zone exists and belongs to the calling user
    zone_result = await db.execute(
        select(Zone)
        .join(Zone.users)
        .where(Zone.zone_id == payload.zone_id, User.user_id == current_user.user_id)
    )
    if not zone_result.scalar_one_or_none():
        raise HTTPException(
            status_code=404, 
            detail="Zone not found or you do not have permission to add cameras to it."
        )

    # 2. Check if the zone already has a camera linked
    existing_camera_result = await db.execute(
        select(Camera).where(Camera.zone_id == payload.zone_id)
    )
    if existing_camera_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Validation failed: This zone already has an active camera assigned. Only one camera per zone is allowed."
        )

    # Initialize and persist the new camera node entity safely
    camera = Camera(**payload.model_dump())
    db.add(camera)
    await db.flush()
    await db.refresh(camera)
    await db.commit()
    return camera


@router.get("", response_model=list[CameraOut])
async def list_cameras(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves ONLY the camera streams that belong to the zones assigned to the current user.
    This applies to both Managers and Parents to strictly maintain privacy boundaries.
    """
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
    """
    Fetches details of a specific camera instance checking profile scope parameters.
    """
    result = await db.execute(select(Camera).where(Camera.camera_id == camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    # Enforce zone ownership validation logic
    if not await _user_can_access_camera(current_user, camera, db):
        raise HTTPException(status_code=403, detail="Access denied: You are not assigned to this camera's zone.")
    return camera


@router.patch("/{camera_id}", response_model=CameraOut)
async def update_camera(
    camera_id: uuid.UUID,
    payload: CameraUpdate,
    current_user: User = Depends(get_current_user),  # Open to both Manager & Parent 
    db: AsyncSession = Depends(get_db),
):
    """
    Modifies runtime configurations or access URLs for an established stream tracker.
    Both Managers and Parents can edit their owned cameras.
    """
    result = await db.execute(select(Camera).where(Camera.camera_id == camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    # Enforce that the user owns the zone this camera belongs to
    if not await _user_can_access_camera(current_user, camera, db):
         raise HTTPException(status_code=403, detail="Access denied: You cannot modify this camera.")
         
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(camera, field, value)
    await db.flush()
    await db.refresh(camera)
    await db.commit()
    return camera


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(
    camera_id: uuid.UUID,
    current_user: User = Depends(get_current_user),  # Open to both Manager & Parent 
    db: AsyncSession = Depends(get_db),
):
    """
    Deletes a registered camera entity from tracking matrices permanently.
    Both Managers and Parents can delete their owned cameras.
    """
    result = await db.execute(select(Camera).where(Camera.camera_id == camera_id))
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    # Enforce that the user owns the zone this camera belongs to
    if not await _user_can_access_camera(current_user, camera, db):
         raise HTTPException(status_code=403, detail="Access denied: You cannot delete this camera.")
         
    await db.delete(camera)
    await db.commit()