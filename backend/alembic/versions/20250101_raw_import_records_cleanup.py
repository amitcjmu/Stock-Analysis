"""Fix raw_import_records table field names

Revision ID: raw_import_records_cleanup_20250101
Revises: database_consolidation_20250101
Create Date: 2025-01-01 12:30:00.000000

This migration fixes field name mismatches in raw_import_records table:
1. Renames row_number to record_index
2. Renames processed_data to cleansed_data
3. Drops deprecated record_id column
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import logging
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'raw_records_fix_20250101'
down_revision = 'database_consolidation_20250101'
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)


def upgrade():
    """Apply raw_import_records field fixes"""
    logger.info("Starting raw_import_records cleanup migration...")
    
    connection = op.get_bind()
    
    # Helper function to check if column exists
    def column_exists(table_name, column_name):
        result = connection.execute(
            text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = :table_name 
                    AND column_name = :column_name
                )
            """).bindparams(table_name=table_name, column_name=column_name)
        )
        return result.scalar()
    
    # Rename row_number to record_index
    if column_exists('raw_import_records', 'row_number') and not column_exists('raw_import_records', 'record_index'):
        op.alter_column('raw_import_records', 'row_number', new_column_name='record_index')
        logger.info("Renamed raw_import_records.row_number to record_index")
    
    # Rename processed_data to cleansed_data
    if column_exists('raw_import_records', 'processed_data') and not column_exists('raw_import_records', 'cleansed_data'):
        op.alter_column('raw_import_records', 'processed_data', new_column_name='cleansed_data')
        logger.info("Renamed raw_import_records.processed_data to cleansed_data")
    
    # Drop deprecated record_id column
    if column_exists('raw_import_records', 'record_id'):
        try:
            with op.batch_alter_table('raw_import_records') as batch_op:
                batch_op.drop_column('record_id')
            logger.info("Dropped deprecated record_id column from raw_import_records")
        except Exception as e:
            logger.warning(f"Could not drop record_id from raw_import_records: {e}")
    
    logger.info("raw_import_records cleanup migration completed successfully")


def downgrade():
    """Rollback raw_import_records field fixes"""
    logger.info("Rolling back raw_import_records cleanup migration...")
    
    connection = op.get_bind()
    
    # Helper function to check if column exists
    def column_exists(table_name, column_name):
        result = connection.execute(
            text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = :table_name 
                    AND column_name = :column_name
                )
            """).bindparams(table_name=table_name, column_name=column_name)
        )
        return result.scalar()
    
    # Revert field renames
    if column_exists('raw_import_records', 'record_index') and not column_exists('raw_import_records', 'row_number'):
        op.alter_column('raw_import_records', 'record_index', new_column_name='row_number')
        logger.info("Reverted raw_import_records.record_index to row_number")
    
    if column_exists('raw_import_records', 'cleansed_data') and not column_exists('raw_import_records', 'processed_data'):
        op.alter_column('raw_import_records', 'cleansed_data', new_column_name='processed_data')
        logger.info("Reverted raw_import_records.cleansed_data to processed_data")
    
    # Recreate record_id column
    if not column_exists('raw_import_records', 'record_id'):
        try:
            with op.batch_alter_table('raw_import_records') as batch_op:
                batch_op.add_column(sa.Column('record_id', sa.String(255), nullable=True))
            logger.info("Recreated record_id column in raw_import_records")
        except Exception as e:
            logger.warning(f"Could not recreate record_id in raw_import_records: {e}")
    
    logger.info("raw_import_records cleanup rollback completed")