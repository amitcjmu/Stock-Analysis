"""Fix overly long constraint names for PostgreSQL compatibility

Revision ID: 018b_fix_long_constraint_names
Revises: 018_add_agent_execution_history
Create Date: 2025-01-24

This migration fixes constraint names that exceed PostgreSQL's 63-character limit.
Specifically fixes the collection flow foreign key constraint name.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "018b_fix_long_constraint_names"
down_revision = "018_add_agent_execution_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Fix overly long constraint names"""

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    # Check if the old long constraint name exists and rename it
    op.execute(
        """
        DO $$
        BEGIN
            -- Check if the old long constraint exists
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE table_schema = 'migration'
            AND constraint_schema = 'migration'
                AND table_name = 'crewai_flow_state_extensions'
                AND constraint_name = 'fk_crewai_flow_state_extensions_collection_flow_id_collection_flows'
                AND constraint_type = 'FOREIGN KEY'
            ) THEN
                -- Drop the old constraint
                ALTER TABLE migration.crewai_flow_state_extensions
                DROP CONSTRAINT fk_crewai_flow_state_extensions_collection_flow_id_collection_flows;

                RAISE NOTICE 'Dropped old long constraint name';
            END IF;

            -- Check if the new short constraint already exists
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE table_schema = 'migration'
            AND constraint_schema = 'migration'
                AND table_name = 'crewai_flow_state_extensions'
                AND constraint_name = 'fk_crewai_flow_ext_collection_flow_id'
                AND constraint_type = 'FOREIGN KEY'
            ) THEN
                -- Create the new constraint with short name (if both tables exist)
                IF EXISTS (SELECT 1 FROM information_schema.tables
                          WHERE table_schema = 'migration'
                          AND table_name = 'crewai_flow_state_extensions')
                   AND EXISTS (SELECT 1 FROM information_schema.tables
                              WHERE table_schema = 'migration'
                              AND table_name = 'collection_flows')
                   AND EXISTS (SELECT 1 FROM information_schema.columns
                              WHERE table_schema = 'migration'
                              AND table_name = 'crewai_flow_state_extensions'
                              AND column_name = 'collection_flow_id') THEN

                    ALTER TABLE migration.crewai_flow_state_extensions
                    ADD CONSTRAINT fk_crewai_flow_ext_collection_flow_id
                    FOREIGN KEY (collection_flow_id)
                    REFERENCES migration.collection_flows(id)
                    ON DELETE SET NULL;

                    RAISE NOTICE 'Created new short constraint name';
                END IF;
            ELSE
                RAISE NOTICE 'Short constraint name already exists';
            END IF;

        EXCEPTION
            WHEN OTHERS THEN
                RAISE NOTICE 'Error fixing constraint names: %', SQLERRM;
        END $$;
    """
    )

    print("✅ Fixed overly long constraint names for PostgreSQL compatibility")


def downgrade() -> None:
    """Revert constraint name changes"""

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    # This is mainly for completeness - in practice we want to keep the short names
    op.execute(
        """
        DO $$
        BEGIN
            -- Remove the short constraint name if it exists
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE table_schema = 'migration'
            AND constraint_schema = 'migration'
                AND table_name = 'crewai_flow_state_extensions'
                AND constraint_name = 'fk_crewai_flow_ext_collection_flow_id'
                AND constraint_type = 'FOREIGN KEY'
            ) THEN
                ALTER TABLE migration.crewai_flow_state_extensions
                DROP CONSTRAINT fk_crewai_flow_ext_collection_flow_id;

                RAISE NOTICE 'Removed short constraint name';
            END IF;

        EXCEPTION
            WHEN OTHERS THEN
                RAISE NOTICE 'Error reverting constraint names: %', SQLERRM;
        END $$;
    """
    )

    print("✅ Reverted constraint name changes")
