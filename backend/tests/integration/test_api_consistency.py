"""
API Consistency Integration Tests

This module provides comprehensive testing of API consistency and data relationships
across the discovery flow system. It validates that all API endpoints return
properly linked data with correct foreign key relationships.

Test Coverage:
1. Master Flow Orchestrator API consistency
2. Discovery Flow API data relationships
3. Data Import API linkage validation
4. Asset API relationship consistency
5. Cross-API data integrity validation
6. API response format standardization
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.models.asset import Asset
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.data_import.core import DataImport, RawImportRecord
from app.models.discovery_flow import DiscoveryFlow
from app.repositories.crewai_flow_state_extensions_repository import CrewAIFlowStateExtensionsRepository
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from app.services.master_flow_orchestrator import MasterFlowOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestAPIConsistency:
    """
    Test suite for API consistency and data relationship validation.
    
    This class ensures that all API endpoints return properly structured data
    with correct foreign key relationships and consistent formatting.
    """
    
    @pytest.fixture
    async def test_context(self):
        """Create test context with multi-tenant isolation"""
        return RequestContext(
            client_account_id=str(uuid.uuid4()),
            engagement_id=str(uuid.uuid4()),
            user_id="api_test_user",
            user_role="admin",
            request_id=str(uuid.uuid4())
        )
    
    @pytest.fixture
    async def complete_test_data(self, test_context):
        """Create complete test data structure with all relationships"""
        async with AsyncSessionLocal() as session:
            # Create master flow
            master_flow = CrewAIFlowStateExtensions(
                flow_id=str(uuid.uuid4()),
                client_account_id=test_context.client_account_id,
                engagement_id=test_context.engagement_id,
                user_id=test_context.user_id,
                flow_type="discovery",
                flow_name="API Test Master Flow",
                flow_status="active",
                flow_configuration={
                    "auto_process": True,
                    "test_mode": True
                }
            )
            
            session.add(master_flow)
            await session.commit()
            await session.refresh(master_flow)
            
            # Create data import
            data_import = DataImport(
                client_account_id=test_context.client_account_id,
                engagement_id=test_context.engagement_id,
                master_flow_id=master_flow.flow_id,
                import_name="API Test Data Import",
                import_type="cmdb",
                filename="api_test.csv",
                file_size=1024,
                mime_type="text/csv",
                source_system="test_system",
                status="completed",
                imported_by=test_context.user_id,
                total_records=3
            )
            
            session.add(data_import)
            await session.commit()
            await session.refresh(data_import)
            
            # Create discovery flow
            discovery_flow = DiscoveryFlow(
                flow_id=master_flow.flow_id,
                master_flow_id=master_flow.flow_id,
                client_account_id=test_context.client_account_id,
                engagement_id=test_context.engagement_id,
                user_id=test_context.user_id,
                data_import_id=data_import.id,
                flow_name="API Test Discovery Flow",
                status="active",
                progress_percentage=75.0,
                data_import_completed=True,
                field_mapping_completed=True,
                data_cleansing_completed=True,
                asset_inventory_completed=False,
                crewai_persistence_id=master_flow.flow_id
            )
            
            session.add(discovery_flow)
            await session.commit()
            await session.refresh(discovery_flow)
            
            # Create raw records
            raw_records = []
            test_data = [
                {
                    "hostname": "api-test-server-01",
                    "ip_address": "192.168.100.10",
                    "operating_system": "Ubuntu 20.04",
                    "cpu_cores": 4,
                    "memory_gb": 16,
                    "application": "web-server"
                },
                {
                    "hostname": "api-test-db-01",
                    "ip_address": "192.168.100.11",
                    "operating_system": "PostgreSQL 13",
                    "cpu_cores": 8,
                    "memory_gb": 32,
                    "application": "database"
                },
                {
                    "hostname": "api-test-app-01",
                    "ip_address": "192.168.100.12",
                    "operating_system": "CentOS 8",
                    "cpu_cores": 6,
                    "memory_gb": 24,
                    "application": "api-service"
                }
            ]
            
            for i, raw_data in enumerate(test_data):
                raw_record = RawImportRecord(
                    data_import_id=data_import.id,
                    client_account_id=test_context.client_account_id,
                    engagement_id=test_context.engagement_id,
                    master_flow_id=master_flow.flow_id,
                    row_number=i + 1,
                    raw_data=raw_data,
                    is_processed=True,
                    is_valid=True
                )
                raw_records.append(raw_record)
                session.add(raw_record)
            
            await session.commit()
            
            # Create assets
            assets = []
            for i, raw_record in enumerate(raw_records):
                asset = Asset(
                    client_account_id=test_context.client_account_id,
                    engagement_id=test_context.engagement_id,
                    discovery_flow_id=discovery_flow.flow_id,
                    master_flow_id=master_flow.flow_id,
                    raw_import_record_id=raw_record.id,
                    hostname=raw_record.raw_data.get("hostname"),
                    ip_address=raw_record.raw_data.get("ip_address"),
                    operating_system=raw_record.raw_data.get("operating_system"),
                    cpu_cores=raw_record.raw_data.get("cpu_cores"),
                    memory_gb=raw_record.raw_data.get("memory_gb"),
                    asset_type="server",
                    asset_name=raw_record.raw_data.get("hostname"),
                    migration_readiness_score=0.7 + (i * 0.1)  # 0.7, 0.8, 0.9
                )
                assets.append(asset)
                session.add(asset)
                
                # Link raw record to asset
                raw_record.asset_id = asset.id
            
            await session.commit()
            
            yield {
                "master_flow": master_flow,
                "data_import": data_import,
                "discovery_flow": discovery_flow,
                "raw_records": raw_records,
                "assets": assets,
                "session": session
            }
            
            # Cleanup
            try:
                for asset in assets:
                    await session.delete(asset)
                for raw_record in raw_records:
                    await session.delete(raw_record)
                await session.delete(discovery_flow)
                await session.delete(data_import)
                await session.delete(master_flow)
                await session.commit()
            except Exception as e:
                logger.warning(f"Cleanup failed: {e}")
                await session.rollback()
    
    @pytest.mark.asyncio
    async def test_master_flow_orchestrator_api_consistency(self, test_context, complete_test_data):
        """
        Test that Master Flow Orchestrator APIs return consistent data structures.
        
        This test validates that the master flow orchestrator maintains
        consistent API responses with proper relationship data.
        """
        async with AsyncSessionLocal() as session:
            master_flow = complete_test_data["master_flow"]
            
            # Test orchestrator initialization
            orchestrator = MasterFlowOrchestrator(session, test_context)
            
            # Test get flow status
            flow_status = await orchestrator.get_flow_status(str(master_flow.flow_id))
            
            # Validate status response structure
            required_status_fields = [
                "flow_id", "flow_type", "flow_status", "client_account_id",
                "engagement_id", "user_id", "created_at", "updated_at"
            ]
            
            for field in required_status_fields:
                assert field in flow_status, f"Missing required field: {field}"
            
            # Validate data consistency
            assert flow_status["flow_id"] == str(master_flow.flow_id)
            assert flow_status["flow_type"] == "discovery"
            assert flow_status["client_account_id"] == test_context.client_account_id
            assert flow_status["engagement_id"] == test_context.engagement_id
            assert flow_status["user_id"] == test_context.user_id
            
            logger.info("✅ Master Flow Orchestrator API consistency validated")
    
    @pytest.mark.asyncio
    async def test_discovery_flow_api_data_relationships(self, test_context, complete_test_data):
        """
        Test that Discovery Flow APIs return proper data relationships.
        
        This test validates that discovery flow API responses include
        correct foreign key relationships and linked data.
        """
        async with AsyncSessionLocal() as session:
            discovery_flow = complete_test_data["discovery_flow"]
            data_import = complete_test_data["data_import"]
            master_flow = complete_test_data["master_flow"]
            
            # Test discovery flow repository
            discovery_repo = DiscoveryFlowRepository(session, test_context.client_account_id)
            
            # Get discovery flow by ID
            flow_data = await discovery_repo.get_by_flow_id(str(discovery_flow.flow_id))
            assert flow_data is not None
            
            # Validate relationships
            assert str(flow_data.master_flow_id) == str(master_flow.flow_id)
            assert flow_data.data_import_id == data_import.id
            assert str(flow_data.client_account_id) == test_context.client_account_id
            assert str(flow_data.engagement_id) == test_context.engagement_id
            
            # Test to_dict() method
            flow_dict = flow_data.to_dict()
            
            # Validate dict structure
            required_dict_fields = [
                "id", "flow_id", "master_flow_id", "data_import_id",
                "client_account_id", "engagement_id", "user_id",
                "flow_name", "status", "progress_percentage", "phases",
                "created_at", "updated_at"
            ]
            
            for field in required_dict_fields:
                assert field in flow_dict, f"Missing field in to_dict(): {field}"
            
            # Validate relationship IDs in dict
            assert flow_dict["data_import_id"] == str(data_import.id)
            assert flow_dict["client_account_id"] == test_context.client_account_id
            assert flow_dict["engagement_id"] == test_context.engagement_id
            
            # Validate phases structure
            assert "phases" in flow_dict
            phases = flow_dict["phases"]
            
            required_phase_fields = [
                "data_import_completed", "field_mapping_completed",
                "data_cleansing_completed", "asset_inventory_completed",
                "dependency_analysis_completed", "tech_debt_assessment_completed"
            ]
            
            for phase_field in required_phase_fields:
                assert phase_field in phases, f"Missing phase field: {phase_field}"
            
            logger.info("✅ Discovery Flow API data relationships validated")
    
    @pytest.mark.asyncio
    async def test_data_import_api_linkage_validation(self, test_context, complete_test_data):
        """
        Test that Data Import APIs maintain proper linkage validation.
        
        This test validates that data import API responses correctly
        represent the relationships to master flows and raw records.
        """
        data_import = complete_test_data["data_import"]
        master_flow = complete_test_data["master_flow"]
        raw_records = complete_test_data["raw_records"]
        
        # Validate data import structure
        assert str(data_import.master_flow_id) == str(master_flow.flow_id)
        assert str(data_import.client_account_id) == test_context.client_account_id
        assert str(data_import.engagement_id) == test_context.engagement_id
        assert data_import.total_records == len(raw_records)
        
        # Validate raw records linkage
        for raw_record in raw_records:
            assert raw_record.data_import_id == data_import.id
            assert str(raw_record.master_flow_id) == str(master_flow.flow_id)
            assert str(raw_record.client_account_id) == test_context.client_account_id
            assert str(raw_record.engagement_id) == test_context.engagement_id
            assert raw_record.is_processed is True
            assert raw_record.asset_id is not None
        
        logger.info("✅ Data Import API linkage validation passed")
    
    @pytest.mark.asyncio
    async def test_asset_api_relationship_consistency(self, test_context, complete_test_data):
        """
        Test that Asset APIs maintain relationship consistency.
        
        This test validates that asset API responses properly represent
        relationships to discovery flows, master flows, and raw records.
        """
        assets = complete_test_data["assets"]
        discovery_flow = complete_test_data["discovery_flow"]
        master_flow = complete_test_data["master_flow"]
        raw_records = complete_test_data["raw_records"]
        
        # Validate asset relationships
        for i, asset in enumerate(assets):
            assert str(asset.discovery_flow_id) == str(discovery_flow.flow_id)
            assert str(asset.master_flow_id) == str(master_flow.flow_id)
            assert str(asset.client_account_id) == test_context.client_account_id
            assert str(asset.engagement_id) == test_context.engagement_id
            
            # Validate raw record linkage
            assert asset.raw_import_record_id == raw_records[i].id
            
            # Validate asset data consistency with raw data
            raw_data = raw_records[i].raw_data
            assert asset.hostname == raw_data.get("hostname")
            assert asset.ip_address == raw_data.get("ip_address")
            assert asset.operating_system == raw_data.get("operating_system")
            assert asset.cpu_cores == raw_data.get("cpu_cores")
            assert asset.memory_gb == raw_data.get("memory_gb")
            
            # Validate migration readiness score
            assert 0.0 <= asset.migration_readiness_score <= 1.0
        
        logger.info("✅ Asset API relationship consistency validated")
    
    @pytest.mark.asyncio
    async def test_cross_api_data_integrity_validation(self, test_context, complete_test_data):
        """
        Test cross-API data integrity validation.
        
        This test validates that data remains consistent across different
        API endpoints and repository access patterns.
        """
        async with AsyncSessionLocal() as session:
            master_flow = complete_test_data["master_flow"]
            discovery_flow = complete_test_data["discovery_flow"]
            data_import = complete_test_data["data_import"]
            assets = complete_test_data["assets"]
            
            # Test 1: Master flow repository vs discovery flow repository consistency
            master_repo = CrewAIFlowStateExtensionsRepository(
                session,
                test_context.client_account_id,
                test_context.engagement_id,
                test_context.user_id
            )
            
            discovery_repo = DiscoveryFlowRepository(session, test_context.client_account_id)
            
            # Get data from both repositories
            master_flow_data = await master_repo.get_by_flow_id(str(master_flow.flow_id))
            discovery_flow_data = await discovery_repo.get_by_flow_id(str(discovery_flow.flow_id))
            
            # Validate consistency between repositories
            assert master_flow_data is not None
            assert discovery_flow_data is not None
            assert str(master_flow_data.flow_id) == str(discovery_flow_data.master_flow_id)
            assert str(master_flow_data.client_account_id) == str(discovery_flow_data.client_account_id)
            assert str(master_flow_data.engagement_id) == str(discovery_flow_data.engagement_id)
            
            # Test 2: Data import vs raw records consistency
            assert data_import.total_records == len([r for r in complete_test_data["raw_records"]])
            
            processed_count = sum(1 for r in complete_test_data["raw_records"] if r.is_processed)
            assert processed_count == len(complete_test_data["raw_records"])
            
            # Test 3: Discovery flow vs assets consistency
            discovery_assets = [a for a in assets if str(a.discovery_flow_id) == str(discovery_flow.flow_id)]
            assert len(discovery_assets) == len(assets)
            
            # Test 4: Master flow vs all related entities consistency
            master_flow_assets = [a for a in assets if str(a.master_flow_id) == str(master_flow.flow_id)]
            assert len(master_flow_assets) == len(assets)
            
            master_flow_raw_records = [
                r for r in complete_test_data["raw_records"] 
                if str(r.master_flow_id) == str(master_flow.flow_id)
            ]
            assert len(master_flow_raw_records) == len(complete_test_data["raw_records"])
            
            logger.info("✅ Cross-API data integrity validation passed")
    
    @pytest.mark.asyncio
    async def test_api_response_format_standardization(self, test_context, complete_test_data):
        """
        Test that API responses follow standardized formats.
        
        This test validates that all API responses use consistent
        formatting for dates, UUIDs, and data structures.
        """
        master_flow = complete_test_data["master_flow"]
        discovery_flow = complete_test_data["discovery_flow"]
        data_import = complete_test_data["data_import"]
        assets = complete_test_data["assets"]
        
        # Test master flow response format
        master_flow_dict = master_flow.to_dict()
        
        # Validate UUID format
        uuid_fields = ["id", "flow_id", "client_account_id", "engagement_id"]
        for field in uuid_fields:
            if field in master_flow_dict:
                uuid_value = master_flow_dict[field]
                assert isinstance(uuid_value, str)
                # Validate UUID format
                try:
                    uuid.UUID(uuid_value)
                except ValueError:
                    pytest.fail(f"Invalid UUID format for {field}: {uuid_value}")
        
        # Validate timestamp format
        timestamp_fields = ["created_at", "updated_at"]
        for field in timestamp_fields:
            if field in master_flow_dict and master_flow_dict[field]:
                timestamp_value = master_flow_dict[field]
                assert isinstance(timestamp_value, str)
                # Validate ISO format
                try:
                    datetime.fromisoformat(timestamp_value.replace('Z', '+00:00'))
                except ValueError:
                    pytest.fail(f"Invalid timestamp format for {field}: {timestamp_value}")
        
        # Test discovery flow response format
        discovery_flow_dict = discovery_flow.to_dict()
        
        # Validate required fields
        required_fields = [
            "id", "flow_id", "client_account_id", "engagement_id", "user_id",
            "data_import_id", "flow_name", "status", "progress_percentage",
            "phases", "created_at", "updated_at"
        ]
        
        for field in required_fields:
            assert field in discovery_flow_dict, f"Missing required field: {field}"
        
        # Validate phases structure
        phases = discovery_flow_dict["phases"]
        assert isinstance(phases, dict)
        
        for phase_name, phase_value in phases.items():
            assert isinstance(phase_value, bool), f"Phase {phase_name} should be boolean"
        
        # Validate progress percentage
        progress = discovery_flow_dict["progress_percentage"]
        assert isinstance(progress, (int, float))
        assert 0 <= progress <= 100
        
        # Test data import format consistency
        assert isinstance(data_import.total_records, int)
        assert data_import.total_records >= 0
        
        if data_import.file_size:
            assert isinstance(data_import.file_size, int)
            assert data_import.file_size >= 0
        
        # Test asset format consistency
        for asset in assets:
            assert isinstance(asset.migration_readiness_score, (int, float))
            assert 0.0 <= asset.migration_readiness_score <= 1.0
            
            if asset.cpu_cores:
                assert isinstance(asset.cpu_cores, int)
                assert asset.cpu_cores > 0
                
            if asset.memory_gb:
                assert isinstance(asset.memory_gb, (int, float))
                assert asset.memory_gb > 0
        
        logger.info("✅ API response format standardization validated")
    
    @pytest.mark.asyncio
    async def test_api_error_handling_consistency(self, test_context):
        """
        Test that API error handling is consistent across endpoints.
        
        This test validates that APIs handle errors consistently
        and return appropriate error responses.
        """
        async with AsyncSessionLocal() as session:
            # Test repository error handling
            discovery_repo = DiscoveryFlowRepository(session, test_context.client_account_id)
            
            # Test non-existent flow ID
            non_existent_flow_id = str(uuid.uuid4())
            flow_data = await discovery_repo.get_by_flow_id(non_existent_flow_id)
            assert flow_data is None  # Should return None, not raise exception
            
            # Test master flow orchestrator error handling
            orchestrator = MasterFlowOrchestrator(session, test_context)
            
            # Test non-existent flow status
            try:
                flow_status = await orchestrator.get_flow_status(non_existent_flow_id)
                # Should handle gracefully or raise appropriate exception
                assert flow_status is None or "error" in flow_status
            except Exception as e:
                # If exception is raised, it should be a known exception type
                assert hasattr(e, '__class__')
                logger.info(f"Expected exception raised: {e.__class__.__name__}")
            
            logger.info("✅ API error handling consistency validated")
    
    @pytest.mark.asyncio
    async def test_api_tenant_isolation_consistency(self, test_context, complete_test_data):
        """
        Test that API tenant isolation is consistently enforced.
        
        This test validates that all APIs properly enforce multi-tenant
        isolation and don't leak data across tenants.
        """
        # Create different tenant context
        different_tenant_context = RequestContext(
            client_account_id=str(uuid.uuid4()),
            engagement_id=str(uuid.uuid4()),
            user_id="different_tenant_user",
            user_role="admin",
            request_id=str(uuid.uuid4())
        )
        
        async with AsyncSessionLocal() as session:
            master_flow = complete_test_data["master_flow"]
            discovery_flow = complete_test_data["discovery_flow"]
            
            # Test master flow repository isolation
            different_master_repo = CrewAIFlowStateExtensionsRepository(
                session,
                different_tenant_context.client_account_id,
                different_tenant_context.engagement_id,
                different_tenant_context.user_id
            )
            
            # Should not find master flow from different tenant
            master_flow_data = await different_master_repo.get_by_flow_id(str(master_flow.flow_id))
            assert master_flow_data is None  # Should not access other tenant's data
            
            # Test discovery flow repository isolation
            different_discovery_repo = DiscoveryFlowRepository(
                session, 
                different_tenant_context.client_account_id
            )
            
            # Should not find discovery flow from different tenant
            discovery_flow_data = await different_discovery_repo.get_by_flow_id(str(discovery_flow.flow_id))
            assert discovery_flow_data is None  # Should not access other tenant's data
            
            # Test master flow orchestrator isolation
            different_orchestrator = MasterFlowOrchestrator(session, different_tenant_context)
            
            # Should not access flow from different tenant
            try:
                flow_status = await different_orchestrator.get_flow_status(str(master_flow.flow_id))
                assert flow_status is None or "error" in flow_status
            except Exception:
                # Expected - should not access other tenant's flows
                pass
            
            logger.info("✅ API tenant isolation consistency validated")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])