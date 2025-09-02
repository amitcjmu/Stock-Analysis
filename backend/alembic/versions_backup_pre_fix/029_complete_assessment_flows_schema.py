"""Complete assessment_flows table schema - consolidated migration

Revision ID: 029_complete_assessment_flows_schema
Revises: 028_add_updated_at_trigger_for_failure_journal
Create Date: 2025-08-11 18:30:00.000000

This consolidated migration adds all missing columns to the assessment_flows table
in a single operation, replacing the need for multiple incremental migrations.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "029_complete_assessment_flows_schema"
down_revision = "028_add_updated_at_trigger_for_failure_journal"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add all missing columns to assessment_flows table in one migration"""

    conn = op.get_bind()

    # Complete list of columns that should exist in assessment_flows
    columns_to_add = [
        # Core identification and status columns
        ("selected_application_ids", postgresql.JSONB(), False, "[]"),
        ("architecture_captured", sa.Boolean(), False, "false"),
        ("status", sa.String(50), False, "'initialized'"),
        ("progress", sa.Integer(), False, "0"),
        ("current_phase", sa.String(100), True, None),
        ("next_phase", sa.String(100), True, None),
        # Data storage columns
        ("pause_points", postgresql.JSONB(), False, "[]"),
        ("user_inputs", postgresql.JSONB(), False, "{}"),
        ("phase_results", postgresql.JSONB(), False, "{}"),
        ("agent_insights", postgresql.JSONB(), False, "[]"),
        ("apps_ready_for_planning", postgresql.JSONB(), False, "[]"),
        # Timestamp columns
        ("last_user_interaction", sa.DateTime(timezone=True), True, None),
        ("completed_at", sa.DateTime(timezone=True), True, None),
    ]

    # Check for created_at and updated_at separately as they might already exist
    timestamp_columns = [
        ("created_at", sa.DateTime(timezone=True), False, "CURRENT_TIMESTAMP"),
        ("updated_at", sa.DateTime(timezone=True), False, "CURRENT_TIMESTAMP"),
    ]

    print("🔄 Starting assessment_flows schema completion...")
    added_count = 0

    # Add missing columns
    for column_name, column_type, nullable, default in (
        columns_to_add + timestamp_columns
    ):
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
            print(f"  ✅ Added {column_name} column")
            added_count += 1
        else:
            print(f"  ℹ️  Column {column_name} already exists")

    # Add indexes for better query performance
    indexes_to_add = [
        ("ix_assessment_flows_status", ["status"]),
        ("ix_assessment_flows_current_phase", ["current_phase"]),
        ("ix_assessment_flows_next_phase", ["next_phase"]),
        ("ix_assessment_flows_engagement_id", ["engagement_id"]),
    ]

    for index_name, columns in indexes_to_add:
        try:
            # Check if index exists first
            result = conn.execute(
                sa.text(
                    """
                    SELECT indexname
                    FROM pg_indexes
                    WHERE schemaname = 'migration'
                    AND tablename = 'assessment_flows'
                    AND indexname = :index_name
                """
                ),
                {"index_name": index_name},
            )

            if not result.fetchone():
                op.create_index(
                    index_name, "assessment_flows", columns, schema="migration"
                )
                print(f"  ✅ Added index {index_name}")
            else:
                print(f"  ℹ️  Index {index_name} already exists")
        except Exception as e:
            print(f"  ⚠️  Could not create index {index_name}: {str(e)}")

    print(
        f"\n✅ Assessment flows schema completion finished - added {added_count} columns"
    )


def downgrade() -> None:
    """Remove all columns added by this migration"""

    print("🔄 Rolling back assessment_flows schema changes...")

    # Drop indexes first
    indexes_to_remove = [
        "ix_assessment_flows_status",
        "ix_assessment_flows_current_phase",
        "ix_assessment_flows_next_phase",
        "ix_assessment_flows_engagement_id",
    ]

    for index_name in indexes_to_remove:
        try:
            op.drop_index(index_name, "assessment_flows", schema="migration")
            print(f"  ✅ Dropped index {index_name}")
        except Exception:
            pass  # Index might not exist

    # Drop columns
    columns_to_remove = [
        "selected_application_ids",
        "architecture_captured",
        "status",
        "progress",
        "current_phase",
        "next_phase",
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
            print(f"  ✅ Removed {column_name} column")
        except Exception:
            pass  # Column might not exist

    print("\n✅ Assessment flows schema rollback completed")
