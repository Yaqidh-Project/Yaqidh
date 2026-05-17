import uuid
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    role_name: Mapped[str] = mapped_column(String(50), nullable=False, default="Teacher")
    notification_prefs: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    phone_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    zones: Mapped[list["Zone"]] = relationship(
        "Zone", secondary="assigned_to", back_populates="users"
    )
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="user")
    incident_notifications: Mapped[list["Incident"]] = relationship(
        "Incident", secondary="notifies", back_populates="notified_users"
    )
    phone_codes: Mapped[list["PhoneVerificationCode"]] = relationship(
        "PhoneVerificationCode", back_populates="user", cascade="all, delete-orphan"
    )
