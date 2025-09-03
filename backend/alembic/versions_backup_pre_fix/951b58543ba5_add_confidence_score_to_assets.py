"""add confidence_score to assets

Revision ID: 951b58543ba5
Revises: 029_complete_assessment_flows_schema
Create Date: 2025-08-11 18:33:24.911446

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "951b58543ba5"
down_revision = "029_complete_assessment_flows_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add confidence_score column to assets table if it doesn't exist
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
                comment="A confidence score (0.0-1.0) indicating reliability of asset data.",
            ),
            schema="migration",
        )


def downgrade() -> None:
    # Remove confidence_score column from assets table
    op.drop_column("assets", "confidence_score", schema="migration")
