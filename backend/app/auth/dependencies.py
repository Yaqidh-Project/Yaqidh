from fastapi import Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.auth.jwt import verify_token
import uuid

bearer_scheme = HTTPBearer(auto_error=False)


async def _load_user(
    credentials: HTTPAuthorizationCredentials | None,
    token_query: str | None,
    db: AsyncSession,
) -> User:
    # Get the token from either the header credentials or fallback to the query parameter
    token = None
    if credentials:
        token = credentials.credentials
    elif token_query:
        token = token_query

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization credentials missing (checked header and query token)",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    payload = verify_token(token, token_type="access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    result = await db.execute(select(User).where(User.user_id == uuid.UUID(user_id_str)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    token: str | None = Query(None, alias="token"),
    db: AsyncSession = Depends(get_db),
) -> User:
    return await _load_user(credentials, token, db)


async def require_phone_verified(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.phone_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Phone number not verified. Please verify via POST /auth/phone/request-code.",
        )
    return current_user


def require_roles(*roles: str):
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role_name not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(roles)}. Your role: {current_user.role_name}",
            )
        return current_user
    return dependency