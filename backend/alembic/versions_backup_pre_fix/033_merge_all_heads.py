"""Merge all migration heads

Revision ID: 033_merge_all_heads
Revises: 032b_rename_metadata_columns, merge_mfo_testing_heads
Create Date: 2025-08-23 17:52:00.000000

This migration merges all heads to create a single migration path.
"""

# revision identifiers, used by Alembic.
revision = "033_merge_all_heads"
down_revision = ("032b_rename_metadata_columns", "merge_mfo_testing_heads")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Merge completed - no operations needed"""
    pass


def downgrade() -> None:
    """Merge revert - no operations needed"""
    pass
