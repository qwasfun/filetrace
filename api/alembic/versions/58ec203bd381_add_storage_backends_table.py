"""add_storage_backends_table

Revision ID: 58ec203bd381
Revises: 4fc0083bcb6d
Create Date: 2026-01-06 12:44:31.250045

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "58ec203bd381"
down_revision: Union[str, Sequence[str], None] = "4fc0083bcb6d"
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
    op.add_column(
        "files", sa.Column("storage_backend_id", sa.String(length=36), nullable=True)
    )
    op.create_foreign_key(
        "fk_files_storage_backend_id",
        "files",
        "storage_backends",
        ["storage_backend_id"],
        ["id"],
    )


def downgrade() -> None:
    """删除存储后端配置表"""
    op.drop_constraint("fk_files_storage_backend_id", "files", type_="foreignkey")
    op.drop_column("files", "storage_backend_id")
    op.drop_index(op.f("ix_storage_backends_name"), table_name="storage_backends")
    op.drop_index(op.f("ix_storage_backends_id"), table_name="storage_backends")
    op.drop_table("storage_backends")
