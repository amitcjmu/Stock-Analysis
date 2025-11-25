"""Align Collection Flow UUIDs with MFO Two-Table Pattern

Revision ID: 136_align_collection_flow_uuids
Revises: 135_add_import_category_to_data_imports
Create Date: 2025-11-24

CC Generated for Issue #1136 - Collection Flow UUID Architecture Fix

This migration aligns existing Collection Flows to the MFO Two-Table Pattern
by setting flow_id = master_flow_id for all existing rows.

Background:
    Collection Flow used a three-UUID pattern (id, flow_id, master_flow_id)
    where all three were different values. This violated the MFO Two-Table
    Pattern used by Discovery/Assessment flows, causing "flow not found" errors.

Solution:
    Set flow_id = master_flow_id for all existing collection flows.
    New flows will be created with this pattern enforced (see
    collection_crud_create_commands.py).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "136_align_collection_flow_uuids"
down_revision = "135_add_import_category_to_data_imports"
branch_labels = None
depends_on = None


def upgrade():
    """
    Align existing Collection Flows to MFO Two-Table Pattern.

    Sets flow_id = master_flow_id for all existing rows where they differ.
    This prevents UUID mismatch bugs in phase handlers and MFO integration.
    """
    # Use PostgreSQL DO block for idempotent execution
    op.execute("""
        DO $$
        DECLARE
            rows_updated INTEGER;
        BEGIN
            -- Update collection_flows: flow_id := master_flow_id
            UPDATE migration.collection_flows
            SET flow_id = master_flow_id
            WHERE flow_id != master_flow_id
              AND master_flow_id IS NOT NULL;

            GET DIAGNOSTICS rows_updated = ROW_COUNT;

            RAISE NOTICE '✅ Migration 136: Updated % collection_flows to align flow_id with master_flow_id', rows_updated;

            -- Log any flows with NULL master_flow_id (should not exist per ADR-006)
            IF EXISTS (
                SELECT 1 FROM migration.collection_flows
                WHERE master_flow_id IS NULL
            ) THEN
                RAISE WARNING '⚠️ Found collection flows with NULL master_flow_id (violates ADR-006). These were NOT updated.';
            END IF;
        END $$;
    """)


def downgrade():
    """
    Rollback: Cannot restore original flow_id values (data loss).

    This migration is irreversible because original flow_id values
    are not preserved. Downgrading would require manual intervention
    to restore the previous UUID values, which is not practical.

    If rollback is absolutely required, you would need to:
    1. Restore from database backup before this migration
    2. Re-run migrations up to 135
    """
    op.execute("""
        DO $$
        BEGIN
            RAISE WARNING '⚠️ Migration 136 downgrade: No action (original flow_id values not preserved)';
            RAISE WARNING '⚠️ To fully rollback, restore from database backup before this migration';
        END $$;
    """)
