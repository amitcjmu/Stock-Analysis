"""Add field_dependency_rules table for data-driven question dependency management

Revision ID: 107_add_field_dependency_rules
Revises: 106_update_existing_tables
Create Date: 2025-10-27

Per GPT5 review: Move hard-coded fallback rules in DynamicQuestionEngine to database table
for tenant-scoped, data-driven, and agent-learnable dependency configuration.
"""

from alembic import op


# revision identifiers, used by Alembic
revision = "107_add_field_dependency_rules"
down_revision = "106_update_existing_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create field_dependency_rules table for storing field-to-question dependencies.
    Enables data-driven configuration instead of hard-coded rules.
    """
    op.execute(
        """
        DO $$
        BEGIN
            -- Create field_dependency_rules table if not exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'field_dependency_rules'
            ) THEN
                CREATE TABLE migration.field_dependency_rules (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    client_account_id UUID NOT NULL,
                    engagement_id UUID,  -- NULL = client-level, non-NULL = engagement-level

                    -- Source field that triggers dependency
                    source_field VARCHAR(100) NOT NULL,

                    -- Affected questions (JSONB array)
                    affected_questions JSONB NOT NULL DEFAULT '[]'::jsonb,

                    -- Rule metadata
                    rule_type VARCHAR(50) NOT NULL DEFAULT 'fallback',
                    confidence_score FLOAT DEFAULT 0.8,
                    learned_by VARCHAR(50) DEFAULT 'manual',  -- 'manual', 'agent', 'analytics'

                    -- Audit fields
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    created_by VARCHAR(255),
                    is_active BOOLEAN DEFAULT true,

                    -- Unique constraint: one rule per field per tenant/engagement
                    UNIQUE(client_account_id, engagement_id, source_field)
                );

                -- Indexes for efficient lookups
                CREATE INDEX idx_field_dep_rules_client_engagement
                ON migration.field_dependency_rules(client_account_id, engagement_id);
                CREATE INDEX idx_field_dep_rules_source_field
                ON migration.field_dependency_rules(source_field);
                CREATE INDEX idx_field_dep_rules_active
                ON migration.field_dependency_rules(is_active) WHERE is_active = true;

                RAISE NOTICE 'Created migration.field_dependency_rules table';
            ELSE
                RAISE NOTICE 'Table migration.field_dependency_rules already exists, skipping';
            END IF;

            -- Seed with default rules from DynamicQuestionEngine (bootstrap)
            -- These serve as global fallbacks when no tenant-specific rules exist
            INSERT INTO migration.field_dependency_rules
                (client_account_id, engagement_id, source_field,
                 affected_questions, rule_type, confidence_score,
                 learned_by, created_by)
            VALUES
                -- Global defaults (UUID all zeros for global scope)
                ('00000000-0000-0000-0000-000000000000'::uuid, NULL, 'os_version',
                 '["tech_stack", "supported_versions", "patch_status"]'::jsonb,
                 'fallback', 0.8, 'bootstrap', 'migration_107'),

                ('00000000-0000-0000-0000-000000000000'::uuid, NULL, 'ip_address',
                 '["network_zone", "firewall_rules", "dns_records"]'::jsonb,
                 'fallback', 0.8, 'bootstrap', 'migration_107'),

                ('00000000-0000-0000-0000-000000000000'::uuid, NULL, 'decommission_status',
                 '["migration_priority", "dependency_count", "cutover_date"]'::jsonb,
                 'fallback', 0.8, 'bootstrap', 'migration_107'),

                ('00000000-0000-0000-0000-000000000000'::uuid, NULL, 'hosting_platform',
                 '["cloud_region", "instance_type", "auto_scaling"]'::jsonb,
                 'fallback', 0.8, 'bootstrap', 'migration_107'),

                ('00000000-0000-0000-0000-000000000000'::uuid, NULL, 'database_type',
                 '["db_version", "connection_string", "replication_mode"]'::jsonb,
                 'fallback', 0.8, 'bootstrap', 'migration_107')
            ON CONFLICT (client_account_id, engagement_id, source_field) DO NOTHING;

            RAISE NOTICE 'Seeded 5 default field dependency rules';

        END $$;
        """
    )


def downgrade() -> None:
    """Drop field_dependency_rules table."""
    op.execute(
        """
        DO $$
        BEGIN
            DROP TABLE IF EXISTS migration.field_dependency_rules CASCADE;
            RAISE NOTICE 'Dropped migration.field_dependency_rules table';
        END $$;
        """
    )
