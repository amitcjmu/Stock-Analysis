"""Security and Data Integrity - Composite FKs, ENUM→CHECK, Categorical Constraints

Addresses three issues:
- #983: Add composite FKs for multi-tenant hierarchy (60 tables)
- #990: Replace PostgreSQL ENUMs with CHECK constraints (3 types)
- #1251: Add CHECK constraints for categorical fields in assets (16 fields)

Also fixes migration 114 bug:
- resource_pools, resource_allocations, resource_skills had INTEGER tenant columns
- SQLAlchemy models expect UUID (code references "per migration 115")
- This migration converts INTEGER→UUID and maps existing data to test UUIDs

Revision ID: 150_security_and_data_integrity
Revises: 149_add_cmdb_assessment_fields_issue_798
Create Date: 2025-12-05
"""

from alembic import op

revision = "150_security_and_data_integrity"
down_revision = "149_add_cmdb_assessment_fields_issue_798"
branch_labels = None
depends_on = None

# Tables requiring composite FK (client_account_id, engagement_id) -> engagements
TENANT_SCOPED_TABLES = [
    "access_audit_log",
    "adaptive_questionnaires",
    "agent_discovered_patterns",
    "agent_execution_history",
    "agent_performance_daily",
    "agent_task_history",
    "application_components",
    "application_name_variants",
    "approval_requests",
    "archive_jobs",
    "assessment_flows",
    "assessments",
    "asset_conflict_resolutions",
    "asset_contacts",
    "asset_custom_attributes",
    "asset_dependencies",
    "asset_eol_assessments",
    "asset_field_conflicts",
    "assets",
    "blackout_periods",
    "cache_metadata",
    "canonical_applications",
    "collection_answer_history",
    "collection_background_tasks",
    "collection_flow_applications",
    "collection_flows",
    "collection_gap_analysis",
    "collection_question_rules",
    "crewai_flow_state_extensions",
    "data_cleansing_recommendations",
    "data_imports",
    "data_retention_policies",
    "decommission_execution_logs",
    "decommission_flows",
    "decommission_plans",
    "decommission_validation_checks",
    "discovery_flows",
    "engagement_architecture_standards",
    "enhanced_access_audit_log",
    "failure_journal",
    "feedback",
    "feedback_summaries",
    "field_dependency_rules",
    "flow_deletion_audit",
    "import_field_mappings",
    "llm_usage_logs",
    "llm_usage_summary",
    "maintenance_windows",
    "migration_exceptions",
    "migration_waves",
    "planning_flows",
    "project_timelines",
    "raw_import_records",
    "resource_allocations",  # INTEGER→UUID fixed in this migration
    "resource_pools",  # INTEGER→UUID fixed in this migration
    "resource_skills",  # INTEGER→UUID fixed in this migration
    "sixr_analyses_archive",
    "tenant_vendor_products",
    "timeline_milestones",
    "timeline_phases",
]

# Tables that need INTEGER→UUID conversion for tenant columns (migration 114 bug)
# Test UUIDs: client=11111111-1111-1111-1111-111111111111, engagement=22222222-2222-2222-2222-222222222222
INTEGER_TO_UUID_TABLES = [
    "resource_allocations",
    "resource_pools",
    "resource_skills",
]

