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

# Global Router Lock: Only Managers and Parents can touch this router.
# Teachers and other roles are completely blocked from the root.
router = APIRouter(
    prefix="/zones",
    tags=["zones"],
    dependencies=[
        Depends(require_phone_verified),
        Depends(require_roles("Manager", "Parent"))
    ],
)


@router.post("", response_model=ZoneOut, status_code=status.HTTP_201_CREATED)
async def create_zone(
    payload: ZoneCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Creates a new infrastructure monitoring zone and establishes initial ownership bounds.
    Accessible by both Managers and Parents.
    """
    zone = Zone(zone_name=payload.zone_name)
    db.add(zone)
    await db.flush()

    result = await db.execute(
        select(Zone).options(selectinload(Zone.users)).where(Zone.zone_id == zone.zone_id)
    )
    zone_with_relations = result.scalar_one()
    
    if current_user not in zone_with_relations.users:
        zone_with_relations.users.append(current_user)
        await db.flush()
        await db.commit()

    final_result = await db.execute(
        select(Zone).options(selectinload(Zone.users)).where(Zone.zone_id == zone.zone_id)
    )
    return final_result.scalar_one()


@router.get("", response_model=list[ZoneOut])
async def list_zones(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Lists zones assigned strictly to the calling Manager or Parent user context.
    """
    result = await db.execute(
        select(Zone)
        .join(Zone.users)
        .options(selectinload(Zone.users))
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
    """
    Retrieves a single zone record enforcing clear security access boundaries.
    """
    result = await db.execute(
        select(Zone)
        .options(selectinload(Zone.users))
        .where(Zone.zone_id == zone_id)
    )
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

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
    current_user: User = Depends(get_current_user),  # Updated: Both Manager and Parent can edit their zones
    db: AsyncSession = Depends(get_db),
):
    """
    Updates configuration data fields metadata inside the specified zone grid.
    Accessible by both Managers and Parents (Data isolation applies).
    """
    result = await db.execute(
        select(Zone)
        .options(selectinload(Zone.users))
        .where(Zone.zone_id == zone_id)
    )
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
        
    # Security Boundary Check: Verify that the Parent/Manager actually owns this zone before updating
    if current_user not in zone.users:
        raise HTTPException(status_code=403, detail="Access denied: You do not own this zone")
        
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(zone, field, value)
        
    await db.flush()
    await db.commit()
    await db.refresh(zone)
    return zone


@router.delete("/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_zone(
    zone_id: uuid.UUID,
    current_user: User = Depends(get_current_user),  # Updated: Both Manager and Parent can delete their zones
    db: AsyncSession = Depends(get_db),
):
    """
    Deletes an isolated infrastructure zone block map permanently.
    Accessible by both Managers and Parents (Data isolation applies).
    """
    result = await db.execute(
        select(Zone)
        .options(selectinload(Zone.users))
        .where(Zone.zone_id == zone_id)
    )
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
        
    # Security Boundary Check: Verify that the Parent/Manager actually owns this zone before deleting
    if current_user not in zone.users:
        raise HTTPException(status_code=403, detail="Access denied: You do not own this zone")
        
    await db.delete(zone)
    await db.commit()


@router.post("/{zone_id}/assign", response_model=ZoneOut)
async def assign_user_to_zone(
    zone_id: uuid.UUID,
    payload: ZoneAssign,
    current_user: User = Depends(require_roles("Manager")),  # Strict Keep: Restricted exclusively to Managers
    db: AsyncSession = Depends(get_db),
):
    """
    Maps an authenticated external identity user to a restricted system zone environment.
    Strictly restricted to Managers only. Parents cannot assign users.
    """
    result = await db.execute(
        select(Zone).options(selectinload(Zone.users)).where(Zone.zone_id == zone_id)
    )
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    # Verify that the Manager owns this zone before letting them assign anyone to it
    if current_user not in zone.users:
        raise HTTPException(status_code=403, detail="Access denied: You do not own this zone")

    user_result = await db.execute(select(User).where(User.user_id == payload.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user not in zone.users:
        zone.users.append(user)
        
    await db.flush()
    await db.commit()
    
    return zone