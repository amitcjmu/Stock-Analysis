"""fix_discovery_master_fk_swap

Fix the discovery_flows.master_flow_id FK to point to crewai_flow_state_extensions.flow_id
instead of crewai_flow_state_extensions.id. Uses single transaction for atomic swap.
Part of Schema Consolidation Plan - Migration 2/3.

This corrects a design issue where the FK pointed to the internal ID instead of
the business flow_id, which should be the canonical reference.

Revision ID: 069_fix_discovery_master_fk_swap
Revises: 068_discovery_columns_rename_and_cleanup
Create Date: 2025-09-18 00:01:00.000000

"""

from alembic import op
from sqlalchemy import text
import logging

# revision identifiers, used by Alembic.
revision = "069_fix_discovery_master_fk_swap"
down_revision = "068_discovery_columns_rename_and_cleanup"
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)


def upgrade() -> None:
    """Fix master_flow_id FK to point to crewai_flow_state_extensions.flow_id - atomic operation"""

    print("🔧 Migration 069: Fix discovery_flows.master_flow_id FK...")

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    conn = op.get_bind()

    # Check current FK constraint
    fk_check_sql = text(
        """
        SELECT conname, pg_get_constraintdef(c.oid) as definition
        FROM pg_constraint c
        JOIN pg_class t ON c.conrelid = t.oid
        JOIN pg_namespace n ON t.relnamespace = n.oid
        WHERE n.nspname = 'migration'
        AND t.relname = 'discovery_flows'
        AND conname LIKE '%master%'
    """
    )

    current_fks = list(conn.execute(fk_check_sql).fetchall())
    print(f"   📋 Current FK constraints: {[(fk[0], fk[1]) for fk in current_fks]}")

    # Check if we need to perform the swap
    needs_swap = any("crewai_flow_state_extensions(id)" in fk[1] for fk in current_fks)
    if not needs_swap:
        # Check if it already points to flow_id
        already_correct = any(
            "crewai_flow_state_extensions(flow_id)" in fk[1] for fk in current_fks
        )
        if already_correct:
            print(
                "   ✅ FK already points to crewai_flow_state_extensions.flow_id - no change needed"
            )
            return
        else:
            print("   ⚠️  No master_flow_id FK found or unexpected structure")

    # BEGIN ATOMIC TRANSACTION - All or nothing
    print("   🚀 Starting atomic FK swap transaction...")

    try:
        # Use single transaction for atomicity
        with conn.begin():
            print("   📊 Analyzing data before swap...")

            # Count total records
            count_sql = text("SELECT COUNT(*) FROM migration.discovery_flows")
            total_flows = conn.execute(count_sql).scalar()
            print(f"     - Total discovery flows: {total_flows}")

            # Count non-null master_flow_id records
            non_null_sql = text(
                """
                SELECT COUNT(*) FROM migration.discovery_flows
                WHERE master_flow_id IS NOT NULL
            """
            )
            non_null_count = conn.execute(non_null_sql).scalar()
            print(f"     - Flows with master_flow_id: {non_null_count}")

            # Step 1: Add new temporary column
            print("   ➕ Adding temporary master_flow_id_new column...")
            op.execute(
                text(
                    """
                ALTER TABLE migration.discovery_flows
                ADD COLUMN IF NOT EXISTS master_flow_id_new UUID
            """
                )
            )

            # Step 2: Update new column with flow_id values from CFSE
            print("   🔄 Updating master_flow_id_new with flow_id values...")
            update_sql = text(
                """
                UPDATE migration.discovery_flows df
                SET master_flow_id_new = cfse.flow_id
                FROM migration.crewai_flow_state_extensions cfse
                WHERE df.master_flow_id = cfse.id
                AND df.master_flow_id IS NOT NULL
            """
            )
            update_result = conn.execute(update_sql)
            print(
                f"     ✅ Updated {update_result.rowcount} records via ID->flow_id lookup"
            )

            # Fallback: Try to match by flow_id if some records are still NULL
            print("   🔍 Checking for fallback matching by flow_id...")
            fallback_sql = text(
                """
                UPDATE migration.discovery_flows df
                SET master_flow_id_new = cfse.flow_id
                FROM migration.crewai_flow_state_extensions cfse
                WHERE df.master_flow_id_new IS NULL
                AND df.flow_id = cfse.flow_id
                AND df.client_account_id = cfse.client_account_id
                AND df.engagement_id = cfse.engagement_id
                AND df.master_flow_id IS NOT NULL
            """
            )
            fallback_result = conn.execute(fallback_sql)
            if fallback_result.rowcount > 0:
                print(
                    f"     ✅ Fallback matched {fallback_result.rowcount} additional records"
                )

            # Check results
            updated_count_sql = text(
                """
                SELECT COUNT(*) FROM migration.discovery_flows
                WHERE master_flow_id_new IS NOT NULL
            """
            )
            updated_count = conn.execute(updated_count_sql).scalar()
            print(
                f"     📊 Successfully mapped {updated_count}/{non_null_count} master flow references"
            )

            # Report orphans if any
            if updated_count < non_null_count:
                orphan_count = non_null_count - updated_count
                print(
                    f"     ⚠️  {orphan_count} orphaned records (master_flow_id points to non-existent CFSE)"
                )

                # Show sample orphans for debugging
                orphan_sql = text(
                    """
                    SELECT df.flow_id, df.master_flow_id, df.client_account_id, df.engagement_id
                    FROM migration.discovery_flows df
                    WHERE df.master_flow_id IS NOT NULL
                    AND df.master_flow_id_new IS NULL
                    LIMIT 3
                """
                )
                orphans = list(conn.execute(orphan_sql).fetchall())
                for orphan in orphans:
                    print(
                        f"       - Flow {orphan[0]} → master_flow_id {orphan[1]} (not found in CFSE)"
                    )

            # Step 3: Drop old FK constraint
            print("   🗑️  Dropping old FK constraint...")
            for fk_name, _ in current_fks:
                if "master" in fk_name.lower():
                    op.drop_constraint(fk_name, "discovery_flows", schema="migration")
                    print(f"     ✅ Dropped constraint: {fk_name}")

            # Step 4: Add new FK constraint to crewai_flow_state_extensions.flow_id
            print(
                "   🔗 Adding new FK constraint to crewai_flow_state_extensions.flow_id..."
            )
            op.create_foreign_key(
                "fk_discovery_master_flow_new",
                "discovery_flows",
                "crewai_flow_state_extensions",
                ["master_flow_id_new"],
                ["flow_id"],
                ondelete="CASCADE",
                schema="migration",
            )

            # Step 5: Drop old master_flow_id column
            print("   🗑️  Dropping old master_flow_id column...")
            op.drop_column("discovery_flows", "master_flow_id", schema="migration")

            # Step 6: Rename new column to master_flow_id
            print("   🔄 Renaming master_flow_id_new to master_flow_id...")
            op.alter_column(
                "discovery_flows",
                "master_flow_id_new",
                new_column_name="master_flow_id",
                schema="migration",
            )

            # Step 7: Create index on master_flow_id for performance
            print("   🔍 Creating index on master_flow_id...")
            op.create_index(
                "ix_discovery_flows_master_flow_id",
                "discovery_flows",
                ["master_flow_id"],
                schema="migration",
            )

            print("   ✅ Atomic FK swap completed successfully")

        # Verify final state outside transaction
        print("   🔍 Verifying final state...")
        final_fk_check = list(conn.execute(fk_check_sql).fetchall())
        for fk_name, fk_def in final_fk_check:
            if "master" in fk_name.lower():
                if "flow_id" in fk_def:
                    print(f"     ✅ FK now points to flow_id: {fk_name}")
                else:
                    print(f"     ⚠️  Unexpected FK definition: {fk_def}")

    except Exception as e:
        print(f"   ❌ Error during FK swap: {e}")
        raise


