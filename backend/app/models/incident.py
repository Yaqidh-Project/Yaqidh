import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Float, Table, Column, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base

notifies = Table(
    "notifies",
    Base.metadata,
    Column("incident_id", UUID(as_uuid=True), ForeignKey("incidents.incident_id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True),
)


class Incident(Base):
    __tablename__ = "incidents"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    danger_category: Mapped[str] = mapped_column(String(100), nullable=False)
    incident_type: Mapped[str] = mapped_column(String(100), nullable=False)
    incident_clip: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="open")
    camera_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cameras.camera_id", ondelete="SET NULL"), nullable=True
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    detections: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    camera: Mapped["Camera"] = relationship("Camera", back_populates="incidents")
    notified_users: Mapped[list["User"]] = relationship(
        "User", secondary="notifies", back_populates="incident_notifications"
    )
    reports: Mapped[list["Report"]] = relationship(
        "Report", secondary="report_incidents", back_populates="incidents"
    )
