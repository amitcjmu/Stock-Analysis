"""Add flow_deletion_audit table for comprehensive deletion tracking

Revision ID: 031_add_flow_deletion_audit_table
Revises: 030_add_sixr_analysis_tables
Create Date: 2025-01-26 14:00:00.000000

This migration creates the flow_deletion_audit table that was referenced in the codebase
but never actually created. The table is used by the flow deletion services to maintain
a comprehensive audit trail of all flow deletion operations.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "031_add_flow_deletion_audit_table"
down_revision = "030_add_sixr_analysis_tables"
branch_labels = None
depends_on = None


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the 'migration' schema."""
    bind = op.get_bind()
    try:
        stmt = sa.text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                  AND table_name = :table_name
            )
            """
        )
        result = bind.execute(stmt, {"table_name": table_name}).scalar()
        return bool(result)
    except Exception as e:
        print(f"Error checking if table {table_name} exists: {e}")
        # Fail safe: indicate table does not exist so creation proceeds
        return False


def create_table_if_not_exists(table_name, *columns, **kwargs):
    """Create a table only if it doesn't already exist"""
    if not table_exists(table_name):
        op.create_table(table_name, *columns, **kwargs)
        return True
    else:
        print(f"Table {table_name} already exists, skipping creation")
        return False


def upgrade() -> None:
    """Create flow_deletion_audit table"""

    print("🔄 Creating flow_deletion_audit table...")

    # Create the flow_deletion_audit table
    if create_table_if_not_exists(
        "flow_deletion_audit",
        # Primary identification
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.func.gen_random_uuid(),
            index=True,
        ),
        sa.Column("flow_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        # Multi-tenant isolation
        sa.Column(
            "client_account_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "engagement_id", postgresql.UUID(as_uuid=True), nullable=False, index=True
        ),
        sa.Column("user_id", sa.String, nullable=False),
        # Deletion metadata
        sa.Column(
            "deletion_type",
            sa.String,
            nullable=False,
            index=True,
            comment="user_requested, auto_cleanup, admin_action, batch_operation",
        ),
        sa.Column("deletion_reason", sa.Text, nullable=True),
        sa.Column(
            "deletion_method",
            sa.String,
            nullable=False,
            comment="manual, api, batch, scheduled",
        ),
        # Comprehensive data deletion summary
        sa.Column(
            "data_deleted",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "deletion_impact",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "cleanup_summary",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        # CrewAI specific cleanup tracking
        sa.Column(
            "shared_memory_cleaned", sa.Boolean, nullable=False, server_default="false"
        ),
        sa.Column(
            "knowledge_base_refs_cleaned",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "agent_memory_cleaned", sa.Boolean, nullable=False, server_default="false"
        ),
        # Audit trail
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            index=True,
        ),
        sa.Column("deleted_by", sa.String, nullable=False),
        sa.Column("deletion_duration_ms", sa.Integer, nullable=True),
        # Recovery information
        sa.Column(
            "recovery_possible", sa.Boolean, nullable=False, server_default="false"
        ),
        sa.Column(
            "recovery_data",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        # Foreign key constraints for multi-tenant isolation
        sa.ForeignKeyConstraint(
            ["client_account_id"], ["migration.client_accounts.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"], ["migration.engagements.id"], ondelete="CASCADE"
        ),
        schema="migration",
    ):
        print("  ✅ Created flow_deletion_audit table")

        # Create additional indexes for optimal query performance
        indexes_to_create = [
            ("ix_flow_deletion_audit_flow_id", "flow_deletion_audit", ["flow_id"]),
            (
                "ix_flow_deletion_audit_client_account_id",
                "flow_deletion_audit",
                ["client_account_id"],
            ),
            (
                "ix_flow_deletion_audit_engagement_id",
                "flow_deletion_audit",
                ["engagement_id"],
            ),
            (
                "ix_flow_deletion_audit_deletion_type",
                "flow_deletion_audit",
                ["deletion_type"],
            ),
            (
                "ix_flow_deletion_audit_deleted_at",
                "flow_deletion_audit",
                ["deleted_at"],
            ),
            # Composite index for common query patterns
            (
                "ix_flow_deletion_audit_tenant_flow",
                "flow_deletion_audit",
                ["client_account_id", "engagement_id", "flow_id"],
            ),
        ]

        for index_name, table_name, columns in indexes_to_create:
            try:
                # Check if index already exists
                bind = op.get_bind()
                result = bind.execute(
                    sa.text(
                        """
                        SELECT indexname
                        FROM pg_indexes
                        WHERE schemaname = 'migration'
                        AND tablename = :table_name
                        AND indexname = :index_name
                    """
                    ),
                    {"table_name": table_name, "index_name": index_name},
                )

                if not result.fetchone():
                    op.create_index(index_name, table_name, columns, schema="migration")
                    print(f"  ✅ Created index {index_name}")
                else:
                    print(f"  ℹ️  Index {index_name} already exists")
            except Exception as e:
                print(f"  ⚠️  Could not create index {index_name}: {str(e)}")

        # Enable Row-Level Security (RLS) for multi-tenant isolation
        try:
            op.execute(
                "ALTER TABLE migration.flow_deletion_audit ENABLE ROW LEVEL SECURITY"
            )
            print("  ✅ Enabled Row-Level Security for flow_deletion_audit")

            # Create RLS policy for multi-tenant access control
            op.execute(
                """
                CREATE POLICY flow_deletion_audit_tenant_isolation
                ON migration.flow_deletion_audit
                USING (
                    client_account_id = current_setting('app.current_client_account_id')::UUID
                    AND engagement_id = current_setting('app.current_engagement_id')::UUID
                )
                """
            )
            print("  ✅ Created RLS policy for flow_deletion_audit")

        except Exception as e:
            print(f"  ⚠️  Could not configure RLS for flow_deletion_audit: {str(e)}")

        print("✅ Flow deletion audit table migration completed successfully")

    else:
        print("ℹ️  flow_deletion_audit table already exists, no changes needed")


def downgrade() -> None:
    """Drop flow_deletion_audit table"""

    print("🔄 Dropping flow_deletion_audit table...")

    # Drop RLS policy first
    try:
        op.execute(
            "DROP POLICY IF EXISTS flow_deletion_audit_tenant_isolation ON migration.flow_deletion_audit"
        )
        print("  ✅ Dropped RLS policy for flow_deletion_audit")
    except Exception as e:
        print(f"  ⚠️  Could not drop RLS policy: {str(e)}")

    # Drop indexes
    indexes_to_drop = [
        "ix_flow_deletion_audit_tenant_flow",
        "ix_flow_deletion_audit_deleted_at",
        "ix_flow_deletion_audit_deletion_type",
        "ix_flow_deletion_audit_engagement_id",
        "ix_flow_deletion_audit_client_account_id",
        "ix_flow_deletion_audit_flow_id",
    ]

    for index_name in indexes_to_drop:
        try:
            op.drop_index(index_name, schema="migration")
            print(f"  ✅ Dropped index {index_name}")
        except Exception:
            pass  # Index might not exist

    # Drop table
    try:
        op.drop_table("flow_deletion_audit", schema="migration")
        print("  ✅ Dropped flow_deletion_audit table")
    except Exception as e:
        print(f"  ⚠️  Could not drop table flow_deletion_audit: {str(e)}")

    print("✅ Flow deletion audit table downgrade completed")
