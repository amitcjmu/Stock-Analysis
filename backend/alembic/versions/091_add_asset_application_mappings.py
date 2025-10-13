"""add_asset_application_mappings

Revision ID: 091_add_asset_application_mappings
Revises: 090_fix_asset_conflict_action_constraint
Create Date: 2025-10-13 10:00:00.000000

CC: Add asset_application_mappings table for Assessment flow Phase 1
Per docs/planning/dependency-to-assessment/README.md Step 1
Resolves asset→application mismatch between Collection and Assessment flows
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "091_add_asset_application_mappings"
down_revision = "090_fix_asset_conflict_action_constraint"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create asset_application_mappings table with tenant scoping and audit fields

    CC: Migration is idempotent with IF NOT EXISTS checks
    All operations execute atomically within Alembic's automatic transaction
    """

    # Create asset_application_mappings table
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS migration.asset_application_mappings (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            assessment_flow_id UUID NOT NULL,
            asset_id UUID NOT NULL,
            application_id UUID NOT NULL,
            mapping_confidence NUMERIC(3,2) DEFAULT 1.00,
            mapping_method VARCHAR(50) NOT NULL DEFAULT 'user_manual',
            client_account_id UUID NOT NULL,
            engagement_id UUID NOT NULL,
            created_by UUID,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            CONSTRAINT uq_asset_app_mapping UNIQUE(assessment_flow_id, asset_id),
            CONSTRAINT ck_mapping_confidence CHECK (
                mapping_confidence >= 0.0 AND mapping_confidence <= 1.0
            ),
            CONSTRAINT ck_mapping_method CHECK (
                mapping_method IN (
                    'user_manual',
                    'agent_suggested',
                    'deduplication_auto'
                )
            )
        );
        """
    )

    # Create indexes for performance
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_mappings_flow
            ON migration.asset_application_mappings(assessment_flow_id);
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_mappings_tenant
            ON migration.asset_application_mappings(client_account_id, engagement_id);
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_mappings_asset
            ON migration.asset_application_mappings(asset_id);
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_mappings_application
            ON migration.asset_application_mappings(application_id);
        """
    )


def downgrade() -> None:
    """Drop asset_application_mappings table and all indexes

    CC: Migration atomicity is guaranteed by Alembic's automatic transaction wrapping
    CASCADE ensures indexes are dropped automatically with the table
    """

    op.execute("DROP TABLE IF EXISTS migration.asset_application_mappings CASCADE;")
