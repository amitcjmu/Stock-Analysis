"""Add missing asset enrichment tables (tech_debt, performance_metrics, cost_optimization)

Revision ID: 133_add_missing_enrichment_tables
Revises: 132_add_gap_value_prediction_fields
Create Date: 2025-11-16

Implements missing enrichment tables from Issue #980 - Intelligent Multi-Layer Gap Detection System
This migration creates the three enrichment tables that were designed but never implemented:
1. asset_tech_debt - Technical debt tracking
2. asset_performance_metrics - Resource utilization metrics
3. asset_cost_optimization - Cost and optimization opportunities

CC Generated
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "133_add_missing_enrichment_tables"
down_revision = "132_gap_value_prediction"
branch_labels = None
depends_on = None


def upgrade():
    """Create missing enrichment tables."""

    # 1. Create asset_tech_debt table
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'migration' AND table_name = 'asset_tech_debt'
            ) THEN
                CREATE TABLE migration.asset_tech_debt (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    asset_id UUID NOT NULL UNIQUE REFERENCES migration.assets(id) ON DELETE CASCADE,
                    tech_debt_score FLOAT,
                    modernization_priority VARCHAR(20),
                    code_quality_score FLOAT,
                    debt_items JSONB NOT NULL DEFAULT '[]'::jsonb,
                    last_assessment_date VARCHAR(50),
                    assessment_method VARCHAR(100),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );

                CREATE INDEX idx_asset_tech_debt_asset_id ON migration.asset_tech_debt(asset_id);

                COMMENT ON TABLE migration.asset_tech_debt IS
                    'Technical debt tracking for assets - modernization priority and debt items';
                COMMENT ON COLUMN migration.asset_tech_debt.tech_debt_score IS
                    'Technical debt score (0-100, higher = more debt)';
                COMMENT ON COLUMN migration.asset_tech_debt.modernization_priority IS
                    'Modernization priority: low, medium, high, critical';
                COMMENT ON COLUMN migration.asset_tech_debt.code_quality_score IS
                    'Code quality score (0-100, higher = better)';
                COMMENT ON COLUMN migration.asset_tech_debt.debt_items IS
                    'List of technical debt items with descriptions';
            END IF;
        END $$;
        """
    )

    # 2. Create asset_performance_metrics table
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'migration' AND table_name = 'asset_performance_metrics'
            ) THEN
                CREATE TABLE migration.asset_performance_metrics (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    asset_id UUID NOT NULL UNIQUE REFERENCES migration.assets(id) ON DELETE CASCADE,
                    cpu_utilization_avg FLOAT,
                    cpu_utilization_peak FLOAT,
                    memory_utilization_avg FLOAT,
                    memory_utilization_peak FLOAT,
                    disk_iops_avg INTEGER,
                    disk_throughput_mbps FLOAT,
                    network_throughput_mbps FLOAT,
                    network_latency_ms FLOAT,
                    monitoring_period_days INTEGER,
                    metrics_source VARCHAR(100),
                    additional_metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );

                CREATE INDEX idx_asset_performance_metrics_asset_id
                    ON migration.asset_performance_metrics(asset_id);

                COMMENT ON TABLE migration.asset_performance_metrics IS
                    'Resource utilization and performance metrics for assets';
                COMMENT ON COLUMN migration.asset_performance_metrics.cpu_utilization_avg IS
                    'Average CPU utilization percentage (0-100)';
                COMMENT ON COLUMN migration.asset_performance_metrics.memory_utilization_avg IS
                    'Average memory utilization percentage (0-100)';
            END IF;
        END $$;
        """
    )

    # 3. Create asset_cost_optimization table
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'migration' AND table_name = 'asset_cost_optimization'
            ) THEN
                CREATE TABLE migration.asset_cost_optimization (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    asset_id UUID NOT NULL UNIQUE REFERENCES migration.assets(id) ON DELETE CASCADE,
                    monthly_cost_usd FLOAT,
                    annual_cost_usd FLOAT,
                    projected_monthly_cost_usd FLOAT,
                    projected_annual_cost_usd FLOAT,
                    optimization_potential_pct FLOAT,
                    optimization_opportunities JSONB NOT NULL DEFAULT '[]'::jsonb,
                    cost_breakdown JSONB NOT NULL DEFAULT '{}'::jsonb,
                    cost_calculation_date VARCHAR(50),
                    cost_source VARCHAR(100),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );

                CREATE INDEX idx_asset_cost_optimization_asset_id
                    ON migration.asset_cost_optimization(asset_id);

                COMMENT ON TABLE migration.asset_cost_optimization IS
                    'Cost tracking and optimization opportunities for assets';
                COMMENT ON COLUMN migration.asset_cost_optimization.monthly_cost_usd IS
                    'Current monthly cost in USD';
                COMMENT ON COLUMN migration.asset_cost_optimization.optimization_potential_pct IS
                    'Potential cost savings percentage (0-100)';
            END IF;
        END $$;
        """
    )


def downgrade():
    """Drop enrichment tables."""
    op.execute("DROP TABLE IF EXISTS migration.asset_tech_debt CASCADE;")
    op.execute("DROP TABLE IF EXISTS migration.asset_performance_metrics CASCADE;")
    op.execute("DROP TABLE IF EXISTS migration.asset_cost_optimization CASCADE;")
