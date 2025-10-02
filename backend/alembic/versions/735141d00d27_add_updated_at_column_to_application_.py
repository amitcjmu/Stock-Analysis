"""Add updated_at column to application_name_variants table

Revision ID: 735141d00d27
Revises: add_created_at_variants
Create Date: 2025-09-30 14:27:49.750515

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "735141d00d27"
down_revision = "add_created_at_variants"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add updated_at column to application_name_variants table
    op.add_column(
        "application_name_variants",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.text("now()"),
        ),
        schema="migration",
    )


def downgrade() -> None:
    # Remove updated_at column from application_name_variants table
    op.drop_column("application_name_variants", "updated_at", schema="migration")
