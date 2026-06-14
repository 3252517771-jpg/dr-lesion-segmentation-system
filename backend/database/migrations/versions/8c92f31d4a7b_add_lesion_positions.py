"""add lesion positions

Revision ID: 8c92f31d4a7b
Revises: 30496e383b13
Create Date: 2026-06-14 16:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "8c92f31d4a7b"
down_revision = "30496e383b13"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("diagnoses", schema=None) as batch_op:
        batch_op.add_column(sa.Column("lesion_positions", sa.Text(), server_default="{}", nullable=False))


def downgrade():
    with op.batch_alter_table("diagnoses", schema=None) as batch_op:
        batch_op.drop_column("lesion_positions")
