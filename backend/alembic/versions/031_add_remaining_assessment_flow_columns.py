"""Add remaining missing columns to assessment_flows table

Revision ID: 031_add_remaining_assessment_flow_columns
Revises: 030_add_missing_assessment_flow_columns
Create Date: 2025-08-11 18:15:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "031_add_remaining_assessment_flow_columns"
down_revision = "030_add_missing_assessment_flow_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add remaining missing columns to assessment_flows table"""

    conn = op.get_bind()

    # List of remaining columns to check and add if missing
    columns_to_add = [
        ("status", sa.String(50), False, "initialized"),
        ("progress", sa.Integer(), False, "0"),
        ("current_phase", sa.String(100), True, None),
        ("next_phase", sa.String(100), True, None),
        ("created_at", sa.DateTime(timezone=True), False, "CURRENT_TIMESTAMP"),
        ("updated_at", sa.DateTime(timezone=True), False, "CURRENT_TIMESTAMP"),
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

    # Add indexes for commonly queried columns
    try:
        op.create_index(
            "ix_assessment_flows_status",
            "assessment_flows",
            ["status"],
            schema="migration",
            if_not_exists=True,
        )
        print("✅ Added index on status column")
    except Exception:
        print("ℹ️ Index on status column already exists")

    try:
        op.create_index(
            "ix_assessment_flows_current_phase",
            "assessment_flows",
            ["current_phase"],
            schema="migration",
            if_not_exists=True,
        )
        print("✅ Added index on current_phase column")
    except Exception:
        print("ℹ️ Index on current_phase column already exists")

    try:
        op.create_index(
            "ix_assessment_flows_next_phase",
            "assessment_flows",
            ["next_phase"],
            schema="migration",
            if_not_exists=True,
        )
        print("✅ Added index on next_phase column")
    except Exception:
        print("ℹ️ Index on next_phase column already exists")


def downgrade() -> None:
    """Remove added columns and indexes"""

    # Drop indexes first
    try:
        op.drop_index(
            "ix_assessment_flows_status", "assessment_flows", schema="migration"
        )
    except Exception:
        pass

    try:
        op.drop_index(
            "ix_assessment_flows_current_phase", "assessment_flows", schema="migration"
        )
    except Exception:
        pass

    try:
        op.drop_index(
            "ix_assessment_flows_next_phase", "assessment_flows", schema="migration"
        )
    except Exception:
        pass

    # Drop columns
    columns_to_remove = [
        "status",
        "progress",
        "current_phase",
        "next_phase",
        "created_at",
        "updated_at",
    ]

    for column_name in columns_to_remove:
        try:
            op.drop_column("assessment_flows", column_name, schema="migration")
            print(f"✅ Removed {column_name} column from assessment_flows table")
        except Exception:
            pass
