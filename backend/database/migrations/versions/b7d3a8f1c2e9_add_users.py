"""add users

Revision ID: b7d3a8f1c2e9
Revises: 8c92f31d4a7b
Create Date: 2026-06-14 22:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "b7d3a8f1c2e9"
down_revision = "8c92f31d4a7b"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("linked_patient_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.CheckConstraint("role IN ('doctor', 'patient')", name="ck_users_role"),
        sa.ForeignKeyConstraint(["linked_patient_id"], ["patients.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.create_index("idx_users_deleted", ["is_deleted"], unique=False)
        batch_op.create_index("idx_users_role", ["role"], unique=False)
        batch_op.create_index("idx_users_username", ["username"], unique=False)


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index("idx_users_username")
        batch_op.drop_index("idx_users_role")
        batch_op.drop_index("idx_users_deleted")
    op.drop_table("users")
