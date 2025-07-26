"""add_auto_generated_uuid_to_raw_import_records

Revision ID: 595ea1f47121
Revises: 019_implement_row_level_security
Create Date: 2025-07-26 01:30:36.687327

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "595ea1f47121"
down_revision = "019_implement_row_level_security"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if table and column exist before altering
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns
                      WHERE table_name = 'raw_import_records' AND column_name = 'id') THEN
                ALTER TABLE raw_import_records ALTER COLUMN id SET DEFAULT gen_random_uuid();
            END IF;
        END $$;
    """
    )


def downgrade() -> None:
    # Check if table and column exist before altering
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns
                      WHERE table_name = 'raw_import_records' AND column_name = 'id') THEN
                ALTER TABLE raw_import_records ALTER COLUMN id DROP DEFAULT;
            END IF;
        END $$;
    """
    )
