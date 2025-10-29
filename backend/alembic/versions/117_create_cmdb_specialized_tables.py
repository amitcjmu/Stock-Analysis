"""Create CMDB specialized tables

Creates asset_eol_assessments and asset_contacts tables for normalized data.
Supports Issue #833 hybrid architecture approach.

Revision ID: 117_create_cmdb_specialized_tables
Revises: 116_add_cmdb_explicit_fields
Create Date: 2025-10-28 14:30:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "117_create_cmdb_specialized_tables"
down_revision = "116_add_cmdb_explicit_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create specialized CMDB tables.

    IDEMPOTENT: Uses IF NOT EXISTS for table creation.
    """
    op.execute(
        """
        DO $$
        BEGIN
            -- Create asset_eol_assessments table
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'asset_eol_assessments'
            ) THEN
                CREATE TABLE migration.asset_eol_assessments (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

                    -- Multi-tenant isolation
                    client_account_id UUID NOT NULL REFERENCES client_accounts(id) ON DELETE CASCADE,
                    engagement_id UUID NOT NULL REFERENCES engagements(id) ON DELETE CASCADE,

                    -- Asset reference
                    asset_id UUID NOT NULL REFERENCES migration.assets(id) ON DELETE CASCADE,

                    -- EOL Assessment Data
                    technology_component VARCHAR(255) NOT NULL,
                    eol_date DATE,
                    eol_risk_level VARCHAR(20),
                    assessment_notes TEXT,
                    remediation_options JSONB DEFAULT '[]'::jsonb,

                    -- Audit fields
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

                    -- Constraints
                    CONSTRAINT chk_eol_risk_level CHECK (
                        eol_risk_level IN ('low', 'medium', 'high', 'critical')
                    )
                );

                -- Indexes
                CREATE INDEX idx_asset_eol_assessments_asset_id
                ON migration.asset_eol_assessments(asset_id);

                CREATE INDEX idx_asset_eol_assessments_client_account
                ON migration.asset_eol_assessments(client_account_id);

                CREATE INDEX idx_asset_eol_assessments_engagement
                ON migration.asset_eol_assessments(engagement_id);

                CREATE INDEX idx_asset_eol_assessments_eol_date
                ON migration.asset_eol_assessments(eol_date);

                -- Comments
                COMMENT ON TABLE migration.asset_eol_assessments IS
                'End-of-life technology assessments for assets';

                COMMENT ON COLUMN migration.asset_eol_assessments.technology_component IS
                'Technology component being assessed (OS, DB, Framework, etc.)';

                COMMENT ON COLUMN migration.asset_eol_assessments.eol_risk_level IS
                'Risk level: low, medium, high, critical';
            END IF;

            -- Create asset_contacts table
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'asset_contacts'
            ) THEN
                CREATE TABLE migration.asset_contacts (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

                    -- Multi-tenant isolation
                    client_account_id UUID NOT NULL REFERENCES client_accounts(id) ON DELETE CASCADE,
                    engagement_id UUID NOT NULL REFERENCES engagements(id) ON DELETE CASCADE,

                    -- Asset reference
                    asset_id UUID NOT NULL REFERENCES migration.assets(id) ON DELETE CASCADE,

                    -- Contact Data
                    contact_type VARCHAR(50) NOT NULL,
                    user_id UUID REFERENCES users(id),
                    email VARCHAR(255),
                    name VARCHAR(255),
                    phone VARCHAR(50),

                    -- Audit fields
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

                    -- Constraints
                    CONSTRAINT contact_identity_check CHECK (
                        user_id IS NOT NULL OR email IS NOT NULL
                    )
                );

                -- Indexes
                CREATE INDEX idx_asset_contacts_asset_id
                ON migration.asset_contacts(asset_id);

                CREATE INDEX idx_asset_contacts_client_account
                ON migration.asset_contacts(client_account_id);

                CREATE INDEX idx_asset_contacts_engagement
                ON migration.asset_contacts(engagement_id);

                CREATE INDEX idx_asset_contacts_contact_type
                ON migration.asset_contacts(contact_type);

                -- Comments
                COMMENT ON TABLE migration.asset_contacts IS
                'Normalized contact information for assets';

                COMMENT ON COLUMN migration.asset_contacts.contact_type IS
                'Contact role: business_owner, technical_owner, architect, etc.';
            END IF;

        END $$;
        """
    )


def downgrade() -> None:
    """
    Drop specialized tables.

    WARNING: This drops tables and loses data!
    """
    op.execute(
        """
        DROP TABLE IF EXISTS migration.asset_contacts CASCADE;
        DROP TABLE IF EXISTS migration.asset_eol_assessments CASCADE;
        """
    )
