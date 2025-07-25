"""Add updated_at column to collection_data_gaps table

Revision ID: 011_add_updated_at_to_collection_data_gaps
Revises: 010_add_timestamp_columns_to_collected_data_inventory
Create Date: 2025-07-21 03:30:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "011_add_updated_at_to_collection_data_gaps"
down_revision = "010_add_timestamp_columns_to_collected_data_inventory"
branch_labels = None
depends_on = None


def upgrade():
    """Add updated_at column to collection_data_gaps table"""
    conn = op.get_bind()
    
    # Add updated_at column to collection_data_gaps table if it doesn't exist
    result = conn.execute(
        sa.text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'migration'
            AND table_name = 'collection_data_gaps' 
            AND column_name = 'updated_at'
        """)
    )
    if not result.fetchone():
        op.add_column(
            "collection_data_gaps",
            sa.Column(
                "updated_at",
                sa.TIMESTAMP(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )

    # Create trigger to automatically update updated_at timestamp
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """
    )

    # Check if trigger exists before creating
    result = conn.execute(
        sa.text("""
            SELECT trigger_name 
            FROM information_schema.triggers 
            WHERE trigger_schema = 'migration'
            AND event_object_schema = 'migration'
            AND event_object_table = 'collection_data_gaps'
            AND trigger_name = 'update_collection_data_gaps_updated_at'
        """)
    )
    if not result.fetchone():
        op.execute(
            """
            CREATE TRIGGER update_collection_data_gaps_updated_at
            BEFORE UPDATE ON collection_data_gaps
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """
        )


def downgrade():
    """Remove updated_at column from collection_data_gaps table"""
    # Drop the trigger first
    op.execute(
        "DROP TRIGGER IF EXISTS update_collection_data_gaps_updated_at ON collection_data_gaps;"
    )

    # Drop the function if no other tables are using it
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")

    # Drop the updated_at column
    op.drop_column("collection_data_gaps", "updated_at")
