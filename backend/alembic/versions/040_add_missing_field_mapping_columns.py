"""Add missing field_type and agent_reasoning columns to import_field_mappings

Revision ID: 040_add_missing_field_mapping_columns
Revises: 039_create_pattern_type_enum
Create Date: 2025-08-29 07:30:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "040_add_missing_field_mapping_columns"
down_revision = "039_create_pattern_type_enum"
branch_labels = None
depends_on = None


def upgrade():
    """Add missing columns to import_field_mappings table."""
    conn = op.get_bind()

    # Check if columns already exist before adding them
    result = conn.execute(
        text(
            """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'migration'
        AND table_name = 'import_field_mappings'
        AND column_name IN ('field_type', 'agent_reasoning')
    """
        )
    )
    existing_columns = [row[0] for row in result]

    # Add field_type column if it doesn't exist
    if "field_type" not in existing_columns:
        op.add_column(
            "import_field_mappings",
            sa.Column(
                "field_type",
                sa.String(50),
                nullable=True,
                comment="Data type of the field (e.g., string, number, date)",
            ),
            schema="migration",
        )

    # Add agent_reasoning column if it doesn't exist
    if "agent_reasoning" not in existing_columns:
        op.add_column(
            "import_field_mappings",
            sa.Column(
                "agent_reasoning",
                sa.Text(),
                nullable=True,
                comment="AI agent reasoning for the mapping suggestion",
            ),
            schema="migration",
        )


def downgrade():
    """Remove the added columns."""
    try:
        op.drop_column("import_field_mappings", "agent_reasoning", schema="migration")
    except Exception as e:
        print(f"⚠️  Could not drop column 'agent_reasoning': {e}")

    try:
        op.drop_column("import_field_mappings", "field_type", schema="migration")
    except Exception as e:
        print(f"⚠️  Could not drop column 'field_type': {e}")
