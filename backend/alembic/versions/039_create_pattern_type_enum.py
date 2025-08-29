"""Create patterntype enum for agent learning

Revision ID: 039_create_pattern_type_enum
Revises: 038_add_agent_pattern_learning_columns
Create Date: 2025-08-29 03:05:00.000000

This migration creates the patterntype enum that's required for the
agent_discovered_patterns table but was never created in the database.

The pattern_type column needs this enum to store the type of patterns
that agents discover during field mapping learning.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "039_create_pattern_type_enum"
down_revision = "038_add_agent_pattern_learning_columns"
branch_labels = None
depends_on = None


def upgrade():
    """Create the patterntype enum for agent_discovered_patterns table"""

    print("🔄 Creating patterntype enum for agent learning...")

    # Check if the enum already exists
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            """
        SELECT 1 FROM pg_type
        WHERE typname = 'patterntype'
        AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'migration')
    """
        )
    )

    if not result.fetchone():
        # Create the enum type with all possible pattern types
        op.execute(
            """
            CREATE TYPE migration.patterntype AS ENUM (
                'technology_correlation',
                'business_value_indicator',
                'risk_factor',
                'modernization_opportunity',
                'dependency_pattern',
                'security_vulnerability',
                'performance_bottleneck',
                'compliance_requirement',
                'field_mapping_approval',
                'field_mapping_rejection',
                'field_mapping_suggestion'
            )
        """
        )
        print("   ✅ Created patterntype enum with 11 pattern types")

        # Now we need to update the column type from varchar to the enum
        # First, we need to temporarily alter the column
        op.execute(
            """
            ALTER TABLE migration.agent_discovered_patterns
            ALTER COLUMN pattern_type TYPE migration.patterntype
            USING pattern_type::text::migration.patterntype
        """
        )
        print("   ✅ Updated pattern_type column to use patterntype enum")
    else:
        print("   ⏭️ patterntype enum already exists, checking for missing values...")

        # Check if field_mapping values are in the enum
        result = conn.execute(
            sa.text(
                """
            SELECT enumlabel FROM pg_enum
            WHERE enumtypid = (
                SELECT oid FROM pg_type
                WHERE typname = 'patterntype'
                AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'migration')
            )
        """
            )
        )

        existing_values = {row[0] for row in result}
        needed_values = {
            "field_mapping_approval",
            "field_mapping_rejection",
            "field_mapping_suggestion",
        }
        missing_values = needed_values - existing_values

        if missing_values:
            for value in missing_values:
                op.execute(
                    f"ALTER TYPE migration.patterntype ADD VALUE IF NOT EXISTS '{value}'"
                )
                print(f"   ✅ Added '{value}' to patterntype enum")
        else:
            print("   ⏭️ All required enum values already exist")

    print(
        "✅ Pattern type enum setup complete - agents can now learn from field mappings!"
    )


def downgrade():
    """Remove the patterntype enum"""

    print("🔄 Removing patterntype enum...")

    # First change the column back to varchar
    op.execute(
        """
        ALTER TABLE migration.agent_discovered_patterns
        ALTER COLUMN pattern_type TYPE VARCHAR(100)
        USING pattern_type::text
    """
    )
    print("   ✅ Converted pattern_type column back to VARCHAR")

    # Then drop the enum type
    op.execute("DROP TYPE IF EXISTS migration.patterntype CASCADE")
    print("   ✅ Dropped patterntype enum")

    print("✅ Downgrade complete - pattern type enum removed")
