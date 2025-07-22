"""
Integration tests for V3 API with current database state
These tests work with the existing database schema before consolidation
"""

import asyncio
import uuid
from datetime import datetime

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.asset import Asset
from app.models.data_import.core import DataImport
from app.models.data_import.mapping import ImportFieldMapping
from app.models.discovery_flow import DiscoveryFlow

# Configure pytest to use asyncio
pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def db_session():
    """Create a test database session"""
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


class TestV3APICurrentState:
    """Test V3 API functionality with current database state"""
    
    async def test_database_connection(self, db_session):
        """Test that we can connect to the database"""
        result = await db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1
    
    async def test_discovery_flow_crud(self, db_session):
        """Test basic CRUD operations on DiscoveryFlow"""
        # Create a discovery flow
        flow = DiscoveryFlow(
            name="Test Flow",
            description="Test Description",
            status="initialized",
            current_phase="initialization",
            client_account_id=uuid.uuid4(),
            engagement_id=uuid.uuid4(),
            created_by_user_id=uuid.uuid4()
        )
        
        db_session.add(flow)
        await db_session.commit()
        await db_session.refresh(flow)
        
        assert flow.id is not None
        assert flow.name == "Test Flow"
        
        # Read the flow
        result = await db_session.execute(
            select(DiscoveryFlow).where(DiscoveryFlow.id == flow.id)
        )
        retrieved_flow = result.scalar_one()
        
        assert retrieved_flow.name == "Test Flow"
        assert retrieved_flow.status == "initialized"
        
        # Update the flow
        retrieved_flow.status = "in_progress"
        await db_session.commit()
        
        # Verify update
        result = await db_session.execute(
            select(DiscoveryFlow).where(DiscoveryFlow.id == flow.id)
        )
        updated_flow = result.scalar_one()
        
        assert updated_flow.status == "in_progress"
        
        # Delete the flow
        await db_session.delete(updated_flow)
        await db_session.commit()
        
        # Verify deletion
        result = await db_session.execute(
            select(DiscoveryFlow).where(DiscoveryFlow.id == flow.id)
        )
        assert result.scalar_one_or_none() is None
    
    async def test_data_import_operations(self, db_session):
        """Test DataImport operations"""
        # Create a data import
        import_data = DataImport(
            name="Test Import",
            description="Test Description",
            import_type="csv",
            status="pending",
            client_account_id=uuid.uuid4(),
            engagement_id=uuid.uuid4(),
            created_by_user_id=uuid.uuid4()
        )
        
        db_session.add(import_data)
        await db_session.commit()
        await db_session.refresh(import_data)
        
        assert import_data.id is not None
        assert import_data.name == "Test Import"
        
        # Clean up
        await db_session.delete(import_data)
        await db_session.commit()
    
    async def test_asset_operations(self, db_session):
        """Test Asset operations"""
        # Create an asset
        asset = Asset(
            asset_name="Test Server",
            asset_type="server",
            status="active",
            client_account_id=uuid.uuid4(),
            engagement_id=uuid.uuid4(),
            created_by_user_id=uuid.uuid4()
        )
        
        db_session.add(asset)
        await db_session.commit()
        await db_session.refresh(asset)
        
        assert asset.id is not None
        assert asset.asset_name == "Test Server"
        
        # Clean up
        await db_session.delete(asset)
        await db_session.commit()
    
    async def test_field_mapping_operations(self, db_session):
        """Test ImportFieldMapping operations"""
        # First create a flow and import
        flow_id = uuid.uuid4()
        import_id = uuid.uuid4()
        
        # Create field mapping
        mapping = ImportFieldMapping(
            import_id=import_id,
            flow_id=flow_id,
            source_field="hostname",
            target_field="asset_name",
            mapping_type="direct",
            confidence_score=0.95,
            client_account_id=uuid.uuid4(),
            created_by_user_id=uuid.uuid4()
        )
        
        db_session.add(mapping)
        await db_session.commit()
        await db_session.refresh(mapping)
        
        assert mapping.id is not None
        assert mapping.source_field == "hostname"
        assert mapping.target_field == "asset_name"
        
        # Clean up
        await db_session.delete(mapping)
        await db_session.commit()
    
    async def test_table_structure_current_state(self, db_session):
        """Test current table structures exist"""
        tables_to_check = [
            'discovery_flows',
            'data_imports',
            'import_field_mappings',
            'assets',
            'client_accounts',
            'engagements',
            'users'
        ]
        
        for table in tables_to_check:
            result = await db_session.execute(
                text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = '{table}'
                    )
                """)
            )
            exists = result.scalar()
            assert exists, f"Table {table} does not exist"
            print(f"✓ Table {table} exists")


@pytest.mark.asyncio
async def test_v3_api_current_state_suite():
    """Run all current state tests"""
    async with AsyncSessionLocal() as session:
        tests = TestV3APICurrentState()
        
        print("\n" + "="*60)
        print("Running V3 API Current State Tests")
        print("="*60)
        
        await tests.test_database_connection(session)
        print("✓ Database connection test passed")
        
        await tests.test_discovery_flow_crud(session)
        print("✓ DiscoveryFlow CRUD test passed")
        
        await tests.test_data_import_operations(session)
        print("✓ DataImport operations test passed")
        
        await tests.test_asset_operations(session)
        print("✓ Asset operations test passed")
        
        await tests.test_field_mapping_operations(session)
        print("✓ Field mapping operations test passed")
        
        await tests.test_table_structure_current_state(session)
        print("✓ Table structure test passed")
        
        print("\n" + "="*60)
        print("✅ All current state tests passed!")
        print("="*60)


if __name__ == "__main__":
    asyncio.run(test_v3_api_current_state_suite())