# Categorical fields in assets table requiring CHECK constraints (#1251)
# Values include both expected values AND existing data values to preserve data
# IMPORTANT: Query `SELECT DISTINCT <field> FROM migration.assets` before adding constraints
ASSET_CATEGORICAL_FIELDS = {
    # application_type: existing data has architecture types (from CMDB import)
    "application_type": [
        "cots",
        "custom",
        "custom_cots",
        "saas",
        "other",  # expected
        "Event-Driven",
        "Layered",
        "Microservices",
        "Monolithic",  # existing
        "Serverless",
        "SOA",  # existing architecture patterns
    ],
    "lifecycle": ["retire", "replace", "retain", "invest"],
    "hosting_model": ["on_prem", "cloud", "hybrid", "colo"],
    "server_role": ["web", "db", "app", "citrix", "file", "email", "other"],
    "security_zone": ["DMZ", "Internal", "External", "Restricted"],
    "application_data_classification": [
        "Public",
        "Internal",
        "Confidential",
        "Restricted",
    ],
    "risk_level": [
        "low",
        "medium",
        "high",
        "critical",
        "Low",
        "Medium",
        "High",
        "Critical",
    ],
    "tshirt_size": ["xs", "s", "m", "l", "xl", "xxl", "XS", "S", "M", "L", "XL", "XXL"],
    "six_r_strategy": [
        "rehost",
        "replatform",
        "refactor",
        "repurchase",
        "retire",
        "retain",
        "rearchitect",
        "replace",
        "Rehost",
        "Replatform",
        "Refactor",
        "Repurchase",
        "Retire",
        "Retain",
        "Rearchitect",
        "Replace",
    ],
    "migration_complexity": ["low", "medium", "high", "Low", "Medium", "High"],
    # sixr_ready: existing data uses not_ready/ready (not Needs Analysis)
    "sixr_ready": [
        "ready",
        "not_ready",
        "Ready",
        "Needs Analysis",
        "needs_analysis",
        "Not Ready",
    ],
    # status: includes flow states (discovered, ready, not_ready) plus standard states
    "status": [
        "active",
        "decommissioned",
        "maintenance",
        "Active",
        "Decommissioned",
        "Maintenance",
        "discovered",
        "ready",
        "not_ready",  # flow states from existing data
    ],
    "migration_status": [
        "discovered",
        "assessed",
        "migrated",
        "Discovered",
        "Assessed",
        "Migrated",
    ],
    # environment: include all existing variants including empty string
    "environment": [
        "",
        "Production",
        "Staging",
        "Development",
        "QA",
        "Test",
        "production",
        "staging",
        "development",
        "qa",
        "test",
        "Production (including Disaster Recovery)",
        "Unknown",
        "Sandbox/Development",
        "Quality Assurance/User Acceptance/Performance",
        "Functional Integration/System Integration",
        "Installed",
    ],
    # criticality: include case variants
    "criticality": [
        "Low",
        "Medium",
        "High",
        "Critical",
        "low",
        "medium",
        "high",
        "critical",
    ],
    # asset_type: include case variants (from existing data)
    "asset_type": [
        "server",
        "database",
        "application",
        "component",
        "network",
        "storage",
        "security_group",
        "load_balancer",
        "virtual_machine",
        "container",
        "other",
        "Server",
        "Database",
        "Application",
        "Component",
        "Network",
        "Storage",
        "Security_Group",
        "Load_Balancer",
        "Virtual_Machine",
        "Container",
        "Other",
    ],
}


