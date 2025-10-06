"""fix_questionnaire_collection_flow_fk

Revision ID: 081_fix_questionnaire_collection_flow_fk
Revises: 080_add_two_phase_gap_analysis_columns
Create Date: 2025-10-05

Fix FK constraint for adaptive_questionnaires.collection_flow_id to reference
collection_flows.flow_id instead of collection_flows.id.

This resolves the recurring bug where questionnaires were being associated with
the wrong flow ID (using internal PK instead of business flow_id).

Root Cause:
- FK pointed to collection_flows(id) - internal UUID primary key
- Application uses collection_flows(flow_id) - business identifier UUID
- These are DIFFERENT UUIDs, causing data corruption

Solution:
1. Drop incorrect FK constraint
2. Migrate data: map questionnaire.collection_flow_id from id → flow_id
3. Create correct FK constraint pointing to flow_id
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "081_fix_questionnaire_collection_flow_fk"
down_revision = "080_add_two_phase_gap_analysis_columns"
branch_labels = None
depends_on = None


def upgrade():
    """
    Fix FK constraint to point to collection_flows.flow_id instead of id.

    Steps:
    1. Drop existing FK constraint
    2. Update questionnaire collection_flow_id values (id → flow_id)
    3. Create new FK constraint pointing to flow_id
    """

    conn = op.get_bind()

    # Step 1: Drop existing FK constraint
    result = conn.execute(
        sa.text(
            """
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_schema = 'migration'
            AND table_name = 'adaptive_questionnaires'
            AND constraint_name = 'fk_adaptive_questionnaires_collection_flow_id_collection_flows'
        """
        )
    )
    if result.fetchone() is not None:
        op.drop_constraint(
            "fk_adaptive_questionnaires_collection_flow_id_collection_flows",
            "adaptive_questionnaires",
            schema="migration",
            type_="foreignkey",
        )

    # Step 2: Migrate data - update collection_flow_id from id to flow_id
    # CRITICAL: This updates questionnaires to point to the correct flow_id
    conn.execute(
        sa.text(
            """
            UPDATE migration.adaptive_questionnaires aq
            SET collection_flow_id = cf.flow_id
            FROM migration.collection_flows cf
            WHERE aq.collection_flow_id = cf.id
            AND aq.collection_flow_id IS NOT NULL
        """
        )
    )

    # Step 3: Create new FK constraint pointing to flow_id
    op.create_foreign_key(
        "fk_adaptive_questionnaires_collection_flow_id_collection_flows",
        "adaptive_questionnaires",
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
            AND table_name = 'adaptive_questionnaires'
            AND constraint_name = 'fk_adaptive_questionnaires_collection_flow_id_collection_flows'
        """
        )
    )
    if result.fetchone() is not None:
        op.drop_constraint(
            "fk_adaptive_questionnaires_collection_flow_id_collection_flows",
            "adaptive_questionnaires",
            schema="migration",
            type_="foreignkey",
        )

    # Step 2: Migrate data back - update collection_flow_id from flow_id to id
    # WARNING: This re-introduces the bug!
    conn.execute(
        sa.text(
            """
            UPDATE migration.adaptive_questionnaires aq
            SET collection_flow_id = cf.id
            FROM migration.collection_flows cf
            WHERE aq.collection_flow_id = cf.flow_id
            AND aq.collection_flow_id IS NOT NULL
        """
        )
    )

    # Step 3: Recreate old FK constraint pointing to id (WRONG)
    op.create_foreign_key(
        "fk_adaptive_questionnaires_collection_flow_id_collection_flows",
        "adaptive_questionnaires",
        "collection_flows",
        ["collection_flow_id"],
        ["id"],
        source_schema="migration",
        referent_schema="migration",
        ondelete="CASCADE",
    )
