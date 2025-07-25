"""Add timestamp columns to collected_data_inventory table

Revision ID: 010_add_timestamp_columns_to_collected_data_inventory
Revises: 009_add_collection_flow_id_to_questionnaires
Create Date: 2025-07-21

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "010_add_timestamp_columns_to_collected_data_inventory"
down_revision = "009_add_collection_flow_id_to_questionnaires"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    
    # Add created_at column to collected_data_inventory table if it doesn't exist
    result = conn.execute(
        sa.text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'migration'
            AND table_name = 'collected_data_inventory' 
            AND column_name = 'created_at'
        """)
    )
    if not result.fetchone():
        op.add_column(
            "collected_data_inventory",
            sa.Column(
                "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
            ),
        )

    # Add updated_at column to collected_data_inventory table if it doesn't exist
    result = conn.execute(
        sa.text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'migration'
            AND table_name = 'collected_data_inventory' 
            AND column_name = 'updated_at'
        """)
    )
    if not result.fetchone():
        op.add_column(
            "collected_data_inventory",
            sa.Column(
                "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
            ),
        )


def downgrade() -> None:
    # Drop updated_at column from collected_data_inventory table
    op.drop_column("collected_data_inventory", "updated_at")

    # Drop created_at column from collected_data_inventory table
    op.drop_column("collected_data_inventory", "created_at")
