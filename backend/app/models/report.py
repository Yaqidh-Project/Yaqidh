import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Table, Column, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base

report_incidents = Table(
    "report_incidents",
    Base.metadata,
    Column("report_id", UUID(as_uuid=True), ForeignKey("reports.report_id", ondelete="CASCADE"), primary_key=True),
    Column("incident_id", UUID(as_uuid=True), ForeignKey("incidents.incident_id", ondelete="CASCADE"), primary_key=True),
)


class Report(Base):
    __tablename__ = "reports"

    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    filter_criteria: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    report_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="reports")
    incidents: Mapped[list["Incident"]] = relationship(
        "Incident", secondary="report_incidents", back_populates="reports"
    )
