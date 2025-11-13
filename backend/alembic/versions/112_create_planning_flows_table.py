"""create_planning_flows_table

Create planning_flows child flow table following Two-Table Pattern (ADR-012).
This table tracks operational state for Wave Planning flows while the master
flow lifecycle is managed in crewai_flow_state_extensions.

Handles:
- Wave planning data and configuration
- Resource allocation results
- Timeline generation
- Cost estimation
- Agent execution tracking
- UI state management
- Multi-tenant scoping

Revision ID: 112_create_planning_flows_table
Revises: 111_remove_sixr_analysis_tables
Create Date: 2025-10-29 00:00:00.000000

Related Issues: #698 (Wave Planning Flow - Database Schema)
"""

from alembic import op
import logging

# revision identifiers, used by Alembic.
revision = "112_create_planning_flows_table"
down_revision = "111_remove_sixr_analysis_tables"
branch_labels = None
depends_on = None

logger = logging.getLogger("alembic")


def upgrade() -> None:
    """
    Create planning_flows table with full schema.

    IDEMPOTENT: Uses IF NOT EXISTS checks for all operations.
    """
    logger.info("Starting migration 112: Create planning_flows table")

    # Step 1: Create the planning_flows table
    logger.info("Step 1: Creating planning_flows table...")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'planning_flows'
            ) THEN
                CREATE TABLE migration.planning_flows (
                    -- Primary Key
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

                    -- Multi-Tenant Scoping (MANDATORY per ADR-012)
                    client_account_id INTEGER NOT NULL,
                    engagement_id INTEGER NOT NULL,

                    -- Master Flow Reference (FK to crewai_flow_state_extensions)
                    master_flow_id UUID NOT NULL,

                    -- Planning Flow Identity (for frontend reference)
                    planning_flow_id UUID NOT NULL UNIQUE,

                    -- Current Phase (operational decisions)
                    current_phase VARCHAR(50) CHECK (current_phase IN (
                        'wave_planning',
                        'resource_allocation',
                        'timeline_generation',
                        'cost_estimation',
                        'synthesis',
                        'completed'
                    )),
                    phase_status VARCHAR(20) CHECK (phase_status IN (
                        'pending',
                        'in_progress',
                        'completed',
                        'failed'
                    )),

                    -- Planning Configuration (from issue #689 answers)
                    planning_config JSONB DEFAULT '{}'::jsonb,
                    -- Example: {"max_apps_per_wave": 50, "wave_duration_limit_days": 90, "sequencing_rules": {...}}

                    -- Wave Planning Results
                    wave_plan_data JSONB DEFAULT '{}'::jsonb,
                    -- Example: {"waves": [{"wave_number": 1, "applications": [...]}]}

                    -- Resource Allocation Results (from issue #690 answers)
                    resource_allocation_data JSONB DEFAULT '{}'::jsonb,
                    -- Example: {"allocations": [{"wave_id": 1, "resources": [...]}], "ai_suggestions": {...}}

                    -- Timeline Results
                    timeline_data JSONB DEFAULT '{}'::jsonb,
                    -- Example: {"phases": [...], "milestones": [...], "gantt_data": {...}}

                    -- Cost Estimation Results
                    cost_estimation_data JSONB DEFAULT '{}'::jsonb,
                    -- Example: {"total_cost": 1500000, "cost_breakdown": {...}}

                    -- Agent Execution Tracking
                    agent_execution_log JSONB DEFAULT '[]'::jsonb,
                    -- Example: [{"agent": "wave_planning_specialist", "started_at": "...", "status": "completed"}]

                    -- UI State Management
                    ui_state JSONB DEFAULT '{}'::jsonb,
                    -- Example: {"selected_wave": 1, "view_mode": "gantt", "filters": {...}}

                    -- Validation & Errors
                    validation_errors JSONB DEFAULT '[]'::jsonb,
                    warnings JSONB DEFAULT '[]'::jsonb,

                    -- Planning Metadata
                    selected_applications JSONB DEFAULT '[]'::jsonb,
                    planning_ready_at TIMESTAMP WITH TIME ZONE,
                    planning_started_at TIMESTAMP WITH TIME ZONE,
                    planning_completed_at TIMESTAMP WITH TIME ZONE,

                    -- Audit Fields
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    created_by UUID,
                    updated_by UUID
                );

                RAISE NOTICE 'Created planning_flows table';
            ELSE
                RAISE NOTICE 'planning_flows table already exists, skipping creation';
            END IF;
        END $$;
        """
    )

    # Step 2: Create indexes for performance optimization
    logger.info("Step 2: Creating indexes...")
    op.execute(
        """
        DO $$
        BEGIN
            -- Composite index for multi-tenant queries
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'planning_flows'
                AND indexname = 'idx_planning_flows_client_engagement'
            ) THEN
                CREATE INDEX idx_planning_flows_client_engagement
                ON migration.planning_flows(client_account_id, engagement_id);
                RAISE NOTICE 'Created index: idx_planning_flows_client_engagement';
            END IF;

            -- Index for master flow lookups
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'planning_flows'
                AND indexname = 'idx_planning_flows_master_flow'
            ) THEN
                CREATE INDEX idx_planning_flows_master_flow
                ON migration.planning_flows(master_flow_id);
                RAISE NOTICE 'Created index: idx_planning_flows_master_flow';
            END IF;

            -- Index for planning flow ID lookups
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'planning_flows'
                AND indexname = 'idx_planning_flows_planning_flow_id'
            ) THEN
                CREATE INDEX idx_planning_flows_planning_flow_id
                ON migration.planning_flows(planning_flow_id);
                RAISE NOTICE 'Created index: idx_planning_flows_planning_flow_id';
            END IF;

            -- Composite index for phase and status queries
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'planning_flows'
                AND indexname = 'idx_planning_flows_phase_status'
            ) THEN
                CREATE INDEX idx_planning_flows_phase_status
                ON migration.planning_flows(current_phase, phase_status);
                RAISE NOTICE 'Created index: idx_planning_flows_phase_status';
            END IF;

            -- GIN index for wave_plan_data JSONB column (fast JSONB searching)
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'planning_flows'
                AND indexname = 'idx_planning_flows_wave_plan_data'
            ) THEN
                CREATE INDEX idx_planning_flows_wave_plan_data
                ON migration.planning_flows USING gin(wave_plan_data);
                RAISE NOTICE 'Created GIN index: idx_planning_flows_wave_plan_data';
            END IF;

            -- GIN index for resource_allocation_data JSONB column
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'planning_flows'
                AND indexname = 'idx_planning_flows_resource_data'
            ) THEN
                CREATE INDEX idx_planning_flows_resource_data
                ON migration.planning_flows USING gin(resource_allocation_data);
                RAISE NOTICE 'Created GIN index: idx_planning_flows_resource_data';
            END IF;

            -- GIN index for timeline_data JSONB column
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'planning_flows'
                AND indexname = 'idx_planning_flows_timeline_data'
            ) THEN
                CREATE INDEX idx_planning_flows_timeline_data
                ON migration.planning_flows USING gin(timeline_data);
                RAISE NOTICE 'Created GIN index: idx_planning_flows_timeline_data';
            END IF;
        END $$;
        """
    )

    # Step 3: Add foreign key constraint to master flow
    logger.info("Step 3: Adding foreign key constraints...")
    op.execute(
        """
        DO $$
        BEGIN
            -- FK to crewai_flow_state_extensions (master flow)
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.table_constraints
                WHERE constraint_schema = 'migration'
                AND table_name = 'planning_flows'
                AND constraint_name = 'fk_planning_flows_master_flow'
            ) THEN
                ALTER TABLE migration.planning_flows
                ADD CONSTRAINT fk_planning_flows_master_flow
                FOREIGN KEY (master_flow_id)
                REFERENCES migration.crewai_flow_state_extensions(flow_id)
                ON DELETE CASCADE;
                RAISE NOTICE 'Created FK constraint: fk_planning_flows_master_flow';
            END IF;
        END $$;
        """
    )

    # Step 4: Create trigger for auto-updating updated_at timestamp
    logger.info("Step 4: Creating updated_at trigger...")
    op.execute(
        """
        DO $$
        BEGIN
            -- Check if trigger exists
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.triggers
                WHERE event_object_schema = 'migration'
                AND event_object_table = 'planning_flows'
                AND trigger_name = 'update_planning_flows_updated_at'
            ) THEN
                CREATE TRIGGER update_planning_flows_updated_at
                BEFORE UPDATE ON migration.planning_flows
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
                RAISE NOTICE 'Created trigger: update_planning_flows_updated_at';
            END IF;
        END $$;
        """
    )

    logger.info("✅ Migration 112 complete: planning_flows table created")
    logger.info(
        "   - Two-Table Pattern (ADR-012): Master flow in crewai_flow_state_extensions"
    )
    logger.info("   - Child flow operational state in planning_flows")
    logger.info("   - Multi-tenant scoping: client_account_id + engagement_id")
    logger.info("   - JSONB columns for flexible planning data storage")
    logger.info("   - GIN indexes for efficient JSONB queries")


def downgrade() -> None:
    """
    Drop planning_flows table and all associated indexes/constraints.

    IDEMPOTENT: Uses IF EXISTS checks for cleanup.
    """
    logger.info("Rolling back migration 112: Dropping planning_flows table...")

    # Drop trigger first
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.triggers
                WHERE event_object_schema = 'migration'
                AND event_object_table = 'planning_flows'
                AND trigger_name = 'update_planning_flows_updated_at'
            ) THEN
                DROP TRIGGER update_planning_flows_updated_at ON migration.planning_flows;
                RAISE NOTICE 'Dropped trigger: update_planning_flows_updated_at';
            END IF;
        END $$;
        """
    )

    # Drop table (CASCADE will drop indexes and constraints)
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'planning_flows'
            ) THEN
                DROP TABLE migration.planning_flows CASCADE;
                RAISE NOTICE 'Dropped planning_flows table';
            ELSE
                RAISE NOTICE 'planning_flows table does not exist, skipping drop';
            END IF;
        END $$;
        """
    )

    logger.info("✅ Migration 112 rollback complete")
