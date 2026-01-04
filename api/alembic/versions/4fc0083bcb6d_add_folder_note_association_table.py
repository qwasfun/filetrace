"""add folder_note_association table

Revision ID: 4fc0083bcb6d
Revises: ebae89491d40
Create Date: 2026-01-04 22:34:57.102546

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4fc0083bcb6d"
down_revision: Union[str, Sequence[str], None] = "ebae89491d40"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "folder_note_association",
        sa.Column(
            "folder_id",
            sa.String(36),
            sa.ForeignKey("folders.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "note_id",
            sa.String(36),
            sa.ForeignKey("notes.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("folder_note_association")
