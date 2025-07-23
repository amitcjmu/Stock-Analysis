"""Add updated_at column to collection_data_gaps table

Revision ID: 011_add_updated_at_to_collection_data_gaps
Revises: 010_add_timestamp_columns_to_collected_data_inventory
Create Date: 2025-07-21 03:30:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '011_add_updated_at_to_collection_data_gaps'
down_revision = '010_add_timestamp_columns_to_collected_data_inventory'
branch_labels = None
depends_on = None


def upgrade():
    """Add updated_at column to collection_data_gaps table"""
    # Add updated_at column to collection_data_gaps table
    op.add_column('collection_data_gaps', 
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), 
                  server_default=sa.text('now()'), nullable=False)
    )
    
    # Create trigger to automatically update updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    op.execute("""
        CREATE TRIGGER update_collection_data_gaps_updated_at
        BEFORE UPDATE ON collection_data_gaps
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade():
    """Remove updated_at column from collection_data_gaps table"""
    # Drop the trigger first
    op.execute("DROP TRIGGER IF EXISTS update_collection_data_gaps_updated_at ON collection_data_gaps;")
    
    # Drop the function if no other tables are using it
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
    
    # Drop the updated_at column
    op.drop_column('collection_data_gaps', 'updated_at')