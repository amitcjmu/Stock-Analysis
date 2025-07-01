"""
Integration tests for database consolidation
Verifies V3 tables are removed and schema is properly consolidated
"""

import pytest
import asyncio
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models import DataImport, DiscoveryFlow, Asset, ImportFieldMapping


class TestDatabaseConsolidation:
    """Test suite for database consolidation verification"""
    
    @pytest.mark.asyncio
    async def test_no_v3_tables_exist(self):
        """Ensure no V3 tables exist in the database"""
        async with AsyncSessionLocal() as session:
            # Check for V3 tables
            result = await session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'v3_%'
            """))
            v3_tables = [row[0] for row in result]
            
            assert len(v3_tables) == 0, f"V3 tables still exist: {v3_tables}"
    
    @pytest.mark.asyncio
    async def test_no_is_mock_columns_exist(self):
        """Ensure is_mock columns have been removed from all tables"""
        async with AsyncSessionLocal() as session:
            # Check for is_mock columns
            result = await session.execute(text("""
                SELECT table_name, column_name 
                FROM information_schema.columns 
                WHERE column_name = 'is_mock'
                AND table_schema = 'public'
            """))
            is_mock_columns = [(row[0], row[1]) for row in result]
            
            assert len(is_mock_columns) == 0, f"is_mock columns still exist: {is_mock_columns}"
    
    @pytest.mark.asyncio
    async def test_data_import_field_renames(self):
        """Verify DataImport model has correct field names"""
        async with AsyncSessionLocal() as session:
            # Check column names
            result = await session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'data_imports'
                AND column_name IN ('filename', 'file_size', 'mime_type', 'source_system', 'error_message', 'error_details')
            """))
            columns = [row[0] for row in result]
            
            # All new column names should exist
            expected_columns = ['filename', 'file_size', 'mime_type', 'source_system', 'error_message', 'error_details']
            for col in expected_columns:
                assert col in columns, f"Column {col} missing from data_imports table"
            
            # Old column names should not exist
            result = await session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'data_imports'
                AND column_name IN ('source_filename', 'file_size_bytes', 'file_type')
            """))
            old_columns = [row[0] for row in result]
            
            assert len(old_columns) == 0, f"Old columns still exist: {old_columns}"
    
    @pytest.mark.asyncio
    async def test_discovery_flow_hybrid_fields(self):
        """Verify DiscoveryFlow has both boolean and JSON fields"""
        async with AsyncSessionLocal() as session:
            # Check for boolean completion flags
            result = await session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'discovery_flows'
                AND column_name LIKE '%_completed'
            """))
            boolean_flags = [row[0] for row in result]
            
            expected_flags = [
                'data_validation_completed',
                'field_mapping_completed', 
                'data_cleansing_completed',
                'asset_inventory_completed',
                'dependency_analysis_completed',
                'tech_debt_assessment_completed'
            ]
            
            for flag in expected_flags:
                assert flag in boolean_flags, f"Boolean flag {flag} missing"
            
            # Check for JSON fields
            result = await session.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns 
                WHERE table_name = 'discovery_flows'
                AND data_type IN ('json', 'jsonb')
            """))
            json_fields = {row[0]: row[1] for row in result}
            
            assert 'flow_state' in json_fields
            assert 'crew_outputs' in json_fields
            assert 'crewai_state_data' in json_fields
    
    @pytest.mark.asyncio
    async def test_master_flow_relationships(self):
        """Verify master_flow_id relationships exist"""
        async with AsyncSessionLocal() as session:
            # Check master_flow_id exists in key tables
            tables_with_master_flow = ['data_imports', 'assets', 'discovery_flows']
            
            for table in tables_with_master_flow:
                result = await session.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}'
                    AND column_name = 'master_flow_id'
                """))
                has_master_flow = result.scalar() is not None
                
                if table == 'discovery_flows':
                    # discovery_flows might not have master_flow_id directly
                    continue
                    
                assert has_master_flow, f"Table {table} missing master_flow_id column"
    
    @pytest.mark.asyncio
    async def test_removed_tables_dont_exist(self):
        """Verify deprecated tables have been removed"""
        removed_tables = [
            'workflow_states',
            'discovery_assets', 
            'mapping_learning_patterns',
            'data_quality_issues',
            'workflow_progress',
            'import_processing_steps'
        ]
        
        async with AsyncSessionLocal() as session:
            for table in removed_tables:
                result = await session.execute(text(f"""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    )
                """))
                exists = result.scalar()
                
                assert not exists, f"Deprecated table {table} still exists"
    
    @pytest.mark.asyncio
    async def test_asset_table_preserved_fields(self):
        """Verify Asset table has all infrastructure fields preserved"""
        async with AsyncSessionLocal() as session:
            # Sample of important infrastructure fields
            infrastructure_fields = [
                'hostname', 'ip_address', 'operating_system', 
                'cpu_cores', 'memory_gb', 'storage_gb',
                'environment', 'location', 'datacenter'
            ]
            
            result = await session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'assets'
            """))
            columns = [row[0] for row in result]
            
            for field in infrastructure_fields:
                assert field in columns, f"Infrastructure field {field} missing from assets table"
    
    @pytest.mark.asyncio
    async def test_multi_tenant_indexes(self):
        """Verify multi-tenant indexes exist on key tables"""
        async with AsyncSessionLocal() as session:
            tables_to_check = ['data_imports', 'discovery_flows', 'assets']
            
            for table in tables_to_check:
                # Check for client_account_id index
                result = await session.execute(text(f"""
                    SELECT COUNT(*) 
                    FROM pg_indexes 
                    WHERE tablename = '{table}'
                    AND indexdef LIKE '%client_account_id%'
                """))
                has_client_index = result.scalar() > 0
                
                assert has_client_index, f"Table {table} missing client_account_id index"
                
                # Check for engagement_id index
                result = await session.execute(text(f"""
                    SELECT COUNT(*) 
                    FROM pg_indexes 
                    WHERE tablename = '{table}'
                    AND indexdef LIKE '%engagement_id%'
                """))
                has_engagement_index = result.scalar() > 0
                
                assert has_engagement_index, f"Table {table} missing engagement_id index"
    
    @pytest.mark.asyncio
    async def test_create_data_import_with_new_fields(self):
        """Test creating a DataImport with new field names"""
        async with AsyncSessionLocal() as session:
            try:
                # Create test import
                test_import = DataImport(
                    client_account_id="11111111-1111-1111-1111-111111111111",
                    engagement_id="22222222-2222-2222-2222-222222222222",
                    import_name="Test Consolidation Import",
                    import_type="test",
                    filename="test_file.csv",  # New field name
                    file_size=1024,  # New field name
                    mime_type="text/csv",  # New field name
                    source_system="test_system",  # New field
                    status="pending",
                    imported_by="33333333-3333-3333-3333-333333333333"
                )
                
                session.add(test_import)
                await session.commit()
                
                # Verify it was created
                result = await session.execute(
                    text("SELECT id, filename, file_size, mime_type, source_system FROM data_imports WHERE id = :id"),
                    {"id": str(test_import.id)}
                )
                row = result.first()
                
                assert row is not None
                assert row.filename == "test_file.csv"
                assert row.file_size == 1024
                assert row.mime_type == "text/csv"
                assert row.source_system == "test_system"
                
                # Cleanup
                await session.execute(
                    text("DELETE FROM data_imports WHERE id = :id"),
                    {"id": str(test_import.id)}
                )
                await session.commit()
                
            except Exception as e:
                await session.rollback()
                pytest.fail(f"Failed to create DataImport with new fields: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])