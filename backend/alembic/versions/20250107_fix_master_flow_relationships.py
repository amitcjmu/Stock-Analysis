"""Fix Master Flow Relationships - Foreign Key Corrections

This migration fixes foreign key references in DataImport, RawImportRecord, and 
DiscoveryFlow models to properly reference crewai_flow_state_extensions.flow_id 
instead of crewai_flow_state_extensions.id for proper flow coordination.

Revision ID: 20250107_fix_master_flow_relationships
Revises: master_flow_orchestrator_001
Create Date: 2025-01-07 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '20250107_fix_master_flow_relationships'
down_revision = 'master_flow_orchestrator_001'
branch_labels = None
depends_on = None


def upgrade():
    """Fix foreign key references to use crewai_flow_state_extensions.flow_id"""
    
    # 1. Fix DataImport model foreign key reference
    print("Fixing DataImport master_flow_id foreign key reference...")
    
    # Drop existing foreign key constraint if it exists
    try:
        op.drop_constraint('data_imports_master_flow_id_fkey', 'data_imports', type_='foreignkey')
    except Exception as e:
        print(f"No existing foreign key constraint to drop for data_imports: {e}")
    
    # Create new foreign key constraint pointing to flow_id
    op.create_foreign_key(
        'fk_data_imports_master_flow_id',
        'data_imports', 
        'crewai_flow_state_extensions',
        ['master_flow_id'], 
        ['flow_id'],
        ondelete='CASCADE'
    )
    
    # 2. Fix RawImportRecord model foreign key reference
    print("Fixing RawImportRecord master_flow_id foreign key reference...")
    
    # Drop existing foreign key constraint if it exists
    try:
        op.drop_constraint('raw_import_records_master_flow_id_fkey', 'raw_import_records', type_='foreignkey')
    except Exception as e:
        print(f"No existing foreign key constraint to drop for raw_import_records: {e}")
    
    # Create new foreign key constraint pointing to flow_id
    op.create_foreign_key(
        'fk_raw_import_records_master_flow_id',
        'raw_import_records', 
        'crewai_flow_state_extensions',
        ['master_flow_id'], 
        ['flow_id'],
        ondelete='CASCADE'
    )
    
    # 3. Fix DiscoveryFlow model - add missing foreign key constraint
    print("Adding missing foreign key constraint for DiscoveryFlow master_flow_id...")
    
    # Drop existing foreign key constraint if it exists
    try:
        op.drop_constraint('discovery_flows_master_flow_id_fkey', 'discovery_flows', type_='foreignkey')
    except Exception as e:
        print(f"No existing foreign key constraint to drop for discovery_flows: {e}")
    
    # Create new foreign key constraint pointing to flow_id
    op.create_foreign_key(
        'fk_discovery_flows_master_flow_id',
        'discovery_flows', 
        'crewai_flow_state_extensions',
        ['master_flow_id'], 
        ['flow_id'],
        ondelete='CASCADE'
    )
    
    # 4. Update any orphaned records (safety measure)
    print("Checking for orphaned records and cleaning up...")
    
    connection = op.get_bind()
    
    # Update data_imports with null master_flow_id for orphaned records
    connection.execute(text("""
        UPDATE data_imports 
        SET master_flow_id = NULL 
        WHERE master_flow_id IS NOT NULL 
        AND master_flow_id NOT IN (
            SELECT flow_id FROM crewai_flow_state_extensions
        )
    """))
    
    # Update raw_import_records with null master_flow_id for orphaned records
    connection.execute(text("""
        UPDATE raw_import_records 
        SET master_flow_id = NULL 
        WHERE master_flow_id IS NOT NULL 
        AND master_flow_id NOT IN (
            SELECT flow_id FROM crewai_flow_state_extensions
        )
    """))
    
    # Update discovery_flows with null master_flow_id for orphaned records
    connection.execute(text("""
        UPDATE discovery_flows 
        SET master_flow_id = NULL 
        WHERE master_flow_id IS NOT NULL 
        AND master_flow_id NOT IN (
            SELECT flow_id FROM crewai_flow_state_extensions
        )
    """))
    
    # 5. Add performance indexes for the new foreign key relationships
    print("Adding performance indexes...")
    
    # Index for data_imports.master_flow_id
    try:
        op.create_index('idx_data_imports_master_flow_id', 'data_imports', ['master_flow_id'])
    except Exception as e:
        print(f"Index already exists or error creating: {e}")
    
    # Index for raw_import_records.master_flow_id
    try:
        op.create_index('idx_raw_import_records_master_flow_id', 'raw_import_records', ['master_flow_id'])
    except Exception as e:
        print(f"Index already exists or error creating: {e}")
    
    # Index for discovery_flows.master_flow_id
    try:
        op.create_index('idx_discovery_flows_master_flow_id', 'discovery_flows', ['master_flow_id'])
    except Exception as e:
        print(f"Index already exists or error creating: {e}")
    
    # 6. Add CHECK constraint to ensure data integrity
    print("Adding data integrity constraints...")
    
    # Ensure master_flow_id values are valid UUIDs when not null
    try:
        op.create_check_constraint(
            'chk_data_imports_master_flow_id_valid',
            'data_imports',
            'master_flow_id IS NULL OR master_flow_id ~ \'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$\''
        )
    except Exception as e:
        print(f"Check constraint already exists or error creating: {e}")
    
    print("Master flow relationship fixes completed successfully!")


def downgrade():
    """Revert foreign key references back to crewai_flow_state_extensions.id"""
    
    print("Reverting master flow relationship fixes...")
    
    # Drop CHECK constraints
    try:
        op.drop_constraint('chk_data_imports_master_flow_id_valid', 'data_imports')
    except Exception as e:
        print(f"No check constraint to drop: {e}")
    
    # Drop performance indexes
    try:
        op.drop_index('idx_discovery_flows_master_flow_id', 'discovery_flows')
    except Exception as e:
        print(f"No index to drop: {e}")
    
    try:
        op.drop_index('idx_raw_import_records_master_flow_id', 'raw_import_records')
    except Exception as e:
        print(f"No index to drop: {e}")
    
    try:
        op.drop_index('idx_data_imports_master_flow_id', 'data_imports')
    except Exception as e:
        print(f"No index to drop: {e}")
    
    # Drop new foreign key constraints
    try:
        op.drop_constraint('fk_discovery_flows_master_flow_id', 'discovery_flows', type_='foreignkey')
    except Exception as e:
        print(f"No foreign key constraint to drop: {e}")
    
    try:
        op.drop_constraint('fk_raw_import_records_master_flow_id', 'raw_import_records', type_='foreignkey')
    except Exception as e:
        print(f"No foreign key constraint to drop: {e}")
    
    try:
        op.drop_constraint('fk_data_imports_master_flow_id', 'data_imports', type_='foreignkey')
    except Exception as e:
        print(f"No foreign key constraint to drop: {e}")
    
    # Re-create old foreign key constraints (pointing to .id instead of .flow_id)
    # Note: This is not recommended but provided for rollback safety
    
    # DataImport - back to .id reference
    try:
        op.create_foreign_key(
            'data_imports_master_flow_id_fkey',
            'data_imports', 
            'crewai_flow_state_extensions',
            ['master_flow_id'], 
            ['id'],
            ondelete='CASCADE'
        )
    except Exception as e:
        print(f"Error re-creating old foreign key: {e}")
    
    # RawImportRecord - back to .id reference
    try:
        op.create_foreign_key(
            'raw_import_records_master_flow_id_fkey',
            'raw_import_records', 
            'crewai_flow_state_extensions',
            ['master_flow_id'], 
            ['id'],
            ondelete='CASCADE'
        )
    except Exception as e:
        print(f"Error re-creating old foreign key: {e}")
    
    # DiscoveryFlow - remove foreign key constraint (back to original state)
    # No action needed as original didn't have foreign key constraint
    
    print("Master flow relationship fixes reverted!")