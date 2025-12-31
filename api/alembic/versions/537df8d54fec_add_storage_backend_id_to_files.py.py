"""add_storage_backend_id_to_files

Revision ID: 537df8d54fec
Revises: c8f9d5e23a1b
Create Date: 2025-12-31 23:47:44.862742

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "537df8d54fec"
down_revision: Union[str, Sequence[str], None] = "c8f9d5e23a1b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加 storage_backend_id 到 files 表"""
    op.add_column(
        "files",
        sa.Column("storage_backend_id", sa.String(length=36), nullable=True),
    )
    op.create_foreign_key(
        "fk_files_storage_backend_id",
        "files",
        "storage_backends",
        ["storage_backend_id"],
        ["id"],
    )


def downgrade() -> None:
    """删除 storage_backend_id 从 files 表"""
    op.drop_constraint("fk_files_storage_backend_id", "files", type_="foreignkey")
    op.drop_column("files", "storage_backend_id")
