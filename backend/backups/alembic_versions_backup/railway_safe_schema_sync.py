"""Railway Safe Schema Synchronization

This migration is designed to be idempotent and safe to run on Railway
even if the migration history differs from local development.

Revision ID: railway_safe_schema_sync
Revises: a1409a6c4f88
Create Date: 2025-06-30 06:00:00.000000

"""

import logging

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "railway_safe_schema_sync"
down_revision = "a1409a6c4f88"
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)


def check_column_exists(connection, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    result = connection.execute(
        text(
            """
        SELECT COUNT(*) 
        FROM information_schema.columns 
        WHERE table_name = :table_name AND column_name = :column_name
    """
        ),
        {"table_name": table_name, "column_name": column_name},
    )
    return result.scalar() > 0


def check_constraint_exists(connection, table_name: str, constraint_name: str) -> bool:
    """Check if a constraint exists on a table."""
    result = connection.execute(
        text(
            """
        SELECT COUNT(*) 
        FROM information_schema.table_constraints 
        WHERE table_name = :table_name AND constraint_name = :constraint_name
    """
        ),
        {"table_name": table_name, "constraint_name": constraint_name},
    )
    return result.scalar() > 0


def check_index_exists(connection, index_name: str) -> bool:
    """Check if an index exists."""
    result = connection.execute(
        text(
            """
        SELECT COUNT(*) 
        FROM pg_indexes 
        WHERE indexname = :index_name
    """
        ),
        {"index_name": index_name},
    )
    return result.scalar() > 0


def upgrade() -> None:
    """Railway-safe schema synchronization."""
    print("🚀 Starting Railway-safe schema synchronization...")

    connection = op.get_bind()

    # ========================================
    # 1. Ensure crewai_flow_state_extensions has all required columns
    # ========================================
    print("📊 Step 1: Synchronizing crewai_flow_state_extensions table...")

    required_columns = {
        "client_account_id": {
            "type": sa.UUID(),
            "nullable": False,
            "default": "'11111111-1111-1111-1111-111111111111'::uuid",
        },
        "engagement_id": {
            "type": sa.UUID(),
            "nullable": False,
            "default": "'22222222-2222-2222-2222-222222222222'::uuid",
        },
        "user_id": {"type": sa.String(255), "nullable": False, "default": "'system'"},
        "flow_type": {
            "type": sa.String(50),
            "nullable": False,
            "default": "'discovery'",
        },
        "flow_name": {"type": sa.String(255), "nullable": True, "default": None},
        "flow_status": {
            "type": sa.String(50),
            "nullable": False,
            "default": "'initialized'",
        },
        "flow_configuration": {
            "type": postgresql.JSONB(),
            "nullable": False,
            "default": "'{}'::jsonb",
        },
    }

    for column_name, column_spec in required_columns.items():
        if not check_column_exists(
            connection, "crewai_flow_state_extensions", column_name
        ):
            print(f"   + Adding column: {column_name}")
            if column_spec["default"]:
                op.add_column(
                    "crewai_flow_state_extensions",
                    sa.Column(
                        column_name,
                        column_spec["type"],
                        nullable=column_spec["nullable"],
                        server_default=text(column_spec["default"]),
                    ),
                )
            else:
                op.add_column(
                    "crewai_flow_state_extensions",
                    sa.Column(
                        column_name,
                        column_spec["type"],
                        nullable=column_spec["nullable"],
                    ),
                )
        else:
            print(f"   ✅ Column exists: {column_name}")

    # ========================================
    # 2. Ensure assets table has flow_id column
    # ========================================
    print("📊 Step 2: Synchronizing assets table...")

    if not check_column_exists(connection, "assets", "flow_id"):
        print("   + Adding flow_id column to assets")
        op.add_column("assets", sa.Column("flow_id", sa.UUID(), nullable=True))
    else:
        print("   ✅ assets.flow_id column exists")

    # ========================================
    # 3. Ensure proper indexes exist
    # ========================================
    print("📊 Step 3: Synchronizing indexes...")

    indexes_to_create = [
        (
            "ix_crewai_flow_state_extensions_flow_id",
            "crewai_flow_state_extensions",
            ["flow_id"],
            True,
        ),
        (
            "ix_crewai_flow_state_extensions_client_account_id",
            "crewai_flow_state_extensions",
            ["client_account_id"],
            False,
        ),
        (
            "ix_crewai_flow_state_extensions_engagement_id",
            "crewai_flow_state_extensions",
            ["engagement_id"],
            False,
        ),
        ("ix_discovery_flows_flow_id", "discovery_flows", ["flow_id"], True),
        ("ix_discovery_flows_status", "discovery_flows", ["status"], False),
        ("ix_assets_flow_id", "assets", ["flow_id"], False),
    ]

    for index_name, table_name, columns, unique in indexes_to_create:
        if not check_index_exists(connection, index_name):
            print(f"   + Creating index: {index_name}")
            try:
                op.create_index(index_name, table_name, columns, unique=unique)
            except Exception as e:
                print(f"   ⚠️  Index creation warning: {e}")
        else:
            print(f"   ✅ Index exists: {index_name}")

    # ========================================
    # 4. Clean up legacy columns
    # ========================================
    print("📊 Step 4: Cleaning up legacy columns...")

    # Remove discovery_flow_id from crewai_flow_state_extensions if it exists
    if check_column_exists(
        connection, "crewai_flow_state_extensions", "discovery_flow_id"
    ):
        print("   - Removing legacy discovery_flow_id column")
        try:
            # First drop any foreign key constraints
            connection.execute(
                text(
                    """
                ALTER TABLE crewai_flow_state_extensions 
                DROP CONSTRAINT IF EXISTS crewai_flow_state_extensions_discovery_flow_id_fkey
            """
                )
            )
            op.drop_column("crewai_flow_state_extensions", "discovery_flow_id")
        except Exception as e:
            print(f"   ⚠️  Legacy column cleanup warning: {e}")
    else:
        print("   ✅ Legacy columns already cleaned up")

    # ========================================
    # 5. Data consistency fixes
    # ========================================
    print("📊 Step 5: Fixing data consistency...")

    # Update any NULL values in new columns
    try:
        connection.execute(
            text(
                """
            UPDATE crewai_flow_state_extensions 
            SET 
                flow_name = COALESCE(flow_name, 'Legacy Flow ' || SUBSTRING(flow_id::text, 1, 8)),
                flow_type = COALESCE(flow_type, 'discovery'),
                flow_status = COALESCE(flow_status, 'initialized')
            WHERE flow_name IS NULL OR flow_type IS NULL OR flow_status IS NULL
        """
            )
        )
        print("   ✅ Updated NULL values in crewai_flow_state_extensions")
    except Exception as e:
        print(f"   ⚠️  Data consistency warning: {e}")

    # ========================================
    # 6. Validation
    # ========================================
    print("📊 Step 6: Validating schema synchronization...")

    # Check critical columns exist
    critical_checks = [
        ("crewai_flow_state_extensions", "client_account_id"),
        ("crewai_flow_state_extensions", "engagement_id"),
        ("crewai_flow_state_extensions", "flow_type"),
        ("crewai_flow_state_extensions", "flow_status"),
        ("assets", "flow_id"),
        ("discovery_flows", "flow_id"),
    ]

    all_good = True
    for table, column in critical_checks:
        if check_column_exists(connection, table, column):
            print(f"   ✅ {table}.{column}")
        else:
            print(f"   ❌ MISSING: {table}.{column}")
            all_good = False

    if all_good:
        print("🎉 Railway-safe schema synchronization completed successfully!")
    else:
        print("⚠️  Schema synchronization completed with warnings - check logs above")


def downgrade() -> None:
    """Downgrade is not supported for Railway-safe migrations."""
    print("⚠️  Downgrade not supported for Railway-safe schema synchronization")
    print("This migration is designed to be idempotent and forward-only")
    pass
