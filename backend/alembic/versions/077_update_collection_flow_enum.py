"""Update collection flow enum to include asset_selection (SUPERSEDED)

Revision ID: 077_update_collection_flow_enum
Revises: 076_remap_collection_flow_phases
Create Date: 2025-09-25 01:40:00.000000

IMPORTANT: This migration is superseded by migrations 086 and 087 (PR #518, Oct 2025).
It was originally created to fix ADR-012 violations but was replaced by a more
comprehensive solution.

This migration is now a NO-OP to maintain migration chain integrity for databases
that already have this migration in their version history.

The correct ADR-012 implementation is in:
- Migration 086: Adds 'running' status, migrates phase values to 'running'
- Migration 087: Adds 'paused' status, removes deprecated phase values

Reference:
- PR #518: Complete ADR-012 compliance for Collection Flow Status
- Memory: adr-012-collection-flow-status-remediation
- COLLECTION_FLOW_STATUS_REMEDIATION_PLAN.md
"""

# revision identifiers, used by Alembic.
revision = "077_update_collection_flow_enum"
down_revision = "076_remap_collection_flow_phases"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    NO-OP: This migration is superseded by migrations 086 and 087.

    Originally attempted to update collectionflowstatus enum but was incorrectly
    mixing lifecycle states (status) with operational phases (current_phase).

    The correct implementation is in migration 087, which sets the enum to:
    - initialized, running, paused, completed, failed, cancelled (lifecycle states only)

    This migration does nothing to avoid breaking the migration chain for databases
    that have already recorded this migration in alembic_version table.
    """
    print("ℹ️  Migration 077 is a NO-OP (superseded by migrations 086-087 from PR #518)")
    print("   CollectionFlowStatus enum will be correctly updated by migration 087")
    print("   Skipping to maintain migration chain integrity...")


def downgrade() -> None:
    """
    NO-OP: Downgrade is not needed as upgrade is also a no-op.

    The actual enum changes are handled by migrations 086 and 087.
    """
    print("ℹ️  Migration 077 downgrade is a NO-OP (migration superseded by 086-087)")
