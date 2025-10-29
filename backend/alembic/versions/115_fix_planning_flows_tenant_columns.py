"""Fix planning and timeline tables tenant ID columns to UUID

Revision ID: 115_fix_planning_flows_tenant_columns
Revises: 114_create_resource_planning_tables
Create Date: 2025-10-29

Changes client_account_id and engagement_id columns in planning and timeline tables
from INTEGER to UUID to match the actual data types used throughout the system.

Tables fixed:
- planning_flows (with data transformation from INTEGER 1 to demo UUIDs)
- project_timelines (empty, simple type change)
- timeline_phases (empty, simple type change)
- timeline_milestones (empty, simple type change)
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "115_fix_planning_flows_tenant_columns"
down_revision: Union[str, None] = "114_create_resource_planning_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Change client_account_id and engagement_id from INTEGER to UUID.

    This migration is idempotent - it checks if columns are already UUID type
    before attempting the conversion. It also maps INTEGER 1 to the demo client UUID.
    """
    # Use PostgreSQL DO block for idempotent migration
    op.execute(
        """
        DO $$
        BEGIN
            -- Check if client_account_id is still INTEGER
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'planning_flows'
                AND column_name = 'client_account_id'
                AND data_type = 'integer'
            ) THEN
                -- Add temporary UUID column
                ALTER TABLE migration.planning_flows
                ADD COLUMN client_account_id_uuid UUID;

                -- Map INTEGER 1 to demo client UUID, others to NULL (should not exist)
                UPDATE migration.planning_flows
                SET client_account_id_uuid = CASE
                    WHEN client_account_id = 1 THEN '11111111-1111-1111-1111-111111111111'::UUID
                    ELSE NULL
                END;

                -- Drop old INTEGER column and rename UUID column
                ALTER TABLE migration.planning_flows DROP COLUMN client_account_id;
                ALTER TABLE migration.planning_flows RENAME COLUMN client_account_id_uuid TO client_account_id;

                RAISE NOTICE 'Converted planning_flows.client_account_id from INTEGER to UUID';
            ELSE
                RAISE NOTICE 'planning_flows.client_account_id already UUID type, skipping';
            END IF;

            -- Check if engagement_id is still INTEGER
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'planning_flows'
                AND column_name = 'engagement_id'
                AND data_type = 'integer'
            ) THEN
                -- Add temporary UUID column
                ALTER TABLE migration.planning_flows
                ADD COLUMN engagement_id_uuid UUID;

                -- Map INTEGER 1 to demo engagement UUID, others to NULL (should not exist)
                UPDATE migration.planning_flows
                SET engagement_id_uuid = CASE
                    WHEN engagement_id = 1 THEN '22222222-2222-2222-2222-222222222222'::UUID
                    ELSE NULL
                END;

                -- Drop old INTEGER column and rename UUID column
                ALTER TABLE migration.planning_flows DROP COLUMN engagement_id;
                ALTER TABLE migration.planning_flows RENAME COLUMN engagement_id_uuid TO engagement_id;

                RAISE NOTICE 'Converted planning_flows.engagement_id from INTEGER to UUID';
            ELSE
                RAISE NOTICE 'planning_flows.engagement_id already UUID type, skipping';
            END IF;
        END $$;
    """
    )

    # Fix timeline tables (empty, simpler conversion)
    op.execute(
        """
        -- project_timelines table
        ALTER TABLE migration.project_timelines
        ALTER COLUMN client_account_id TYPE UUID USING client_account_id::text::uuid;

        ALTER TABLE migration.project_timelines
        ALTER COLUMN engagement_id TYPE UUID USING engagement_id::text::uuid;

        -- timeline_phases table
        ALTER TABLE migration.timeline_phases
        ALTER COLUMN client_account_id TYPE UUID USING client_account_id::text::uuid;

        ALTER TABLE migration.timeline_phases
        ALTER COLUMN engagement_id TYPE UUID USING engagement_id::text::uuid;

        -- timeline_milestones table
        ALTER TABLE migration.timeline_milestones
        ALTER COLUMN client_account_id TYPE UUID USING client_account_id::text::uuid;

        ALTER TABLE migration.timeline_milestones
        ALTER COLUMN engagement_id TYPE UUID USING engagement_id::text::uuid;
    """
    )


