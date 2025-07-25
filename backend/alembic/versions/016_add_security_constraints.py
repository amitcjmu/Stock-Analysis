"""Add security constraints and data protection measures

Revision ID: 016_add_security_constraints
Revises: 015_add_asset_dependencies
Create Date: 2025-01-24

This migration adds security constraints and data protection measures
including encryption validation, data sanitization, and retention policies.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "016_add_security_constraints"
down_revision = "015_add_asset_dependencies"
branch_labels = None
depends_on = None


def table_exists(table_name):
    """Check if a table exists in the database"""
    bind = op.get_bind()
    try:
        # Use parameterized query with proper escaping
        # Note: table_name is a string literal value, not an identifier
        result = bind.execute(
            sa.text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'migration'
                    AND table_name = :table_name
                )
            """
            ).bindparams(table_name=table_name)
        ).scalar()
        return result
    except Exception as e:
        print(f"Error checking if table {table_name} exists: {e}")
        # If we get an error, assume table exists to avoid trying to create it
        return True


def create_table_if_not_exists(table_name, *columns, **kwargs):
    """Create a table only if it doesn't already exist"""
    if not table_exists(table_name):
        op.create_table(table_name, *columns, **kwargs)
    else:
        print(f"Table {table_name} already exists, skipping creation")


