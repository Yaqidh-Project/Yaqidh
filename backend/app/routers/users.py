from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserOut, UserUpdate, UserRoleUpdate
from app.auth.dependencies import get_current_user, require_roles
import bcrypt
import uuid

router = APIRouter(prefix="/users", tags=["users"])

ALLOWED_ROLES = {"Manager", "Teacher", "Parent"}


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserOut)
async def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    await db.flush()
    await db.refresh(current_user)
    return current_user


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    current_user: User = Depends(require_roles("Manager")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")
    if payload.role_name not in ALLOWED_ROLES:
        raise HTTPException(status_code=422, detail=f"role_name must be one of {ALLOWED_ROLES}")
    user = User(
        full_name=payload.full_name,
        email=payload.email,
        password=_hash_password(payload.password),
        phone_number=payload.phone_number,
        role_name=payload.role_name,
        notification_prefs=payload.notification_prefs,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@router.get("", response_model=list[UserOut])
async def list_users(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_roles("Manager")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: uuid.UUID,
    current_user: User = Depends(require_roles("Manager")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}/role", response_model=UserOut)
async def update_user_role(
    user_id: uuid.UUID,
    payload: UserRoleUpdate,
    current_user: User = Depends(require_roles("Manager")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.role_name not in ALLOWED_ROLES:
        raise HTTPException(status_code=422, detail=f"role_name must be one of {ALLOWED_ROLES}")
    user.role_name = payload.role_name
    await db.flush()
    await db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(require_roles("Manager")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
