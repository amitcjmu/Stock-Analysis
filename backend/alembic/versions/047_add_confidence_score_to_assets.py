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
    # Check if column already exists
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'migration'
            AND table_name = 'assets'
            AND column_name = 'confidence_score'
            """
        )
    )

    if not result.fetchone():
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
        print("✅ Added confidence_score column to assets table")
    else:
        print(
            "⚠️  Column 'confidence_score' already exists in assets table, skipping creation"
        )


def downgrade() -> None:
    """Remove confidence_score column from assets table"""
    try:
        op.drop_column("assets", "confidence_score", schema="migration")
        print("✅ Removed confidence_score column from assets table")
    except Exception as e:
        print(f"⚠️  Could not drop column 'confidence_score': {e}")
