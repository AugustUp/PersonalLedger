"""add system_configs table for ledger customization

Revision ID: c0ffee000001
Revises: a1b2c3d4e5f6
Create Date: 2026-08-02 22:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c0ffee000001'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'system_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('key', sa.String(length=64), nullable=False),
        sa.Column('value_json', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('system_configs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_system_configs_key'), ['key'], unique=True)


def downgrade() -> None:
    with op.batch_alter_table('system_configs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_system_configs_key'))
    op.drop_table('system_configs')