def downgrade() -> None:
    """Reverse the FK swap - point back to crewai_flow_state_extensions.id"""

    print("🔄 Downgrading Migration 069: Reversing FK swap...")

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    conn = op.get_bind()

    try:
        with conn.begin():
            print("   ➕ Adding temporary master_flow_id_old column...")
            op.execute(
                text(
                    """
                ALTER TABLE migration.discovery_flows
                ADD COLUMN IF NOT EXISTS master_flow_id_old UUID
            """
                )
            )

            print("   🔄 Converting flow_id back to id values...")
            # Map flow_id back to id
            revert_sql = text(
                """
                UPDATE migration.discovery_flows df
                SET master_flow_id_old = cfse.id
                FROM migration.crewai_flow_state_extensions cfse
                WHERE df.master_flow_id = cfse.flow_id
                AND df.master_flow_id IS NOT NULL
            """
            )
            result = conn.execute(revert_sql)
            print(f"     ✅ Reverted {result.rowcount} records")

            # Drop current FK
            print("   🗑️  Dropping current FK constraint...")
            op.drop_constraint(
                "fk_discovery_master_flow_new", "discovery_flows", schema="migration"
            )

            # Add old FK constraint back
            print("   🔗 Restoring FK to crewai_flow_state_extensions.id...")
            op.create_foreign_key(
                "fk_discovery_flows_master_flow",
                "discovery_flows",
                "crewai_flow_state_extensions",
                ["master_flow_id_old"],
                ["id"],
                ondelete="CASCADE",
                schema="migration",
            )

            # Replace columns
            op.drop_column("discovery_flows", "master_flow_id", schema="migration")
            op.alter_column(
                "discovery_flows",
                "master_flow_id_old",
                new_column_name="master_flow_id",
                schema="migration",
            )

            print("   ✅ FK swap downgrade completed")

    except Exception as e:
        print(f"   ❌ Error during downgrade: {e}")
        raise
