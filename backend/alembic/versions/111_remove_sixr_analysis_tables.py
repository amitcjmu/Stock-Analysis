"""
Remove deprecated 6R Analysis tables.

All 6R recommendations now use Assessment Flow with MFO integration.
Tables to drop: sixr_analyses, sixr_iterations, sixr_recommendations,
                sixr_analysis_parameters, sixr_qualifying_questions,
                sixr_question_responses, sixr_parameters, sixr_questions

Revision ID: 111
Revises: 110
Create Date: 2025-10-28

Assessment Flow MFO Migration Phase 4 (Issue #840)
"""

from alembic import op
import logging

# revision identifiers, used by Alembic.
revision = "111_remove_sixr_analysis_tables"
down_revision = "110_add_tenant_fields_to_asset_dependencies"
branch_labels = None
depends_on = None

logger = logging.getLogger("alembic")


def upgrade():
    """Drop deprecated 6R Analysis tables and archive data."""
    logger.info("Starting migration 111: Remove deprecated 6R Analysis tables")

    # Archive data before dropping tables
    logger.info("Step 1: Creating archive tables for historical reference...")

    # Archive main tables with idempotent checks
    op.execute(
        """
        DO $$
        BEGIN
            -- Archive sixr_analyses
            IF EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'sixr_analyses'
            ) THEN
                EXECUTE '
                    CREATE TABLE IF NOT EXISTS migration.sixr_analyses_archive AS
                    SELECT * FROM migration.sixr_analyses
                ';
                RAISE NOTICE 'Created sixr_analyses_archive table';
            ELSE
                RAISE NOTICE 'sixr_analyses table does not exist, skipping archive';
            END IF;

            -- Archive sixr_iterations
            IF EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'sixr_iterations'
            ) THEN
                EXECUTE '
                    CREATE TABLE IF NOT EXISTS migration.sixr_iterations_archive AS
                    SELECT * FROM migration.sixr_iterations
                ';
                RAISE NOTICE 'Created sixr_iterations_archive table';
            ELSE
                RAISE NOTICE 'sixr_iterations table does not exist, skipping archive';
            END IF;

            -- Archive sixr_recommendations
            IF EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'sixr_recommendations'
            ) THEN
                EXECUTE '
                    CREATE TABLE IF NOT EXISTS migration.sixr_recommendations_archive AS
                    SELECT * FROM migration.sixr_recommendations
                ';
                RAISE NOTICE 'Created sixr_recommendations_archive table';
            ELSE
                RAISE NOTICE 'sixr_recommendations table does not exist, skipping archive';
            END IF;
        END $$;
    """
    )

    logger.info("Step 2: Dropping deprecated 6R Analysis tables...")

    # Drop tables in correct order (respect foreign keys)
    # Child tables first, then parent tables
    op.execute(
        """
        DO $$
        BEGIN
            -- Drop sixr_iterations (references sixr_analyses)
            IF EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'sixr_iterations'
            ) THEN
                DROP TABLE migration.sixr_iterations CASCADE;
                RAISE NOTICE 'Dropped table: sixr_iterations';
            ELSE
                RAISE NOTICE 'Table sixr_iterations does not exist, skipping';
            END IF;

            -- Drop sixr_recommendations (references sixr_analyses)
            IF EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'sixr_recommendations'
            ) THEN
                DROP TABLE migration.sixr_recommendations CASCADE;
                RAISE NOTICE 'Dropped table: sixr_recommendations';
            ELSE
                RAISE NOTICE 'Table sixr_recommendations does not exist, skipping';
            END IF;

            -- Drop sixr_analysis_parameters (references sixr_iterations)
            IF EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'sixr_analysis_parameters'
            ) THEN
                DROP TABLE migration.sixr_analysis_parameters CASCADE;
                RAISE NOTICE 'Dropped table: sixr_analysis_parameters';
            ELSE
                RAISE NOTICE 'Table sixr_analysis_parameters does not exist, skipping';
            END IF;

            -- Drop sixr_question_responses
            IF EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'sixr_question_responses'
            ) THEN
                DROP TABLE migration.sixr_question_responses CASCADE;
                RAISE NOTICE 'Dropped table: sixr_question_responses';
            ELSE
                RAISE NOTICE 'Table sixr_question_responses does not exist, skipping';
            END IF;

            -- Drop sixr_qualifying_questions
            IF EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'sixr_qualifying_questions'
            ) THEN
                DROP TABLE migration.sixr_qualifying_questions CASCADE;
                RAISE NOTICE 'Dropped table: sixr_qualifying_questions';
            ELSE
                RAISE NOTICE 'Table sixr_qualifying_questions does not exist, skipping';
            END IF;

            -- Drop sixr_questions (master list)
            IF EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'sixr_questions'
            ) THEN
                DROP TABLE migration.sixr_questions CASCADE;
                RAISE NOTICE 'Dropped table: sixr_questions';
            ELSE
                RAISE NOTICE 'Table sixr_questions does not exist, skipping';
            END IF;

            -- Drop sixr_parameters (global config)
            IF EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'sixr_parameters'
            ) THEN
                DROP TABLE migration.sixr_parameters CASCADE;
                RAISE NOTICE 'Dropped table: sixr_parameters';
            ELSE
                RAISE NOTICE 'Table sixr_parameters does not exist, skipping';
            END IF;

            -- Drop sixr_analyses (parent table - last)
            IF EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'sixr_analyses'
            ) THEN
                DROP TABLE migration.sixr_analyses CASCADE;
                RAISE NOTICE 'Dropped table: sixr_analyses';
            ELSE
                RAISE NOTICE 'Table sixr_analyses does not exist, skipping';
            END IF;
        END $$;
    """
    )

    logger.info("✅ Migration 111 complete: All deprecated 6R Analysis tables removed")
    logger.info("   Historical data preserved in *_archive tables")
    logger.info(
        "   Use Assessment Flow endpoints at /assessment-flow/* for 6R recommendations"
    )


def downgrade():
    """
    Downgrade not supported - this is a one-way migration.

    Historical data is preserved in archive tables:
    - migration.sixr_analyses_archive
    - migration.sixr_iterations_archive
    - migration.sixr_recommendations_archive

    Use Assessment Flow going forward.
    """
    raise NotImplementedError(
        "Downgrade not supported for migration 111. "
        "6R Analysis tables have been permanently removed. "
        "Use Assessment Flow with MFO integration for all 6R recommendations. "
        "Historical data available in *_archive tables."
    )
