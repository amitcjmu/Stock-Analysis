"""Rename metadata columns to avoid SQLAlchemy reserved word conflict

Revision ID: 032b_rename_metadata_columns
Revises: 032_add_master_flow_id_to_assessment_flows
Create Date: 2025-08-23 17:50:00.000000

This migration renames all 'metadata' columns to avoid conflict with SQLAlchemy's
reserved attribute name. The 'metadata' attribute is reserved by SQLAlchemy's
Declarative API and cannot be used as a column name.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "032b_rename_metadata_columns"
down_revision = "032_add_master_flow_id_to_assessment_flows"
branch_labels = None
depends_on = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table within the 'migration' schema."""
    bind = op.get_bind()
    try:
        stmt = sa.text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                  AND table_name = :table_name
                  AND column_name = :column_name
            )
            """
        )
        result = bind.execute(
            stmt, {"table_name": table_name, "column_name": column_name}
        ).scalar()
        return bool(result)
    except Exception as e:
        print(f"Error checking if column {column_name} exists in {table_name}: {e}")
        return False


def upgrade() -> None:
    """Rename metadata columns to avoid SQLAlchemy reserved word conflict"""

    print("🔄 Renaming metadata columns to avoid SQLAlchemy reserved word conflict...")

    # Define column renames: (table_name, old_column_name, new_column_name)
    column_renames = [
        # assessment_flows table
        ("assessment_flows", "metadata", "flow_metadata"),
        # engagement_architecture_standards table (formerly assessment_flow_scores)
        ("engagement_architecture_standards", "metadata", "score_metadata"),
        # tech_debt_analyses table (formerly assessment_risks)
        ("tech_debt_analyses", "metadata", "risk_metadata"),
        # sixr_decisions table (formerly architecture_decisions)
        ("sixr_decisions", "metadata", "decision_metadata"),
        # assessment_learning_feedback table (formerly recommendations)
        ("assessment_learning_feedback", "metadata", "recommendation_metadata"),
        # application_architecture_overrides table
        ("application_architecture_overrides", "metadata", "override_metadata"),
        # application_components table
        ("application_components", "metadata", "component_metadata"),
        # component_treatments table (formerly migration_tasks)
        ("component_treatments", "metadata", "task_metadata"),
        # cache tables
        ("cache_metadata", "metadata", "cache_metadata"),
        ("cache_performance_logs", "metadata", "operation_metadata"),
        ("cache_invalidation_logs", "metadata", "invalidation_metadata"),
    ]

    for table_name, old_column_name, new_column_name in column_renames:
        try:
            # Check if old column exists and new column doesn't
            if column_exists(table_name, old_column_name) and not column_exists(
                table_name, new_column_name
            ):
                op.alter_column(
                    table_name,
                    old_column_name,
                    new_column_name=new_column_name,
                    schema="migration",
                )
                print(
                    f"  ✅ Renamed column {old_column_name} to {new_column_name} in table {table_name}"
                )
            elif column_exists(table_name, new_column_name):
                print(
                    f"  ℹ️  Column {new_column_name} already exists in table {table_name}, skipping"
                )
            else:
                print(
                    f"  ⚠️  Table {table_name} or column {old_column_name} does not exist, skipping"
                )
        except Exception as e:
            print(
                f"  ⚠️  Could not rename column {old_column_name} in table {table_name}: {str(e)}"
            )

    print("✅ Metadata column rename migration completed successfully")


def downgrade() -> None:
    """Revert column renames"""

    print("🔄 Reverting metadata column renames...")

    # Define column renames in reverse: (table_name, new_column_name, old_column_name)
    column_renames = [
        ("assessment_flows", "flow_metadata", "metadata"),
        ("engagement_architecture_standards", "score_metadata", "metadata"),
        ("tech_debt_analyses", "risk_metadata", "metadata"),
        ("sixr_decisions", "decision_metadata", "metadata"),
        ("assessment_learning_feedback", "recommendation_metadata", "metadata"),
        ("application_architecture_overrides", "override_metadata", "metadata"),
        ("application_components", "component_metadata", "metadata"),
        ("component_treatments", "task_metadata", "metadata"),
        ("cache_metadata", "cache_metadata", "metadata"),
        ("cache_performance_logs", "operation_metadata", "metadata"),
        ("cache_invalidation_logs", "invalidation_metadata", "metadata"),
    ]

    for table_name, new_column_name, old_column_name in column_renames:
        try:
            # Check if new column exists and old column doesn't
            if column_exists(table_name, new_column_name) and not column_exists(
                table_name, old_column_name
            ):
                op.alter_column(
                    table_name,
                    new_column_name,
                    new_column_name=old_column_name,
                    schema="migration",
                )
                print(
                    f"  ✅ Reverted column {new_column_name} to {old_column_name} in table {table_name}"
                )
            elif column_exists(table_name, old_column_name):
                print(
                    f"  ℹ️  Column {old_column_name} already exists in table {table_name}, skipping"
                )
            else:
                print(
                    f"  ⚠️  Table {table_name} or column {new_column_name} does not exist, skipping"
                )
        except Exception as e:
            print(
                f"  ⚠️  Could not revert column {new_column_name} in table {table_name}: {str(e)}"
            )

    print("✅ Metadata column revert completed")
