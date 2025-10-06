"""fix_gaps_collection_flow_fk

Revision ID: 082_fix_gaps_collection_flow_fk
Revises: 081_fix_questionnaire_collection_flow_fk
Create Date: 2025-10-05

Fix FK constraint for collection_data_gaps.collection_flow_id to reference
collection_flows.flow_id instead of collection_flows.id.

This is the SAME bug that affected questionnaires - gaps were being stored
with the wrong flow ID (using internal PK instead of business flow_id).

Root Cause:
- resolve_collection_flow_id() was returning flow.id instead of flow.flow_id
- FK pointed to collection_flows(id) - internal UUID primary key
- Application uses collection_flows(flow_id) - business identifier UUID
- These are DIFFERENT UUIDs, causing gaps to be orphaned

Solution:
1. Drop incorrect FK constraint
2. Migrate data: map gaps.collection_flow_id from id → flow_id
3. Create correct FK constraint pointing to flow_id
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "082_fix_gaps_collection_flow_fk"
down_revision = "081_fix_questionnaire_collection_flow_fk"
branch_labels = None
depends_on = None


def upgrade():
    """
    Fix FK constraint to point to collection_flows.flow_id instead of id.

    Steps:
    1. Drop existing FK constraint
    2. Update gaps collection_flow_id values (id → flow_id)
    3. Create new FK constraint pointing to flow_id
    """

    conn = op.get_bind()

    # Step 1: Drop existing FK constraint if it exists
    result = conn.execute(
        sa.text(
            """
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_schema = 'migration'
            AND table_name = 'collection_data_gaps'
            AND constraint_name = 'fk_collection_data_gaps_collection_flow_id_collection_flows'
        """
        )
    )
    if result.fetchone() is not None:
        op.drop_constraint(
            "fk_collection_data_gaps_collection_flow_id_collection_flows",
            "collection_data_gaps",
            schema="migration",
            type_="foreignkey",
        )

    # Step 2: Migrate data - update collection_flow_id from id to flow_id
    # CRITICAL: This updates gaps to point to the correct flow_id
    conn.execute(
        sa.text(
            """
            UPDATE migration.collection_data_gaps g
            SET collection_flow_id = cf.flow_id
            FROM migration.collection_flows cf
            WHERE g.collection_flow_id = cf.id
            AND g.collection_flow_id IS NOT NULL
        """
        )
    )

    # Step 3: Create new FK constraint pointing to flow_id
    op.create_foreign_key(
        "fk_collection_data_gaps_collection_flow_id_collection_flows",
        "collection_data_gaps",
        "collection_flows",
        ["collection_flow_id"],
        ["flow_id"],
        source_schema="migration",
        referent_schema="migration",
        ondelete="CASCADE",
    )


def downgrade():
    """
    Rollback FK constraint fix - revert to pointing at id.

    WARNING: This will BREAK application logic that uses flow_id.
    Only use for emergency rollback.
    """

    conn = op.get_bind()

    # Step 1: Drop the correct FK constraint
    result = conn.execute(
        sa.text(
            """
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_schema = 'migration'
            AND table_name = 'collection_data_gaps'
            AND constraint_name = 'fk_collection_data_gaps_collection_flow_id_collection_flows'
        """
        )
    )
    if result.fetchone() is not None:
        op.drop_constraint(
            "fk_collection_data_gaps_collection_flow_id_collection_flows",
            "collection_data_gaps",
            schema="migration",
            type_="foreignkey",
        )

    # Step 2: Migrate data back - update collection_flow_id from flow_id to id
    # WARNING: This re-introduces the bug!
    conn.execute(
        sa.text(
            """
            UPDATE migration.collection_data_gaps g
            SET collection_flow_id = cf.id
            FROM migration.collection_flows cf
            WHERE g.collection_flow_id = cf.flow_id
            AND g.collection_flow_id IS NOT NULL
        """
        )
    )

    # Step 3: Recreate old FK constraint pointing to id (WRONG)
    op.create_foreign_key(
        "fk_collection_data_gaps_collection_flow_id_collection_flows",
        "collection_data_gaps",
        "collection_flows",
        ["collection_flow_id"],
        ["id"],
        source_schema="migration",
        referent_schema="migration",
        ondelete="CASCADE",
    )
