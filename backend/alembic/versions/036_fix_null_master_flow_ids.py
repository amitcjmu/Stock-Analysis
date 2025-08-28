"""Fix NULL master_flow_ids and add proper FK constraints

Revision ID: 036_fix_null_master_flow_ids
Revises: 035_fix_engagement_architecture_standards_schema
Create Date: 2025-08-28 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "036_fix_null_master_flow_ids"
down_revision: Union[str, None] = "035_fix_engagement_architecture_standards_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Fix NULL master_flow_ids with self-referential pattern and add proper FK constraints
    """
    # Step 1: Backfill all NULL master_flow_ids in discovery_flows
    print(
        "🔧 CC FIX: Backfilling NULL master_flow_ids in discovery_flows with self-referential pattern"
    )
    op.execute(
        text(
            """
        UPDATE discovery_flows
        SET master_flow_id = flow_id, updated_at = NOW()
        WHERE master_flow_id IS NULL
    """
        )
    )

    # Check if any rows were updated
    result = op.get_bind().execute(
        text(
            """
        SELECT COUNT(*) as updated_count
        FROM discovery_flows
        WHERE master_flow_id = flow_id
        AND updated_at > NOW() - INTERVAL '1 minute'
    """
        )
    )
    updated_count = result.scalar()
    print(f"✅ Updated {updated_count} discovery_flows records")

    # Step 2: Backfill all NULL master_flow_ids in assessment_flows (if table exists)
    try:
        op.execute(
            text(
                """
            UPDATE assessment_flows
            SET master_flow_id = flow_id, updated_at = NOW()
            WHERE master_flow_id IS NULL
        """
            )
        )

        result = op.get_bind().execute(
            text(
                """
            SELECT COUNT(*) as updated_count
            FROM assessment_flows
            WHERE master_flow_id = flow_id
            AND updated_at > NOW() - INTERVAL '1 minute'
        """
            )
        )
        updated_count = result.scalar()
        print(f"✅ Updated {updated_count} assessment_flows records")
    except Exception as e:
        print(f"⚠️ assessment_flows table not found or accessible: {e}")

    # Step 3: Backfill all NULL master_flow_ids in collection_flows (if table exists)
    try:
        op.execute(
            text(
                """
            UPDATE collection_flows
            SET master_flow_id = flow_id, updated_at = NOW()
            WHERE master_flow_id IS NULL
        """
            )
        )

        result = op.get_bind().execute(
            text(
                """
            SELECT COUNT(*) as updated_count
            FROM collection_flows
            WHERE master_flow_id = flow_id
            AND updated_at > NOW() - INTERVAL '1 minute'
        """
            )
        )
        updated_count = result.scalar()
        print(f"✅ Updated {updated_count} collection_flows records")
    except Exception as e:
        print(f"⚠️ collection_flows table not found or accessible: {e}")

    # Step 4: Make master_flow_id NOT NULL on discovery_flows
    print("🔧 CC FIX: Making master_flow_id NOT NULL on discovery_flows")
    op.alter_column(
        "discovery_flows", "master_flow_id", existing_type=UUID(), nullable=False
    )

    # Step 5: Make master_flow_id NOT NULL on assessment_flows (if exists)
    try:
        print("🔧 CC FIX: Making master_flow_id NOT NULL on assessment_flows")
        op.alter_column(
            "assessment_flows", "master_flow_id", existing_type=UUID(), nullable=False
        )
    except Exception as e:
        print(f"⚠️ Could not update assessment_flows: {e}")

    # Step 6: Make master_flow_id NOT NULL on collection_flows (if exists)
    try:
        print("🔧 CC FIX: Making master_flow_id NOT NULL on collection_flows")
        op.alter_column(
            "collection_flows", "master_flow_id", existing_type=UUID(), nullable=False
        )
    except Exception as e:
        print(f"⚠️ Could not update collection_flows: {e}")

    # Step 7: Drop existing FK constraint and recreate as DEFERRABLE INITIALLY DEFERRED
    print("🔧 CC FIX: Updating FK constraints to be DEFERRABLE INITIALLY DEFERRED")

    # Discovery flows FK constraint
    try:
        # First, try to drop the existing constraint (name might vary)
        op.execute(
            text(
                """
            ALTER TABLE discovery_flows
            DROP CONSTRAINT IF EXISTS discovery_flows_master_flow_id_fkey
        """
            )
        )
    except Exception as e:
        print(f"⚠️ Could not drop existing FK constraint on discovery_flows: {e}")

    # Create new deferrable FK constraint for discovery_flows
    op.execute(
        text(
            """
        ALTER TABLE discovery_flows
        ADD CONSTRAINT discovery_flows_master_flow_id_fkey
        FOREIGN KEY (master_flow_id)
        REFERENCES crewai_flow_state_extensions (flow_id)
        ON DELETE CASCADE
        DEFERRABLE INITIALLY DEFERRED
    """
        )
    )

    # Assessment flows FK constraint (if table exists)
    try:
        op.execute(
            text(
                """
            ALTER TABLE assessment_flows
            DROP CONSTRAINT IF EXISTS assessment_flows_master_flow_id_fkey
        """
            )
        )

        op.execute(
            text(
                """
            ALTER TABLE assessment_flows
            ADD CONSTRAINT assessment_flows_master_flow_id_fkey
            FOREIGN KEY (master_flow_id)
            REFERENCES crewai_flow_state_extensions (flow_id)
            ON DELETE CASCADE
            DEFERRABLE INITIALLY DEFERRED
        """
            )
        )
        print("✅ Updated assessment_flows FK constraint")
    except Exception as e:
        print(f"⚠️ Could not update assessment_flows FK constraint: {e}")

    # Collection flows FK constraint (if table exists)
    try:
        op.execute(
            text(
                """
            ALTER TABLE collection_flows
            DROP CONSTRAINT IF EXISTS collection_flows_master_flow_id_fkey
        """
            )
        )

        op.execute(
            text(
                """
            ALTER TABLE collection_flows
            ADD CONSTRAINT collection_flows_master_flow_id_fkey
            FOREIGN KEY (master_flow_id)
            REFERENCES crewai_flow_state_extensions (flow_id)
            ON DELETE CASCADE
            DEFERRABLE INITIALLY DEFERRED
        """
            )
        )
        print("✅ Updated collection_flows FK constraint")
    except Exception as e:
        print(f"⚠️ Could not update collection_flows FK constraint: {e}")

    print(
        "✅ Migration completed successfully - master_flow_id constraints updated for better transaction control"
    )


