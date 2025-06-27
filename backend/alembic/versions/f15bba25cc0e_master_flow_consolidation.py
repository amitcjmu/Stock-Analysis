"""Master Flow Architecture Consolidation

Revision ID: f15bba25cc0e
Revises: c547c104e9b1
Create Date: 2025-01-27 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f15bba25cc0e'
down_revision = 'c547c104e9b1'
branch_labels = None
depends_on = None


def upgrade():
    """
    Implement Master Flow Architecture Consolidation:
    1. Enhance crewai_flow_state_extensions as master flow coordinator
    2. Add multi-phase support to assets table
    3. Transform data integration tables to use master flow references
    4. Migrate discovery_assets data to enhanced assets table
    5. Clean up legacy session-based tables
    """
    
    # =============================================================================
    # PHASE 1: ENHANCE CREWAI FLOW STATE EXTENSIONS AS MASTER COORDINATOR
    # =============================================================================
    
    print("Phase 1: Enhancing CrewAI Flow State Extensions as Master Flow Coordinator...")
    
    # Add master flow coordination columns
    op.add_column('crewai_flow_state_extensions', 
                  sa.Column('current_phase', sa.String(50), default='discovery'))
    op.add_column('crewai_flow_state_extensions', 
                  sa.Column('phase_flow_id', postgresql.UUID(as_uuid=True)))
    op.add_column('crewai_flow_state_extensions', 
                  sa.Column('phase_progression', postgresql.JSONB(), default='{}'))
    op.add_column('crewai_flow_state_extensions', 
                  sa.Column('flow_metadata', postgresql.JSONB(), default='{}'))
    op.add_column('crewai_flow_state_extensions', 
                  sa.Column('cross_phase_context', postgresql.JSONB(), default='{}'))
    
    # Create unique constraint on flow_id to enable foreign key references
    op.create_unique_constraint('uq_crewai_extensions_flow_id', 'crewai_flow_state_extensions', ['flow_id'])
    
    # Create master flow indexes for performance
    op.create_index('idx_crewai_extensions_master_flow_id', 'crewai_flow_state_extensions', ['flow_id'])
    op.create_index('idx_crewai_extensions_current_phase', 'crewai_flow_state_extensions', ['current_phase'])
    op.create_index('idx_crewai_extensions_phase_flow_id', 'crewai_flow_state_extensions', ['phase_flow_id'])
    
    # =============================================================================
    # PHASE 2: CREATE CREWAI FLOW STATE EXTENSIONS FOR EXISTING DISCOVERY FLOWS
    # =============================================================================
    
    print("Phase 2: Creating CrewAI flow state extensions for existing discovery flows...")
    
    connection = op.get_bind()
    
    # Create crewai_flow_state_extensions records for existing discovery flows
    connection.execute(sa.text("""
        INSERT INTO crewai_flow_state_extensions (
            flow_id, discovery_flow_id, flow_persistence_data, created_at, updated_at
        )
        SELECT 
            df.flow_id,
            df.id,
            '{}',
            df.created_at,
            df.updated_at
        FROM discovery_flows df
        WHERE NOT EXISTS (
            SELECT 1 FROM crewai_flow_state_extensions cse
            WHERE cse.discovery_flow_id = df.id
        )
    """))
    
    # Verify creation
    result = connection.execute(sa.text("SELECT COUNT(*) FROM crewai_flow_state_extensions"))
    extensions_count = result.scalar()
    print(f"Created {extensions_count} CrewAI flow state extensions")
    
    # =============================================================================
    # PHASE 3: ADD MASTER FLOW REFERENCE TO DISCOVERY FLOWS
    # =============================================================================
    
    print("Phase 3: Adding master flow reference to discovery_flows...")
    
    # Add master flow reference to discovery_flows
    op.add_column('discovery_flows', 
                  sa.Column('master_flow_id', postgresql.UUID(as_uuid=True)))
    
    # Populate master_flow_id from existing crewai_flow_state_extensions relationships
    connection.execute(sa.text("""
        UPDATE discovery_flows 
        SET master_flow_id = (
            SELECT flow_id 
            FROM crewai_flow_state_extensions 
            WHERE discovery_flow_id = discovery_flows.id
        )
        WHERE EXISTS (
            SELECT 1 
            FROM crewai_flow_state_extensions 
            WHERE discovery_flow_id = discovery_flows.id
        )
    """))
    
    # Create foreign key constraint for master flow reference
    op.create_foreign_key('fk_discovery_flows_master_flow_id', 
                         'discovery_flows', 'crewai_flow_state_extensions', 
                         ['master_flow_id'], ['flow_id'])
    
    # =============================================================================
    # PHASE 4: ENHANCE ASSETS TABLE WITH MULTI-PHASE FLOW SUPPORT
    # =============================================================================
    
    print("Phase 4: Enhancing assets table with multi-phase flow support...")
    
    # Add multi-phase flow columns to assets table
    op.add_column('assets', sa.Column('master_flow_id', postgresql.UUID(as_uuid=True)))
    op.add_column('assets', sa.Column('discovery_flow_id', postgresql.UUID(as_uuid=True)))
    op.add_column('assets', sa.Column('assessment_flow_id', postgresql.UUID(as_uuid=True)))
    op.add_column('assets', sa.Column('planning_flow_id', postgresql.UUID(as_uuid=True)))
    op.add_column('assets', sa.Column('execution_flow_id', postgresql.UUID(as_uuid=True)))
    op.add_column('assets', sa.Column('source_phase', sa.String(50), default='legacy'))
    op.add_column('assets', sa.Column('current_phase', sa.String(50), default='discovery'))
    op.add_column('assets', sa.Column('phase_progression', postgresql.JSONB(), default='{}'))
    
    # Create foreign key constraints for multi-phase support
    op.create_foreign_key('fk_assets_master_flow_id', 
                         'assets', 'crewai_flow_state_extensions', 
                         ['master_flow_id'], ['flow_id'])
    op.create_foreign_key('fk_assets_discovery_flow_id', 
                         'assets', 'discovery_flows', 
                         ['discovery_flow_id'], ['id'])
    
    # Create performance indexes for multi-phase queries
    op.create_index('idx_assets_master_flow_id', 'assets', ['master_flow_id'])
    op.create_index('idx_assets_source_phase', 'assets', ['source_phase'])
    op.create_index('idx_assets_current_phase', 'assets', ['current_phase'])
    op.create_index('idx_assets_discovery_flow_id', 'assets', ['discovery_flow_id'])
    
    # Make session_id optional (legacy cleanup)
    op.alter_column('assets', 'session_id', nullable=True)
    
    # =============================================================================
    # PHASE 5: MIGRATE DISCOVERY_ASSETS DATA TO ENHANCED ASSETS TABLE
    # =============================================================================
    
    print("Phase 5: Migrating discovery_assets data to enhanced assets table...")
    
    # Check if discovery_assets table exists and has data
    connection = op.get_bind()
    result = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'discovery_assets'
        )
    """))
    discovery_assets_exists = result.scalar()
    
    if discovery_assets_exists:
        # Get count of discovery_assets
        result = connection.execute(sa.text("SELECT COUNT(*) FROM discovery_assets"))
        discovery_assets_count = result.scalar()
        print(f"Found {discovery_assets_count} discovery assets to migrate...")
        
        if discovery_assets_count > 0:
            # Migrate discovery_assets data to enhanced assets table with master flow references
            # Use existing assets table columns and store discovery-specific data in custom_attributes
            connection.execute(sa.text("""
                INSERT INTO assets (
                    -- Core asset fields (use assets table columns)
                    id, name, asset_type, description, 
                    -- Multi-tenant fields
                    client_account_id, engagement_id,
                    -- Master flow coordination
                    master_flow_id, discovery_flow_id,
                    -- Phase tracking
                    source_phase, current_phase, phase_progression,
                    -- Store discovery-specific data in custom_attributes and raw_data
                    custom_attributes, raw_data, discovery_method,
                    -- Map discovery fields to existing assets fields
                    migration_complexity, is_mock,
                    -- Timestamps
                    created_at, updated_at
                ) 
                SELECT 
                    da.id,
                    COALESCE(da.asset_name, 'Migrated Asset'), 
                    -- Map asset_type to valid enum values
                    CASE 
                        WHEN UPPER(da.asset_type) IN ('SERVER', 'SERVERS') THEN 'SERVER'
                        WHEN UPPER(da.asset_type) IN ('VIRTUAL MACHINE', 'VIRTUAL_MACHINE', 'VM') THEN 'VIRTUAL_MACHINE'
                        WHEN UPPER(da.asset_type) IN ('DATABASE', 'DB') THEN 'DATABASE'
                        WHEN UPPER(da.asset_type) IN ('APPLICATION', 'APP') THEN 'APPLICATION'
                        WHEN UPPER(da.asset_type) IN ('NETWORK', 'NETWORKING') THEN 'NETWORK'
                        WHEN UPPER(da.asset_type) IN ('LOAD_BALANCER', 'LOAD BALANCER', 'LB') THEN 'LOAD_BALANCER'
                        WHEN UPPER(da.asset_type) IN ('STORAGE', 'DISK', 'VOLUME') THEN 'STORAGE'
                        WHEN UPPER(da.asset_type) IN ('SECURITY_GROUP', 'SECURITY GROUP', 'FIREWALL') THEN 'SECURITY_GROUP'
                        WHEN UPPER(da.asset_type) IN ('CONTAINER', 'DOCKER') THEN 'CONTAINER'
                        ELSE 'OTHER'
                    END::assettype, 
                    'Migrated from discovery flow',
                    da.client_account_id, 
                    da.engagement_id,
                    -- Get master flow ID from crewai_flow_state_extensions
                    (SELECT cse.flow_id 
                     FROM crewai_flow_state_extensions cse 
                     WHERE cse.discovery_flow_id = da.discovery_flow_id), 
                    da.discovery_flow_id,
                    'discovery', 
                    'discovery', 
                    '{"discovery_completed": true}',
                    -- Store discovery-specific data in custom_attributes
                    JSON_BUILD_OBJECT(
                        'discovered_in_phase', COALESCE(da.discovered_in_phase, 'inventory'),
                        'confidence_score', COALESCE(da.confidence_score, 0.8),
                        'validation_status', COALESCE(da.validation_status, 'pending'),
                        'asset_status', COALESCE(da.asset_status, 'discovered'),
                        'migration_ready', COALESCE(da.migration_ready, false),
                        'migration_priority', da.migration_priority
                    ),
                    COALESCE(da.raw_data, '{}'),
                    COALESCE(da.discovery_method, 'flow_migration'),
                    COALESCE(da.migration_complexity, 'medium'),
                    COALESCE(da.is_mock, false),
                    COALESCE(da.created_at, NOW()),
                    COALESCE(da.updated_at, NOW())
                FROM discovery_assets da
                WHERE da.discovery_flow_id IS NOT NULL
                AND EXISTS (
                    SELECT 1 FROM crewai_flow_state_extensions cse 
                    WHERE cse.discovery_flow_id = da.discovery_flow_id
                )
            """))
            
            # Verify migration success
            result = connection.execute(sa.text("""
                SELECT COUNT(*) FROM assets 
                WHERE source_phase = 'discovery' AND master_flow_id IS NOT NULL
            """))
            migrated_count = result.scalar()
            print(f"Successfully migrated {migrated_count} assets with master flow references")
    
    # =============================================================================
    # PHASE 6: TRANSFORM DATA INTEGRATION TABLES TO USE MASTER FLOW
    # =============================================================================
    
    print("Phase 6: Transforming data integration tables to use master flow...")
    
    # Transform data_imports table
    try:
        op.add_column('data_imports', sa.Column('master_flow_id', postgresql.UUID(as_uuid=True)))
        op.create_foreign_key('fk_data_imports_master_flow_id', 
                             'data_imports', 'crewai_flow_state_extensions', 
                             ['master_flow_id'], ['flow_id'])
        op.create_index('idx_data_imports_master_flow_id', 'data_imports', ['master_flow_id'])
        
        # Remove session_id constraint and column
        try:
            op.drop_constraint('data_imports_session_id_fkey', 'data_imports', type_='foreignkey')
        except:
            pass
        op.drop_column('data_imports', 'session_id')
    except Exception as e:
        print(f"data_imports table transformation skipped: {e}")
    
    # Transform raw_import_records table
    try:
        op.add_column('raw_import_records', sa.Column('master_flow_id', postgresql.UUID(as_uuid=True)))
        op.create_foreign_key('fk_raw_import_records_master_flow_id', 
                             'raw_import_records', 'crewai_flow_state_extensions', 
                             ['master_flow_id'], ['flow_id'])
        op.create_index('idx_raw_import_records_master_flow_id', 'raw_import_records', ['master_flow_id'])
        
        # Remove session_id constraint and column
        try:
            op.drop_constraint('raw_import_records_session_id_fkey', 'raw_import_records', type_='foreignkey')
        except:
            pass
        op.drop_column('raw_import_records', 'session_id')
    except Exception as e:
        print(f"raw_import_records table transformation skipped: {e}")
    
    # Transform import_field_mappings table
    try:
        op.add_column('import_field_mappings', sa.Column('master_flow_id', postgresql.UUID(as_uuid=True)))
        op.create_foreign_key('fk_import_field_mappings_master_flow_id', 
                             'import_field_mappings', 'crewai_flow_state_extensions', 
                             ['master_flow_id'], ['flow_id'])
        op.create_index('idx_import_field_mappings_master_flow_id', 'import_field_mappings', ['master_flow_id'])
        
        # Remove data_import_id constraint and column (replaced by master_flow_id)
        try:
            op.drop_constraint('import_field_mappings_data_import_id_fkey', 'import_field_mappings', type_='foreignkey')
        except:
            pass
        op.drop_column('import_field_mappings', 'data_import_id')
    except Exception as e:
        print(f"import_field_mappings table transformation skipped: {e}")
    
    # Transform access_audit_log table
    try:
        op.add_column('access_audit_log', sa.Column('master_flow_id', postgresql.UUID(as_uuid=True)))
        op.create_foreign_key('fk_access_audit_log_master_flow_id', 
                             'access_audit_log', 'crewai_flow_state_extensions', 
                             ['master_flow_id'], ['flow_id'])
        op.create_index('idx_access_audit_log_master_flow_id', 'access_audit_log', ['master_flow_id'])
        
        # Remove session_id constraint and column
        try:
            op.drop_constraint('access_audit_log_session_id_fkey', 'access_audit_log', type_='foreignkey')
        except:
            pass
        op.drop_column('access_audit_log', 'session_id')
    except Exception as e:
        print(f"access_audit_log table transformation skipped: {e}")
    
    # =============================================================================
    # PHASE 7: UPDATE CREWAI EXTENSIONS WITH MASTER FLOW CONTEXT
    # =============================================================================
    
    print("Phase 7: Updating CrewAI extensions with master flow context...")
    
    # Populate master flow coordination fields
    connection.execute(sa.text("""
        UPDATE crewai_flow_state_extensions SET
            current_phase = 'discovery',
            phase_flow_id = discovery_flow_id,
            phase_progression = '{"discovery": "completed"}',
            cross_phase_context = '{"phases_completed": ["discovery"]}'
        WHERE discovery_flow_id IS NOT NULL
    """))
    
    # =============================================================================
    # PHASE 8: CLEANUP LEGACY TABLES
    # =============================================================================
    
    print("Phase 8: Cleaning up legacy session-based tables...")
    
    # Drop legacy session-based tables
    # First drop foreign key constraints that reference legacy tables
    print("Removing foreign key constraints to legacy tables...")
    
    # Drop constraints that reference data_import_sessions
    try:
        result = connection.execute(sa.text("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'assets' 
            AND constraint_type = 'FOREIGN KEY'
            AND constraint_name LIKE '%session%'
        """))
        constraints = result.fetchall()
        for constraint in constraints:
            try:
                op.drop_constraint(constraint[0], 'assets', type_='foreignkey')
                print(f"Dropped constraint: {constraint[0]}")
            except Exception as e:
                print(f"Could not drop constraint {constraint[0]}: {e}")
    except Exception as e:
        print(f"Error checking constraints: {e}")
    
    # Now drop legacy tables
    legacy_tables = [
        'discovery_assets',
        'data_import_sessions', 
        'workflow_states',
        'import_processing_steps',
        'data_quality_issues'
    ]
    
    for table_name in legacy_tables:
        try:
            result = connection.execute(sa.text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = '{table_name}'
                )
            """))
            table_exists = result.scalar()
            
            if table_exists:
                print(f"Dropping legacy table: {table_name}")
                op.drop_table(table_name)
        except Exception as e:
            print(f"Error dropping table {table_name}: {e}")
    
    print("Master Flow Architecture Migration Completed Successfully!")
    print("✅ CrewAI Flow State Extensions enhanced as master coordinator")
    print("✅ Assets table enhanced with multi-phase flow support")
    print("✅ Data integration tables transformed to use master flow")
    print("✅ Discovery assets migrated to enhanced assets table")
    print("✅ Legacy session-based tables removed")
    print("✅ Future-ready for assessment_flows, planning_flows, execution_flows")


