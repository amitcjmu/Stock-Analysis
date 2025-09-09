"""Add missing columns to assessment_flows table

Revision ID: 062_add_description_to_assessment_flows
Revises: 061_fix_null_master_flow_ids
Create Date: 2025-01-09

This migration adds all missing columns to the assessment_flows table
in an idempotent way, checking for existence before adding each column.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "062_add_description_to_assessment_flows"
down_revision = "061_fix_null_master_flow_ids"
branch_labels = None
depends_on = None


def column_exists(table_name: str, column_name: str, schema: str = "migration") -> bool:
    """Check if column exists in table."""
    bind = op.get_bind()
    try:
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
    except Exception:
        return False


def upgrade():
    """Add all missing columns to assessment_flows table if they don't exist."""

    # Add description column if it doesn't exist
    if not column_exists("assessment_flows", "description"):
        op.add_column(
            "assessment_flows",
            sa.Column("description", sa.Text(), nullable=True),
            schema="migration",
        )
        print("Added 'description' column to assessment_flows table")
    else:
        print("Column 'description' already exists, skipping")

    # Add flow_name column if it doesn't exist
    if not column_exists("assessment_flows", "flow_name"):
        # First add as nullable
        op.add_column(
            "assessment_flows",
            sa.Column("flow_name", sa.String(255), nullable=True),
            schema="migration",
        )

        # Update existing rows to have a default flow_name
        op.execute(
            """
            UPDATE migration.assessment_flows
            SET flow_name = COALESCE(flow_name, 'Assessment Flow')
            WHERE flow_name IS NULL
        """
        )

        # Now make it non-nullable
        op.alter_column(
            "assessment_flows", "flow_name", nullable=False, schema="migration"
        )
        print("Added 'flow_name' column to assessment_flows table")
    else:
        print("Column 'flow_name' already exists, skipping")

    # Add phase_progress column if it doesn't exist (JSONB for tracking phase progress)
    if not column_exists("assessment_flows", "phase_progress"):
        op.add_column(
            "assessment_flows",
            sa.Column("phase_progress", JSONB, nullable=False, server_default="{}"),
            schema="migration",
        )
        print("Added 'phase_progress' column to assessment_flows table")
    else:
        print("Column 'phase_progress' already exists, skipping")

    # Add configuration column if it doesn't exist
    if not column_exists("assessment_flows", "configuration"):
        op.add_column(
            "assessment_flows",
            sa.Column("configuration", JSONB, nullable=False, server_default="{}"),
            schema="migration",
        )
        print("Added 'configuration' column to assessment_flows table")
    else:
        print("Column 'configuration' already exists, skipping")

    # Add runtime_state column if it doesn't exist
    if not column_exists("assessment_flows", "runtime_state"):
        op.add_column(
            "assessment_flows",
            sa.Column("runtime_state", JSONB, nullable=False, server_default="{}"),
            schema="migration",
        )
        print("Added 'runtime_state' column to assessment_flows table")
    else:
        print("Column 'runtime_state' already exists, skipping")

    # Add flow_metadata column if it doesn't exist
    if not column_exists("assessment_flows", "flow_metadata"):
        op.add_column(
            "assessment_flows",
            sa.Column("flow_metadata", JSONB, nullable=False, server_default="{}"),
            schema="migration",
        )
        print("Added 'flow_metadata' column to assessment_flows table")
    else:
        print("Column 'flow_metadata' already exists, skipping")

    # Add last_error column if it doesn't exist
    if not column_exists("assessment_flows", "last_error"):
        op.add_column(
            "assessment_flows",
            sa.Column("last_error", sa.Text(), nullable=True),
            schema="migration",
        )
        print("Added 'last_error' column to assessment_flows table")
    else:
        print("Column 'last_error' already exists, skipping")

    # Add error_count column if it doesn't exist
    if not column_exists("assessment_flows", "error_count"):
        op.add_column(
            "assessment_flows",
            sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
            schema="migration",
        )
        print("Added 'error_count' column to assessment_flows table")
    else:
        print("Column 'error_count' already exists, skipping")

    # Add started_at column if it doesn't exist
    if not column_exists("assessment_flows", "started_at"):
        op.add_column(
            "assessment_flows",
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            schema="migration",
        )
        print("Added 'started_at' column to assessment_flows table")
    else:
        print("Column 'started_at' already exists, skipping")

    # Add completed_at column if it doesn't exist
    if not column_exists("assessment_flows", "completed_at"):
        op.add_column(
            "assessment_flows",
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            schema="migration",
        )
        print("Added 'completed_at' column to assessment_flows table")
    else:
        print("Column 'completed_at' already exists, skipping")

    # Set default for flow_status column if it exists (legacy column)
    if column_exists("assessment_flows", "flow_status"):
        try:
            op.alter_column(
                "assessment_flows",
                "flow_status",
                server_default="initialized",
                schema="migration",
            )
            print("Set default for 'flow_status' column")
        except Exception:
            pass  # Ignore if already has default


def downgrade():
    """Remove added columns from assessment_flows table."""
    # Only remove columns that this migration specifically added
    # We check existence to make downgrade idempotent too

    if column_exists("assessment_flows", "completed_at"):
        op.drop_column("assessment_flows", "completed_at", schema="migration")

    if column_exists("assessment_flows", "started_at"):
        op.drop_column("assessment_flows", "started_at", schema="migration")

    if column_exists("assessment_flows", "error_count"):
        op.drop_column("assessment_flows", "error_count", schema="migration")

    if column_exists("assessment_flows", "last_error"):
        op.drop_column("assessment_flows", "last_error", schema="migration")

    if column_exists("assessment_flows", "flow_metadata"):
        op.drop_column("assessment_flows", "flow_metadata", schema="migration")

    if column_exists("assessment_flows", "runtime_state"):
        op.drop_column("assessment_flows", "runtime_state", schema="migration")

    if column_exists("assessment_flows", "configuration"):
        op.drop_column("assessment_flows", "configuration", schema="migration")

    if column_exists("assessment_flows", "phase_progress"):
        op.drop_column("assessment_flows", "phase_progress", schema="migration")

    if column_exists("assessment_flows", "description"):
        op.drop_column("assessment_flows", "description", schema="migration")

    # Don't drop flow_name on downgrade as it might have existed before this migration
