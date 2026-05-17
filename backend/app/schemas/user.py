import uuid
from pydantic import BaseModel, EmailStr
from typing import Optional, Any
from app.models.enums import UserRole


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    phone_number: Optional[str] = None
    role_name: UserRole = UserRole.Parent
    notification_prefs: Optional[dict[str, Any]] = None


class TeacherCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    phone_number: Optional[str] = None
    notification_prefs: Optional[dict[str, Any]] = None
    zone_id: Optional[uuid.UUID] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    notification_prefs: Optional[dict[str, Any]] = None


class UserRoleUpdate(BaseModel):
    role_name: UserRole


class UserOut(BaseModel):
    user_id: uuid.UUID
    full_name: str
    email: str
    phone_number: Optional[str] = None
    role_name: str
    notification_prefs: Optional[dict[str, Any]] = None
    is_active: bool = True
    phone_verified: bool = False

    model_config = {"from_attributes": True}
