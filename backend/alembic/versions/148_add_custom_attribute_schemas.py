"""Add custom_attribute_schemas table for JSONB validation (Issue #1240)

Creates infrastructure for client-specific schema validation of the
custom_attributes JSONB column in assets table.

Benefits:
- Consistent field names across assets (no more app_owner vs AppOwner)
- Type enforcement (integer vs string)
- Required field validation per client
- Data quality improvement for 6R assessments

Revision ID: 148_add_custom_attribute_schemas
Revises: 147_optimize_pgvector_index
Create Date: 2025-12-05
"""

from alembic import op

revision = "148_add_custom_attribute_schemas"
down_revision = "147_optimize_pgvector_index"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create custom_attribute_schemas table for JSONB validation."""
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS migration.custom_attribute_schemas (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            client_account_id UUID NOT NULL
                REFERENCES migration.client_accounts(id) ON DELETE CASCADE,
            schema_name VARCHAR(100) NOT NULL,
            schema_version INTEGER NOT NULL DEFAULT 1,
            json_schema JSONB NOT NULL,
            description TEXT,
            is_active BOOLEAN NOT NULL DEFAULT true,
            strict_mode BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            created_by VARCHAR(255),
            UNIQUE(client_account_id, schema_name, schema_version)
        );
        """
    )

    # Add index for quick schema lookups by client
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_custom_attr_schemas_client_active
        ON migration.custom_attribute_schemas (client_account_id, is_active)
        WHERE is_active = true;
        """
    )

    # Add comment explaining the table purpose
    op.execute(
        """
        COMMENT ON TABLE migration.custom_attribute_schemas IS
        'Client-specific JSON schemas for validating custom_attributes. Uses JSON Schema draft-07.';
        """
    )

    op.execute(
        """
        COMMENT ON COLUMN migration.custom_attribute_schemas.strict_mode IS
        'When true, validation failures reject the data. When false, failures log warnings only.';
        """
    )


def downgrade() -> None:
    """Remove custom_attribute_schemas table."""
    op.execute("DROP INDEX IF EXISTS migration.ix_custom_attr_schemas_client_active;")
    op.execute("DROP TABLE IF EXISTS migration.custom_attribute_schemas;")