def upgrade() -> None:
    """Add composite FKs, convert ENUMs to CHECK, add categorical constraints."""

    # =========================================================================
    # PART 0: Fix INTEGER→UUID for resource tables (migration 114 bug fix)
    # =========================================================================
    # Migration 114 created these tables with INTEGER tenant columns, but the
    # SQLAlchemy models expect UUID. This fixes the type mismatch.
    # Test data maps: INTEGER 1 → UUID 11111111.../22222222...

    for table in INTEGER_TO_UUID_TABLES:
        op.execute(
            f"""
            DO $$
            BEGIN
                -- Only convert if columns are still INTEGER
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'migration'
                    AND table_name = '{table}'
                    AND column_name = 'client_account_id'
                    AND data_type = 'integer'
                ) THEN
                    -- Drop existing indexes that use these columns
                    DROP INDEX IF EXISTS migration.idx_pools_client_engagement;
                    DROP INDEX IF EXISTS migration.idx_allocations_client_engagement;
                    DROP INDEX IF EXISTS migration.idx_skills_client_engagement;

                    -- Add new UUID columns
                    ALTER TABLE migration.{table}
                    ADD COLUMN client_account_id_new UUID,
                    ADD COLUMN engagement_id_new UUID;

                    -- Map existing INTEGER values to test UUIDs
                    -- INTEGER 1 maps to test tenant UUIDs
                    UPDATE migration.{table}
                    SET client_account_id_new = '11111111-1111-1111-1111-111111111111'::uuid,
                        engagement_id_new = '22222222-2222-2222-2222-222222222222'::uuid
                    WHERE client_account_id = 1 AND engagement_id = 1;

                    -- For any other values, generate deterministic UUIDs
                    UPDATE migration.{table}
                    SET client_account_id_new = COALESCE(
                            client_account_id_new,
                            ('00000000-0000-0000-0000-' || LPAD(client_account_id::text, 12, '0'))::uuid
                        ),
                        engagement_id_new = COALESCE(
                            engagement_id_new,
                            ('00000000-0000-0000-0001-' || LPAD(engagement_id::text, 12, '0'))::uuid
                        )
                    WHERE client_account_id_new IS NULL;

                    -- Drop old columns
                    ALTER TABLE migration.{table}
                    DROP COLUMN client_account_id,
                    DROP COLUMN engagement_id;

                    -- Rename new columns
                    ALTER TABLE migration.{table}
                    RENAME COLUMN client_account_id_new TO client_account_id;
                    ALTER TABLE migration.{table}
                    RENAME COLUMN engagement_id_new TO engagement_id;

                    -- Set NOT NULL constraints
                    ALTER TABLE migration.{table}
                    ALTER COLUMN client_account_id SET NOT NULL,
                    ALTER COLUMN engagement_id SET NOT NULL;

                    -- Add indexes back
                    CREATE INDEX IF NOT EXISTS idx_{table}_client_engagement
                    ON migration.{table}(client_account_id, engagement_id);

                    RAISE NOTICE 'Converted {table} tenant columns from INTEGER to UUID';
                END IF;
            END $$;
            """
        )

    # =========================================================================
    # PART 1: Composite Foreign Keys for Multi-Tenant Hierarchy (#983)
    # =========================================================================

    # First, add unique constraint on engagements(client_account_id, id)
    # Required for composite FK to reference
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'uq_engagements_client_account_id'
            ) THEN
                ALTER TABLE migration.engagements
                ADD CONSTRAINT uq_engagements_client_account_id
                UNIQUE (client_account_id, id);
            END IF;
        END $$;
        """
    )

    # Add composite FK to each tenant-scoped table
    for table in TENANT_SCOPED_TABLES:
        constraint_name = f"fk_{table}_engagement_hierarchy"
        op.execute(
            f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = '{constraint_name}'
                ) THEN
                    ALTER TABLE migration.{table}
                    ADD CONSTRAINT {constraint_name}
                    FOREIGN KEY (client_account_id, engagement_id)
                    REFERENCES migration.engagements (client_account_id, id)
                    ON DELETE CASCADE;
                END IF;
            END $$;
            """
        )

        # Add composite index for performance (if not exists)
        index_name = f"ix_{table}_tenant_composite"
        op.execute(
            f"""
            CREATE INDEX IF NOT EXISTS {index_name}
            ON migration.{table} (client_account_id, engagement_id);
            """
        )

    # =========================================================================
    # PART 2: Convert PostgreSQL ENUMs to CHECK Constraints (#990)
    # =========================================================================
    # Uses atomic ALTER COLUMN TYPE conversion (simpler than add/migrate/drop/rename)

    # Convert assessments.assessment_type (ENUM -> VARCHAR + CHECK)
    op.execute(
        """
        DO $$
        BEGIN
            -- Check if column is still ENUM type
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assessments'
                AND column_name = 'assessment_type'
                AND udt_name = 'assessmenttype'
            ) THEN
                -- Atomically convert ENUM to VARCHAR
                ALTER TABLE migration.assessments
                ALTER COLUMN assessment_type TYPE VARCHAR(50)
                USING assessment_type::text;

                -- Add CHECK constraint
                ALTER TABLE migration.assessments
                ADD CONSTRAINT chk_assessments_assessment_type
                CHECK (assessment_type IN (
                    'TECHNICAL', 'BUSINESS', 'SECURITY', 'COMPLIANCE', 'PERFORMANCE'
                ) OR assessment_type IS NULL);
            END IF;
        END $$;
        """
    )

    # Convert assessments.status (ENUM -> VARCHAR + CHECK)
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assessments'
                AND column_name = 'status'
                AND udt_name = 'assessmentstatus'
            ) THEN
                -- Atomically convert ENUM to VARCHAR
                ALTER TABLE migration.assessments
                ALTER COLUMN status TYPE VARCHAR(50)
                USING status::text;

                -- Add CHECK constraint
                ALTER TABLE migration.assessments
                ADD CONSTRAINT chk_assessments_status
                CHECK (status IN (
                    'PENDING', 'IN_PROGRESS', 'COMPLETED', 'REVIEWED',
                    'APPROVED', 'REJECTED'
                ) OR status IS NULL);
            END IF;
        END $$;
        """
    )

    # Convert assessments.risk_level (ENUM -> VARCHAR + CHECK)
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'assessments'
                AND column_name = 'risk_level'
                AND udt_name = 'risklevel'
            ) THEN
                -- Atomically convert ENUM to VARCHAR
                ALTER TABLE migration.assessments
                ALTER COLUMN risk_level TYPE VARCHAR(20)
                USING risk_level::text;

                -- Add CHECK constraint
                ALTER TABLE migration.assessments
                ADD CONSTRAINT chk_assessments_risk_level
                CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
                       OR risk_level IS NULL);
            END IF;
        END $$;
        """
    )

    # =========================================================================
    # PART 3: Add CHECK Constraints for Categorical Fields in Assets (#1251)
    # =========================================================================

    for field, values in ASSET_CATEGORICAL_FIELDS.items():
        constraint_name = f"chk_assets_{field}"
        values_str = ", ".join(f"'{v}'" for v in values)
        op.execute(
            f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = '{constraint_name}'
                ) THEN
                    ALTER TABLE migration.assets
                    ADD CONSTRAINT {constraint_name}
                    CHECK ({field} IN ({values_str}) OR {field} IS NULL);
                END IF;
            END $$;
            """
        )


def downgrade() -> None:
    """Remove composite FKs, revert to ENUMs, remove CHECK constraints."""

    # =========================================================================
    # PART 3 ROLLBACK: Remove CHECK constraints from assets
    # =========================================================================

    for field in ASSET_CATEGORICAL_FIELDS.keys():
        constraint_name = f"chk_assets_{field}"
        op.execute(
            f"""
            ALTER TABLE migration.assets
            DROP CONSTRAINT IF EXISTS {constraint_name};
            """
        )

    # =========================================================================
    # PART 2 ROLLBACK: Revert to ENUMs (complex - just remove CHECK for now)
    # =========================================================================

    op.execute(
        """
        ALTER TABLE migration.assessments
        DROP CONSTRAINT IF EXISTS chk_assessments_assessment_type;
        """
    )
    op.execute(
        """
        ALTER TABLE migration.assessments
        DROP CONSTRAINT IF EXISTS chk_assessments_status;
        """
    )
    op.execute(
        """
        ALTER TABLE migration.assessments
        DROP CONSTRAINT IF EXISTS chk_assessments_risk_level;
        """
    )

    # =========================================================================
    # PART 1 ROLLBACK: Remove composite FKs and indexes
    # =========================================================================

    for table in TENANT_SCOPED_TABLES:
        constraint_name = f"fk_{table}_engagement_hierarchy"
        index_name = f"ix_{table}_tenant_composite"
        op.execute(
            f"""
            ALTER TABLE migration.{table}
            DROP CONSTRAINT IF EXISTS {constraint_name};
            """
        )
        op.execute(
            f"""
            DROP INDEX IF EXISTS migration.{index_name};
            """
        )

    # Remove unique constraint from engagements
    op.execute(
        """
        ALTER TABLE migration.engagements
        DROP CONSTRAINT IF EXISTS uq_engagements_client_account_id;
        """
    )

    # =========================================================================
    # PART 0 ROLLBACK: Revert UUID→INTEGER for resource tables
    # =========================================================================
    # Note: This restores the original INTEGER type but loses UUID precision.
    # Only use if you need to fully roll back to pre-migration state.

    for table in INTEGER_TO_UUID_TABLES:
        op.execute(
            f"""
            DO $$
            BEGIN
                -- Only revert if columns are UUID (meaning upgrade ran)
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'migration'
                    AND table_name = '{table}'
                    AND column_name = 'client_account_id'
                    AND data_type = 'uuid'
                ) THEN
                    -- Drop the composite FK and index first
                    ALTER TABLE migration.{table}
                    DROP CONSTRAINT IF EXISTS fk_{table}_engagement_hierarchy;
                    DROP INDEX IF EXISTS migration.idx_{table}_client_engagement;
                    DROP INDEX IF EXISTS migration.ix_{table}_tenant_composite;

                    -- Add new INTEGER columns
                    ALTER TABLE migration.{table}
                    ADD COLUMN client_account_id_old INTEGER,
                    ADD COLUMN engagement_id_old INTEGER;

                    -- Map test UUIDs back to INTEGER 1
                    UPDATE migration.{table}
                    SET client_account_id_old = 1,
                        engagement_id_old = 1
                    WHERE client_account_id = '11111111-1111-1111-1111-111111111111'::uuid
                      AND engagement_id = '22222222-2222-2222-2222-222222222222'::uuid;

                    -- For other UUIDs, try to extract from deterministic pattern
                    UPDATE migration.{table}
                    SET client_account_id_old = COALESCE(
                            client_account_id_old,
                            CAST(RIGHT(client_account_id::text, 12) AS INTEGER)
                        ),
                        engagement_id_old = COALESCE(
                            engagement_id_old,
                            CAST(RIGHT(engagement_id::text, 12) AS INTEGER)
                        )
                    WHERE client_account_id_old IS NULL;

                    -- Drop UUID columns
                    ALTER TABLE migration.{table}
                    DROP COLUMN client_account_id,
                    DROP COLUMN engagement_id;

                    -- Rename columns back
                    ALTER TABLE migration.{table}
                    RENAME COLUMN client_account_id_old TO client_account_id;
                    ALTER TABLE migration.{table}
                    RENAME COLUMN engagement_id_old TO engagement_id;

                    -- Set NOT NULL
                    ALTER TABLE migration.{table}
                    ALTER COLUMN client_account_id SET NOT NULL,
                    ALTER COLUMN engagement_id SET NOT NULL;

                    -- Recreate original indexes
                    CREATE INDEX IF NOT EXISTS idx_{table}_client_engagement
                    ON migration.{table}(client_account_id, engagement_id);

                    RAISE NOTICE 'Reverted {table} tenant columns from UUID to INTEGER';
                END IF;
            END $$;
            """
        )
