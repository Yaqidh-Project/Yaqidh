import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.zone import Zone
from app.models.user import User
from app.schemas.zone import ZoneCreate, ZoneUpdate, ZoneOut, ZoneAssign
from app.auth.dependencies import get_current_user, require_roles, require_phone_verified

router = APIRouter(
    prefix="/zones",
    tags=["zones"],
    dependencies=[Depends(require_phone_verified)],
)


@router.post("", response_model=ZoneOut, status_code=status.HTTP_201_CREATED)
async def create_zone(
    payload: ZoneCreate,
    current_user: User = Depends(require_roles("Manager")),
    db: AsyncSession = Depends(get_db),
):
    zone = Zone(zone_name=payload.zone_name)
    db.add(zone)
    await db.flush()
    await db.refresh(zone)
    return zone


@router.get("", response_model=list[ZoneOut])
async def list_zones(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role_name == "Manager":
        result = await db.execute(select(Zone).offset(skip).limit(limit))
        return result.scalars().all()

    result = await db.execute(
        select(Zone)
        .join(Zone.users)
        .where(User.user_id == current_user.user_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{zone_id}", response_model=ZoneOut)
async def get_zone(
    zone_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Zone).where(Zone.zone_id == zone_id))
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    if current_user.role_name != "Manager":
        assigned_result = await db.execute(
            select(Zone)
            .join(Zone.users)
            .where(Zone.zone_id == zone_id, User.user_id == current_user.user_id)
        )
        if not assigned_result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Access denied to this zone")

    return zone


@router.patch("/{zone_id}", response_model=ZoneOut)
async def update_zone(
    zone_id: uuid.UUID,
    payload: ZoneUpdate,
    current_user: User = Depends(require_roles("Manager")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Zone).where(Zone.zone_id == zone_id))
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(zone, field, value)
    await db.flush()
    await db.refresh(zone)
    return zone


@router.delete("/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_zone(
    zone_id: uuid.UUID,
    current_user: User = Depends(require_roles("Manager")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Zone).where(Zone.zone_id == zone_id))
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    await db.delete(zone)


@router.post("/{zone_id}/assign", response_model=ZoneOut)
async def assign_user_to_zone(
    zone_id: uuid.UUID,
    payload: ZoneAssign,
    current_user: User = Depends(require_roles("Manager")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Zone).options(selectinload(Zone.users)).where(Zone.zone_id == zone_id)
    )
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    user_result = await db.execute(select(User).where(User.user_id == payload.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user not in zone.users:
        zone.users.append(user)
    await db.flush()
    return zone
