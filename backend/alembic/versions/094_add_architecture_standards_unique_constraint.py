"""Add unique constraint to engagement_architecture_standards

Revision ID: 094_add_architecture_standards_unique_constraint
Revises: 093_assessment_data_model_refactor
Create Date: 2025-10-16

CRITICAL BUG FIX: Adds missing unique constraint required by architecture_commands.py
The save_architecture_standards method uses ON CONFLICT (engagement_id, requirement_type, standard_name)
but the table was missing this constraint, causing 500 errors.

Error message:
  sqlalchemy.dialects.postgresql.asyncpg.ProgrammingError:
  there is no unique or exclusion constraint matching the ON CONFLICT specification
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '094_add_architecture_standards_unique_constraint'
down_revision = '093_assessment_data_model_refactor'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add unique constraint for architecture standards upsert operations"""

    # Add unique constraint on (engagement_id, requirement_type, standard_name)
    # This enables ON CONFLICT DO UPDATE in save_architecture_standards()
    op.execute("""
        DO $$
        BEGIN
            -- Check if constraint already exists
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'uq_engagement_architecture_standards_composite'
            ) THEN
                -- Add unique constraint
                ALTER TABLE migration.engagement_architecture_standards
                ADD CONSTRAINT uq_engagement_architecture_standards_composite
                UNIQUE (engagement_id, requirement_type, standard_name);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """Remove unique constraint"""

    op.execute("""
        DO $$
        BEGIN
            -- Check if constraint exists before dropping
            IF EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'uq_engagement_architecture_standards_composite'
            ) THEN
                -- Drop unique constraint
                ALTER TABLE migration.engagement_architecture_standards
                DROP CONSTRAINT uq_engagement_architecture_standards_composite;
            END IF;
        END $$;
    """)
