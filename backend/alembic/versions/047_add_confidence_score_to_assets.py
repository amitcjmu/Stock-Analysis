"""Add confidence_score column to assets table

Revision ID: 047_add_confidence_score_to_assets
Revises: 046_fix_application_name_variants_timestamps
Create Date: 2025-09-03 01:50:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "047_add_confidence_score_to_assets"
down_revision = "046_fix_application_name_variants_timestamps"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add confidence_score column to assets table"""
    op.add_column(
        "assets",
        sa.Column(
            "confidence_score",
            sa.Float(),
            nullable=True,
            comment="Confidence score for the asset (0.0-1.0)",
        ),
        schema="migration",
    )


def downgrade() -> None:
    """Remove confidence_score column from assets table"""
    op.drop_column("assets", "confidence_score", schema="migration")
