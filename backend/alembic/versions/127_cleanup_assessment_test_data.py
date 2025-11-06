"""cleanup assessment test data and add constraint

Revision ID: 127_cleanup_assessment_test_data
Revises: 120_create_decommission_tables
Create Date: 2025-11-06

Per issue #962: Clean test data pollution and prevent future test errors in phase_results
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "127_cleanup_assessment_test_data"
down_revision = "120_create_decommission_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    1. Clean test data from phase_results in assessment_flows table
    2. Add CHECK constraint to prevent "Test error" strings in future
    3. Make idempotent with existence checks
    """

    # Use PostgreSQL DO block for idempotent operations
    op.execute(
        """
        DO $$
        BEGIN
            -- Clean existing test data from phase_results
            -- Remove any phase_results entries containing "Test error" string
            UPDATE migration.assessment_flows
            SET phase_results = (
                SELECT jsonb_object_agg(key, value)
                FROM jsonb_each(phase_results)
                WHERE NOT (value::text LIKE '%Test error%')
            )
            WHERE phase_results IS NOT NULL
              AND phase_results::text LIKE '%Test error%';

            RAISE NOTICE 'Cleaned test data from assessment_flows.phase_results';

        EXCEPTION
            WHEN OTHERS THEN
                RAISE NOTICE 'Test data cleanup failed (may be expected if no data exists): %', SQLERRM;
        END $$;
    """
    )

    # Add CHECK constraint to prevent future test data pollution
    # Note: CHECK constraints in PostgreSQL don't support JSONB text search directly
    # Instead, we'll add a validation trigger
    op.execute(
        """
        DO $$
        BEGIN
            -- Create validation function if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM pg_proc WHERE proname = 'validate_no_test_errors_in_phase_results'
            ) THEN
                CREATE OR REPLACE FUNCTION migration.validate_no_test_errors_in_phase_results()
                RETURNS TRIGGER AS $func$
                BEGIN
                    -- Prevent insertion/update of phase_results containing "Test error"
                    IF NEW.phase_results IS NOT NULL
                       AND NEW.phase_results::text LIKE '%Test error%' THEN
                        RAISE EXCEPTION
                            'phase_results contains test error data. This is not allowed in production. '
                            'Found in flow_id: %', NEW.id
                        USING ERRCODE = '23514',  -- check_violation
                              HINT = 'Remove "Test error" strings from phase_results before saving';
                    END IF;
                    RETURN NEW;
                END;
                $func$ LANGUAGE plpgsql;

                RAISE NOTICE 'Created validation function validate_no_test_errors_in_phase_results';
            END IF;

            -- Create trigger if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM pg_trigger
                WHERE tgname = 'prevent_test_errors_in_phase_results'
                  AND tgrelid = 'migration.assessment_flows'::regclass
            ) THEN
                CREATE TRIGGER prevent_test_errors_in_phase_results
                    BEFORE INSERT OR UPDATE OF phase_results
                    ON migration.assessment_flows
                    FOR EACH ROW
                    EXECUTE FUNCTION migration.validate_no_test_errors_in_phase_results();

                RAISE NOTICE 'Created trigger prevent_test_errors_in_phase_results';
            END IF;

        EXCEPTION
            WHEN OTHERS THEN
                RAISE NOTICE 'Constraint creation failed: %', SQLERRM;
        END $$;
    """
    )


def downgrade() -> None:
    """
    Remove validation trigger and function
    Note: Does not restore cleaned test data (intentional - we don't want test data back)
    """

    op.execute(
        """
        DO $$
        BEGIN
            -- Drop trigger if exists
            IF EXISTS (
                SELECT 1 FROM pg_trigger
                WHERE tgname = 'prevent_test_errors_in_phase_results'
                  AND tgrelid = 'migration.assessment_flows'::regclass
            ) THEN
                DROP TRIGGER prevent_test_errors_in_phase_results
                    ON migration.assessment_flows;

                RAISE NOTICE 'Dropped trigger prevent_test_errors_in_phase_results';
            END IF;

            -- Drop function if exists
            IF EXISTS (
                SELECT 1 FROM pg_proc WHERE proname = 'validate_no_test_errors_in_phase_results'
            ) THEN
                DROP FUNCTION IF EXISTS migration.validate_no_test_errors_in_phase_results();

                RAISE NOTICE 'Dropped function validate_no_test_errors_in_phase_results';
            END IF;

        EXCEPTION
            WHEN OTHERS THEN
                RAISE NOTICE 'Constraint removal failed: %', SQLERRM;
        END $$;
    """
    )
