"""add maintenance.related_system column

Revision ID: a1b2c3d4e5f6
Revises: 23d8758cb419
Create Date: 2026-07-27 10:30:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '23d8758cb419'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('maintenance_records', schema=None) as batch_op:
        batch_op.add_column(sa.Column('related_system', sa.String(length=100), nullable=True))
        batch_op.create_index(batch_op.f('ix_maintenance_records_related_system'), ['related_system'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('maintenance_records', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_maintenance_records_related_system'))
        batch_op.drop_column('related_system')