def downgrade() -> None:
    """
    Revert the changes - make master_flow_id nullable again and remove deferrable constraints
    """
    print("🔄 CC FIX: Reverting master_flow_id constraint changes")

    # Step 1: Drop deferrable FK constraints and recreate as regular constraints
    # Discovery flows
    try:
        op.execute(
            text(
                """
            ALTER TABLE discovery_flows
            DROP CONSTRAINT IF EXISTS discovery_flows_master_flow_id_fkey
        """
            )
        )

        op.create_foreign_key(
            "discovery_flows_master_flow_id_fkey",
            "discovery_flows",
            "crewai_flow_state_extensions",
            ["master_flow_id"],
            ["flow_id"],
            ondelete="CASCADE",
        )
    except Exception as e:
        print(f"⚠️ Could not revert discovery_flows FK constraint: {e}")

    # Assessment flows
    try:
        op.execute(
            text(
                """
            ALTER TABLE assessment_flows
            DROP CONSTRAINT IF EXISTS assessment_flows_master_flow_id_fkey
        """
            )
        )

        op.create_foreign_key(
            "assessment_flows_master_flow_id_fkey",
            "assessment_flows",
            "crewai_flow_state_extensions",
            ["master_flow_id"],
            ["flow_id"],
            ondelete="CASCADE",
        )
    except Exception as e:
        print(f"⚠️ Could not revert assessment_flows FK constraint: {e}")

    # Collection flows
    try:
        op.execute(
            text(
                """
            ALTER TABLE collection_flows
            DROP CONSTRAINT IF EXISTS collection_flows_master_flow_id_fkey
        """
            )
        )

        op.create_foreign_key(
            "collection_flows_master_flow_id_fkey",
            "collection_flows",
            "crewai_flow_state_extensions",
            ["master_flow_id"],
            ["flow_id"],
            ondelete="CASCADE",
        )
    except Exception as e:
        print(f"⚠️ Could not revert collection_flows FK constraint: {e}")

    # Step 2: Make master_flow_id nullable again
    op.alter_column(
        "discovery_flows", "master_flow_id", existing_type=UUID(), nullable=True
    )

    try:
        op.alter_column(
            "assessment_flows", "master_flow_id", existing_type=UUID(), nullable=True
        )
    except Exception:
        pass

    try:
        op.alter_column(
            "collection_flows", "master_flow_id", existing_type=UUID(), nullable=True
        )
    except Exception:
        pass

    print("✅ Downgrade completed - reverted to nullable master_flow_id")
