"""Implement Row-Level Security for multi-tenant isolation

Revision ID: 019_implement_row_level_security
Revises: 018_fix_long_constraint_names
Create Date: 2025-01-24

This migration implements PostgreSQL Row-Level Security (RLS) policies for all
multi-tenant tables to ensure complete data isolation between tenants.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "019_implement_row_level_security"
down_revision = "018_fix_long_constraint_names"
branch_labels = None
depends_on = None

# List of all multi-tenant tables identified by the scan
MULTI_TENANT_TABLES = [
    "agent_discovered_patterns",
    "agent_performance_daily",
    "agent_task_history",
    "assessment_flows",
    "assessments",
    "assets",
    "client_accounts",
    "collection_flows",
    "crewai_flow_state_extensions",
    "custom_target_fields",
    "data_imports",
    "discovery_flows",
    "feedback",
    "flow_deletion_audit",
    "import_field_mappings",
    "llm_usage_logs",
    "platform_credentials",
    "sixr_analyses",
    "tags",
    "user_profiles",
]


def upgrade() -> None:
    """Implement Row-Level Security for multi-tenant isolation"""

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    # 1. Create application role if it doesn't exist
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_roles WHERE rolname = 'application_role'
            ) THEN
                CREATE ROLE application_role;
                RAISE NOTICE 'Created application_role';
            ELSE
                RAISE NOTICE 'application_role already exists';
            END IF;
        END $$;
    """
    )

    # 2. Grant necessary permissions to application_role
    # Split into separate statements for asyncpg compatibility
    op.execute("GRANT USAGE ON SCHEMA migration TO application_role")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA migration TO application_role"
    )
    op.execute("GRANT USAGE ON ALL SEQUENCES IN SCHEMA migration TO application_role")

    # 3. Enable RLS on all multi-tenant tables
    print("🔒 Enabling Row-Level Security on multi-tenant tables...")
    for table in MULTI_TENANT_TABLES:
        # Use dynamic SQL inside PL/pgSQL to safely handle table names
        op.execute(
            f"""
            DO $$
            DECLARE
                v_table_name text := '{table}';
            BEGIN
                -- Check if table exists before enabling RLS
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'migration'
                    AND table_name = v_table_name
                ) THEN
                    EXECUTE format('ALTER TABLE migration.%I ENABLE ROW LEVEL SECURITY', v_table_name);
                    RAISE NOTICE 'Enabled RLS on %', v_table_name;
                ELSE
                    RAISE NOTICE 'Table % does not exist, skipping RLS', v_table_name;
                END IF;
            END $$;
        """
        )

    # 4. Create RLS policies for tenant isolation
    print("🛡️ Creating RLS policies for tenant isolation...")
    for table in MULTI_TENANT_TABLES:
        policy_name = f"rls_{table}_tenant_isolation"
        op.execute(
            f"""
            DO $$
            DECLARE
                v_table_name text := '{table}';
                v_policy_name text := '{policy_name}';
            BEGIN
                -- Check if table exists and has client_account_id column
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'migration'
                    AND table_name = v_table_name
                    AND column_name = 'client_account_id'
                ) THEN
                    -- Drop existing policy if it exists
                    EXECUTE format('DROP POLICY IF EXISTS %I ON migration.%I', v_policy_name, v_table_name);

                    -- Create new policy
                    EXECUTE format(
                        'CREATE POLICY %I ON migration.%I FOR ALL TO application_role USING (client_account_id = current_setting(''app.client_id'', true)::uuid)',
                        v_policy_name, v_table_name
                    );

                    RAISE NOTICE 'Created RLS policy for %', v_table_name;
                ELSE
                    RAISE NOTICE 'Table % does not have client_account_id, skipping policy', v_table_name;
                END IF;
            END $$;
        """
        )

    # 5. Special handling for client_accounts table (users see only their own account)
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'client_accounts'
            ) THEN
                -- Drop and recreate policy for client_accounts
                DROP POLICY IF EXISTS rls_client_accounts_tenant_isolation ON migration.client_accounts;

                CREATE POLICY rls_client_accounts_tenant_isolation ON migration.client_accounts
                FOR ALL TO application_role
                USING (id = current_setting('app.client_id', true)::uuid);

                RAISE NOTICE 'Created special RLS policy for client_accounts';
            END IF;
        END $$;
    """
    )

    # 6. Create bypass policies for superusers (admin operations)
    print("👑 Creating bypass policies for superusers...")
    for table in MULTI_TENANT_TABLES:
        bypass_policy_name = f"rls_{table}_superuser_bypass"
        op.execute(
            f"""
            DO $$
            DECLARE
                v_table_name text := '{table}';
                v_policy_name text := '{bypass_policy_name}';
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'migration'
                    AND table_name = v_table_name
                ) THEN
                    -- Create bypass policy for superusers
                    EXECUTE format(
                        'CREATE POLICY %I ON migration.%I FOR ALL TO postgres USING (true)',
                        v_policy_name, v_table_name
                    );

                    RAISE NOTICE 'Created superuser bypass policy for %', v_table_name;
                END IF;
            END $$;
        """
        )

    # 7. Create function to set tenant context (used by middleware)
    op.execute(
        """
        CREATE OR REPLACE FUNCTION migration.set_tenant_context(p_client_id uuid)
        RETURNS void AS $$
        BEGIN
            -- Set the client_id in session config
            PERFORM set_config('app.client_id', p_client_id::text, false);
            RAISE NOTICE 'Set tenant context to %', p_client_id;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER
        """
    )

    # Grant execute permission to application_role
    op.execute(
        "GRANT EXECUTE ON FUNCTION migration.set_tenant_context(uuid) TO application_role"
    )

    # 8. Create function to get current tenant context
    op.execute(
        """
        CREATE OR REPLACE FUNCTION migration.get_current_tenant()
        RETURNS uuid AS $$
        BEGIN
            RETURN current_setting('app.client_id', true)::uuid;
        EXCEPTION
            WHEN OTHERS THEN
                RETURN NULL;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER
        """
    )

    # Grant execute permission to application_role
    op.execute(
        "GRANT EXECUTE ON FUNCTION migration.get_current_tenant() TO application_role"
    )

    print("✅ Row-Level Security implementation completed successfully")


def downgrade() -> None:
    """Remove Row-Level Security implementation"""

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    # Drop helper functions
    op.execute("DROP FUNCTION IF EXISTS migration.get_current_tenant()")
    op.execute("DROP FUNCTION IF EXISTS migration.set_tenant_context(uuid)")

    # Drop all RLS policies and disable RLS
    print("🔓 Removing Row-Level Security policies...")
    for table in MULTI_TENANT_TABLES:
        op.execute(
            f"""
            DO $$
            DECLARE
                v_table_name text := '{table}';
                v_policy_name text := 'rls_{table}_tenant_isolation';
                v_bypass_policy text := 'rls_{table}_superuser_bypass';
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'migration'
                    AND table_name = v_table_name
                ) THEN
                    -- Drop all policies on the table
                    EXECUTE format('DROP POLICY IF EXISTS %I ON migration.%I', v_policy_name, v_table_name);
                    EXECUTE format('DROP POLICY IF EXISTS %I ON migration.%I', v_bypass_policy, v_table_name);

                    -- Disable RLS
                    EXECUTE format('ALTER TABLE migration.%I DISABLE ROW LEVEL SECURITY', v_table_name);

                    RAISE NOTICE 'Removed RLS from %', v_table_name;
                END IF;
            END $$;
        """
        )

    # Note: We don't drop the application_role as it might be used elsewhere

    print("✅ Row-Level Security removal completed")
