"""add_user_role_column

Revision ID: 6cd3c02fe655
Revises: 58ec203bd381
Create Date: 2026-01-06 14:17:46.711956

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6cd3c02fe655"
down_revision: Union[str, Sequence[str], None] = "58ec203bd381"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 添加role列，默认值为'user'
    op.add_column("users", sa.Column("role", sa.String(), nullable=True))
    # 更新现有用户角色为'user'
    op.execute("UPDATE users SET role = 'user' WHERE role IS NULL")


def downgrade() -> None:
    """Downgrade schema."""
    # 删除role列
    op.drop_column("users", "role")
