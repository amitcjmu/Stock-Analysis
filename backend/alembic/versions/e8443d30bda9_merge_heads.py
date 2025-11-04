"""merge_heads (legacy hash - temporary for Railway transition)

Revision ID: e8443d30bda9
Revises: 119_add_storage_used_and_tech_debt_fields, 124_add_soft_delete_to_assets
Create Date: 2025-11-04 05:50:19.484635

NOTE: This file is a temporary duplicate of 125_merge_heads.py
      It exists only to allow Railway to transition from the old hash-based
      revision ID (e8443d30bda9) to the new 3-digit convention (125_merge_heads).
      This file should be DELETED after Railway successfully deploys migration 126.
"""

# No imports needed for merge migration


# revision identifiers, used by Alembic.
revision = "e8443d30bda9"
down_revision = (
    "119_add_storage_used_and_tech_debt_fields",
    "124_add_soft_delete_to_assets",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
