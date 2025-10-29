"""create_resource_planning_tables

Create resource planning tables for wave resource allocation and skill tracking.
This migration establishes the database schema for managing resource pools,
resource allocations to waves, and skill gap analysis.

Handles:
- Resource pools with role-based capacity and cost tracking
- Resource allocations to migration waves with AI suggestions
- Skill requirements and gap analysis per wave
- Multi-tenant scoping and audit trails
- Performance indexes for efficient queries

Related to #690 (Resource Management - ANSWERED):
- Role-based resources (not individual contributors)
- Hourly rate cost tracking per role
- Skill gap warnings (non-blocking)
- AI suggestions with manual override capability

Revision ID: 114_create_resource_planning_tables
Revises: 113_create_timeline_tables
Create Date: 2025-10-29 00:00:00.000000

Related Issues: #704 (Resource Planning Database Schema)
"""

from alembic import op
import logging

# revision identifiers, used by Alembic.
revision = "114_create_resource_planning_tables"
down_revision = "113_create_timeline_tables"
branch_labels = None
depends_on = None

logger = logging.getLogger("alembic")


def upgrade() -> None:
    """
    Create resource planning tables with full schema.

    IDEMPOTENT: Uses IF NOT EXISTS checks for all operations.
    """
    logger.info("Starting migration 114: Create resource planning tables")

    # Step 1: Create resource_pools table
    logger.info("Step 1: Creating resource_pools table...")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'resource_pools'
            ) THEN
                CREATE TABLE migration.resource_pools (
                    -- Primary Key
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

                    -- Multi-Tenant Scoping (MANDATORY)
                    client_account_id INTEGER NOT NULL,
                    engagement_id INTEGER NOT NULL,

                    -- Resource Pool Identity
                    pool_name VARCHAR(255) NOT NULL,
                    description TEXT,

                    -- Resource Type (from #690: role-based resources)
                    resource_type VARCHAR(50) CHECK (resource_type IN ('individual', 'role', 'team')) DEFAULT 'role',
                    role_name VARCHAR(255) NOT NULL,

                    -- Capacity Tracking
                    total_capacity_hours NUMERIC(10,2) NOT NULL,
                    available_capacity_hours NUMERIC(10,2) NOT NULL,
                    allocated_capacity_hours NUMERIC(10,2) DEFAULT 0.00,

                    -- Cost Tracking (from #690: hourly rates)
                    hourly_rate NUMERIC(10,2),
                    currency VARCHAR(3) DEFAULT 'USD',

                    -- Skills (JSONB array for flexible skill tracking)
                    skills JSONB DEFAULT '[]'::jsonb,

                    -- Location & Availability
                    location VARCHAR(255),
                    timezone VARCHAR(50),
                    availability_start_date TIMESTAMP WITH TIME ZONE,
                    availability_end_date TIMESTAMP WITH TIME ZONE,

                    -- Resource Pool Metadata
                    is_active BOOLEAN DEFAULT true,
                    utilization_percentage NUMERIC(5,2) DEFAULT 0.00 CHECK (utilization_percentage >= 0 AND utilization_percentage <= 100),

                    -- Audit Fields
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    created_by UUID,
                    updated_by UUID
                );

                RAISE NOTICE 'Created resource_pools table';
            ELSE
                RAISE NOTICE 'resource_pools table already exists, skipping creation';
            END IF;
        END $$;
        """
    )

    # Step 2: Create resource_allocations table
    logger.info("Step 2: Creating resource_allocations table...")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'resource_allocations'
            ) THEN
                CREATE TABLE migration.resource_allocations (
                    -- Primary Key
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

                    -- Multi-Tenant Scoping (MANDATORY)
                    client_account_id INTEGER NOT NULL,
                    engagement_id INTEGER NOT NULL,

                    -- Planning Flow Reference
                    planning_flow_id UUID NOT NULL,

                    -- Wave Reference (FK to migration_waves)
                    wave_id UUID NOT NULL,

                    -- Resource Pool Reference
                    resource_pool_id UUID NOT NULL,

                    -- Allocation Details
                    allocated_hours NUMERIC(10,2) NOT NULL,
                    allocation_percentage NUMERIC(5,2) CHECK (allocation_percentage >= 0 AND allocation_percentage <= 100),

                    -- Dates
                    allocation_start_date TIMESTAMP WITH TIME ZONE NOT NULL,
                    allocation_end_date TIMESTAMP WITH TIME ZONE NOT NULL,

                    -- Cost Calculation
                    estimated_cost NUMERIC(15,2),
                    actual_cost NUMERIC(15,2),

                    -- AI-Generated Allocation (from #690: AI suggestions with manual override)
                    is_ai_suggested BOOLEAN DEFAULT false,
                    ai_confidence_score NUMERIC(5,2) CHECK (ai_confidence_score >= 0 AND ai_confidence_score <= 100),
                    manual_override BOOLEAN DEFAULT false,
                    override_reason TEXT,

                    -- Status
                    status VARCHAR(20) CHECK (status IN ('planned', 'confirmed', 'in_progress', 'completed', 'cancelled')) DEFAULT 'planned',

                    -- Audit Fields
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    created_by UUID,
                    updated_by UUID
                );

                RAISE NOTICE 'Created resource_allocations table';
            ELSE
                RAISE NOTICE 'resource_allocations table already exists, skipping creation';
            END IF;
        END $$;
        """
    )

    # Step 3: Create resource_skills table
    logger.info("Step 3: Creating resource_skills table...")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'resource_skills'
            ) THEN
                CREATE TABLE migration.resource_skills (
                    -- Primary Key
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

                    -- Multi-Tenant Scoping (MANDATORY)
                    client_account_id INTEGER NOT NULL,
                    engagement_id INTEGER NOT NULL,

                    -- Wave Reference (FK to migration_waves)
                    wave_id UUID NOT NULL,

                    -- Skill Requirement
                    skill_name VARCHAR(255) NOT NULL,
                    skill_category VARCHAR(100),
                    proficiency_level VARCHAR(20) CHECK (proficiency_level IN ('beginner', 'intermediate', 'advanced', 'expert')),

                    -- Requirement Details
                    required_hours NUMERIC(10,2) NOT NULL,
                    available_hours NUMERIC(10,2) DEFAULT 0.00,

                    -- Gap Analysis (from #690: skill gap warnings)
                    has_gap BOOLEAN DEFAULT false,
                    gap_severity VARCHAR(20) CHECK (gap_severity IN ('none', 'low', 'medium', 'high', 'critical')) DEFAULT 'none',
                    gap_description TEXT,

                    -- Mitigation Plan
                    mitigation_plan TEXT,
                    training_required BOOLEAN DEFAULT false,
                    external_hire_needed BOOLEAN DEFAULT false,

                    -- Audit Fields
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                );

                RAISE NOTICE 'Created resource_skills table';
            ELSE
                RAISE NOTICE 'resource_skills table already exists, skipping creation';
            END IF;
        END $$;
        """
    )

    # Step 4: Create indexes for resource_pools
    logger.info("Step 4: Creating indexes for resource_pools...")
    op.execute(
        """
        DO $$
        BEGIN
            -- Composite index for multi-tenant queries
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'resource_pools'
                AND indexname = 'idx_pools_client_engagement'
            ) THEN
                CREATE INDEX idx_pools_client_engagement
                ON migration.resource_pools(client_account_id, engagement_id);
                RAISE NOTICE 'Created index: idx_pools_client_engagement';
            END IF;

            -- Index for role name lookups
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'resource_pools'
                AND indexname = 'idx_pools_role'
            ) THEN
                CREATE INDEX idx_pools_role
                ON migration.resource_pools(role_name);
                RAISE NOTICE 'Created index: idx_pools_role';
            END IF;

            -- Partial index for active pools
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'resource_pools'
                AND indexname = 'idx_pools_active'
            ) THEN
                CREATE INDEX idx_pools_active
                ON migration.resource_pools(is_active) WHERE is_active = true;
                RAISE NOTICE 'Created index: idx_pools_active';
            END IF;

            -- Index for utilization queries
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'resource_pools'
                AND indexname = 'idx_pools_utilization'
            ) THEN
                CREATE INDEX idx_pools_utilization
                ON migration.resource_pools(utilization_percentage);
                RAISE NOTICE 'Created index: idx_pools_utilization';
            END IF;

            -- GIN index for skills JSONB column (fast skill searching)
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'resource_pools'
                AND indexname = 'idx_pools_skills'
            ) THEN
                CREATE INDEX idx_pools_skills
                ON migration.resource_pools USING gin(skills);
                RAISE NOTICE 'Created GIN index: idx_pools_skills';
            END IF;
        END $$;
        """
    )

    # Step 5: Create indexes for resource_allocations
    logger.info("Step 5: Creating indexes for resource_allocations...")
    op.execute(
        """
        DO $$
        BEGIN
            -- Composite index for multi-tenant queries
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'resource_allocations'
                AND indexname = 'idx_allocations_client_engagement'
            ) THEN
                CREATE INDEX idx_allocations_client_engagement
                ON migration.resource_allocations(client_account_id, engagement_id);
                RAISE NOTICE 'Created index: idx_allocations_client_engagement';
            END IF;

            -- Index for planning flow lookups
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'resource_allocations'
                AND indexname = 'idx_allocations_planning_flow'
            ) THEN
                CREATE INDEX idx_allocations_planning_flow
                ON migration.resource_allocations(planning_flow_id);
                RAISE NOTICE 'Created index: idx_allocations_planning_flow';
            END IF;

            -- Index for wave lookups
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'resource_allocations'
                AND indexname = 'idx_allocations_wave'
            ) THEN
                CREATE INDEX idx_allocations_wave
                ON migration.resource_allocations(wave_id);
                RAISE NOTICE 'Created index: idx_allocations_wave';
            END IF;

            -- Index for resource pool lookups
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'resource_allocations'
                AND indexname = 'idx_allocations_pool'
            ) THEN
                CREATE INDEX idx_allocations_pool
                ON migration.resource_allocations(resource_pool_id);
                RAISE NOTICE 'Created index: idx_allocations_pool';
            END IF;

            -- Index for status queries
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'resource_allocations'
                AND indexname = 'idx_allocations_status'
            ) THEN
                CREATE INDEX idx_allocations_status
                ON migration.resource_allocations(status);
                RAISE NOTICE 'Created index: idx_allocations_status';
            END IF;

            -- Partial index for AI-suggested allocations
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'resource_allocations'
                AND indexname = 'idx_allocations_ai_suggested'
            ) THEN
                CREATE INDEX idx_allocations_ai_suggested
                ON migration.resource_allocations(is_ai_suggested) WHERE is_ai_suggested = true;
                RAISE NOTICE 'Created index: idx_allocations_ai_suggested';
            END IF;

            -- Composite index for date range queries
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'resource_allocations'
                AND indexname = 'idx_allocations_dates'
            ) THEN
                CREATE INDEX idx_allocations_dates
                ON migration.resource_allocations(allocation_start_date, allocation_end_date);
                RAISE NOTICE 'Created index: idx_allocations_dates';
            END IF;
        END $$;
        """
    )

    # Step 6: Create indexes for resource_skills
    logger.info("Step 6: Creating indexes for resource_skills...")
    op.execute(
        """
        DO $$
        BEGIN
            -- Composite index for multi-tenant queries
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'resource_skills'
                AND indexname = 'idx_skills_client_engagement'
            ) THEN
                CREATE INDEX idx_skills_client_engagement
                ON migration.resource_skills(client_account_id, engagement_id);
                RAISE NOTICE 'Created index: idx_skills_client_engagement';
            END IF;

            -- Index for wave lookups
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'resource_skills'
                AND indexname = 'idx_skills_wave'
            ) THEN
                CREATE INDEX idx_skills_wave
                ON migration.resource_skills(wave_id);
                RAISE NOTICE 'Created index: idx_skills_wave';
            END IF;

            -- Index for skill name lookups
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'resource_skills'
                AND indexname = 'idx_skills_name'
            ) THEN
                CREATE INDEX idx_skills_name
                ON migration.resource_skills(skill_name);
                RAISE NOTICE 'Created index: idx_skills_name';
            END IF;

            -- Partial index for gaps
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'resource_skills'
                AND indexname = 'idx_skills_gap'
            ) THEN
                CREATE INDEX idx_skills_gap
                ON migration.resource_skills(has_gap) WHERE has_gap = true;
                RAISE NOTICE 'Created index: idx_skills_gap';
            END IF;

            -- Index for gap severity queries
            IF NOT EXISTS (
                SELECT 1
                FROM pg_indexes
                WHERE schemaname = 'migration'
                AND tablename = 'resource_skills'
                AND indexname = 'idx_skills_severity'
            ) THEN
                CREATE INDEX idx_skills_severity
                ON migration.resource_skills(gap_severity);
                RAISE NOTICE 'Created index: idx_skills_severity';
            END IF;
        END $$;
        """
    )

    # Step 7: Create foreign key constraints
    logger.info("Step 7: Adding foreign key constraints...")
    op.execute(
        """
        DO $$
        BEGIN
            -- FK: resource_allocations → planning_flows
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.table_constraints
                WHERE constraint_schema = 'migration'
                AND table_name = 'resource_allocations'
                AND constraint_name = 'fk_allocations_planning_flow'
            ) THEN
                ALTER TABLE migration.resource_allocations
                ADD CONSTRAINT fk_allocations_planning_flow
                FOREIGN KEY (planning_flow_id)
                REFERENCES migration.planning_flows(planning_flow_id)
                ON DELETE CASCADE;
                RAISE NOTICE 'Created FK constraint: fk_allocations_planning_flow';
            END IF;

            -- FK: resource_allocations → migration_waves
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.table_constraints
                WHERE constraint_schema = 'migration'
                AND table_name = 'resource_allocations'
                AND constraint_name = 'fk_allocations_wave'
            ) THEN
                ALTER TABLE migration.resource_allocations
                ADD CONSTRAINT fk_allocations_wave
                FOREIGN KEY (wave_id)
                REFERENCES migration.migration_waves(id)
                ON DELETE CASCADE;
                RAISE NOTICE 'Created FK constraint: fk_allocations_wave';
            END IF;

            -- FK: resource_allocations → resource_pools
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.table_constraints
                WHERE constraint_schema = 'migration'
                AND table_name = 'resource_allocations'
                AND constraint_name = 'fk_allocations_pool'
            ) THEN
                ALTER TABLE migration.resource_allocations
                ADD CONSTRAINT fk_allocations_pool
                FOREIGN KEY (resource_pool_id)
                REFERENCES migration.resource_pools(id)
                ON DELETE RESTRICT;
                RAISE NOTICE 'Created FK constraint: fk_allocations_pool';
            END IF;

            -- FK: resource_skills → migration_waves
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.table_constraints
                WHERE constraint_schema = 'migration'
                AND table_name = 'resource_skills'
                AND constraint_name = 'fk_skills_wave'
            ) THEN
                ALTER TABLE migration.resource_skills
                ADD CONSTRAINT fk_skills_wave
                FOREIGN KEY (wave_id)
                REFERENCES migration.migration_waves(id)
                ON DELETE CASCADE;
                RAISE NOTICE 'Created FK constraint: fk_skills_wave';
            END IF;
        END $$;
        """
    )

    # Step 8: Create updated_at triggers
    logger.info("Step 8: Creating updated_at triggers...")
    op.execute(
        """
        DO $$
        BEGIN
            -- Trigger for resource_pools
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.triggers
                WHERE event_object_schema = 'migration'
                AND event_object_table = 'resource_pools'
                AND trigger_name = 'update_pools_updated_at'
            ) THEN
                CREATE TRIGGER update_pools_updated_at
                BEFORE UPDATE ON migration.resource_pools
                FOR EACH ROW
                EXECUTE FUNCTION migration.update_updated_at_column();
                RAISE NOTICE 'Created trigger: update_pools_updated_at';
            END IF;

            -- Trigger for resource_allocations
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.triggers
                WHERE event_object_schema = 'migration'
                AND event_object_table = 'resource_allocations'
                AND trigger_name = 'update_allocations_updated_at'
            ) THEN
                CREATE TRIGGER update_allocations_updated_at
                BEFORE UPDATE ON migration.resource_allocations
                FOR EACH ROW
                EXECUTE FUNCTION migration.update_updated_at_column();
                RAISE NOTICE 'Created trigger: update_allocations_updated_at';
            END IF;

            -- Trigger for resource_skills
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.triggers
                WHERE event_object_schema = 'migration'
                AND event_object_table = 'resource_skills'
                AND trigger_name = 'update_skills_updated_at'
            ) THEN
                CREATE TRIGGER update_skills_updated_at
                BEFORE UPDATE ON migration.resource_skills
                FOR EACH ROW
                EXECUTE FUNCTION migration.update_updated_at_column();
                RAISE NOTICE 'Created trigger: update_skills_updated_at';
            END IF;
        END $$;
        """
    )

    # Step 9: Create utilization calculation trigger function and trigger
    logger.info("Step 9: Creating utilization calculation trigger...")
    op.execute(
        """
        DO $$
        BEGIN
            -- Create function to auto-calculate utilization percentage
            IF NOT EXISTS (
                SELECT 1
                FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE n.nspname = 'migration'
                AND p.proname = 'update_resource_pool_utilization'
            ) THEN
                CREATE FUNCTION migration.update_resource_pool_utilization()
                RETURNS TRIGGER AS $func$
                BEGIN
                    NEW.utilization_percentage =
                        CASE
                            WHEN NEW.total_capacity_hours > 0 THEN
                                ROUND((NEW.allocated_capacity_hours / NEW.total_capacity_hours) * 100, 2)
                            ELSE 0
                        END;
                    RETURN NEW;
                END;
                $func$ LANGUAGE plpgsql;
                RAISE NOTICE 'Created function: update_resource_pool_utilization';
            END IF;

            -- Create trigger to auto-calculate utilization
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.triggers
                WHERE event_object_schema = 'migration'
                AND event_object_table = 'resource_pools'
                AND trigger_name = 'calculate_pool_utilization'
            ) THEN
                CREATE TRIGGER calculate_pool_utilization
                BEFORE INSERT OR UPDATE ON migration.resource_pools
                FOR EACH ROW
                EXECUTE FUNCTION migration.update_resource_pool_utilization();
                RAISE NOTICE 'Created trigger: calculate_pool_utilization';
            END IF;
        END $$;
        """
    )

    logger.info("✅ Migration 114 complete: Resource planning tables created")
    logger.info("   - resource_pools: Role-based resource capacity with cost tracking")
    logger.info(
        "   - resource_allocations: Resource assignments to waves with AI suggestions"
    )
    logger.info("   - resource_skills: Skill requirements and gap analysis")
    logger.info("   - Multi-tenant scoping: client_account_id + engagement_id")
    logger.info("   - Foreign keys to planning_flows and migration_waves")
    logger.info("   - Auto-calculated utilization percentage for resource pools")
    logger.info("   - Comprehensive indexes for efficient queries")


def downgrade() -> None:
    """
    Drop resource planning tables and all associated objects.

    IDEMPOTENT: Uses IF EXISTS checks for cleanup.
    """
    logger.info("Rolling back migration 114: Dropping resource planning tables...")

    # Step 1: Drop triggers
    logger.info("Step 1: Dropping triggers...")
    op.execute(
        """
        DO $$
        BEGIN
            -- Drop utilization calculation trigger
            IF EXISTS (
                SELECT 1
                FROM information_schema.triggers
                WHERE event_object_schema = 'migration'
                AND event_object_table = 'resource_pools'
                AND trigger_name = 'calculate_pool_utilization'
            ) THEN
                DROP TRIGGER calculate_pool_utilization ON migration.resource_pools;
                RAISE NOTICE 'Dropped trigger: calculate_pool_utilization';
            END IF;

            -- Drop updated_at triggers
            IF EXISTS (
                SELECT 1
                FROM information_schema.triggers
                WHERE event_object_schema = 'migration'
                AND event_object_table = 'resource_pools'
                AND trigger_name = 'update_pools_updated_at'
            ) THEN
                DROP TRIGGER update_pools_updated_at ON migration.resource_pools;
                RAISE NOTICE 'Dropped trigger: update_pools_updated_at';
            END IF;

            IF EXISTS (
                SELECT 1
                FROM information_schema.triggers
                WHERE event_object_schema = 'migration'
                AND event_object_table = 'resource_allocations'
                AND trigger_name = 'update_allocations_updated_at'
            ) THEN
                DROP TRIGGER update_allocations_updated_at ON migration.resource_allocations;
                RAISE NOTICE 'Dropped trigger: update_allocations_updated_at';
            END IF;

            IF EXISTS (
                SELECT 1
                FROM information_schema.triggers
                WHERE event_object_schema = 'migration'
                AND event_object_table = 'resource_skills'
                AND trigger_name = 'update_skills_updated_at'
            ) THEN
                DROP TRIGGER update_skills_updated_at ON migration.resource_skills;
                RAISE NOTICE 'Dropped trigger: update_skills_updated_at';
            END IF;
        END $$;
        """
    )

    # Step 2: Drop function
    logger.info("Step 2: Dropping utilization calculation function...")
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE n.nspname = 'migration'
                AND p.proname = 'update_resource_pool_utilization'
            ) THEN
                DROP FUNCTION migration.update_resource_pool_utilization();
                RAISE NOTICE 'Dropped function: update_resource_pool_utilization';
            END IF;
        END $$;
        """
    )

    # Step 3: Drop tables (CASCADE will drop foreign keys and indexes)
    logger.info("Step 3: Dropping tables...")
    op.execute(
        """
        DO $$
        BEGIN
            -- Drop resource_skills table
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'resource_skills'
            ) THEN
                DROP TABLE migration.resource_skills CASCADE;
                RAISE NOTICE 'Dropped resource_skills table';
            END IF;

            -- Drop resource_allocations table
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'resource_allocations'
            ) THEN
                DROP TABLE migration.resource_allocations CASCADE;
                RAISE NOTICE 'Dropped resource_allocations table';
            END IF;

            -- Drop resource_pools table
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'resource_pools'
            ) THEN
                DROP TABLE migration.resource_pools CASCADE;
                RAISE NOTICE 'Dropped resource_pools table';
            END IF;
        END $$;
        """
    )

    logger.info("✅ Migration 114 rollback complete")
