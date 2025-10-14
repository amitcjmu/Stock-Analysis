"""add_phase_deprecation_comments_adr027

Add deprecation comments to discovery_flows columns for phases
migrated to assessment flow per ADR-027.

Revision ID: 10ae8e355c48
Revises: 090_fix_asset_conflict_action_constraint
Create Date: 2025-10-14 20:51:50.245126

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "10ae8e355c48"
down_revision = "090_fix_asset_conflict_action_constraint"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add deprecation comments to columns for phases that moved
    from Discovery to Assessment flow per ADR-027.

    These columns are retained for backward compatibility but
    should not be used for new flows.
    """
    # Add comment to dependency_analysis_completed column
    op.execute(
        """
        COMMENT ON COLUMN migration.discovery_flows.dependency_analysis_completed IS
        'DEPRECATED: This phase moved to Assessment flow in v3.0.0. '
        'Kept for backward compatibility with legacy data. '
        'New flows should use Assessment flow for dependency analysis. '
        'See ADR-027 for details.'
    """
    )

    # Add comment to tech_debt_assessment_completed column
    op.execute(
        """
        COMMENT ON COLUMN migration.discovery_flows.tech_debt_assessment_completed IS
        'DEPRECATED: This phase moved to Assessment flow in v3.0.0. '
        'Kept for backward compatibility with legacy data. '
        'New flows should use Assessment flow for technical debt assessment. '
        'See ADR-027 for details.'
    """
    )

    # Add comment to tech_debt_analysis column
    op.execute(
        """
        COMMENT ON COLUMN migration.discovery_flows.tech_debt_analysis IS
        'DEPRECATED: Tech debt analysis moved to Assessment flow in v3.0.0. '
        'This column is retained for backward compatibility only. '
        'See ADR-027 for details.'
    """
    )


def downgrade() -> None:
    """Remove deprecation comments"""
    op.execute(
        "COMMENT ON COLUMN migration.discovery_flows.dependency_analysis_completed IS NULL"
    )
    op.execute(
        "COMMENT ON COLUMN migration.discovery_flows.tech_debt_assessment_completed IS NULL"
    )
    op.execute("COMMENT ON COLUMN migration.discovery_flows.tech_debt_analysis IS NULL")
