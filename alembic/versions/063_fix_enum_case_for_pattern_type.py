"""fix_enum_case_for_pattern_type

Fix PostgreSQL enum patterntype to use UPPERCASE values to match SQLAlchemy expectations.

This addresses the production error:
invalid input value for enum patterntype: "FIELD_MAPPING_APPROVAL"

The issue is that SQLAlchemy automatically converts string literals to uppercase
enum member names when it encounters a PostgreSQL enum type, but our enum
was defined with lowercase values.

Revision ID: 063_fix_enum_case_for_pattern_type
Revises: 062_add_description_to_assessment_flows
Create Date: 2025-09-10 16:55:31.179820

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '063_fix_enum_case_for_pattern_type'
down_revision = '062_add_description_to_assessment_flows'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Fix enum case by recreating with uppercase values - idempotent"""

    print("🔧 Fixing PostgreSQL enum patterntype case to match SQLAlchemy expectations...")

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    # Check if enum exists and what values it has
    conn = op.get_bind()
    enum_check = conn.execute(
        sa.text("""
            SELECT 1 FROM pg_type
            WHERE typname = 'patterntype'
            AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'migration')
        """)
    )

    enum_exists = enum_check.fetchone() is not None

    # Check if we already have uppercase values (migration already applied)
    if enum_exists:
        uppercase_check = conn.execute(
            sa.text("""
                SELECT enumlabel FROM pg_enum e
                JOIN pg_type t ON e.enumtypid = t.oid
                WHERE t.typname = 'patterntype'
                AND t.typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'migration')
                AND enumlabel = 'FIELD_MAPPING_APPROVAL'
            """)
        )

        if uppercase_check.fetchone():
            print("   ✅ Enum already has uppercase values - migration already applied")
            return

    # Check if table exists
    table_check = conn.execute(
        sa.text("""
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'migration'
            AND table_name = 'agent_discovered_patterns'
        """)
    )

    table_exists = table_check.fetchone() is not None

    if enum_exists and table_exists:
        print("   📝 Existing enum found with lowercase values, recreating with uppercase...")

        # First, change column to varchar temporarily
        op.execute("""
            ALTER TABLE migration.agent_discovered_patterns
            ALTER COLUMN pattern_type TYPE varchar(100)
        """)

        # Drop the old enum
        op.execute("DROP TYPE migration.patterntype CASCADE")

    elif enum_exists:
        print("   📝 Enum exists but table doesn't, dropping old enum...")
        op.execute("DROP TYPE migration.patterntype CASCADE")

    # Create new enum with uppercase values to match SQLAlchemy expectations
    print("   🆕 Creating enum with uppercase values...")
    op.execute("""
        CREATE TYPE migration.patterntype AS ENUM (
            'FIELD_MAPPING_APPROVAL',
            'FIELD_MAPPING_REJECTION',
            'FIELD_MAPPING_SUGGESTION',
            'TECHNOLOGY_CORRELATION',
            'BUSINESS_VALUE_INDICATOR',
            'RISK_FACTOR',
            'MODERNIZATION_OPPORTUNITY',
            'DEPENDENCY_PATTERN',
            'SECURITY_VULNERABILITY',
            'PERFORMANCE_BOTTLENECK',
            'COMPLIANCE_REQUIREMENT'
        )
    """)

    if table_exists:
        # Convert any existing lowercase values to uppercase
        op.execute("""
            UPDATE migration.agent_discovered_patterns
            SET pattern_type = UPPER(pattern_type)
            WHERE pattern_type IS NOT NULL
        """)

        # Change column back to enum type with safe default for invalid values
        op.execute("""
            ALTER TABLE migration.agent_discovered_patterns
            ALTER COLUMN pattern_type TYPE migration.patterntype
            USING CASE
                WHEN UPPER(pattern_type) IN (
                    'FIELD_MAPPING_APPROVAL',
                    'FIELD_MAPPING_REJECTION',
                    'FIELD_MAPPING_SUGGESTION',
                    'TECHNOLOGY_CORRELATION',
                    'BUSINESS_VALUE_INDICATOR',
                    'RISK_FACTOR',
                    'MODERNIZATION_OPPORTUNITY',
                    'DEPENDENCY_PATTERN',
                    'SECURITY_VULNERABILITY',
                    'PERFORMANCE_BOTTLENECK',
                    'COMPLIANCE_REQUIREMENT'
                )
                THEN UPPER(pattern_type)::migration.patterntype
                ELSE 'FIELD_MAPPING_SUGGESTION'::migration.patterntype
            END
        """)

        print("   ✅ Successfully updated enum and column with uppercase values")
    else:
        print("   ✅ Created new enum with uppercase values (table will use it when created)")


def downgrade() -> None:
    """Revert to lowercase enum values - idempotent"""

    print("🔄 Reverting enum to lowercase values...")

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    # Check if enum exists
    conn = op.get_bind()
    enum_check = conn.execute(
        sa.text("""
            SELECT 1 FROM pg_type
            WHERE typname = 'patterntype'
            AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'migration')
        """)
    )

    if not enum_check.fetchone():
        print("   ℹ️  No enum exists - nothing to downgrade")
        return

    # Check if we already have lowercase values (downgrade already applied)
    lowercase_check = conn.execute(
        sa.text("""
            SELECT enumlabel FROM pg_enum e
            JOIN pg_type t ON e.enumtypid = t.oid
            WHERE t.typname = 'patterntype'
            AND t.typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'migration')
            AND enumlabel = 'field_mapping_approval'
        """)
    )

    if lowercase_check.fetchone():
        print("   ✅ Enum already has lowercase values - downgrade already applied")
        return

    # Check if table exists
    table_check = conn.execute(
        sa.text("""
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'migration'
            AND table_name = 'agent_discovered_patterns'
        """)
    )

    table_exists = table_check.fetchone() is not None

    if table_exists:
        # Change column to varchar temporarily
        op.execute("""
            ALTER TABLE migration.agent_discovered_patterns
            ALTER COLUMN pattern_type TYPE varchar(100)
        """)

    # Drop the uppercase enum
    op.execute("DROP TYPE migration.patterntype CASCADE")

    # Recreate with lowercase values
    op.execute("""
        CREATE TYPE migration.patterntype AS ENUM (
            'field_mapping_approval',
            'field_mapping_rejection',
            'field_mapping_suggestion',
            'technology_correlation',
            'business_value_indicator',
            'risk_factor',
            'modernization_opportunity',
            'dependency_pattern',
            'security_vulnerability',
            'performance_bottleneck',
            'compliance_requirement'
        )
    """)

    if table_exists:
        # Convert uppercase values back to lowercase
        op.execute("""
            UPDATE migration.agent_discovered_patterns
            SET pattern_type = LOWER(pattern_type)
            WHERE pattern_type IS NOT NULL
        """)

        # Change column back to enum type
        op.execute("""
            ALTER TABLE migration.agent_discovered_patterns
            ALTER COLUMN pattern_type TYPE migration.patterntype
            USING CASE
                WHEN LOWER(pattern_type) IN (
                    'field_mapping_approval',
                    'field_mapping_rejection',
                    'field_mapping_suggestion',
                    'technology_correlation',
                    'business_value_indicator',
                    'risk_factor',
                    'modernization_opportunity',
                    'dependency_pattern',
                    'security_vulnerability',
                    'performance_bottleneck',
                    'compliance_requirement'
                )
                THEN LOWER(pattern_type)::migration.patterntype
                ELSE 'field_mapping_suggestion'::migration.patterntype
            END
        """)

    print("   ✅ Reverted to lowercase enum values")
