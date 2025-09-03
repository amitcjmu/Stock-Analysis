"""fix_timestamp_mixin_timezone_issues

Revision ID: c279c3c0699d
Revises: 7cc356fcc04a
Create Date: 2025-08-11 18:47:10.107772

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "c279c3c0699d"
down_revision = "7cc356fcc04a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Fix timezone issues in TimestampMixin columns for all affected tables
    # Convert timezone-naive columns to timezone-aware columns

    tables_to_fix = [
        "collected_data_inventory",
        "platform_adapters",
        "cache_metadata",
        "collection_data_gaps",
        "collection_questionnaire_responses",
        "collection_flows",
    ]

    for table_name in tables_to_fix:
        # Convert created_at to TIMESTAMPTZ
        op.execute(
            f"""
            ALTER TABLE migration.{table_name}
            ALTER COLUMN created_at TYPE TIMESTAMPTZ
            USING created_at AT TIME ZONE 'UTC'
        """
        )

        # Convert updated_at to TIMESTAMPTZ
        op.execute(
            f"""
            ALTER TABLE migration.{table_name}
            ALTER COLUMN updated_at TYPE TIMESTAMPTZ
            USING updated_at AT TIME ZONE 'UTC'
        """
        )


def downgrade() -> None:
    # Revert timezone-aware columns back to timezone-naive

    tables_to_fix = [
        "collected_data_inventory",
        "platform_adapters",
        "cache_metadata",
        "collection_data_gaps",
        "collection_questionnaire_responses",
        "collection_flows",
    ]

    for table_name in tables_to_fix:
        # Convert created_at back to TIMESTAMP
        op.execute(
            f"""
            ALTER TABLE migration.{table_name}
            ALTER COLUMN created_at TYPE TIMESTAMP
            USING created_at AT TIME ZONE 'UTC'
        """
        )

        # Convert updated_at back to TIMESTAMP
        op.execute(
            f"""
            ALTER TABLE migration.{table_name}
            ALTER COLUMN updated_at TYPE TIMESTAMP
            USING updated_at AT TIME ZONE 'UTC'
        """
        )
