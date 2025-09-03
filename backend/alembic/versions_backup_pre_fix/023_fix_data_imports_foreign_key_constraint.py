"""Fix data_imports foreign key constraint to allow flow creation

Revision ID: 023_fix_data_imports_foreign_key_constraint
Revises: 022_add_is_admin_to_users
Create Date: 2025-07-28

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "023_fix_data_imports_foreign_key_constraint"
down_revision = "022_add_is_admin_to_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Fix the foreign key constraint on data_imports.master_flow_id"""

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    # Check if the constraint exists before trying to drop it
    constraint_check = (
        op.get_bind()
        .execute(
            sa.text(
                """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.table_constraints
            WHERE table_schema = 'migration'
            AND table_name = 'data_imports'
            AND constraint_name = 'fk_data_imports_master_flow_id_crewai_flow_state_extensions'
        )
    """
            )
        )
        .scalar()
    )

    if constraint_check:
        # Drop the existing foreign key constraint
        op.drop_constraint(
            "fk_data_imports_master_flow_id_crewai_flow_state_extensions",
            "data_imports",
            type_="foreignkey",
            schema="migration",
        )
        print("Dropped existing foreign key constraint on data_imports.master_flow_id")

    # Check if the master_flow_id column allows NULL
    column_nullable = (
        op.get_bind()
        .execute(
            sa.text(
                """
        SELECT is_nullable FROM information_schema.columns
        WHERE table_schema = 'migration'
        AND table_name = 'data_imports'
        AND column_name = 'master_flow_id'
    """
            )
        )
        .scalar()
    )

    if column_nullable == "NO":
        # Make the column nullable to allow data_imports creation without flow  # noqa
        op.alter_column(
            "data_imports", "master_flow_id", nullable=True, schema="migration"
        )
        print("Made data_imports.master_flow_id nullable")

    # Recreate the foreign key constraint as deferrable
    op.execute(
        """
        ALTER TABLE migration.data_imports
        ADD CONSTRAINT fk_data_imports_master_flow_id_crewai_flow_state_extensions
        FOREIGN KEY (master_flow_id)
        REFERENCES migration.crewai_flow_state_extensions(flow_id)
        DEFERRABLE INITIALLY DEFERRED
    """
    )
    print("Created deferrable foreign key constraint on data_imports.master_flow_id")


def downgrade() -> None:
    """Restore the original foreign key constraint"""

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    # Drop the deferrable constraint
    constraint_check = (
        op.get_bind()
        .execute(
            sa.text(
                """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.table_constraints
            WHERE table_schema = 'migration'
            AND table_name = 'data_imports'
            AND constraint_name = 'fk_data_imports_master_flow_id_crewai_flow_state_extensions'
        )
    """
            )
        )
        .scalar()
    )

    if constraint_check:
        op.drop_constraint(
            "fk_data_imports_master_flow_id_crewai_flow_state_extensions",
            "data_imports",
            type_="foreignkey",
            schema="migration",
        )

    # Recreate the original non-deferrable constraint
    op.create_foreign_key(
        "fk_data_imports_master_flow_id_crewai_flow_state_extensions",
        "data_imports",
        "crewai_flow_state_extensions",
        ["master_flow_id"],
        ["flow_id"],
        schema="migration",
    )

    # Make the column non-nullable again (this might fail if there are NULL values)
    try:
        op.alter_column(
            "data_imports", "master_flow_id", nullable=False, schema="migration"
        )
    except Exception as e:
        print(f"Warning: Could not make master_flow_id non-nullable: {e}")
