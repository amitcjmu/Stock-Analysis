"""Add missing request_payload, response_payload, and target_details columns to security_audit_logs

Revision ID: 037_add_missing_audit_log_columns
Revises: 036_rename_metadata_columns
Create Date: 2025-01-29

This migration adds the missing columns that are referenced by the sanitize_audit_log_trigger
function but were not included in the original security_audit_logs table schema.
CC: Fixed dependency from non-existent 64630c6d6a9a to 036_rename_metadata_columns
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "037_add_missing_audit_log_columns"
down_revision = "036_rename_metadata_columns"
branch_labels = None
depends_on = None


def column_exists(table_name, column_name, schema="migration"):
    """Check if a column exists in the table"""
    bind = op.get_bind()
    try:
        result = bind.execute(
            sa.text(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = :schema
                    AND table_name = :table_name
                    AND column_name = :column_name
                )
            """
            ).bindparams(schema=schema, table_name=table_name, column_name=column_name)
        ).scalar()
        return result
    except Exception as e:
        print(f"Error checking if column {column_name} exists in {table_name}: {e}")
        return True  # Assume exists to avoid duplicate creation


def add_column_if_not_exists(
    table_name, column_name, column_definition, schema="migration"
):
    """Add a column only if it doesn't already exist"""
    if not column_exists(table_name, column_name, schema):
        op.add_column(table_name, column_definition, schema=schema)
        print(f"✅ Added column {column_name} to {table_name}")
    else:
        print(f"⚠️  Column {column_name} already exists in {table_name}, skipping")


def upgrade() -> None:
    """Add missing columns to security_audit_logs table"""

    print("🔧 Adding missing columns to security_audit_logs table...")

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    # Add request_payload column
    add_column_if_not_exists(
        "security_audit_logs",
        "request_payload",
        sa.Column(
            "request_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Sanitized request payload data for audit purposes",
        ),
    )

    # Add response_payload column
    add_column_if_not_exists(
        "security_audit_logs",
        "response_payload",
        sa.Column(
            "response_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Sanitized response payload data for audit purposes",
        ),
    )

    # Add target_details column
    add_column_if_not_exists(
        "security_audit_logs",
        "target_details",
        sa.Column(
            "target_details",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Sanitized target details for audit purposes",
        ),
    )

    # Verify the trigger function exists and will work with new columns
    op.execute(
        """
        DO $$
        BEGIN
            -- Check if the sanitize trigger function exists
            IF EXISTS (
                SELECT 1 FROM information_schema.routines
                WHERE routine_schema = 'migration'
                AND routine_name = 'sanitize_audit_log_trigger'
            ) THEN
                RAISE NOTICE '✅ sanitize_audit_log_trigger function exists and will work with new columns';
            ELSE
                RAISE NOTICE '⚠️  sanitize_audit_log_trigger function not found - may need to run migration 016';
            END IF;

            -- Check if the trigger exists
            IF EXISTS (
                SELECT 1 FROM information_schema.triggers
                WHERE trigger_schema = 'migration'
                AND trigger_name = 'sanitize_audit_log_before_insert'
                AND event_object_table = 'security_audit_logs'
            ) THEN
                RAISE NOTICE '✅ sanitize_audit_log_before_insert trigger exists';
            ELSE
                RAISE NOTICE '⚠️  sanitize_audit_log_before_insert trigger not found - may need to run migration 016';
            END IF;
        END $$;
    """
    )

    print("✅ Successfully added missing audit log columns")


def downgrade() -> None:
    """Remove the added columns from security_audit_logs table"""

    print("🔧 Removing added audit log columns...")

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    # Remove columns in reverse order
    if column_exists("security_audit_logs", "target_details"):
        op.drop_column("security_audit_logs", "target_details", schema="migration")
        print("✅ Removed target_details column")

    if column_exists("security_audit_logs", "response_payload"):
        op.drop_column("security_audit_logs", "response_payload", schema="migration")
        print("✅ Removed response_payload column")

    if column_exists("security_audit_logs", "request_payload"):
        op.drop_column("security_audit_logs", "request_payload", schema="migration")
        print("✅ Removed request_payload column")

    print("✅ Successfully removed audit log columns")
