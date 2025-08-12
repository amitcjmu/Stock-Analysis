"""add technical_details to assets

Revision ID: 7cc356fcc04a
Revises: 951b58543ba5
Create Date: 2025-08-11 18:36:57.583309

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7cc356fcc04a"
down_revision = "951b58543ba5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add technical_details column to assets table
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