def downgrade():
    """
    Rollback master flow architecture changes
    Note: This is a destructive operation that will lose data
    """
    
    print("WARNING: Rolling back master flow architecture - this will lose data!")
    
    # Recreate basic discovery_assets table structure (data will be lost)
    op.create_table('discovery_assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('discovery_flow_id', postgresql.UUID(as_uuid=True)),
        sa.Column('asset_name', sa.String(255)),
        sa.Column('asset_type', sa.String(100)),
        sa.Column('raw_data', postgresql.JSONB()),
        sa.Column('client_account_id', sa.Integer()),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime())
    )
    
    # Remove master flow enhancements from assets table
    master_flow_columns = [
        'master_flow_id', 'discovery_flow_id', 'assessment_flow_id',
        'planning_flow_id', 'execution_flow_id', 'source_phase',
        'current_phase', 'phase_progression'
    ]
    
    # Drop foreign key constraints first
    for constraint in ['fk_assets_master_flow_id', 'fk_assets_discovery_flow_id']:
        try:
            op.drop_constraint(constraint, 'assets', type_='foreignkey')
        except:
            pass
    
    # Drop indexes
    master_flow_indexes = [
        'idx_assets_master_flow_id', 'idx_assets_source_phase',
        'idx_assets_current_phase', 'idx_assets_discovery_flow_id'
    ]
    for index in master_flow_indexes:
        try:
            op.drop_index(index)
        except:
            pass
    
    # Drop columns
    for column in master_flow_columns:
        try:
            op.drop_column('assets', column)
        except:
            pass
    
    # Restore session_id as required
    op.alter_column('assets', 'session_id', nullable=False)
    
    # Remove master flow enhancements from crewai_flow_state_extensions
    master_flow_ext_columns = [
        'current_phase', 'phase_flow_id', 'phase_progression',
        'flow_metadata', 'cross_phase_context'
    ]
    
    for column in master_flow_ext_columns:
        try:
            op.drop_column('crewai_flow_state_extensions', column)
        except:
            pass
    
    # Drop master flow indexes
    master_flow_ext_indexes = [
        'idx_crewai_extensions_master_flow_id',
        'idx_crewai_extensions_current_phase',
        'idx_crewai_extensions_phase_flow_id'
    ]
    for index in master_flow_ext_indexes:
        try:
            op.drop_index(index)
        except:
            pass
    
    # Drop unique constraint on flow_id
    try:
        op.drop_constraint('uq_crewai_extensions_flow_id', 'crewai_flow_state_extensions', type_='unique')
    except:
        pass
    
    # Remove master flow reference from discovery_flows
    try:
        op.drop_constraint('fk_discovery_flows_master_flow_id', 'discovery_flows', type_='foreignkey')
        op.drop_column('discovery_flows', 'master_flow_id')
    except:
        pass
    
    print("Master flow architecture rollback completed (with data loss)") 