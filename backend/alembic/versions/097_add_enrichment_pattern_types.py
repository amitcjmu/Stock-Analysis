"""Add enrichment pattern types to patterntype enum

Revision ID: 097_add_enrichment_pattern_types
Revises: 096_update_application_architecture_overrides_schema
Create Date: 2025-10-16

This migration adds new enum values to support enrichment agent pattern storage:
- PRODUCT_MATCHING: Product catalog matching patterns
- COMPLIANCE_ANALYSIS: Compliance requirement patterns
- LICENSING_ANALYSIS: Software licensing patterns
- VULNERABILITY_ANALYSIS: Security vulnerability patterns
- RESILIENCE_ANALYSIS: HA/DR resilience patterns
- DEPENDENCY_ANALYSIS: Asset dependency patterns

These patterns are used by the AutoEnrichmentPipeline agents to store learned
patterns via TenantMemoryManager (ADR-024).
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "097_add_enrichment_pattern_types"
down_revision = "096_update_application_architecture_overrides_schema"
branch_labels = None
depends_on = None


def upgrade():
    """Add enrichment pattern types to patterntype enum."""

    # Add new enum values for enrichment agents
    # Note: PostgreSQL doesn't allow removing enum values, so downgrade is no-op
    op.execute(
        """
        DO $$
        BEGIN
            -- PRODUCT_MATCHING: For ProductMatchingAgent
            IF NOT EXISTS (
                SELECT 1 FROM pg_enum
                WHERE enumlabel = 'PRODUCT_MATCHING'
                AND enumtypid = 'migration.patterntype'::regtype
            ) THEN
                ALTER TYPE migration.patterntype ADD VALUE 'PRODUCT_MATCHING';
            END IF;

            -- COMPLIANCE_ANALYSIS: For ComplianceEnrichmentAgent
            IF NOT EXISTS (
                SELECT 1 FROM pg_enum
                WHERE enumlabel = 'COMPLIANCE_ANALYSIS'
                AND enumtypid = 'migration.patterntype'::regtype
            ) THEN
                ALTER TYPE migration.patterntype ADD VALUE 'COMPLIANCE_ANALYSIS';
            END IF;

            -- LICENSING_ANALYSIS: For LicensingEnrichmentAgent
            IF NOT EXISTS (
                SELECT 1 FROM pg_enum
                WHERE enumlabel = 'LICENSING_ANALYSIS'
                AND enumtypid = 'migration.patterntype'::regtype
            ) THEN
                ALTER TYPE migration.patterntype ADD VALUE 'LICENSING_ANALYSIS';
            END IF;

            -- VULNERABILITY_ANALYSIS: For VulnerabilityEnrichmentAgent
            IF NOT EXISTS (
                SELECT 1 FROM pg_enum
                WHERE enumlabel = 'VULNERABILITY_ANALYSIS'
                AND enumtypid = 'migration.patterntype'::regtype
            ) THEN
                ALTER TYPE migration.patterntype ADD VALUE 'VULNERABILITY_ANALYSIS';
            END IF;

            -- RESILIENCE_ANALYSIS: For ResilienceEnrichmentAgent
            IF NOT EXISTS (
                SELECT 1 FROM pg_enum
                WHERE enumlabel = 'RESILIENCE_ANALYSIS'
                AND enumtypid = 'migration.patterntype'::regtype
            ) THEN
                ALTER TYPE migration.patterntype ADD VALUE 'RESILIENCE_ANALYSIS';
            END IF;

            -- DEPENDENCY_ANALYSIS: For DependencyEnrichmentAgent
            IF NOT EXISTS (
                SELECT 1 FROM pg_enum
                WHERE enumlabel = 'DEPENDENCY_ANALYSIS'
                AND enumtypid = 'migration.patterntype'::regtype
            ) THEN
                ALTER TYPE migration.patterntype ADD VALUE 'DEPENDENCY_ANALYSIS';
            END IF;

        END $$;
    """
    )


def downgrade():
    """
    Cannot remove enum values in PostgreSQL without recreating the entire type.

    To properly downgrade, you would need to:
    1. Create a new enum type without these values
    2. Alter all columns using the old enum to use the new enum
    3. Drop the old enum type
    4. Rename the new enum type to the old name

    This is complex and risky in production, so we don't support downgrade.
    If you need to remove these values, do it manually or create a new migration.
    """
    pass
