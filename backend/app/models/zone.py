import uuid
from sqlalchemy import String, Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

assigned_to = Table(
    "assigned_to",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True),
    Column("zone_id", UUID(as_uuid=True), ForeignKey("zones.zone_id", ondelete="CASCADE"), primary_key=True),
)


class Zone(Base):
    __tablename__ = "zones"

    zone_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    zone_name: Mapped[str] = mapped_column(String(255), nullable=False)

    users: Mapped[list["User"]] = relationship(
        "User", secondary="assigned_to", back_populates="zones"
    )
    cameras: Mapped[list["Camera"]] = relationship("Camera", back_populates="zone")
