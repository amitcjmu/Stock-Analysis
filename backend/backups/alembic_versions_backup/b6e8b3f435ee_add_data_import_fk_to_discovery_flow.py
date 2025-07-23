"""add_data_import_fk_to_discovery_flow

Revision ID: b6e8b3f435ee
Revises: 9d112703d929
Create Date: 2025-06-30 23:36:29.480922

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'b6e8b3f435ee'
down_revision = '9d112703d929'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if the foreign key constraint already exists
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT COUNT(*)
        FROM information_schema.table_constraints
        WHERE constraint_name = 'discovery_flows_data_import_id_fkey'
        AND table_name = 'discovery_flows'
    """))
    constraint_exists = result.scalar() > 0
    
    if not constraint_exists:
        # Add foreign key constraint
        op.create_foreign_key(
            'discovery_flows_data_import_id_fkey',
            'discovery_flows',
            'data_imports',
            ['data_import_id'],
            ['id'],
            ondelete='SET NULL'
        )


def downgrade() -> None:
    # Remove foreign key constraint
    op.drop_constraint('discovery_flows_data_import_id_fkey', 'discovery_flows', type_='foreignkey') 