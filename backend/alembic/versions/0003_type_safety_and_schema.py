"""Type safety, schema expansion, and JSONB fields

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-05 00:00:00.000000

Changes:
- users: add is_active boolean; convert notification_prefs Text → JSONB
- cameras: add stream_url, ip_address, status
- incidents: add detections JSONB column
- reports: convert filter_criteria Text → JSONB
"""
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users ---
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.execute(
        "ALTER TABLE users ALTER COLUMN notification_prefs TYPE JSONB USING "
        "CASE WHEN notification_prefs IS NULL THEN NULL "
        "ELSE notification_prefs::jsonb END"
    )

    # --- cameras ---
    op.add_column(
        "cameras",
        sa.Column("stream_url", sa.String(500), nullable=False, server_default=""),
    )
    op.add_column(
        "cameras",
        sa.Column("ip_address", sa.String(100), nullable=True),
    )
    op.add_column(
        "cameras",
        sa.Column("status", sa.String(50), nullable=False, server_default="Active"),
    )

    # --- incidents ---
    op.add_column(
        "incidents",
        sa.Column("detections", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    # --- reports ---
    op.execute(
        "ALTER TABLE reports ALTER COLUMN filter_criteria TYPE JSONB USING "
        "CASE WHEN filter_criteria IS NULL THEN NULL "
        "ELSE filter_criteria::jsonb END"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE reports ALTER COLUMN filter_criteria TYPE TEXT USING filter_criteria::text"
    )
    op.drop_column("incidents", "detections")
    op.drop_column("cameras", "status")
    op.drop_column("cameras", "ip_address")
    op.drop_column("cameras", "stream_url")
    op.execute(
        "ALTER TABLE users ALTER COLUMN notification_prefs TYPE TEXT USING notification_prefs::text"
    )
    op.drop_column("users", "is_active")
