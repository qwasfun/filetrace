"""add_allow_client_direct_upload_column

Revision ID: 58d5027c1abd
Revises: 6cd3c02fe655
Create Date: 2026-01-09 18:18:42.622942

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "58d5027c1abd"
down_revision: Union[str, Sequence[str], None] = "6cd3c02fe655"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加allow_client_direct_upload字段到storage_backends表"""
    op.add_column(
        "storage_backends",
        sa.Column(
            "allow_client_direct_upload",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    """删除allow_client_direct_upload字段"""
    op.drop_column("storage_backends", "allow_client_direct_upload")
