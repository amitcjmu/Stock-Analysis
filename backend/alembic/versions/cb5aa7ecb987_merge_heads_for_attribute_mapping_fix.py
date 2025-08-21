"""merge heads for attribute mapping fix

Revision ID: cb5aa7ecb987
Revises: 020_merge_heads, 030_add_sixr_analysis_tables
Create Date: 2025-08-20 23:08:47.588919

"""

# Merge migration - no imports needed


# revision identifiers, used by Alembic.
revision = "cb5aa7ecb987"
down_revision = ("020_merge_heads", "030_add_sixr_analysis_tables")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
