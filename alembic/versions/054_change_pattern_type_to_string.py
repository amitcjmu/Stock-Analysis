"""054_change_pattern_type_to_string

Revision ID: 054_change_pattern_type_to_string
Revises: 053_add_assessment_transition_tracking
Create Date: 2025-09-06

Purpose:
    Change pattern_type column from enum to string(100) to match SQLAlchemy model.
    This fixes the issue where the model expects a string but the database has an enum.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '054_change_pattern_type_to_string'
down_revision = '67da5e784e40'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Change pattern_type from enum to string(100) to match SQLAlchemy model.
    This is done safely with a temporary column to preserve data.
    """

    # Check if the column already is a string type (idempotent check)
    connection = op.get_bind()
    result = connection.execute(text("""
        SELECT data_type
        FROM information_schema.columns
        WHERE table_schema = 'migration'
        AND table_name = 'agent_discovered_patterns'
        AND column_name = 'pattern_type';
    """)).fetchone()

    if result and result[0] == 'character varying':
        print("Column pattern_type is already a string type, skipping migration")
        return

    # Create a temporary column with the string type
    op.add_column('agent_discovered_patterns',
                  sa.Column('pattern_type_new', sa.String(100), nullable=True),
                  schema='migration')

    # Copy the enum values to the new column as strings
    op.execute("""
        UPDATE migration.agent_discovered_patterns
        SET pattern_type_new = pattern_type::text
        WHERE pattern_type IS NOT NULL;
    """)

    # Drop the index on the old column
    op.drop_index('ix_agent_discovered_patterns_pattern_type',
                  table_name='agent_discovered_patterns',
                  schema='migration',
                  if_exists=True)

    # Drop the old enum column
    op.drop_column('agent_discovered_patterns', 'pattern_type', schema='migration')

    # Rename the new column to pattern_type
    op.alter_column('agent_discovered_patterns', 'pattern_type_new',
                    new_column_name='pattern_type',
                    schema='migration')

    # Make it not nullable with the same constraints as before
    op.alter_column('agent_discovered_patterns', 'pattern_type',
                    nullable=False,
                    schema='migration')

    # Recreate the index
    op.create_index('ix_agent_discovered_patterns_pattern_type',
                    'agent_discovered_patterns', ['pattern_type'],
                    schema='migration')

    print("Successfully converted pattern_type from enum to string(100)")


def downgrade() -> None:
    """
    Revert pattern_type back to enum type.
    This recreates the enum with all known values.
    """

    # Check if already an enum (idempotent check)
    connection = op.get_bind()
    result = connection.execute(text("""
        SELECT data_type
        FROM information_schema.columns
        WHERE table_schema = 'migration'
        AND table_name = 'agent_discovered_patterns'
        AND column_name = 'pattern_type';
    """)).fetchone()

    if result and result[0] == 'USER-DEFINED':
        print("Column pattern_type is already an enum type, skipping downgrade")
        return

    # Drop the index
    op.drop_index('ix_agent_discovered_patterns_pattern_type',
                  table_name='agent_discovered_patterns',
                  schema='migration',
                  if_exists=True)

    # Create the enum type if it doesn't exist
    patterntype_enum = postgresql.ENUM(
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
        'field_mapping_suggestion',
        name='patterntype',
        schema='migration'
    )

    # Create enum type in database if it doesn't exist
    patterntype_enum.create(op.get_bind(), checkfirst=True)

    # Add temporary enum column
    op.add_column('agent_discovered_patterns',
                  sa.Column('pattern_type_enum',
                           patterntype_enum,
                           nullable=True),
                  schema='migration')

    # Copy string values back to enum, handling any invalid values
    op.execute("""
        UPDATE migration.agent_discovered_patterns
        SET pattern_type_enum = CASE
            WHEN pattern_type IN (
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
            ) THEN pattern_type::migration.patterntype
            ELSE 'technology_correlation'::migration.patterntype  -- Default fallback
        END;
    """)

    # Drop the string column
    op.drop_column('agent_discovered_patterns', 'pattern_type', schema='migration')

    # Rename enum column back
    op.alter_column('agent_discovered_patterns', 'pattern_type_enum',
                    new_column_name='pattern_type',
                    schema='migration')

    # Make it not nullable
    op.alter_column('agent_discovered_patterns', 'pattern_type',
                    nullable=False,
                    schema='migration')

    # Recreate the index
    op.create_index('ix_agent_discovered_patterns_pattern_type',
                    'agent_discovered_patterns', ['pattern_type'],
                    schema='migration')

    print("Successfully reverted pattern_type to enum type")
