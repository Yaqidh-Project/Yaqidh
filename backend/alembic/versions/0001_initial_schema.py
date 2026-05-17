"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-02 00:00:00.000000

"""
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password", sa.String(255), nullable=False),
        sa.Column("phone_number", sa.String(50), nullable=True),
        sa.Column("role_name", sa.String(50), nullable=False, server_default="Teacher"),
        sa.Column("notification_prefs", sa.Text(), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "zones",
        sa.Column("zone_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("zone_name", sa.String(255), nullable=False),
    )

    op.create_table(
        "assigned_to",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("zone_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("zones.zone_id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "cameras",
        sa.Column("camera_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("camera_name", sa.String(255), nullable=False),
        sa.Column("camera_type", sa.String(100), nullable=False, server_default="IP"),
        sa.Column("zone_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("zones.zone_id", ondelete="CASCADE"), nullable=False),
    )

    op.create_table(
        "incidents",
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("danger_category", sa.String(100), nullable=False),
        sa.Column("incident_type", sa.String(100), nullable=False),
        sa.Column("incident_clip", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="open"),
        sa.Column("camera_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cameras.camera_id", ondelete="SET NULL"), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
    )

    op.create_table(
        "notifies",
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.incident_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "reports",
        sa.Column("report_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("filter_criteria", sa.Text(), nullable=True),
        sa.Column("report_summary", sa.Text(), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False),
    )

    op.create_table(
        "report_incidents",
        sa.Column("report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reports.report_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.incident_id", ondelete="CASCADE"), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("report_incidents")
    op.drop_table("reports")
    op.drop_table("notifies")
    op.drop_table("incidents")
    op.drop_table("cameras")
    op.drop_table("assigned_to")
    op.drop_table("zones")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