def downgrade() -> None:
    """
    Revert client_account_id and engagement_id back to INTEGER.

    Maps demo client UUID back to INTEGER 1.
    """
    op.execute(
        """
        DO $$
        BEGIN
            -- Check if client_account_id is UUID
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'planning_flows'
                AND column_name = 'client_account_id'
                AND data_type = 'uuid'
            ) THEN
                -- Add temporary INTEGER column
                ALTER TABLE migration.planning_flows
                ADD COLUMN client_account_id_int INTEGER;

                -- Map demo client UUID back to INTEGER 1
                UPDATE migration.planning_flows
                SET client_account_id_int = CASE
                    WHEN client_account_id = '11111111-1111-1111-1111-111111111111'::UUID THEN 1
                    ELSE NULL
                END;

                -- Drop UUID column and rename INTEGER column
                ALTER TABLE migration.planning_flows DROP COLUMN client_account_id;
                ALTER TABLE migration.planning_flows RENAME COLUMN client_account_id_int TO client_account_id;

                RAISE NOTICE 'Reverted planning_flows.client_account_id from UUID to INTEGER';
            ELSE
                RAISE NOTICE 'planning_flows.client_account_id already INTEGER type, skipping';
            END IF;

            -- Check if engagement_id is UUID
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'planning_flows'
                AND column_name = 'engagement_id'
                AND data_type = 'uuid'
            ) THEN
                -- Add temporary INTEGER column
                ALTER TABLE migration.planning_flows
                ADD COLUMN engagement_id_int INTEGER;

                -- Map demo engagement UUID back to INTEGER 1
                UPDATE migration.planning_flows
                SET engagement_id_int = CASE
                    WHEN engagement_id = '22222222-2222-2222-2222-222222222222'::UUID THEN 1
                    ELSE NULL
                END;

                -- Drop UUID column and rename INTEGER column
                ALTER TABLE migration.planning_flows DROP COLUMN engagement_id;
                ALTER TABLE migration.planning_flows RENAME COLUMN engagement_id_int TO engagement_id;

                RAISE NOTICE 'Reverted planning_flows.engagement_id from UUID to INTEGER';
            ELSE
                RAISE NOTICE 'planning_flows.engagement_id already INTEGER type, skipping';
            END IF;
        END $$;
    """
    )

    # Revert timeline tables (will fail if there are non-integer UUIDs)
    op.execute(
        """
        -- project_timelines table
        ALTER TABLE migration.project_timelines
        ALTER COLUMN client_account_id TYPE INTEGER USING NULLIF(client_account_id::text, '')::integer;

        ALTER TABLE migration.project_timelines
        ALTER COLUMN engagement_id TYPE INTEGER USING NULLIF(engagement_id::text, '')::integer;

        -- timeline_phases table
        ALTER TABLE migration.timeline_phases
        ALTER COLUMN client_account_id TYPE INTEGER USING NULLIF(client_account_id::text, '')::integer;

        ALTER TABLE migration.timeline_phases
        ALTER COLUMN engagement_id TYPE INTEGER USING NULLIF(engagement_id::text, '')::integer;

        -- timeline_milestones table
        ALTER TABLE migration.timeline_milestones
        ALTER COLUMN client_account_id TYPE INTEGER USING NULLIF(client_account_id::text, '')::integer;

        ALTER TABLE migration.timeline_milestones
        ALTER COLUMN engagement_id TYPE INTEGER USING NULLIF(engagement_id::text, '')::integer;
    """
    )
