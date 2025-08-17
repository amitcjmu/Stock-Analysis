"""Add Row Level Security policies for multi-tenant isolation

Revision ID: rls_policies_001
Revises:
Create Date: 2024-06-30 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "rls_policies_001"
down_revision = "001_consolidated_schema"  # RLS must run after schema is created
branch_labels = None
depends_on = None


def upgrade():
    """Add RLS policies to all tenant-scoped tables"""

    # Check if application_role exists, create if not (for development/testing)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'application_role') THEN
                -- For production, this role should be created during database setup
                -- This is a fallback for development environments
                RAISE NOTICE 'Role application_role does not exist. RLS policies will be created for PUBLIC role instead.';
            END IF;
        END
        $$;
    """
    )

    # Determine which role to use based on environment
    role_check = (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'application_role')"
            )
        )
        .scalar()
    )
    target_role = "application_role" if role_check else "PUBLIC"

    # Enable RLS on tables
    tables_with_rls = [
        "data_imports",
        "raw_import_records",
        "import_field_mappings",
        "assets",
        "applications",
        "dependencies",
        "crewai_flow_state_extensions",
    ]

    for table in tables_with_rls:
        # Check if table exists before enabling RLS
        table_exists = (
            op.get_bind()
            .execute(
                sa.text(
                    f"SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                    f"WHERE table_name = '{table}')"  # nosec B608
                )
            )
            .scalar()
        )

        if not table_exists:
            print(f"Table {table} does not exist, skipping RLS setup")
            continue

        # Enable RLS
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")

        # Create policy for client account isolation
        op.execute(
            f"""
            CREATE POLICY {table}_client_isolation ON {table}
            FOR ALL
            TO {target_role}
            USING (client_account_id = current_setting('app.client_account_id')::uuid)
            WITH CHECK (client_account_id = current_setting('app.client_account_id')::uuid);
        """
        )

        # Create policy for engagement isolation (if applicable)
        if table not in ["clients", "engagements"]:
            op.execute(
                f"""
                CREATE POLICY {table}_engagement_isolation ON {table}
                FOR ALL
                TO {target_role}
                USING (
                    engagement_id = current_setting('app.engagement_id', true)::uuid
                    OR current_setting('app.engagement_id', true) IS NULL
                );
            """
            )

    # Create function to set context in database session
    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_tenant_context(
            p_client_account_id uuid,
            p_engagement_id uuid DEFAULT NULL
        ) RETURNS void AS $$
        BEGIN
            PERFORM set_config('app.client_account_id', p_client_account_id::text, false);
            IF p_engagement_id IS NOT NULL THEN
                PERFORM set_config('app.engagement_id', p_engagement_id::text, false);
            END IF;
        END;
        $$ LANGUAGE plpgsql;
    """
    )


def downgrade():
    """Remove RLS policies"""
    tables_with_rls = [
        "data_imports",
        "raw_import_records",
        "import_field_mappings",
        "assets",
        "applications",
        "dependencies",
        "crewai_flow_state_extensions",
    ]

    for table in tables_with_rls:
        op.execute(f"DROP POLICY IF EXISTS {table}_client_isolation ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_engagement_isolation ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    op.execute("DROP FUNCTION IF EXISTS set_tenant_context;")
