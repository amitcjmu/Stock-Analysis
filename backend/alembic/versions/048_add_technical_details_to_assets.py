"""add technical_details to assets

Revision ID: 048_add_technical_details_to_assets
Revises: 047_add_confidence_score_to_assets
Create Date: 2025-09-03 03:32:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "048_add_technical_details_to_assets"
down_revision = "047_add_confidence_score_to_assets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add technical_details column to assets table if it doesn't exist
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'migration'
            AND table_name = 'assets'
            AND column_name = 'technical_details'
        """
        )
    )
    if not result.fetchone():
        op.add_column(
            "assets",
            sa.Column(
                "technical_details",
                sa.JSON(),
                nullable=True,
                comment="A JSON blob containing technical details and enrichments for the asset.",
            ),
            schema="migration",
        )


def downgrade() -> None:
    # Remove technical_details column from assets table
    op.drop_column("assets", "technical_details", schema="migration")
