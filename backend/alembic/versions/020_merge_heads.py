"""Merge migration heads

Revision ID: 020_merge_heads
Revises: 019_implement_row_level_security
Create Date: 2025-01-13 02:00:00.000000

CC: Merge multiple heads to resolve alembic migration conflict
"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "020_merge_heads"
down_revision: Union[str, Sequence[str], None] = "019_implement_row_level_security"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge point for multiple heads - no operations needed"""
    pass


def downgrade() -> None:
    """Merge point for multiple heads - no operations needed"""
    pass
