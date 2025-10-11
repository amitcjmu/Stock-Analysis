"""Add asset conflict resolution table

Revision ID: 089_add_asset_conflict_resolution
Revises: 088_add_asset_dedup_composite_indexes
Create Date: 2025-01-11

CC: Implements user-choice asset deduplication with conflict tracking
Per: /docs/development/discovery/asset-deduplication-user-choice-implementation-plan.md
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "089_add_asset_conflict_resolution"
down_revision = "088_add_asset_dedup_composite_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create asset_conflict_resolutions table for user-choice deduplication"""

    # Create table
    op.create_table(
        "asset_conflict_resolutions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Multi-tenant context (MANDATORY for all queries)
        sa.Column("client_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("engagement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "flow_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Discovery flow ID where conflict was detected",
        ),
        sa.Column(
            "data_import_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="Source data import batch",
        ),
        # Conflict identification
        sa.Column(
            "conflict_type",
            sa.String(50),
            nullable=False,
            comment="Type: hostname, ip_address, or name",
        ),
        sa.Column(
            "conflict_key",
            sa.String(255),
            nullable=False,
            comment="The duplicate value (e.g., hostname value)",
        ),
        # Asset references
        sa.Column(
            "existing_asset_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="ID of existing asset in database",
        ),
        sa.Column(
            "existing_asset_snapshot",
            postgresql.JSONB,
            nullable=False,
            comment="Full snapshot of existing asset at detection time",
        ),
        sa.Column(
            "new_asset_data",
            postgresql.JSONB,
            nullable=False,
            comment="Full data for incoming asset",
        ),
        # Resolution tracking
        sa.Column(
            "resolution_status",
            sa.String(20),
            nullable=False,
            server_default="pending",
            comment="pending, resolved, skipped, or system_merged",
        ),
        sa.Column(
            "resolution_action",
            sa.String(20),
            nullable=True,
            comment="keep_existing, replace, or merge (null for pending)",
        ),
        sa.Column(
            "merge_field_selections",
            postgresql.JSONB,
            nullable=True,
            comment='For merge action: {field_name: source} where source is "existing" or "new"',
        ),
        # Audit trail
        sa.Column(
            "resolved_by",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="User ID who resolved (null for pending/system)",
        ),
        sa.Column(
            "resolved_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When resolution was applied",
        ),
        sa.Column(
            "resolution_notes",
            sa.Text,
            nullable=True,
            comment="Optional user notes for resolution decision",
        ),
        # Standard timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            onupdate=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        # Foreign keys
        sa.ForeignKeyConstraint(
            ["client_account_id"],
            ["migration.client_accounts.id"],
            name="fk_asset_conflicts_client",
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"],
            ["migration.engagements.id"],
            name="fk_asset_conflicts_engagement",
        ),
        sa.ForeignKeyConstraint(
            ["flow_id"],
            ["migration.discovery_flows.id"],
            name="fk_asset_conflicts_flow",
        ),
        sa.ForeignKeyConstraint(
            ["data_import_id"],
            ["migration.data_imports.id"],
            name="fk_asset_conflicts_import",
        ),
        sa.ForeignKeyConstraint(
            ["existing_asset_id"],
            ["migration.assets.id"],
            name="fk_asset_conflicts_existing_asset",
        ),
        sa.ForeignKeyConstraint(
            ["resolved_by"],
            ["migration.users.id"],
            name="fk_asset_conflicts_resolved_by",
        ),
        # CHECK constraints (not PostgreSQL ENUMs per CLAUDE.md guidelines)
        sa.CheckConstraint(
            "conflict_type IN ('hostname', 'ip_address', 'name')",
            name="ck_asset_conflicts_type",
        ),
        sa.CheckConstraint(
            "resolution_status IN ('pending', 'resolved', 'skipped', 'system_merged')",
            name="ck_asset_conflicts_status",
        ),
        sa.CheckConstraint(
            "resolution_action IN ('keep_existing', 'replace', 'merge') OR resolution_action IS NULL",
            name="ck_asset_conflicts_action",
        ),
        sa.CheckConstraint(
            """(resolution_status = 'pending'
                AND resolution_action IS NULL
                AND resolved_by IS NULL
                AND resolved_at IS NULL)
            OR (resolution_status != 'pending'
                AND resolution_action IS NOT NULL)""",
            name="ck_asset_conflicts_resolution_consistency",
        ),
        schema="migration",
    )

    # Indexes for common query patterns

    # Query 1: List pending conflicts for a flow (most common in UI)
    op.create_index(
        "ix_asset_conflicts_pending_by_flow",
        "asset_conflict_resolutions",
        ["flow_id", "resolution_status"],
        unique=False,
        schema="migration",
        postgresql_where=sa.text("resolution_status = 'pending'"),
    )

    # Query 2: Multi-tenant scoped queries (ALL queries must include these)
    op.create_index(
        "ix_asset_conflicts_tenant_scope",
        "asset_conflict_resolutions",
        ["client_account_id", "engagement_id", "flow_id"],
        unique=False,
        schema="migration",
    )

    # Query 3: Lookup by existing asset (for cascade checks)
    op.create_index(
        "ix_asset_conflicts_existing_asset",
        "asset_conflict_resolutions",
        ["existing_asset_id"],
        unique=False,
        schema="migration",
    )

    # Query 4: Conflict detection lookup (check if conflict already recorded)
    op.create_index(
        "ix_asset_conflicts_dedup_key",
        "asset_conflict_resolutions",
        ["client_account_id", "engagement_id", "conflict_type", "conflict_key"],
        unique=False,
        schema="migration",
    )


def downgrade() -> None:
    """Drop asset_conflict_resolutions table and indexes"""

    # Drop indexes first
    op.drop_index(
        "ix_asset_conflicts_dedup_key",
        table_name="asset_conflict_resolutions",
        schema="migration",
    )
    op.drop_index(
        "ix_asset_conflicts_existing_asset",
        table_name="asset_conflict_resolutions",
        schema="migration",
    )
    op.drop_index(
        "ix_asset_conflicts_tenant_scope",
        table_name="asset_conflict_resolutions",
        schema="migration",
    )
    op.drop_index(
        "ix_asset_conflicts_pending_by_flow",
        table_name="asset_conflict_resolutions",
        schema="migration",
    )

    # Drop table
    op.drop_table("asset_conflict_resolutions", schema="migration")
