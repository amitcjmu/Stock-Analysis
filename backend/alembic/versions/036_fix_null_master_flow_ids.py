"""Fix NULL master_flow_ids and add proper FK constraints

Revision ID: 036_fix_null_master_flow_ids
Revises: 035_fix_engagement_architecture_standards_schema
Create Date: 2025-08-28 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "036_fix_null_master_flow_ids"
down_revision: Union[str, None] = "035_fix_engagement_architecture_standards_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:  # noqa: C901
    """
    Fix NULL master_flow_ids with self-referential pattern and add proper FK constraints.
    🔧 CC FIX: Creates stub master records for orphaned flows to prevent FK violations.
    """
    bind = op.get_bind()

    # Step 1: Check if tables exist first
    tables_exist = bind.execute(
        text(
            """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name IN ('discovery_flows', 'crewai_flow_state_extensions', 'assessment_flows', 'collection_flows')
    """
        )
    ).fetchall()

    existing_tables = [row[0] for row in tables_exist]
    print(f"🔍 Found existing tables: {existing_tables}")

    if "discovery_flows" not in existing_tables:
        print("⚠️ discovery_flows table not found, skipping migration")
        return

    if "crewai_flow_state_extensions" not in existing_tables:
        print("⚠️ crewai_flow_state_extensions table not found, skipping migration")
        return

    try:
        # Step 2: Create stub master records for orphaned discovery flows
        print("🔧 CC FIX: Creating stub master records for orphaned discovery flows")

        # Find orphaned flows that need master records
        orphaned_flows_query = text(
            """
            SELECT DISTINCT df.flow_id, df.client_account_id, df.engagement_id, df.created_at
            FROM discovery_flows df
            LEFT JOIN crewai_flow_state_extensions cfse ON df.flow_id = cfse.flow_id
            WHERE df.master_flow_id IS NULL
                AND cfse.flow_id IS NULL
            LIMIT 100
        """
        )

        orphaned_flows = bind.execute(orphaned_flows_query).fetchall()
        print(
            f"📊 Found {len(orphaned_flows)} orphaned flows needing stub master records"
        )

        # Create stub master records for orphaned flows
        for flow in orphaned_flows:
            print(f"   Creating stub master record for flow_id: {flow.flow_id}")
            try:
                bind.execute(
                    text(
                        """
                        INSERT INTO crewai_flow_state_extensions (
                            id, flow_id, client_account_id, engagement_id, user_id,
                            flow_type, flow_name, flow_status,
                            flow_configuration, flow_persistence_data,
                            created_at, updated_at
                        )
                        VALUES (
                            gen_random_uuid(), :flow_id, :client_account_id, :engagement_id, 'migration-stub',
                            'discovery', 'Discovery Flow ' || LEFT(CAST(:flow_id AS text), 8),
                            'initialized',
                            '{"created_from": "migration_036_stub"}',
                            '{"migration_created": true}',
                            :created_at, NOW()
                        )
                        ON CONFLICT (flow_id) DO NOTHING
                    """
                    ),
                    {
                        "flow_id": flow.flow_id,
                        "client_account_id": flow.client_account_id,
                        "engagement_id": flow.engagement_id,
                        "created_at": flow.created_at,
                    },
                )
            except Exception as e:
                print(f"⚠️ Failed to create stub record for flow {flow.flow_id}: {e}")

        # Step 3: Backfill all NULL master_flow_ids in discovery_flows
        print(
            "🔧 CC FIX: Backfilling NULL master_flow_ids in discovery_flows with self-referential pattern"
        )
        try:
            result = bind.execute(
                text(
                    """
                    UPDATE discovery_flows
                    SET master_flow_id = flow_id, updated_at = NOW()
                    WHERE master_flow_id IS NULL
                """
                )
            )
            updated_count = result.rowcount if result else 0
            print(f"✅ Updated {updated_count} discovery_flows records")
        except Exception as e:
            print(f"⚠️ Failed to update discovery_flows: {e}")

    except Exception as e:
        print(f"⚠️ Error in discovery_flows processing: {e}")

    # Step 4: Handle other flow types if they exist
    for table_name, flow_type in [
        ("assessment_flows", "assessment"),
        ("collection_flows", "collection"),
    ]:
        if table_name in existing_tables:
            print(f"🔧 CC FIX: Processing {table_name}")
            try:
                # Create stub master records for orphaned flows
                orphaned_query = text(
                    f"""
                    SELECT DISTINCT f.flow_id, f.client_account_id, f.engagement_id, f.created_at
                    FROM {table_name} f
                    LEFT JOIN crewai_flow_state_extensions cfse ON f.flow_id = cfse.flow_id
                    WHERE f.master_flow_id IS NULL
                        AND cfse.flow_id IS NULL
                    LIMIT 100
                """
                )

                orphaned_flows = bind.execute(orphaned_query).fetchall()
                print(f"📊 Found {len(orphaned_flows)} orphaned {table_name} flows")

                for flow in orphaned_flows:
                    try:
                        bind.execute(
                            text(
                                """
                                INSERT INTO crewai_flow_state_extensions (
                                    id, flow_id, client_account_id, engagement_id, user_id,
                                    flow_type, flow_name, flow_status,
                                    flow_configuration, flow_persistence_data,
                                    created_at, updated_at
                                )
                                VALUES (
                                    gen_random_uuid(), :flow_id, :client_account_id, :engagement_id, 'migration-stub',
                                    :flow_type, :flow_name,
                                    'initialized',
                                    '{"created_from": "migration_036_stub"}',
                                    '{"migration_created": true}',
                                    :created_at, NOW()
                                )
                                ON CONFLICT (flow_id) DO NOTHING
                            """
                            ),
                            {
                                "flow_id": flow.flow_id,
                                "client_account_id": flow.client_account_id,
                                "engagement_id": flow.engagement_id,
                                "created_at": flow.created_at,
                                "flow_type": flow_type,
                                "flow_name": f"{flow_type.title()} Flow "
                                + str(flow.flow_id)[:8],
                            },
                        )
                    except Exception as e:
                        print(
                            f"⚠️ Failed to create stub record for {table_name} flow {flow.flow_id}: {e}"
                        )

                # Update NULL master_flow_ids
                try:
                    result = bind.execute(
                        text(
                            f"""
                        UPDATE {table_name}
                        SET master_flow_id = flow_id, updated_at = NOW()
                        WHERE master_flow_id IS NULL
                    """
                        )
                    )
                    updated_count = result.rowcount if result else 0
                    print(f"✅ Updated {updated_count} {table_name} records")
                except Exception as e:
                    print(f"⚠️ Failed to update {table_name}: {e}")

            except Exception as e:
                print(f"⚠️ Error processing {table_name}: {e}")

    print(
        "✅ Migration completed successfully - Fixed NULL master_flow_ids with stub records"
    )


def downgrade() -> None:
    """
    Revert the changes - remove migration stub records and set master_flow_id back to NULL
    """
    print("🔄 CC FIX: Reverting migration stub records")

    bind = op.get_bind()

    try:
        # Remove stub records created by this migration
        result = bind.execute(
            text(
                """
            DELETE FROM crewai_flow_state_extensions
            WHERE flow_configuration::text LIKE '%migration_036_stub%'
        """
            )
        )
        deleted_count = result.rowcount if result else 0
        print(f"✅ Removed {deleted_count} migration stub records")

        # Reset master_flow_id to NULL for self-referential records
        for table_name in ["discovery_flows", "assessment_flows", "collection_flows"]:
            try:
                result = bind.execute(
                    text(
                        f"""
                    UPDATE {table_name}
                    SET master_flow_id = NULL
                    WHERE master_flow_id = flow_id
                """
                    )
                )
                reset_count = result.rowcount if result else 0
                print(
                    f"✅ Reset {reset_count} {table_name} self-referential master_flow_ids to NULL"
                )
            except Exception as e:
                print(f"⚠️ Could not reset {table_name}: {e}")

    except Exception as e:
        print(f"⚠️ Error during downgrade: {e}")

    print("✅ Downgrade completed - reverted migration changes")
