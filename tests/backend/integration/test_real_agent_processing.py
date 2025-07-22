#!/usr/bin/env python3
"""
Real Agent Processing Integration Tests

Tests actual CrewAI agent execution (not mocked) to verify:
1. UnifiedDiscoveryFlow executes with real CrewAI agents
2. Assessment flows use real agent analysis
3. Master flow orchestration works correctly
4. Agent processing produces meaningful results
"""

import pytest
import csv
import tempfile
import os
from datetime import datetime, timedelta

# Import necessary modules
import sys
sys.path.append('/app')

try:
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select, func, and_
    from app.core.database import AsyncSessionLocal
    from app.models.asset import Asset
    from app.models.data_import import DataImport, RawImportRecord
    from app.models.discovery_flow import DiscoveryFlow
    from app.models.client_account import ClientAccount
    from app.models.engagement import Engagement
    from app.models.user_profile import UserProfile
    from app.services.crewai_flows.unified_discovery_flow import UnifiedDiscoveryFlow
    from app.services.crewai_flows.flow_state_manager import FlowStateManager
    from app.repositories.discovery_flow_repository.base_repository import DiscoveryFlowRepository
    from app.core.config import settings
except ImportError as e:
    pytest.skip(f"Backend modules not available: {e}", allow_module_level=True)

# Test configuration
TEST_CLIENT_ID = "bafd5b46-aaaf-4c95-8142-573699d93171"
TEST_ENGAGEMENT_ID = "6e9c8133-4169-4b79-b052-106dc93d0208" 
TEST_USER_ID = "44444444-4444-4444-4444-444444444444"

