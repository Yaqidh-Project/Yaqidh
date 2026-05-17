"""
Manager-only operations:
- Create teachers and link them to a zone
"""
import uuid
import bcrypt

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User
from app.models.zone import Zone
from app.schemas.user import TeacherCreate, UserOut
from app.auth.dependencies import require_roles

router = APIRouter(prefix="/manager", tags=["manager"])


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


@router.post(
    "/create-teacher",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Teacher account (Manager only)",
)
async def create_teacher(
    payload: TeacherCreate,
    current_user: User = Depends(require_roles("Manager")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    teacher = User(
        full_name=payload.full_name,
        email=payload.email,
        password=_hash_password(payload.password),
        phone_number=payload.phone_number,
        role_name="Teacher",
        notification_prefs=payload.notification_prefs,
        phone_verified=False,
    )
    db.add(teacher)
    await db.flush()
    await db.refresh(teacher)

    if payload.zone_id:
        zone_result = await db.execute(
            select(Zone)
            .options(selectinload(Zone.users))
            .where(Zone.zone_id == payload.zone_id)
        )
        zone = zone_result.scalar_one_or_none()
        if not zone:
            raise HTTPException(status_code=404, detail="Zone not found")
        if teacher not in zone.users:
            zone.users.append(teacher)
        await db.flush()

    return teacher


