"""revert_questionnaire_fk_to_id

Revision ID: 083_revert_questionnaire_fk_to_id
Revises: 082_fix_gaps_collection_flow_fk
Create Date: 2025-10-05

REVERT INCORRECT FK RETARGETING - Migration 081 was wrong!

Root Cause Analysis:
- ORM models define FK as: ForeignKey("collection_flows.id", ondelete="CASCADE")
- Migration 081 changed FK to point to "collection_flows.flow_id" (business identifier)
- This breaks ORM relationships, cascades, and performance

Correct Architecture:
- FK must point to PRIMARY KEY (collection_flows.id) per SQLAlchemy/PostgreSQL best practices
- flow_id is a business identifier for external APIs, NOT for internal FK relationships
- The bug was in resolve_collection_flow_id() querying wrong column, not in FK definition

This migration:
1. Drops FK pointing to flow_id (incorrect)
2. Migrates data: flow_id values → id values (restore FK integrity)
3. Recreates FK pointing to id (correct, matches ORM)
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "083_revert_questionnaire_fk_to_id"
down_revision = "082_fix_gaps_collection_flow_fk"
branch_labels = None
depends_on = None


def upgrade():
    """
    Revert FK to point to collection_flows.id (PRIMARY KEY).

    Steps:
    1. Drop incorrect FK (points to flow_id)
    2. Migrate data: map collection_flow_id from flow_id → id
    3. Create correct FK (points to id/PK)
    """

    conn = op.get_bind()

    # Step 1: Drop FK pointing to flow_id (from migration 081)
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

    # Step 2: Migrate data - translate flow_id values back to id (PK) values
    # CRITICAL: Questionnaires currently store flow_id, need to map to id for FK
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

    # Step 3: Create correct FK pointing to PRIMARY KEY (id)
    op.create_foreign_key(
        "fk_adaptive_questionnaires_collection_flow_id_collection_flows",
        "adaptive_questionnaires",
        "collection_flows",
        ["collection_flow_id"],
        ["id"],  # Point to PRIMARY KEY, not flow_id
        source_schema="migration",
        referent_schema="migration",
        ondelete="CASCADE",
    )


def downgrade():
    """
    Downgrade back to incorrect FK (points to flow_id).

    WARNING: This recreates the bug! Only for rollback testing.
    """

    conn = op.get_bind()

    # Drop correct FK
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

    # Migrate data back to flow_id
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

    # Recreate incorrect FK (points to flow_id)
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
