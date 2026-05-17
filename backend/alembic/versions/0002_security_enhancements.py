"""Security enhancements: phone OTP verification

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-02 12:00:00.000000

"""
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

# Revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Update users table to add phone verification status ---
    op.add_column(
        "users",
        sa.Column("phone_verified", sa.Boolean(), nullable=False, server_default="false"),
    )

    # --- Create phone_verification_codes table for OTP system ---
    op.create_table(
        "phone_verification_codes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(6), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False, server_default="false"),
    )
    
    # Create index for faster lookups by user_id
    op.create_index(
        "ix_phone_codes_user_id",
        "phone_verification_codes",
        ["user_id"],
    )


def downgrade() -> None:
    # Reverse changes in case of rollback
    op.drop_index("ix_phone_codes_user_id", table_name="phone_verification_codes")
    op.drop_table("phone_verification_codes")
    op.drop_column("users", "phone_verified")