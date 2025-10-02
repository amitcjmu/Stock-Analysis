"""Add updated_at column to application_name_variants table

Revision ID: 078_add_updated_at_to_name_variants
Revises: add_created_at_variants
Create Date: 2025-09-30 14:27:49.750515

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "078_add_updated_at_to_name_variants"
down_revision = "add_created_at_variants"
branch_labels = None
depends_on = None


def column_exists(table_name: str, column_name: str, schema: str = "migration") -> bool:
    """Check if column exists in table.

    Note: Exceptions are allowed to propagate to ensure migration fails
    on unexpected database errors rather than silently returning False.
    """
    bind = op.get_bind()
    stmt = sa.text(
        """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = :schema
              AND table_name = :table_name
              AND column_name = :column_name
        )
    """
    )
    result = bind.execute(
        stmt,
        {"schema": schema, "table_name": table_name, "column_name": column_name},
    ).scalar()
    return bool(result)


def upgrade() -> None:
    """Add updated_at column to application_name_variants table."""
    # Check if column already exists before adding
    if not column_exists("application_name_variants", "updated_at"):
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
    """Remove updated_at column from application_name_variants table."""
    # Check if column exists before dropping
    if column_exists("application_name_variants", "updated_at"):
        op.drop_column("application_name_variants", "updated_at", schema="migration")
