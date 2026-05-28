"""add otp_verification table

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-29 12:00:00.000000

"""
from datetime import datetime, timezone
import sqlalchemy as sa
from alembic import op
import uuid

# revision identifiers, used by Alembic.
revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'otp_verification',
        sa.Column('otp_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('otp_code', sa.String(6), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('failed_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('otp_id')
    )
    op.create_index('ix_otp_verification_user_id', 'otp_verification', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_otp_verification_user_id', table_name='otp_verification')
    op.drop_table('otp_verification')
