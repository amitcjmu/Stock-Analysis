"""create_decommission_tables

Create comprehensive decommission flow schema with two-table MFO pattern.
6 tables: decommission_flows (child), decommission_plans, data_retention_policies,
archive_jobs, decommission_execution_logs, decommission_validation_checks.

CRITICAL: Phase column names match FlowTypeConfig per ADR-027:
- decommission_planning_status (NOT planning_status)
- data_migration_status (NOT data_retention_status)
- system_shutdown_status (NOT execution_status)

Revision ID: 120_create_decommission_tables
Revises: 119_add_storage_used_and_tech_debt_fields
Create Date: 2025-11-05 00:00:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "120_create_decommission_tables"
down_revision = "119_add_storage_used_and_tech_debt_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create decommission flow tables with MFO two-table pattern.

    IDEMPOTENT: Uses IF NOT EXISTS checks for all table creations.
    """

    # Table 1: decommission_flows (child flow - ADR-006 two-table pattern)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'decommission_flows'
            ) THEN
                CREATE TABLE migration.decommission_flows (
                    -- Identity
                    flow_id UUID PRIMARY KEY,
                    master_flow_id UUID NOT NULL REFERENCES migration.crewai_flow_state_extensions(flow_id),

                    -- Multi-tenant scoping
                    client_account_id UUID NOT NULL,
                    engagement_id UUID NOT NULL,

                    -- Flow metadata
                    flow_name VARCHAR(255),
                    created_by VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

                    -- Operational status (child flow - operational decisions per ADR-012)
                    status VARCHAR(50) NOT NULL DEFAULT 'initialized',
                    current_phase VARCHAR(50) NOT NULL DEFAULT 'decommission_planning',

                    -- Selected systems for decommission
                    selected_system_ids UUID[] NOT NULL,
                    system_count INTEGER NOT NULL,

                    -- Phase progress tracking (ALIGNED WITH FLOWTYPECONFIG - ADR-027)
                    decommission_planning_status VARCHAR(50) DEFAULT 'pending',
                    decommission_planning_completed_at TIMESTAMP WITH TIME ZONE,

                    data_migration_status VARCHAR(50) DEFAULT 'pending',
                    data_migration_completed_at TIMESTAMP WITH TIME ZONE,

                    system_shutdown_status VARCHAR(50) DEFAULT 'pending',
                    system_shutdown_started_at TIMESTAMP WITH TIME ZONE,
                    system_shutdown_completed_at TIMESTAMP WITH TIME ZONE,

                    -- Configuration and runtime state
                    decommission_strategy JSONB NOT NULL DEFAULT '{}'::jsonb,
                    runtime_state JSONB NOT NULL DEFAULT '{}'::jsonb,

                    -- Aggregated metrics
                    total_systems_decommissioned INTEGER DEFAULT 0,
                    estimated_annual_savings DECIMAL(15, 2),
                    actual_annual_savings DECIMAL(15, 2),
                    compliance_score DECIMAL(5, 2),

                    -- Constraints
                    CONSTRAINT fk_decom_client_account FOREIGN KEY (client_account_id)
                        REFERENCES migration.client_accounts(id),
                    CONSTRAINT fk_decom_engagement FOREIGN KEY (engagement_id)
                        REFERENCES migration.engagements(id),
                    CONSTRAINT valid_decom_status CHECK (status IN (
                        'initialized', 'decommission_planning', 'data_migration',
                        'system_shutdown', 'completed', 'failed'
                    )),
                    CONSTRAINT valid_decom_phase CHECK (current_phase IN (
                        'decommission_planning', 'data_migration', 'system_shutdown', 'completed'
                    ))
                );

                -- Indexes for performance
                CREATE INDEX idx_decom_flows_tenant ON migration.decommission_flows(client_account_id, engagement_id);
                CREATE INDEX idx_decom_flows_status ON migration.decommission_flows(status);
                CREATE INDEX idx_decom_flows_master ON migration.decommission_flows(master_flow_id);
                CREATE INDEX idx_decom_flows_created ON migration.decommission_flows(created_at DESC);
            END IF;
        END $$;
        """
    )

    # Table 2: decommission_plans (per-system decommission plans)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'decommission_plans'
            ) THEN
                CREATE TABLE migration.decommission_plans (
                    plan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    flow_id UUID NOT NULL REFERENCES migration.decommission_flows(flow_id),
                    client_account_id UUID NOT NULL,
                    engagement_id UUID NOT NULL,

                    system_id UUID NOT NULL REFERENCES migration.assets(id),
                    system_name VARCHAR(255) NOT NULL,
                    system_type VARCHAR(100),

                    -- Dependencies
                    dependencies JSONB NOT NULL DEFAULT '[]'::jsonb,

                    -- Risk assessment
                    risk_level VARCHAR(50) NOT NULL,
                    risk_factors JSONB NOT NULL DEFAULT '[]'::jsonb,
                    mitigation_strategies JSONB NOT NULL DEFAULT '[]'::jsonb,

                    -- Scheduling
                    scheduled_date TIMESTAMP WITH TIME ZONE,
                    estimated_duration_hours INTEGER,
                    priority VARCHAR(50),

                    -- Approvals
                    requires_approvals JSONB NOT NULL DEFAULT '[]'::jsonb,
                    approval_status VARCHAR(50) DEFAULT 'pending',
                    approved_by VARCHAR(255),
                    approved_at TIMESTAMP WITH TIME ZONE,

                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

                    CONSTRAINT fk_decom_plan_flow FOREIGN KEY (flow_id)
                        REFERENCES migration.decommission_flows(flow_id) ON DELETE CASCADE
                );

                CREATE INDEX idx_decom_plans_flow ON migration.decommission_plans(flow_id);
                CREATE INDEX idx_decom_plans_system ON migration.decommission_plans(system_id);
            END IF;
        END $$;
        """
    )

    # Table 3: data_retention_policies (compliance-driven retention policies)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'data_retention_policies'
            ) THEN
                CREATE TABLE migration.data_retention_policies (
                    policy_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    client_account_id UUID NOT NULL,
                    engagement_id UUID NOT NULL,

                    policy_name VARCHAR(255) NOT NULL,
                    description TEXT,

                    -- Retention requirements
                    retention_period_days INTEGER NOT NULL,
                    compliance_requirements VARCHAR[] NOT NULL,

                    -- Data classification
                    data_types VARCHAR[] NOT NULL,
                    storage_location VARCHAR(255) NOT NULL,
                    encryption_required BOOLEAN DEFAULT true,

                    -- Status
                    status VARCHAR(50) DEFAULT 'active',

                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

                    CONSTRAINT fk_retention_client FOREIGN KEY (client_account_id)
                        REFERENCES migration.client_accounts(id)
                );

                CREATE INDEX idx_retention_policies_tenant
                    ON migration.data_retention_policies(client_account_id, engagement_id);
            END IF;
        END $$;
        """
    )

    # Table 4: archive_jobs (data archival tracking)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'archive_jobs'
            ) THEN
                CREATE TABLE migration.archive_jobs (
                    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    flow_id UUID NOT NULL REFERENCES migration.decommission_flows(flow_id),
                    policy_id UUID NOT NULL REFERENCES migration.data_retention_policies(policy_id),

                    client_account_id UUID NOT NULL,
                    engagement_id UUID NOT NULL,

                    system_id UUID NOT NULL REFERENCES migration.assets(id),
                    system_name VARCHAR(255) NOT NULL,

                    -- Job details
                    data_size_gb DECIMAL(15, 2),
                    archive_location VARCHAR(500),

                    status VARCHAR(50) NOT NULL DEFAULT 'queued',
                    progress_percentage INTEGER DEFAULT 0,

                    -- Timing
                    scheduled_start TIMESTAMP WITH TIME ZONE,
                    actual_start TIMESTAMP WITH TIME ZONE,
                    estimated_completion TIMESTAMP WITH TIME ZONE,
                    actual_completion TIMESTAMP WITH TIME ZONE,

                    -- Verification
                    integrity_verified BOOLEAN DEFAULT false,
                    verification_checksum VARCHAR(255),

                    error_message TEXT,

                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

                    CONSTRAINT fk_archive_job_flow FOREIGN KEY (flow_id)
                        REFERENCES migration.decommission_flows(flow_id) ON DELETE CASCADE,
                    CONSTRAINT valid_archive_status CHECK (status IN (
                        'queued', 'in_progress', 'completed', 'failed', 'cancelled'
                    ))
                );

                CREATE INDEX idx_archive_jobs_flow ON migration.archive_jobs(flow_id);
                CREATE INDEX idx_archive_jobs_status ON migration.archive_jobs(status);
                CREATE INDEX idx_archive_jobs_system ON migration.archive_jobs(system_id);
            END IF;
        END $$;
        """
    )

    # Table 5: decommission_execution_logs (audit trail)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'decommission_execution_logs'
            ) THEN
                CREATE TABLE migration.decommission_execution_logs (
                    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    flow_id UUID NOT NULL REFERENCES migration.decommission_flows(flow_id),
                    plan_id UUID NOT NULL REFERENCES migration.decommission_plans(plan_id),

                    client_account_id UUID NOT NULL,
                    engagement_id UUID NOT NULL,

                    system_id UUID NOT NULL REFERENCES migration.assets(id),

                    -- Execution details
                    execution_phase VARCHAR(100) NOT NULL,
                    status VARCHAR(50) NOT NULL,

                    started_at TIMESTAMP WITH TIME ZONE,
                    completed_at TIMESTAMP WITH TIME ZONE,

                    executed_by VARCHAR(255),

                    -- Safety checks
                    safety_checks_passed JSONB NOT NULL DEFAULT '[]'::jsonb,
                    safety_checks_failed JSONB NOT NULL DEFAULT '[]'::jsonb,
                    rollback_available BOOLEAN DEFAULT true,

                    -- Logging
                    execution_log JSONB NOT NULL DEFAULT '[]'::jsonb,
                    error_details TEXT,

                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

                    CONSTRAINT fk_execution_flow FOREIGN KEY (flow_id)
                        REFERENCES migration.decommission_flows(flow_id) ON DELETE CASCADE
                );

                CREATE INDEX idx_execution_logs_flow ON migration.decommission_execution_logs(flow_id);
                CREATE INDEX idx_execution_logs_plan ON migration.decommission_execution_logs(plan_id);
                CREATE INDEX idx_execution_logs_status ON migration.decommission_execution_logs(status);
            END IF;
        END $$;
        """
    )

    # Table 6: decommission_validation_checks (post-decommission validation)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'decommission_validation_checks'
            ) THEN
                CREATE TABLE migration.decommission_validation_checks (
                    check_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    flow_id UUID NOT NULL REFERENCES migration.decommission_flows(flow_id),
                    system_id UUID NOT NULL REFERENCES migration.assets(id),

                    client_account_id UUID NOT NULL,
                    engagement_id UUID NOT NULL,

                    -- Check details
                    validation_category VARCHAR(100) NOT NULL,
                    check_name VARCHAR(255) NOT NULL,
                    check_description TEXT,
                    is_critical BOOLEAN DEFAULT false,

                    -- Results
                    status VARCHAR(50) NOT NULL DEFAULT 'pending',
                    result_details JSONB,
                    issues_found INTEGER DEFAULT 0,

                    validated_by VARCHAR(255),
                    validated_at TIMESTAMP WITH TIME ZONE,

                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

                    CONSTRAINT fk_validation_flow FOREIGN KEY (flow_id)
                        REFERENCES migration.decommission_flows(flow_id) ON DELETE CASCADE,
                    CONSTRAINT valid_validation_status CHECK (status IN (
                        'pending', 'passed', 'warning', 'failed'
                    ))
                );

                CREATE INDEX idx_validation_checks_flow ON migration.decommission_validation_checks(flow_id);
                CREATE INDEX idx_validation_checks_system ON migration.decommission_validation_checks(system_id);
                CREATE INDEX idx_validation_checks_status ON migration.decommission_validation_checks(status);
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """
    Remove decommission flow tables in reverse dependency order.

    IDEMPOTENT: Uses IF EXISTS checks for all table drops.
    """

    # Drop tables in reverse order (dependent tables first)
    op.execute(
        """
        DO $$
        BEGIN
            -- Drop validation checks
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'decommission_validation_checks'
            ) THEN
                DROP TABLE migration.decommission_validation_checks CASCADE;
            END IF;

            -- Drop execution logs
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'decommission_execution_logs'
            ) THEN
                DROP TABLE migration.decommission_execution_logs CASCADE;
            END IF;

            -- Drop archive jobs
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'archive_jobs'
            ) THEN
                DROP TABLE migration.archive_jobs CASCADE;
            END IF;

            -- Drop data retention policies
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'data_retention_policies'
            ) THEN
                DROP TABLE migration.data_retention_policies CASCADE;
            END IF;

            -- Drop decommission plans
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'decommission_plans'
            ) THEN
                DROP TABLE migration.decommission_plans CASCADE;
            END IF;

            -- Drop decommission flows (child flow table)
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'decommission_flows'
            ) THEN
                DROP TABLE migration.decommission_flows CASCADE;
            END IF;
        END $$;
        """
    )