def constraint_exists(constraint_name, table_name):
    """Check if a constraint exists"""
    bind = op.get_bind()
    try:
        result = bind.execute(
            sa.text(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints
                    WHERE table_schema = 'migration'
                    AND constraint_schema = 'migration'
                    AND table_name = :table_name
                    AND constraint_name = :constraint_name
                )
            """
            ).bindparams(table_name=table_name, constraint_name=constraint_name)
        ).scalar()
        return result
    except Exception as e:
        print(f"Error checking if constraint {constraint_name} exists: {e}")
        # If we get an error, assume constraint exists
        return True


def upgrade() -> None:
    """Add security constraints and data protection measures"""

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    # Skip adding constraint for non-existent encryption_key_id column
    # The platform_credentials table uses encrypted_data and encryption_metadata instead

    # Add columns for key rotation tracking with error handling
    op.execute(
        """
        DO $$
        BEGIN
            -- Add encryption_algorithm column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'platform_credentials'
                AND column_name = 'encryption_algorithm'
            ) THEN
                ALTER TABLE migration.platform_credentials
                ADD COLUMN encryption_algorithm VARCHAR(50);
            END IF;

            -- Add key_rotation_required column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'platform_credentials'
                AND column_name = 'key_rotation_required'
            ) THEN
                ALTER TABLE migration.platform_credentials
                ADD COLUMN key_rotation_required BOOLEAN DEFAULT false;
            END IF;

            -- Add last_rotation_checked_at column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'platform_credentials'
                AND column_name = 'last_rotation_checked_at'
            ) THEN
                ALTER TABLE migration.platform_credentials
                ADD COLUMN last_rotation_checked_at TIMESTAMP WITH TIME ZONE;
            END IF;
        END $$;
    """
    )

    # Add constraint for encryption algorithm
    if not constraint_exists("ck_encryption_algorithm", "platform_credentials"):
        op.create_check_constraint(
            "ck_encryption_algorithm",
            "platform_credentials",
            "encryption_algorithm IN ('AES-256-GCM', 'AES-256-CBC', 'RSA-4096', 'ChaCha20-Poly1305')",
            schema="migration",
        )

    # 2. Add data sanitization function for security logs
    op.execute(
        """
        CREATE OR REPLACE FUNCTION migration.sanitize_log_data(data JSONB)
        RETURNS JSONB AS $$
        DECLARE
            sensitive_keys TEXT[] := ARRAY[
                'password', 'secret', 'token', 'api_key', 'apikey',
                'authorization', 'private_key', 'privatekey', 'credentials',
                'access_token', 'refresh_token', 'session_token',
                'client_secret', 'encryption_key', 'salt'
            ];
            key TEXT;
        BEGIN
            -- Recursively sanitize JSONB data
            IF jsonb_typeof(data) = 'object' THEN
                FOREACH key IN ARRAY (SELECT array_agg(k) FROM jsonb_object_keys(data) k)
                LOOP
                    -- Check if key contains sensitive patterns
                    IF EXISTS (
                        SELECT 1 FROM unnest(sensitive_keys) sk
                        WHERE LOWER(key) LIKE '%' || sk || '%'
                    ) THEN
                        data = jsonb_set(data, ARRAY[key], '"[REDACTED]"'::jsonb);
                    ELSE
                        -- Recursively sanitize nested objects
                        data = jsonb_set(
                            data,
                            ARRAY[key],
                            migration.sanitize_log_data(data->key)
                        );
                    END IF;
                END LOOP;
            ELSIF jsonb_typeof(data) = 'array' THEN
                -- Sanitize array elements
                SELECT jsonb_agg(migration.sanitize_log_data(value))
                INTO data
                FROM jsonb_array_elements(data) AS value;
            END IF;

            RETURN data;
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
    """
    )

    # Add trigger to sanitize security audit logs
    op.execute(
        """
        CREATE OR REPLACE FUNCTION migration.sanitize_audit_log_trigger()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Sanitize request_payload
            IF NEW.request_payload IS NOT NULL THEN
                NEW.request_payload = migration.sanitize_log_data(NEW.request_payload);
            END IF;

            -- Sanitize response_payload
            IF NEW.response_payload IS NOT NULL THEN
                NEW.response_payload = migration.sanitize_log_data(NEW.response_payload);
            END IF;

            -- Sanitize target_details
            IF NEW.target_details IS NOT NULL THEN
                NEW.target_details = migration.sanitize_log_data(NEW.target_details);
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    op.execute(
        """
        CREATE TRIGGER sanitize_audit_log_before_insert
        BEFORE INSERT ON migration.security_audit_logs
        FOR EACH ROW
        EXECUTE FUNCTION migration.sanitize_audit_log_trigger();
    """
    )

    # 3. Add PII data classification and retention policies

    # Add data classification columns
    op.add_column(
        "client_accounts",
        sa.Column("data_retention_days", sa.Integer(), server_default="365"),
        schema="migration",
    )
    op.add_column(
        "client_accounts",
        sa.Column("pii_data_consent", sa.Boolean(), server_default=sa.text("false")),
        schema="migration",
    )
    op.add_column(
        "client_accounts",
        sa.Column("pii_consent_date", sa.TIMESTAMP(timezone=True)),
        schema="migration",
    )

    # Create PII data tracking table
    create_table_if_not_exists(
        "pii_data_registry",
        sa.Column(
            "id",
            postgresql.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("table_name", sa.String(100), nullable=False),
        sa.Column("column_name", sa.String(100), nullable=False),
        sa.Column(
            "data_classification",
            sa.String(50),
            nullable=False,
            comment="PII, SPII, PUBLIC, INTERNAL, CONFIDENTIAL",
        ),
        sa.Column("encryption_required", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("retention_days", sa.Integer(), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=True),
        sa.Column(
            "legal_basis",
            sa.String(100),
            nullable=True,
            comment="consent, contract, legal_obligation, legitimate_interest",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("table_name", "column_name"),
        schema="migration",
    )

    # Insert PII data registry entries
    op.execute(
        """
        INSERT INTO migration.pii_data_registry
        (table_name, column_name, data_classification, retention_days, purpose, legal_basis)
        VALUES
        -- client_accounts PII fields (3 years retention for GDPR compliance)
        ('client_accounts', 'primary_contact_name', 'PII', 1095, 'Business contact', 'contract'),
        ('client_accounts', 'primary_contact_email', 'PII', 1095, 'Business communication', 'contract'),
        ('client_accounts', 'primary_contact_phone', 'PII', 1095, 'Business communication', 'contract'),
        -- users PII fields (3 years retention for GDPR compliance)
        ('users', 'email', 'PII', 1095, 'Authentication and communication', 'contract'),
        ('users', 'full_name', 'PII', 1095, 'User identification', 'contract'),
        -- security_audit_logs fields
        ('security_audit_logs', 'actor_email', 'PII', 90, 'Security auditing', 'legal_obligation'),
        ('security_audit_logs', 'ip_address', 'PII', 90, 'Security monitoring', 'legitimate_interest'),
        -- platform_credentials sensitive fields
        ('platform_credentials', 'encrypted_data', 'CONFIDENTIAL', 365, 'Platform integration', 'contract'),
        ('platform_credentials', 'vault_reference', 'CONFIDENTIAL', 365, 'Vault key management', 'contract');
    """
    )

    # 4. Create vector index with proper error handling (if tables exist)
    op.execute(
        """
        DO $$
        BEGIN
            -- Check if the vector type and agent_learning_patterns table exist
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'vector')
               AND EXISTS (SELECT 1 FROM information_schema.tables
                          WHERE table_schema = 'migration'
                          AND table_name = 'agent_learning_patterns') THEN
                -- Create index only if vector type and table exist
                CREATE INDEX IF NOT EXISTS ix_agent_learning_embedding
                ON migration.agent_learning_patterns
                USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64);

                RAISE NOTICE 'Vector index created successfully';
            ELSE
                RAISE NOTICE 'Vector type or agent_learning_patterns table not available, skipping index creation';
            END IF;
        EXCEPTION
            WHEN undefined_object THEN
                RAISE NOTICE 'Vector extension not installed, skipping index creation';
            WHEN OTHERS THEN
                RAISE NOTICE 'Error creating vector index: %', SQLERRM;
        END $$;
    """
    )

    # 5. Add audit log retention policy
    op.execute(
        """
        CREATE OR REPLACE FUNCTION migration.cleanup_old_audit_logs()
        RETURNS void AS $$
        BEGIN
            -- Delete audit logs older than retention period
            DELETE FROM migration.security_audit_logs
            WHERE created_at < NOW() - INTERVAL '90 days'
            AND severity IN ('INFO', 'DEBUG');

            -- Keep ERROR and CRITICAL logs for 1 year
            DELETE FROM migration.security_audit_logs
            WHERE created_at < NOW() - INTERVAL '365 days'
            AND severity IN ('ERROR', 'CRITICAL');
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    print("✅ Security constraints and data protection measures added successfully")


def downgrade() -> None:
    """Remove security constraints and data protection measures"""

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    # Remove audit log cleanup function
    op.execute("DROP FUNCTION IF EXISTS migration.cleanup_old_audit_logs()")

    # Remove vector index if it exists
    op.execute("DROP INDEX IF EXISTS migration.ix_agent_learning_embedding")

    # Drop PII registry table
    op.drop_table("pii_data_registry", schema="migration")

    # Remove PII columns from client_accounts
    op.drop_column("client_accounts", "pii_consent_date", schema="migration")
    op.drop_column("client_accounts", "pii_data_consent", schema="migration")
    op.drop_column("client_accounts", "data_retention_days", schema="migration")

    # Remove audit log sanitization trigger and functions
    op.execute(
        "DROP TRIGGER IF EXISTS sanitize_audit_log_before_insert ON migration.security_audit_logs"
    )
    op.execute("DROP FUNCTION IF EXISTS migration.sanitize_audit_log_trigger()")
    op.execute("DROP FUNCTION IF EXISTS migration.sanitize_log_data(JSONB)")

    # Remove encryption validation constraints and columns
    op.drop_constraint(
        "ck_encryption_algorithm", "platform_credentials", schema="migration"
    )
    # Skip dropping non-existent ck_encryption_key_format constraint
    op.drop_column(
        "platform_credentials", "last_rotation_checked_at", schema="migration"
    )
    op.drop_column("platform_credentials", "key_rotation_required", schema="migration")
    op.drop_column("platform_credentials", "encryption_algorithm", schema="migration")

    print("✅ Security constraints and data protection measures removed")
