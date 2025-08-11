"""Add all missing columns to assessment_flows table

Revision ID: 030_add_missing_assessment_flow_columns
Revises: 029_add_selected_application_ids
Create Date: 2025-08-11 18:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "030_add_missing_assessment_flow_columns"
down_revision = "029_add_selected_application_ids"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add all missing columns to assessment_flows table"""

    conn = op.get_bind()

    # List of columns to check and add if missing
    columns_to_add = [
        ("architecture_captured", sa.Boolean(), False, "false"),
        ("pause_points", postgresql.JSONB(), False, "[]"),
        ("user_inputs", postgresql.JSONB(), False, "{}"),
        ("phase_results", postgresql.JSONB(), False, "{}"),
        ("agent_insights", postgresql.JSONB(), False, "[]"),
        ("apps_ready_for_planning", postgresql.JSONB(), False, "[]"),
        ("last_user_interaction", sa.DateTime(timezone=True), True, None),
        ("completed_at", sa.DateTime(timezone=True), True, None),
    ]

    for column_name, column_type, nullable, default in columns_to_add:
        # Check if column exists
        result = conn.execute(
            sa.text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assessment_flows'
                AND column_name = :column_name
            """
            ),
            {"column_name": column_name},
        )

        if not result.fetchone():
            # Add the column
            col = sa.Column(column_name, column_type, nullable=nullable)
            if default is not None:
                col.server_default = default

            op.add_column("assessment_flows", col, schema="migration")
            print(f"✅ Added {column_name} column to assessment_flows table")
        else:
            print(f"ℹ️ Column {column_name} already exists in assessment_flows table")


def downgrade() -> None:
    """Remove added columns"""
    columns_to_remove = [
        "architecture_captured",
        "pause_points",
        "user_inputs",
        "phase_results",
        "agent_insights",
        "apps_ready_for_planning",
        "last_user_interaction",
        "completed_at",
    ]

    for column_name in columns_to_remove:
        try:
            op.drop_column("assessment_flows", column_name, schema="migration")
            print(f"✅ Removed {column_name} column from assessment_flows table")
        except Exception:
            pass
