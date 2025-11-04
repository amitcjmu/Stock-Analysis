"""merge_heads

Revision ID: 125_merge_heads
Revises: 119_add_storage_used_and_tech_debt_fields, 124_add_soft_delete_to_assets
Create Date: 2025-11-04 05:50:19.484635

"""

# No imports needed for merge migration


# revision identifiers, used by Alembic.
revision = "125_merge_heads"
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