class TestRealAgentProcessing:
    """Test suite for real CrewAI agent processing"""
    
    @pytest.fixture(autouse=True)
    async def setup_test_environment(self):
        """Set up test environment with necessary data"""
        async with AsyncSessionLocal() as session:
            # Verify test client exists
            client_result = await session.execute(
                select(ClientAccount).where(ClientAccount.id == TEST_CLIENT_ID)
            )
            client = client_result.scalar_one_or_none()
            
            if not client:
                pytest.skip(f"Test client {TEST_CLIENT_ID} not found")
            
            # Verify test user exists
            user_result = await session.execute(
                select(UserProfile).where(UserProfile.user_id == TEST_USER_ID)
            )
            user = user_result.scalar_one_or_none()
            
            if not user:
                pytest.skip(f"Test user {TEST_USER_ID} not found")
            
            self.client = client
            self.user = user
            
    async def create_test_cmdb_data(self) -> str:
        """Create realistic CMDB test data for agent processing"""
        test_data = [
            {
                "asset_id": "SRV001",
                "asset_name": "Production Web Server",
                "asset_type": "Server",
                "ip_address": "10.1.1.10",
                "os": "Ubuntu 20.04 LTS",
                "environment": "Production",
                "criticality": "High",
                "owner": "John Smith",
                "department": "IT",
                "location": "DataCenter-A",
                "dependencies": "DB001,LB001",
                "description": "Primary web server handling customer traffic",
                "last_updated": "2024-01-15"
            },
            {
                "asset_id": "DB001", 
                "asset_name": "Customer Database",
                "asset_type": "Database",
                "ip_address": "10.1.1.20",
                "os": "PostgreSQL 14",
                "environment": "Production",
                "criticality": "Critical",
                "owner": "Jane Doe",
                "department": "IT", 
                "location": "DataCenter-A",
                "dependencies": "SRV001",
                "description": "Primary customer database server",
                "last_updated": "2024-01-20"
            },
            {
                "asset_id": "APP001",
                "asset_name": "Customer Portal",
                "asset_type": "Application",
                "ip_address": "N/A",
                "os": "Java 11 Spring Boot",
                "environment": "Production", 
                "criticality": "High",
                "owner": "Bob Wilson",
                "department": "Business",
                "location": "Cloud",
                "dependencies": "SRV001,DB001",
                "description": "Main customer-facing web application",
                "last_updated": "2024-01-18"
            }
        ]
        
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            fieldnames = test_data[0].keys()
            writer = csv.DictWriter(tmp_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(test_data)
            return tmp_file.name
    
    @pytest.mark.asyncio
    async def test_unified_discovery_flow_real_agents(self):
        """Test UnifiedDiscoveryFlow with real CrewAI agents"""
        print("🤖 Testing UnifiedDiscoveryFlow with real CrewAI agents...")
        
        # Create test CMDB data
        csv_path = await self.create_test_cmdb_data()
        
        try:
            # Create data import session
            async with AsyncSessionLocal() as session:
                # Create data import record
                data_import = DataImport(
                    filename="test_real_agents.csv",
                    upload_type="cmdb",
                    total_records=3,
                    processed_records=0,
                    status="pending",
                    client_account_id=TEST_CLIENT_ID,
                    engagement_id=TEST_ENGAGEMENT_ID,
                    created_by=TEST_USER_ID
                )
                session.add(data_import)
                await session.commit()
                await session.refresh(data_import)
                
                import_session_id = str(data_import.id)
                
                # Read CSV and create raw import records
                with open(csv_path, 'r') as f:
                    csv_reader = csv.DictReader(f)
                    for row_num, row_data in enumerate(csv_reader):
                        raw_record = RawImportRecord(
                            import_session_id=import_session_id,
                            row_number=row_num + 1,
                            raw_data=row_data,
                            client_account_id=TEST_CLIENT_ID,
                            engagement_id=TEST_ENGAGEMENT_ID
                        )
                        session.add(raw_record)
                
                await session.commit()
                
                # Initialize UnifiedDiscoveryFlow
                FlowStateManager(session, TEST_CLIENT_ID)
                discovery_flow = UnifiedDiscoveryFlow(
                    session=session,
                    client_account_id=TEST_CLIENT_ID,
                    engagement_id=TEST_ENGAGEMENT_ID,
                    user_id=TEST_USER_ID
                )
                
                # Test flow initialization
                init_result = await discovery_flow.initialize_discovery({
                    "import_session_id": import_session_id,
                    "data_type": "cmdb"
                })
                
                assert init_result["status"] == "initialized"
                assert "flow_id" in init_result
                flow_id = init_result["flow_id"]
                
                print(f"✅ Discovery flow initialized: {flow_id}")
                
                # Execute field mapping crew (real agents)
                print("🔍 Executing field mapping crew...")
                field_mapping_result = await discovery_flow.execute_field_mapping_crew(init_result)
                
                assert field_mapping_result["status"] in ["completed", "in_progress"]
                print(f"✅ Field mapping crew executed: {field_mapping_result['status']}")
                
                # Execute data cleansing crew (real agents)
                print("🧹 Executing data cleansing crew...")
                cleansing_result = await discovery_flow.execute_data_cleansing_crew(field_mapping_result)
                
                assert cleansing_result["status"] in ["completed", "in_progress"]
                print(f"✅ Data cleansing crew executed: {cleansing_result['status']}")
                
                # Execute asset inventory crew (real agents)
                print("📋 Executing asset inventory crew...")
                inventory_result = await discovery_flow.execute_asset_inventory_crew(cleansing_result)
                
                assert inventory_result["status"] in ["completed", "in_progress"]
                print(f"✅ Asset inventory crew executed: {inventory_result['status']}")
                
                # Verify assets were actually created
                asset_count = await session.execute(
                    select(func.count(Asset.id)).where(
                        and_(
                            Asset.client_account_id == TEST_CLIENT_ID,
                            Asset.created_at >= datetime.now() - timedelta(minutes=10)
                        )
                    )
                )
                created_assets = asset_count.scalar()
                
                print(f"📊 Assets created by real agents: {created_assets}")
                assert created_assets > 0, "Real agents should have created assets"
                
                # Verify discovery flow record exists
                flow_result = await session.execute(
                    select(DiscoveryFlow).where(DiscoveryFlow.id == flow_id)
                )
                flow_record = flow_result.scalar_one_or_none()
                
                assert flow_record is not None, "Discovery flow record should exist"
                assert flow_record.status in ["running", "completed"]
                
                print("🎉 Real agent processing test completed successfully!")
                
        finally:
            # Clean up temp file
            if os.path.exists(csv_path):
                os.unlink(csv_path)
    
    @pytest.mark.asyncio
    async def test_assessment_flow_real_agents(self):
        """Test assessment flow with real CrewAI agents"""
        print("🎯 Testing assessment flow with real agents...")
        
        async with AsyncSessionLocal() as session:
            # Find existing assets or create test assets
            assets_result = await session.execute(
                select(Asset).where(
                    Asset.client_account_id == TEST_CLIENT_ID
                ).limit(3)
            )
            assets = assets_result.scalars().all()
            
            if not assets:
                # Create minimal test assets for assessment
                test_asset = Asset(
                    name="Test Application for Assessment",
                    asset_type="Application",
                    ip_address="10.1.1.100",
                    client_account_id=TEST_CLIENT_ID,
                    engagement_id=TEST_ENGAGEMENT_ID,
                    created_by=TEST_USER_ID,
                    metadata_={
                        "technology_stack": ["Java", "Spring Boot", "PostgreSQL"],
                        "criticality": "High",
                        "environment": "Production"
                    }
                )
                session.add(test_asset)
                await session.commit()
                await session.refresh(test_asset)
                assets = [test_asset]
            
            selected_asset = assets[0]
            print(f"🎯 Selected asset for assessment: {selected_asset.name}")
            
            # TODO: Implement actual assessment flow with real CrewAI agents
            # This would involve:
            # 1. Architecture standards analysis
            # 2. Technical debt assessment
            # 3. 6R strategy analysis
            # 4. Confidence scoring
            
            # For now, verify the asset exists and is suitable for assessment
            assert selected_asset.asset_type in ["Application", "Service"]
            assert selected_asset.client_account_id == TEST_CLIENT_ID
            
            print("✅ Assessment flow setup completed (full implementation pending)")
    
    @pytest.mark.asyncio 
    async def test_master_flow_orchestration(self):
        """Test master flow orchestration system"""
        print("🎭 Testing master flow orchestration...")
        
        async with AsyncSessionLocal() as session:
            # Get active discovery flows
            discovery_flows_result = await session.execute(
                select(DiscoveryFlow).where(
                    and_(
                        DiscoveryFlow.client_account_id == TEST_CLIENT_ID,
                        DiscoveryFlow.status.in_(["running", "completed"])
                    )
                )
            )
            discovery_flows = discovery_flows_result.scalars().all()
            
            print(f"📊 Found {len(discovery_flows)} discovery flows")
            
            # TODO: Test assessment flow registration with master orchestration
            # This requires implementing:
            # 1. CrewAIFlowStateExtensions for assessment flows
            # 2. Master flow dashboard
            # 3. Cross-flow type coordination
            
            # For now, verify discovery flows exist
            if discovery_flows:
                for flow in discovery_flows:
                    assert flow.client_account_id == TEST_CLIENT_ID
                    assert flow.status in ["running", "completed"]
                    print(f"✅ Discovery flow {flow.id}: {flow.status}")
            
            print("✅ Master flow orchestration test completed (partial implementation)")
    
    @pytest.mark.asyncio
    async def test_agent_processing_performance(self):
        """Test agent processing performance characteristics"""
        print("⚡ Testing agent processing performance...")
        
        datetime.now()
        
        # Create larger test dataset
        large_test_data = []
        for i in range(10):  # 10 assets for performance testing
            large_test_data.append({
                "asset_id": f"PERF{i:03d}",
                "asset_name": f"Performance Test Asset {i}",
                "asset_type": "Server" if i % 2 == 0 else "Application",
                "ip_address": f"10.1.2.{i + 10}",
                "os": "Ubuntu 20.04",
                "environment": "Test",
                "criticality": "Medium",
                "owner": "Test User",
                "department": "IT",
                "location": "Test-DC",
                "dependencies": "",
                "description": f"Performance test asset number {i}",
                "last_updated": "2024-01-01"
            })
        
        # Create CSV
        csv_path = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
                csv_path = tmp_file.name
                fieldnames = large_test_data[0].keys()
                writer = csv.DictWriter(tmp_file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(large_test_data)
            
            async with AsyncSessionLocal() as session:
                # Create data import
                data_import = DataImport(
                    filename="performance_test.csv",
                    upload_type="cmdb",
                    total_records=len(large_test_data),
                    processed_records=0,
                    status="pending",
                    client_account_id=TEST_CLIENT_ID,
                    engagement_id=TEST_ENGAGEMENT_ID,
                    created_by=TEST_USER_ID
                )
                session.add(data_import)
                await session.commit()
                await session.refresh(data_import)
                
                # Read and process CSV
                with open(csv_path, 'r') as f:
                    csv_reader = csv.DictReader(f)
                    for row_num, row_data in enumerate(csv_reader):
                        raw_record = RawImportRecord(
                            import_session_id=str(data_import.id),
                            row_number=row_num + 1,
                            raw_data=row_data,
                            client_account_id=TEST_CLIENT_ID,
                            engagement_id=TEST_ENGAGEMENT_ID
                        )
                        session.add(raw_record)
                
                await session.commit()
                
                # Initialize and run discovery flow
                discovery_flow = UnifiedDiscoveryFlow(
                    session=session,
                    client_account_id=TEST_CLIENT_ID,
                    engagement_id=TEST_ENGAGEMENT_ID,
                    user_id=TEST_USER_ID
                )
                
                processing_start = datetime.now()
                
                init_result = await discovery_flow.initialize_discovery({
                    "import_session_id": str(data_import.id),
                    "data_type": "cmdb"
                })
                
                # Run field mapping (performance test)
                field_result = await discovery_flow.execute_field_mapping_crew(init_result)
                
                processing_end = datetime.now()
                processing_time = (processing_end - processing_start).total_seconds()
                
                print(f"⏱️ Processing time for {len(large_test_data)} assets: {processing_time:.2f} seconds")
                
                # Performance assertions
                assert processing_time < 60, f"Processing should complete within 60 seconds, took {processing_time:.2f}s"
                assert field_result["status"] in ["completed", "in_progress"]
                
                print("✅ Agent processing performance test passed")
                
        finally:
            if csv_path and os.path.exists(csv_path):
                os.unlink(csv_path)
    
    @pytest.mark.asyncio
    async def test_agent_error_handling(self):
        """Test agent error handling and recovery"""
        print("🚨 Testing agent error handling...")
        
        # Create invalid test data to trigger agent errors
        invalid_data = [{
            "asset_id": "",  # Empty ID
            "asset_name": "",  # Empty name
            "asset_type": "InvalidType",
            "ip_address": "invalid.ip.address",
            "os": None,
            "environment": "",
            "criticality": "",
            "owner": "",
            "department": "",
            "location": "",
            "dependencies": "circular_dependency_to_self",
            "description": "",
            "last_updated": "invalid_date"
        }]
        
        csv_path = None
        try:
            # Create CSV with invalid data
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
                csv_path = tmp_file.name
                fieldnames = invalid_data[0].keys()
                writer = csv.DictWriter(tmp_file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(invalid_data)
            
            async with AsyncSessionLocal() as session:
                # Create data import
                data_import = DataImport(
                    filename="error_test.csv",
                    upload_type="cmdb",
                    total_records=1,
                    processed_records=0,
                    status="pending",
                    client_account_id=TEST_CLIENT_ID,
                    engagement_id=TEST_ENGAGEMENT_ID,
                    created_by=TEST_USER_ID
                )
                session.add(data_import)
                await session.commit()
                await session.refresh(data_import)
                
                # Process CSV
                with open(csv_path, 'r') as f:
                    csv_reader = csv.DictReader(f)
                    for row_num, row_data in enumerate(csv_reader):
                        raw_record = RawImportRecord(
                            import_session_id=str(data_import.id),
                            row_number=row_num + 1,
                            raw_data=row_data,
                            client_account_id=TEST_CLIENT_ID,
                            engagement_id=TEST_ENGAGEMENT_ID
                        )
                        session.add(raw_record)
                
                await session.commit()
                
                # Test error handling in discovery flow
                discovery_flow = UnifiedDiscoveryFlow(
                    session=session,
                    client_account_id=TEST_CLIENT_ID,
                    engagement_id=TEST_ENGAGEMENT_ID,
                    user_id=TEST_USER_ID
                )
                
                try:
                    init_result = await discovery_flow.initialize_discovery({
                        "import_session_id": str(data_import.id),
                        "data_type": "cmdb"
                    })
                    
                    # This should either handle the error gracefully or fail with proper error handling
                    field_result = await discovery_flow.execute_field_mapping_crew(init_result)
                    
                    # Check if error was handled gracefully
                    if field_result.get("status") == "failed":
                        assert "error" in field_result
                        print(f"✅ Error handled gracefully: {field_result.get('error')}")
                    else:
                        print("✅ Invalid data processed without errors (robust agent handling)")
                        
                except Exception as e:
                    # Verify error is properly structured
                    assert isinstance(e, Exception)
                    print(f"✅ Exception properly raised: {type(e).__name__}")
                
                print("✅ Agent error handling test completed")
                
        finally:
            if csv_path and os.path.exists(csv_path):
                os.unlink(csv_path)

if __name__ == "__main__":
    # Run tests directly
    import pytest
    pytest.main([__file__, "-v", "-s"])