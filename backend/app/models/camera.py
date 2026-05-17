import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Camera(Base):
    __tablename__ = "cameras"

    camera_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    camera_name: Mapped[str] = mapped_column(String(255), nullable=False)
    camera_type: Mapped[str] = mapped_column(String(100), nullable=False, default="IP")
    stream_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    ip_address: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Active")
    zone_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("zones.zone_id", ondelete="CASCADE"), nullable=False
    )

    zone: Mapped["Zone"] = relationship("Zone", back_populates="cameras")
    incidents: Mapped[list["Incident"]] = relationship("Incident", back_populates="camera")
