"""update_existing_tables

Add collection-related columns to adaptive_questionnaires and enrichment tables.
Supports bulk answer storage and import tracking.

Revision ID: 106_update_existing_tables
Revises: 105_collection_background_tasks
Create Date: 2025-10-23 21:34:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "106_update_existing_tables"
down_revision = "105_collection_background_tasks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add columns to adaptive_questionnaires and enrichment tables.

    IDEMPOTENT: Uses IF NOT EXISTS checks for column additions.
    """
    # Update adaptive_questionnaires table
    op.execute(
        """
        DO $$
        BEGIN
            -- Add answers column for bulk answer storage
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'adaptive_questionnaires'
                AND column_name = 'answers'
            ) THEN
                ALTER TABLE migration.adaptive_questionnaires
                ADD COLUMN answers JSONB DEFAULT '{}'::jsonb;

                COMMENT ON COLUMN migration.adaptive_questionnaires.answers IS
                'Stores question_id -> answer_value mapping for quick lookup';
            END IF;

            -- Add closed_questions column
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'adaptive_questionnaires'
                AND column_name = 'closed_questions'
            ) THEN
                ALTER TABLE migration.adaptive_questionnaires
                ADD COLUMN closed_questions JSONB DEFAULT '[]'::jsonb;

                COMMENT ON COLUMN migration.adaptive_questionnaires.closed_questions IS
                'Array of question_ids that have been answered and closed';
            END IF;

            -- Add bulk operation tracking
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'adaptive_questionnaires'
                AND column_name = 'last_bulk_update_at'
            ) THEN
                ALTER TABLE migration.adaptive_questionnaires
                ADD COLUMN last_bulk_update_at TIMESTAMP WITH TIME ZONE;
            END IF;
        END $$;
        """
    )

    # Update application_enrichment table
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'application_enrichment'
            ) THEN
                IF NOT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'migration'
                    AND table_name = 'application_enrichment'
                    AND column_name = 'last_import_source'
                ) THEN
                    ALTER TABLE migration.application_enrichment
                    ADD COLUMN last_import_source VARCHAR(100),
                    ADD COLUMN last_import_batch_id UUID,
                    ADD COLUMN last_import_timestamp TIMESTAMP WITH TIME ZONE;
                END IF;
            END IF;
        END $$;
        """
    )

    # Update server_enrichment table
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'server_enrichment'
            ) THEN
                IF NOT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'migration'
                    AND table_name = 'server_enrichment'
                    AND column_name = 'last_import_source'
                ) THEN
                    ALTER TABLE migration.server_enrichment
                    ADD COLUMN last_import_source VARCHAR(100),
                    ADD COLUMN last_import_batch_id UUID,
                    ADD COLUMN last_import_timestamp TIMESTAMP WITH TIME ZONE;
                END IF;
            END IF;
        END $$;
        """
    )

    # Update database_enrichment table
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'database_enrichment'
            ) THEN
                IF NOT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'migration'
                    AND table_name = 'database_enrichment'
                    AND column_name = 'last_import_source'
                ) THEN
                    ALTER TABLE migration.database_enrichment
                    ADD COLUMN last_import_source VARCHAR(100),
                    ADD COLUMN last_import_batch_id UUID,
                    ADD COLUMN last_import_timestamp TIMESTAMP WITH TIME ZONE;
                END IF;
            END IF;
        END $$;
        """
    )

    # Update network_enrichment table
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'network_enrichment'
            ) THEN
                IF NOT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'migration'
                    AND table_name = 'network_enrichment'
                    AND column_name = 'last_import_source'
                ) THEN
                    ALTER TABLE migration.network_enrichment
                    ADD COLUMN last_import_source VARCHAR(100),
                    ADD COLUMN last_import_batch_id UUID,
                    ADD COLUMN last_import_timestamp TIMESTAMP WITH TIME ZONE;
                END IF;
            END IF;
        END $$;
        """
    )

    # Update storage_enrichment table
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'storage_enrichment'
            ) THEN
                IF NOT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'migration'
                    AND table_name = 'storage_enrichment'
                    AND column_name = 'last_import_source'
                ) THEN
                    ALTER TABLE migration.storage_enrichment
                    ADD COLUMN last_import_source VARCHAR(100),
                    ADD COLUMN last_import_batch_id UUID,
                    ADD COLUMN last_import_timestamp TIMESTAMP WITH TIME ZONE;
                END IF;
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """
    Remove added columns from adaptive_questionnaires and enrichment tables.

    IDEMPOTENT: Uses IF EXISTS checks for column removal.
    """
    # Revert adaptive_questionnaires changes
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'adaptive_questionnaires'
                AND column_name = 'last_bulk_update_at'
            ) THEN
                ALTER TABLE migration.adaptive_questionnaires
                DROP COLUMN last_bulk_update_at;
            END IF;

            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'adaptive_questionnaires'
                AND column_name = 'closed_questions'
            ) THEN
                ALTER TABLE migration.adaptive_questionnaires
                DROP COLUMN closed_questions;
            END IF;

            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'adaptive_questionnaires'
                AND column_name = 'answers'
            ) THEN
                ALTER TABLE migration.adaptive_questionnaires
                DROP COLUMN answers;
            END IF;
        END $$;
        """
    )

    # Revert enrichment table changes (application)
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'application_enrichment'
            ) THEN
                ALTER TABLE migration.application_enrichment
                DROP COLUMN IF EXISTS last_import_timestamp,
                DROP COLUMN IF EXISTS last_import_batch_id,
                DROP COLUMN IF EXISTS last_import_source;
            END IF;
        END $$;
        """
    )

    # Revert enrichment table changes (server)
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'server_enrichment'
            ) THEN
                ALTER TABLE migration.server_enrichment
                DROP COLUMN IF EXISTS last_import_timestamp,
                DROP COLUMN IF EXISTS last_import_batch_id,
                DROP COLUMN IF EXISTS last_import_source;
            END IF;
        END $$;
        """
    )

    # Revert enrichment table changes (database)
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'database_enrichment'
            ) THEN
                ALTER TABLE migration.database_enrichment
                DROP COLUMN IF EXISTS last_import_timestamp,
                DROP COLUMN IF EXISTS last_import_batch_id,
                DROP COLUMN IF EXISTS last_import_source;
            END IF;
        END $$;
        """
    )

    # Revert enrichment table changes (network)
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'network_enrichment'
            ) THEN
                ALTER TABLE migration.network_enrichment
                DROP COLUMN IF EXISTS last_import_timestamp,
                DROP COLUMN IF EXISTS last_import_batch_id,
                DROP COLUMN IF EXISTS last_import_source;
            END IF;
        END $$;
        """
    )

    # Revert enrichment table changes (storage)
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                AND table_name = 'storage_enrichment'
            ) THEN
                ALTER TABLE migration.storage_enrichment
                DROP COLUMN IF EXISTS last_import_timestamp,
                DROP COLUMN IF EXISTS last_import_batch_id,
                DROP COLUMN IF EXISTS last_import_source;
            END IF;
        END $$;
        """
    )
