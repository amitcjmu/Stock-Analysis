"""merge_heads_fix_questionnaire_asset_linkage

Revision ID: cef530e273d4
Revises: 017_add_asset_id_to_questionnaire_responses, 1687c833bfcc
Create Date: 2025-08-27 09:05:04.208424

"""

# Merge migration - no operations needed


# revision identifiers, used by Alembic.
revision = "cef530e273d4"
down_revision = ("017_add_asset_id_to_questionnaire_responses", "1687c833bfcc")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
