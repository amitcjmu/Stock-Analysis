"""create_timeline_tables

Create timeline planning tables following Two-Table Pattern (ADR-012) for
Gantt chart visualization and structured timeline management.

Three tables:
1. project_timelines - Master timeline per planning flow
2. timeline_phases - Migration phases within timeline
3. timeline_milestones - Key milestones and deliverables

Handles:
- Timeline visualization data for Gantt charts
- Phase dependency tracking (finish-to-start, etc.)
- Critical path analysis
- Milestone tracking and notifications
- Multi-tenant scoping
- Integration with planning flows and wave plans

Revision ID: 113_create_timeline_tables
Revises: 112_create_planning_flows_table
Create Date: 2025-10-29 00:00:00.000000

Related Issues: #701 (Timeline Planning Integration)
"""

from alembic import op
import logging

# revision identifiers, used by Alembic.
revision = "113_create_timeline_tables"
down_revision = "112_create_planning_flows_table"
branch_labels = None
depends_on = None

logger = logging.getLogger("alembic")


def upgrade() -> None:
    """
    Create timeline tables with full schema.

    IDEMPOTENT: Uses IF NOT EXISTS checks for all operations.
    """
    logger.info("Starting migration 113: Create timeline tables")

    # Step 1: Create project_timelines table (master timeline)
    logger.info("Step 1: Creating project_timelines table...")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'project_timelines'
            ) THEN
                CREATE TABLE migration.project_timelines (
                    -- Primary Key
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

                    -- Multi-Tenant Scoping (MANDATORY)
                    client_account_id INTEGER NOT NULL,
                    engagement_id INTEGER NOT NULL,

                    -- Planning Flow Reference
                    planning_flow_id UUID NOT NULL,

                    -- Timeline Metadata
                    timeline_name VARCHAR(255) NOT NULL,
                    description TEXT,

                    -- Timeline Dates
                    overall_start_date TIMESTAMP WITH TIME ZONE NOT NULL,
                    overall_end_date TIMESTAMP WITH TIME ZONE NOT NULL,
                    baseline_start_date TIMESTAMP WITH TIME ZONE,
                    baseline_end_date TIMESTAMP WITH TIME ZONE,

                    -- Critical Path Analysis
                    critical_path_data JSONB DEFAULT '{}'::jsonb,
                    -- Example: {"critical_tasks": [...], "total_duration_days": 180}

                    -- Status
                    status VARCHAR(20) CHECK (status IN (
                        'draft',
                        'active',
                        'on_track',
                        'at_risk',
                        'delayed',
                        'completed'
                    )) NOT NULL DEFAULT 'draft',
                    progress_percentage NUMERIC(5,2) DEFAULT 0.00
                        CHECK (progress_percentage >= 0 AND progress_percentage <= 100),

                    -- AI-Generated Insights
                    ai_recommendations JSONB DEFAULT '{}'::jsonb,
                    optimization_score NUMERIC(5,2)
                        CHECK (optimization_score IS NULL OR (optimization_score >= 0 AND optimization_score <= 100)),

                    -- Audit Fields
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    created_by UUID,
                    updated_by UUID
                );

                RAISE NOTICE 'Created project_timelines table';
            ELSE
                RAISE NOTICE 'project_timelines table already exists, skipping creation';
            END IF;
        END $$;
        """
    )

    # Step 2: Create timeline_phases table
    logger.info("Step 2: Creating timeline_phases table...")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'timeline_phases'
            ) THEN
                CREATE TABLE migration.timeline_phases (
                    -- Primary Key
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

                    -- Multi-Tenant Scoping (MANDATORY)
                    client_account_id INTEGER NOT NULL,
                    engagement_id INTEGER NOT NULL,

                    -- Timeline Reference
                    timeline_id UUID NOT NULL,

                    -- Wave Reference (optional - phase may span multiple waves)
                    wave_id UUID,

                    -- Phase Identity
                    phase_number INTEGER NOT NULL,
                    phase_name VARCHAR(255) NOT NULL,
                    description TEXT,

                    -- Phase Dates
                    planned_start_date TIMESTAMP WITH TIME ZONE NOT NULL,
                    planned_end_date TIMESTAMP WITH TIME ZONE NOT NULL,
                    actual_start_date TIMESTAMP WITH TIME ZONE,
                    actual_end_date TIMESTAMP WITH TIME ZONE,

                    -- Dependencies
                    predecessor_phase_ids JSONB DEFAULT '[]'::jsonb,
                    -- Array of phase IDs that must complete before this phase
                    dependency_type VARCHAR(20) CHECK (dependency_type IN (
                        'finish_to_start',
                        'start_to_start',
                        'finish_to_finish',
                        'start_to_finish'
                    )) DEFAULT 'finish_to_start',
                    lag_days INTEGER DEFAULT 0,

                    -- Phase Details
                    effort_hours NUMERIC(10,2),
                    estimated_cost NUMERIC(15,2),
                    assigned_resources JSONB DEFAULT '[]'::jsonb,
                    -- Example: [{"resource_id": "uuid", "allocation_percentage": 50}]

                    -- Status Tracking
                    status VARCHAR(20) CHECK (status IN (
                        'not_started',
                        'in_progress',
                        'on_hold',
                        'completed',
                        'cancelled'
                    )) NOT NULL DEFAULT 'not_started',
                    progress_percentage NUMERIC(5,2) DEFAULT 0.00
                        CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
                    is_on_critical_path BOOLEAN DEFAULT false,

                    -- Risk & Issues
                    risk_level VARCHAR(20) CHECK (risk_level IN (
                        'low',
                        'medium',
                        'high',
                        'critical'
                    )) DEFAULT 'low',
                    blocking_issues JSONB DEFAULT '[]'::jsonb,
                    -- Example: [{"issue_id": "uuid", "description": "...", "severity": "high"}]

                    -- Audit Fields
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                );

                RAISE NOTICE 'Created timeline_phases table';
            ELSE
                RAISE NOTICE 'timeline_phases table already exists, skipping creation';
            END IF;
        END $$;
        """
    )

    # Step 3: Create timeline_milestones table
    logger.info("Step 3: Creating timeline_milestones table...")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'timeline_milestones'
            ) THEN
                CREATE TABLE migration.timeline_milestones (
                    -- Primary Key
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

                    -- Multi-Tenant Scoping (MANDATORY)
                    client_account_id INTEGER NOT NULL,
                    engagement_id INTEGER NOT NULL,

                    -- Timeline Reference
                    timeline_id UUID NOT NULL,

                    -- Phase Reference (optional - milestone may be cross-phase)
                    phase_id UUID,

                    -- Milestone Identity
                    milestone_name VARCHAR(255) NOT NULL,
                    description TEXT,
                    milestone_type VARCHAR(50) CHECK (milestone_type IN (
                        'phase_completion',
                        'deliverable',
                        'gate_review',
                        'dependency',
                        'custom'
                    )) NOT NULL DEFAULT 'custom',

                    -- Milestone Date
                    target_date TIMESTAMP WITH TIME ZONE NOT NULL,
                    actual_date TIMESTAMP WITH TIME ZONE,
                    baseline_date TIMESTAMP WITH TIME ZONE,

                    -- Status
                    status VARCHAR(20) CHECK (status IN (
                        'pending',
                        'at_risk',
                        'achieved',
                        'missed'
                    )) NOT NULL DEFAULT 'pending',
                    is_critical BOOLEAN DEFAULT false,

                    -- Deliverables
                    deliverables JSONB DEFAULT '[]'::jsonb,
                    -- Example: [{"name": "Migration plan", "status": "completed", "link": "..."}]

                    -- Dependencies
                    depends_on_milestone_ids JSONB DEFAULT '[]'::jsonb,
                    -- Array of milestone IDs that must complete before this milestone

                    -- Notification Settings
                    notify_days_before INTEGER DEFAULT 7,
                    notification_sent BOOLEAN DEFAULT false,

                    -- Audit Fields
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                );

                RAISE NOTICE 'Created timeline_milestones table';
            ELSE
                RAISE NOTICE 'timeline_milestones table already exists, skipping creation';
            END IF;
        END $$;
        """
    )

    # Step 4: Create indexes for project_timelines
    logger.info("Step 4: Creating indexes for project_timelines...")
    op.execute(
        """
        DO $$
        BEGIN
            -- Composite index for multi-tenant queries
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'project_timelines'
                AND indexname = 'idx_timelines_client_engagement'
            ) THEN
                CREATE INDEX idx_timelines_client_engagement
                ON migration.project_timelines(client_account_id, engagement_id);
                RAISE NOTICE 'Created index: idx_timelines_client_engagement';
            END IF;

            -- Index for planning flow lookups
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'project_timelines'
                AND indexname = 'idx_timelines_planning_flow'
            ) THEN
                CREATE INDEX idx_timelines_planning_flow
                ON migration.project_timelines(planning_flow_id);
                RAISE NOTICE 'Created index: idx_timelines_planning_flow';
            END IF;

            -- Index for status queries
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'project_timelines'
                AND indexname = 'idx_timelines_status'
            ) THEN
                CREATE INDEX idx_timelines_status
                ON migration.project_timelines(status);
                RAISE NOTICE 'Created index: idx_timelines_status';
            END IF;

            -- Index for date range queries
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'project_timelines'
                AND indexname = 'idx_timelines_dates'
            ) THEN
                CREATE INDEX idx_timelines_dates
                ON migration.project_timelines(overall_start_date, overall_end_date);
                RAISE NOTICE 'Created index: idx_timelines_dates';
            END IF;

            -- GIN index for critical_path_data JSONB
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'project_timelines'
                AND indexname = 'idx_timelines_critical_path_data'
            ) THEN
                CREATE INDEX idx_timelines_critical_path_data
                ON migration.project_timelines USING gin(critical_path_data);
                RAISE NOTICE 'Created GIN index: idx_timelines_critical_path_data';
            END IF;
        END $$;
        """
    )

    # Step 5: Create indexes for timeline_phases
    logger.info("Step 5: Creating indexes for timeline_phases...")
    op.execute(
        """
        DO $$
        BEGIN
            -- Index for timeline lookups
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'timeline_phases'
                AND indexname = 'idx_phases_timeline'
            ) THEN
                CREATE INDEX idx_phases_timeline
                ON migration.timeline_phases(timeline_id);
                RAISE NOTICE 'Created index: idx_phases_timeline';
            END IF;

            -- Index for wave lookups
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'timeline_phases'
                AND indexname = 'idx_phases_wave'
            ) THEN
                CREATE INDEX idx_phases_wave
                ON migration.timeline_phases(wave_id);
                RAISE NOTICE 'Created index: idx_phases_wave';
            END IF;

            -- Index for status queries
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'timeline_phases'
                AND indexname = 'idx_phases_status'
            ) THEN
                CREATE INDEX idx_phases_status
                ON migration.timeline_phases(status);
                RAISE NOTICE 'Created index: idx_phases_status';
            END IF;

            -- Partial index for critical path phases
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'timeline_phases'
                AND indexname = 'idx_phases_critical_path'
            ) THEN
                CREATE INDEX idx_phases_critical_path
                ON migration.timeline_phases(is_on_critical_path)
                WHERE is_on_critical_path = true;
                RAISE NOTICE 'Created partial index: idx_phases_critical_path';
            END IF;

            -- Index for date range queries
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'timeline_phases'
                AND indexname = 'idx_phases_dates'
            ) THEN
                CREATE INDEX idx_phases_dates
                ON migration.timeline_phases(planned_start_date, planned_end_date);
                RAISE NOTICE 'Created index: idx_phases_dates';
            END IF;

            -- Composite index for multi-tenant queries
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'timeline_phases'
                AND indexname = 'idx_phases_client_engagement'
            ) THEN
                CREATE INDEX idx_phases_client_engagement
                ON migration.timeline_phases(client_account_id, engagement_id);
                RAISE NOTICE 'Created index: idx_phases_client_engagement';
            END IF;
        END $$;
        """
    )

    # Step 6: Create indexes for timeline_milestones
    logger.info("Step 6: Creating indexes for timeline_milestones...")
    op.execute(
        """
        DO $$
        BEGIN
            -- Index for timeline lookups
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'timeline_milestones'
                AND indexname = 'idx_milestones_timeline'
            ) THEN
                CREATE INDEX idx_milestones_timeline
                ON migration.timeline_milestones(timeline_id);
                RAISE NOTICE 'Created index: idx_milestones_timeline';
            END IF;

            -- Index for phase lookups
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'timeline_milestones'
                AND indexname = 'idx_milestones_phase'
            ) THEN
                CREATE INDEX idx_milestones_phase
                ON migration.timeline_milestones(phase_id);
                RAISE NOTICE 'Created index: idx_milestones_phase';
            END IF;

            -- Index for target date queries (important for notifications)
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'timeline_milestones'
                AND indexname = 'idx_milestones_target_date'
            ) THEN
                CREATE INDEX idx_milestones_target_date
                ON migration.timeline_milestones(target_date);
                RAISE NOTICE 'Created index: idx_milestones_target_date';
            END IF;

            -- Partial index for critical milestones
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'timeline_milestones'
                AND indexname = 'idx_milestones_critical'
            ) THEN
                CREATE INDEX idx_milestones_critical
                ON migration.timeline_milestones(is_critical)
                WHERE is_critical = true;
                RAISE NOTICE 'Created partial index: idx_milestones_critical';
            END IF;

            -- Composite index for multi-tenant queries
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'timeline_milestones'
                AND indexname = 'idx_milestones_client_engagement'
            ) THEN
                CREATE INDEX idx_milestones_client_engagement
                ON migration.timeline_milestones(client_account_id, engagement_id);
                RAISE NOTICE 'Created index: idx_milestones_client_engagement';
            END IF;

            -- Index for status queries
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'timeline_milestones'
                AND indexname = 'idx_milestones_status'
            ) THEN
                CREATE INDEX idx_milestones_status
                ON migration.timeline_milestones(status);
                RAISE NOTICE 'Created index: idx_milestones_status';
            END IF;
        END $$;
        """
    )

    # Step 7: Add foreign key constraints
    logger.info("Step 7: Adding foreign key constraints...")
    op.execute(
        """
        DO $$
        BEGIN
            -- project_timelines → planning_flows
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_schema = 'migration'
                AND table_name = 'project_timelines'
                AND constraint_name = 'fk_timelines_planning_flow'
            ) THEN
                ALTER TABLE migration.project_timelines
                ADD CONSTRAINT fk_timelines_planning_flow
                FOREIGN KEY (planning_flow_id)
                REFERENCES migration.planning_flows(planning_flow_id)
                ON DELETE CASCADE;
                RAISE NOTICE 'Created FK: fk_timelines_planning_flow';
            END IF;

            -- timeline_phases → project_timelines
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_schema = 'migration'
                AND table_name = 'timeline_phases'
                AND constraint_name = 'fk_phases_timeline'
            ) THEN
                ALTER TABLE migration.timeline_phases
                ADD CONSTRAINT fk_phases_timeline
                FOREIGN KEY (timeline_id)
                REFERENCES migration.project_timelines(id)
                ON DELETE CASCADE;
                RAISE NOTICE 'Created FK: fk_phases_timeline';
            END IF;

            -- timeline_phases → migration_waves (optional)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_schema = 'migration'
                AND table_name = 'timeline_phases'
                AND constraint_name = 'fk_phases_wave'
            ) THEN
                ALTER TABLE migration.timeline_phases
                ADD CONSTRAINT fk_phases_wave
                FOREIGN KEY (wave_id)
                REFERENCES migration.migration_waves(id)
                ON DELETE SET NULL;
                RAISE NOTICE 'Created FK: fk_phases_wave';
            END IF;

            -- timeline_milestones → project_timelines
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_schema = 'migration'
                AND table_name = 'timeline_milestones'
                AND constraint_name = 'fk_milestones_timeline'
            ) THEN
                ALTER TABLE migration.timeline_milestones
                ADD CONSTRAINT fk_milestones_timeline
                FOREIGN KEY (timeline_id)
                REFERENCES migration.project_timelines(id)
                ON DELETE CASCADE;
                RAISE NOTICE 'Created FK: fk_milestones_timeline';
            END IF;

            -- timeline_milestones → timeline_phases (optional)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_schema = 'migration'
                AND table_name = 'timeline_milestones'
                AND constraint_name = 'fk_milestones_phase'
            ) THEN
                ALTER TABLE migration.timeline_milestones
                ADD CONSTRAINT fk_milestones_phase
                FOREIGN KEY (phase_id)
                REFERENCES migration.timeline_phases(id)
                ON DELETE SET NULL;
                RAISE NOTICE 'Created FK: fk_milestones_phase';
            END IF;
        END $$;
        """
    )

    # Step 8: Create triggers for auto-updating updated_at timestamps
    logger.info("Step 8: Creating updated_at triggers...")
    op.execute(
        """
        DO $$
        BEGIN
            -- Trigger for project_timelines
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.triggers
                WHERE event_object_schema = 'migration'
                AND event_object_table = 'project_timelines'
                AND trigger_name = 'update_timelines_updated_at'
            ) THEN
                CREATE TRIGGER update_timelines_updated_at
                BEFORE UPDATE ON migration.project_timelines
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
                RAISE NOTICE 'Created trigger: update_timelines_updated_at';
            END IF;

            -- Trigger for timeline_phases
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.triggers
                WHERE event_object_schema = 'migration'
                AND event_object_table = 'timeline_phases'
                AND trigger_name = 'update_phases_updated_at'
            ) THEN
                CREATE TRIGGER update_phases_updated_at
                BEFORE UPDATE ON migration.timeline_phases
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
                RAISE NOTICE 'Created trigger: update_phases_updated_at';
            END IF;

            -- Trigger for timeline_milestones
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.triggers
                WHERE event_object_schema = 'migration'
                AND event_object_table = 'timeline_milestones'
                AND trigger_name = 'update_milestones_updated_at'
            ) THEN
                CREATE TRIGGER update_milestones_updated_at
                BEFORE UPDATE ON migration.timeline_milestones
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
                RAISE NOTICE 'Created trigger: update_milestones_updated_at';
            END IF;
        END $$;
        """
    )

    logger.info("✅ Migration 113 complete: Timeline tables created")
    logger.info("   - project_timelines: Master timeline per planning flow")
    logger.info("   - timeline_phases: Migration phases with dependencies")
    logger.info("   - timeline_milestones: Key milestones and deliverables")
    logger.info("   - Multi-tenant scoping: client_account_id + engagement_id")
    logger.info("   - JSONB columns for flexible timeline data")
    logger.info("   - Critical path tracking and risk management")
    logger.info("   - Full integration with planning_flows and migration_waves")


def downgrade() -> None:
    """
    Drop timeline tables and all associated indexes/constraints.

    IDEMPOTENT: Uses IF EXISTS checks for cleanup.
    """
    logger.info("Rolling back migration 113: Dropping timeline tables...")

    # Drop triggers first
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.triggers
                WHERE event_object_schema = 'migration'
                AND event_object_table = 'project_timelines'
                AND trigger_name = 'update_timelines_updated_at'
            ) THEN
                DROP TRIGGER update_timelines_updated_at ON migration.project_timelines;
                RAISE NOTICE 'Dropped trigger: update_timelines_updated_at';
            END IF;

            IF EXISTS (
                SELECT 1 FROM information_schema.triggers
                WHERE event_object_schema = 'migration'
                AND event_object_table = 'timeline_phases'
                AND trigger_name = 'update_phases_updated_at'
            ) THEN
                DROP TRIGGER update_phases_updated_at ON migration.timeline_phases;
                RAISE NOTICE 'Dropped trigger: update_phases_updated_at';
            END IF;

            IF EXISTS (
                SELECT 1 FROM information_schema.triggers
                WHERE event_object_schema = 'migration'
                AND event_object_table = 'timeline_milestones'
                AND trigger_name = 'update_milestones_updated_at'
            ) THEN
                DROP TRIGGER update_milestones_updated_at ON migration.timeline_milestones;
                RAISE NOTICE 'Dropped trigger: update_milestones_updated_at';
            END IF;
        END $$;
        """
    )

    # Drop tables in reverse dependency order (CASCADE will handle indexes and constraints)
    op.execute(
        """
        DO $$
        BEGIN
            -- Drop timeline_milestones first (child of phases and timelines)
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'timeline_milestones'
            ) THEN
                DROP TABLE migration.timeline_milestones CASCADE;
                RAISE NOTICE 'Dropped timeline_milestones table';
            END IF;

            -- Drop timeline_phases (child of timelines)
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'timeline_phases'
            ) THEN
                DROP TABLE migration.timeline_phases CASCADE;
                RAISE NOTICE 'Dropped timeline_phases table';
            END IF;

            -- Drop project_timelines (parent table)
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'project_timelines'
            ) THEN
                DROP TABLE migration.project_timelines CASCADE;
                RAISE NOTICE 'Dropped project_timelines table';
            END IF;
        END $$;
        """
    )

    logger.info("✅ Migration 113 rollback complete")
