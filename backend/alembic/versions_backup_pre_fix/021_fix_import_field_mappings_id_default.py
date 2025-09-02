"""Fix missing default UUID generation for import_field_mappings.id

Revision ID: 021_fix_import_field_mappings_id_default
Revises: 595ea1f47121
Create Date: 2025-07-28

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "021_fix_import_field_mappings_id_default"
down_revision = "595ea1f47121"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add default UUID generation to import_field_mappings.id column"""

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    # Add default value for id column using gen_random_uuid()
    op.execute(
        """
        ALTER TABLE import_field_mappings
        ALTER COLUMN id SET DEFAULT gen_random_uuid()
    """
    )

    print("Added UUID generation default to import_field_mappings.id")


def downgrade() -> None:
    """Remove default UUID generation from import_field_mappings.id column"""

    # Set schema search path
    op.execute("SET search_path TO migration, public")

    # Remove default value
    op.execute(
        """
        ALTER TABLE import_field_mappings
        ALTER COLUMN id DROP DEFAULT
    """
    )

    print("Removed UUID generation default from import_field_mappings.id")
