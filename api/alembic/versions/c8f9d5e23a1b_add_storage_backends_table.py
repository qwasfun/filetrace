"""add_storage_backends_table

Revision ID: c8f9d5e23a1b
Revises: ebae89491d40
Create Date: 2025-12-31 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c8f9d5e23a1b"
down_revision: Union[str, Sequence[str], None] = "ebae89491d40"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加存储后端配置表"""
    op.create_table(
        "storage_backends",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("backend_type", sa.String(), nullable=False),
        sa.Column("is_active", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_default", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("config_json", sa.Text(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_storage_backends_id"), "storage_backends", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_storage_backends_name"), "storage_backends", ["name"], unique=True
    )


def downgrade() -> None:
    """删除存储后端配置表"""
    op.drop_index(op.f("ix_storage_backends_name"), table_name="storage_backends")
    op.drop_index(op.f("ix_storage_backends_id"), table_name="storage_backends")
    op.drop_table("storage_backends")
