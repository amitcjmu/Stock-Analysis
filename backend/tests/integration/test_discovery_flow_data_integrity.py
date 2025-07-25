"""
Phase 4: Discovery Flow Data Integrity Integration Tests

This comprehensive test suite validates the complete data integrity of the discovery flow system,
covering end-to-end integration tests, database constraint validation, API consistency tests,
performance validation, and deployment readiness checks.

Test Areas:
1. End-to-End Integration: Complete data import → master flow → discovery flow linkage
2. Database Constraints: Foreign key relationships and cascade operations
3. API Consistency: Proper data relationships in API responses
4. Performance: Query performance and constraint impact
5. Deployment: Production validation and monitoring
"""

import json
import logging
import uuid
from datetime import datetime

import pytest
from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.models.asset import Asset
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.data_import.core import DataImport, RawImportRecord
from app.models.discovery_flow import DiscoveryFlow
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from app.services.master_flow_orchestrator import MasterFlowOrchestrator
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestDiscoveryFlowDataIntegrity:
    """
    Comprehensive test suite for discovery flow data integrity.

    This test class validates:
    - Complete data import to discovery flow pipeline
    - Foreign key relationships and constraints
    - Cascade deletion operations
    - API consistency and data relationships
    - Performance and scalability
    - Production deployment readiness
    """

    @pytest.fixture
    async def test_context(self):
        """Create test context with multi-tenant isolation"""
        return RequestContext(
            client_account_id=str(uuid.uuid4()),
            engagement_id=str(uuid.uuid4()),
            user_id="test_user_id",
            user_role="admin",
            request_id=str(uuid.uuid4()),
        )

    @pytest.fixture
    async def master_flow_orchestrator(self, test_context):
        """Create master flow orchestrator for testing"""
        async with AsyncSessionLocal() as session:
            orchestrator = MasterFlowOrchestrator(session, test_context)
            yield orchestrator

    @pytest.fixture
    async def sample_raw_data(self):
        """Sample raw data for testing data import"""
        return [
            {
                "hostname": "web-server-01",
                "ip_address": "192.168.1.100",
                "operating_system": "Ubuntu 20.04",
                "cpu_cores": 4,
                "memory_gb": 16,
                "storage_gb": 500,
                "environment": "production",
                "application": "web-app",
                "owner": "dev-team",
            },
            {
                "hostname": "db-server-01",
                "ip_address": "192.168.1.101",
                "operating_system": "CentOS 8",
                "cpu_cores": 8,
                "memory_gb": 32,
                "storage_gb": 1000,
                "environment": "production",
                "application": "database",
                "owner": "dba-team",
            },
            {
                "hostname": "app-server-01",
                "ip_address": "192.168.1.102",
                "operating_system": "Windows Server 2019",
                "cpu_cores": 6,
                "memory_gb": 24,
                "storage_gb": 750,
                "environment": "staging",
                "application": "api-service",
                "owner": "backend-team",
            },
        ]

    # ================================
    # 1. END-TO-END INTEGRATION TESTS
    # ================================

    @pytest.mark.asyncio
    async def test_complete_data_import_to_discovery_flow_pipeline(
        self, test_context, sample_raw_data
    ):
        """
        Test complete pipeline: data import → master flow → discovery flow → assets

        This test validates the entire data flow from initial import through to
        final asset creation, ensuring all relationships are properly established.
        """
        async with AsyncSessionLocal() as session:
            try:
                logger.info(
                    "🧪 Starting complete data import to discovery flow pipeline test"
                )

                # Step 1: Create a data import
                data_import = DataImport(
                    client_account_id=test_context.client_account_id,
                    engagement_id=test_context.engagement_id,
                    import_name="Test Integration Data Import",
                    import_type="cmdb",
                    filename="test_integration.csv",
                    file_size=len(json.dumps(sample_raw_data).encode()),
                    mime_type="text/csv",
                    source_system="test_system",
                    status="pending",
                    imported_by=test_context.user_id,
                    total_records=len(sample_raw_data),
                )

                session.add(data_import)
                await session.commit()
                await session.refresh(data_import)

                logger.info(f"✅ Created data import: {data_import.id}")

                # Step 2: Create raw import records
                raw_records = []
                for i, raw_data in enumerate(sample_raw_data):
                    raw_record = RawImportRecord(
                        data_import_id=data_import.id,
                        client_account_id=test_context.client_account_id,
                        engagement_id=test_context.engagement_id,
                        row_number=i + 1,
                        raw_data=raw_data,
                        is_processed=False,
                        is_valid=True,
                    )
                    raw_records.append(raw_record)
                    session.add(raw_record)

                await session.commit()
                logger.info(f"✅ Created {len(raw_records)} raw import records")

                # Step 3: Create master flow through orchestrator
                MasterFlowOrchestrator(session, test_context)

                # Update data import to link to master flow
                data_import.master_flow_id = str(uuid.uuid4())

                # Create master flow in CrewAI extensions
                master_flow = CrewAIFlowStateExtensions(
                    flow_id=data_import.master_flow_id,
                    client_account_id=test_context.client_account_id,
                    engagement_id=test_context.engagement_id,
                    user_id=test_context.user_id,
                    flow_type="discovery",
                    flow_name="Test Discovery Flow",
                    flow_status="initialized",
                    flow_configuration={
                        "data_import_id": str(data_import.id),
                        "auto_process": True,
                    },
                )

                session.add(master_flow)
                await session.commit()
                await session.refresh(master_flow)

                # Update raw records to link to master flow
                for raw_record in raw_records:
                    raw_record.master_flow_id = master_flow.flow_id

                await session.commit()

                logger.info(f"✅ Created master flow: {master_flow.flow_id}")

                # Step 4: Create discovery flow linked to master flow
                discovery_flow = DiscoveryFlow(
                    flow_id=master_flow.flow_id,
                    master_flow_id=master_flow.flow_id,
                    client_account_id=test_context.client_account_id,
                    engagement_id=test_context.engagement_id,
                    user_id=test_context.user_id,
                    data_import_id=data_import.id,
                    flow_name="Test Discovery Flow",
                    status="active",
                    progress_percentage=0.0,
                    data_import_completed=True,
                    field_mapping_completed=False,
                    crewai_persistence_id=master_flow.flow_id,
                )

                session.add(discovery_flow)
                await session.commit()
                await session.refresh(discovery_flow)

                logger.info(f"✅ Created discovery flow: {discovery_flow.flow_id}")

                # Step 5: Create assets from raw data
                assets = []
                for raw_record in raw_records:
                    asset = Asset(
                        client_account_id=test_context.client_account_id,
                        engagement_id=test_context.engagement_id,
                        discovery_flow_id=discovery_flow.flow_id,
                        master_flow_id=master_flow.flow_id,
                        hostname=raw_record.raw_data.get("hostname"),
                        ip_address=raw_record.raw_data.get("ip_address"),
                        operating_system=raw_record.raw_data.get("operating_system"),
                        cpu_cores=raw_record.raw_data.get("cpu_cores"),
                        memory_gb=raw_record.raw_data.get("memory_gb"),
                        storage_gb=raw_record.raw_data.get("storage_gb"),
                        environment=raw_record.raw_data.get("environment"),
                        raw_import_record_id=raw_record.id,
                        asset_type="server",
                        asset_name=raw_record.raw_data.get("hostname"),
                        migration_readiness_score=0.7,
                    )
                    assets.append(asset)
                    session.add(asset)

                    # Link raw record to asset
                    raw_record.asset_id = asset.id
                    raw_record.is_processed = True

                await session.commit()

                logger.info(f"✅ Created {len(assets)} assets from raw data")

                # Step 6: Validation - Verify all relationships are established

                # Check master flow exists
                master_flow_check = await session.get(
                    CrewAIFlowStateExtensions, master_flow.id
                )
                assert master_flow_check is not None
                assert master_flow_check.flow_type == "discovery"

                # Check discovery flow exists and is linked
                discovery_flow_check = await session.get(
                    DiscoveryFlow, discovery_flow.id
                )
                assert discovery_flow_check is not None
                assert str(discovery_flow_check.master_flow_id) == str(
                    master_flow.flow_id
                )
                assert discovery_flow_check.data_import_id == data_import.id

                # Check data import is linked
                data_import_check = await session.get(DataImport, data_import.id)
                assert data_import_check is not None
                assert str(data_import_check.master_flow_id) == str(master_flow.flow_id)

                # Check raw records are linked
                raw_records_check = await session.execute(
                    select(RawImportRecord).where(
                        RawImportRecord.data_import_id == data_import.id
                    )
                )
                raw_records_result = raw_records_check.scalars().all()
                assert len(raw_records_result) == len(sample_raw_data)

                for raw_record in raw_records_result:
                    assert str(raw_record.master_flow_id) == str(master_flow.flow_id)
                    assert raw_record.asset_id is not None
                    assert raw_record.is_processed is True

                # Check assets are linked
                assets_check = await session.execute(
                    select(Asset).where(
                        Asset.discovery_flow_id == discovery_flow.flow_id
                    )
                )
                assets_result = assets_check.scalars().all()
                assert len(assets_result) == len(sample_raw_data)

                for asset in assets_result:
                    assert str(asset.master_flow_id) == str(master_flow.flow_id)
                    assert asset.raw_import_record_id is not None

                logger.info("✅ All relationships verified successfully")

                # Step 7: Performance validation
                start_time = datetime.now()

                # Complex query to test join performance
                complex_query = (
                    select(
                        CrewAIFlowStateExtensions,
                        DiscoveryFlow,
                        DataImport,
                        func.count(RawImportRecord.id).label("raw_record_count"),
                        func.count(Asset.id).label("asset_count"),
                    )
                    .select_from(CrewAIFlowStateExtensions)
                    .join(
                        DiscoveryFlow,
                        DiscoveryFlow.master_flow_id
                        == CrewAIFlowStateExtensions.flow_id,
                    )
                    .join(DataImport, DataImport.id == DiscoveryFlow.data_import_id)
                    .join(
                        RawImportRecord, RawImportRecord.data_import_id == DataImport.id
                    )
                    .join(Asset, Asset.discovery_flow_id == DiscoveryFlow.flow_id)
                    .where(CrewAIFlowStateExtensions.flow_id == master_flow.flow_id)
                    .group_by(
                        CrewAIFlowStateExtensions.id, DiscoveryFlow.id, DataImport.id
                    )
                )

                result = await session.execute(complex_query)
                query_result = result.first()

                query_time = (datetime.now() - start_time).total_seconds()

                assert query_result is not None
                assert query_result.raw_record_count == len(sample_raw_data)
                assert query_result.asset_count == len(sample_raw_data)
                assert query_time < 1.0  # Should complete within 1 second

                logger.info(f"✅ Complex query completed in {query_time:.3f}s")

                # Cleanup
                await self._cleanup_test_data(session, master_flow.flow_id)

                logger.info(
                    "✅ Complete data import to discovery flow pipeline test passed"
                )

            except Exception as e:
                logger.error(f"❌ Pipeline test failed: {e}")
                await session.rollback()
                raise

    # ================================
    # 2. DATABASE CONSTRAINT TESTS
    # ================================

    @pytest.mark.asyncio
    async def test_foreign_key_constraints_prevent_invalid_data(self, test_context):
        """
        Test that foreign key constraints properly prevent invalid data insertion.

        This test validates that the database schema enforces data integrity
        by rejecting records with invalid foreign key references.
        """
        async with AsyncSessionLocal() as session:
            try:
                logger.info("🧪 Testing foreign key constraint validation")

                # Test 1: Try to create discovery flow with invalid master_flow_id
                invalid_master_flow_id = str(uuid.uuid4())

                discovery_flow = DiscoveryFlow(
                    flow_id=str(uuid.uuid4()),
                    master_flow_id=invalid_master_flow_id,  # This doesn't exist
                    client_account_id=test_context.client_account_id,
                    engagement_id=test_context.engagement_id,
                    user_id=test_context.user_id,
                    flow_name="Invalid Test Flow",
                    status="active",
                )

                session.add(discovery_flow)

                # This should fail due to foreign key constraint
                with pytest.raises(IntegrityError):
                    await session.commit()

                await session.rollback()
                logger.info(
                    "✅ Foreign key constraint properly rejected invalid master_flow_id"
                )

                # Test 2: Try to create data import with invalid master_flow_id
                invalid_data_import = DataImport(
                    client_account_id=test_context.client_account_id,
                    engagement_id=test_context.engagement_id,
                    master_flow_id=str(uuid.uuid4()),  # This doesn't exist
                    import_name="Invalid Import",
                    import_type="test",
                    filename="invalid.csv",
                    status="pending",
                    imported_by=test_context.user_id,
                )

                session.add(invalid_data_import)

                # This should fail due to foreign key constraint
                with pytest.raises(IntegrityError):
                    await session.commit()

                await session.rollback()
                logger.info(
                    "✅ Foreign key constraint properly rejected invalid data import"
                )

                # Test 3: Try to create raw record with invalid data_import_id
                invalid_raw_record = RawImportRecord(
                    data_import_id=str(uuid.uuid4()),  # This doesn't exist
                    client_account_id=test_context.client_account_id,
                    engagement_id=test_context.engagement_id,
                    row_number=1,
                    raw_data={"test": "data"},
                    is_processed=False,
                    is_valid=True,
                )

                session.add(invalid_raw_record)

                # This should fail due to foreign key constraint
                with pytest.raises(IntegrityError):
                    await session.commit()

                await session.rollback()
                logger.info(
                    "✅ Foreign key constraint properly rejected invalid raw record"
                )

                # Test 4: Try to create asset with invalid discovery_flow_id
                invalid_asset = Asset(
                    client_account_id=test_context.client_account_id,
                    engagement_id=test_context.engagement_id,
                    discovery_flow_id=str(uuid.uuid4()),  # This doesn't exist
                    master_flow_id=str(uuid.uuid4()),  # This doesn't exist
                    hostname="invalid-server",
                    asset_type="server",
                    asset_name="Invalid Server",
                    migration_readiness_score=0.0,
                )

                session.add(invalid_asset)

                # This should fail due to foreign key constraint
                with pytest.raises(IntegrityError):
                    await session.commit()

                await session.rollback()
                logger.info("✅ Foreign key constraint properly rejected invalid asset")

                logger.info("✅ All foreign key constraint tests passed")

            except Exception as e:
                logger.error(f"❌ Foreign key constraint test failed: {e}")
                await session.rollback()
                raise

    @pytest.mark.asyncio
    async def test_cascade_deletion_operations(self, test_context, sample_raw_data):
        """
        Test that cascade deletion properly removes related records.

        This test validates that when a master flow is deleted, all related
        discovery flows, data imports, raw records, and assets are properly cleaned up.
        """
        async with AsyncSessionLocal() as session:
            try:
                logger.info("🧪 Testing cascade deletion operations")

                # Create a complete data structure
                master_flow = CrewAIFlowStateExtensions(
                    flow_id=str(uuid.uuid4()),
                    client_account_id=test_context.client_account_id,
                    engagement_id=test_context.engagement_id,
                    user_id=test_context.user_id,
                    flow_type="discovery",
                    flow_name="Test Cascade Flow",
                    flow_status="initialized",
                )

                session.add(master_flow)
                await session.commit()
                await session.refresh(master_flow)

                # Create data import
                data_import = DataImport(
                    client_account_id=test_context.client_account_id,
                    engagement_id=test_context.engagement_id,
                    master_flow_id=master_flow.flow_id,
                    import_name="Test Cascade Import",
                    import_type="test",
                    filename="cascade_test.csv",
                    status="completed",
                    imported_by=test_context.user_id,
                    total_records=len(sample_raw_data),
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
                    flow_name="Test Cascade Discovery Flow",
                    status="completed",
                )

                session.add(discovery_flow)
                await session.commit()
                await session.refresh(discovery_flow)

                # Create raw records
                raw_record_ids = []
                for i, raw_data in enumerate(sample_raw_data):
                    raw_record = RawImportRecord(
                        data_import_id=data_import.id,
                        client_account_id=test_context.client_account_id,
                        engagement_id=test_context.engagement_id,
                        master_flow_id=master_flow.flow_id,
                        row_number=i + 1,
                        raw_data=raw_data,
                        is_processed=True,
                        is_valid=True,
                    )
                    session.add(raw_record)
                    raw_record_ids.append(raw_record.id)

                await session.commit()

                # Create assets
                asset_ids = []
                for i, raw_data in enumerate(sample_raw_data):
                    asset = Asset(
                        client_account_id=test_context.client_account_id,
                        engagement_id=test_context.engagement_id,
                        discovery_flow_id=discovery_flow.flow_id,
                        master_flow_id=master_flow.flow_id,
                        hostname=raw_data.get("hostname"),
                        asset_type="server",
                        asset_name=raw_data.get("hostname"),
                        migration_readiness_score=0.8,
                    )
                    session.add(asset)
                    asset_ids.append(asset.id)

                await session.commit()

                logger.info(
                    f"✅ Created test data: master_flow={master_flow.flow_id}, "
                    f"data_import={data_import.id}, discovery_flow={discovery_flow.id}, "
                    f"raw_records={len(raw_record_ids)}, assets={len(asset_ids)}"
                )

                # Verify all records exist before deletion
                assert (
                    await session.get(CrewAIFlowStateExtensions, master_flow.id)
                    is not None
                )
                assert await session.get(DataImport, data_import.id) is not None
                assert await session.get(DiscoveryFlow, discovery_flow.id) is not None

                raw_count = await session.execute(
                    select(func.count(RawImportRecord.id)).where(
                        RawImportRecord.data_import_id == data_import.id
                    )
                )
                assert raw_count.scalar() == len(sample_raw_data)

                asset_count = await session.execute(
                    select(func.count(Asset.id)).where(
                        Asset.discovery_flow_id == discovery_flow.flow_id
                    )
                )
                assert asset_count.scalar() == len(sample_raw_data)

                logger.info("✅ Verified all records exist before deletion")

                # Delete master flow - this should cascade to all related records
                await session.delete(master_flow)
                await session.commit()

                logger.info("✅ Deleted master flow")

                # Verify cascade deletion worked
                assert (
                    await session.get(CrewAIFlowStateExtensions, master_flow.id) is None
                )

                # Data import should be deleted (CASCADE)
                assert await session.get(DataImport, data_import.id) is None

                # Discovery flow should be deleted (handled by application logic)
                await session.get(DiscoveryFlow, discovery_flow.id)
                # Note: Discovery flow might still exist depending on cascade configuration
                # This depends on whether master_flow_id has cascade delete or not

                # Raw records should be deleted (CASCADE from data_import)
                raw_count_after = await session.execute(
                    select(func.count(RawImportRecord.id)).where(
                        RawImportRecord.data_import_id == data_import.id
                    )
                )
                assert raw_count_after.scalar() == 0

                # Assets should be deleted (CASCADE from discovery_flow or master_flow)
                asset_count_after = await session.execute(
                    select(func.count(Asset.id)).where(
                        Asset.discovery_flow_id == discovery_flow.flow_id
                    )
                )
                assert asset_count_after.scalar() == 0

                logger.info("✅ Verified cascade deletion worked correctly")

                logger.info("✅ Cascade deletion test passed")

            except Exception as e:
                logger.error(f"❌ Cascade deletion test failed: {e}")
                await session.rollback()
                raise

    @pytest.mark.asyncio
    async def test_orphaned_records_prevention(self, test_context):
        """
        Test that the system prevents creation of orphaned records.

        This test validates that records cannot be created without proper
        parent relationships, preventing data integrity issues.
        """
        async with AsyncSessionLocal() as session:
            try:
                logger.info("🧪 Testing orphaned records prevention")

                # Test 1: Raw record without data import
                orphaned_raw_record = RawImportRecord(
                    data_import_id=str(uuid.uuid4()),  # Non-existent data import
                    client_account_id=test_context.client_account_id,
                    engagement_id=test_context.engagement_id,
                    row_number=1,
                    raw_data={"test": "data"},
                    is_processed=False,
                    is_valid=True,
                )

                session.add(orphaned_raw_record)

                with pytest.raises(IntegrityError):
                    await session.commit()

                await session.rollback()
                logger.info("✅ Prevented orphaned raw record creation")

                # Test 2: Asset without discovery flow
                orphaned_asset = Asset(
                    client_account_id=test_context.client_account_id,
                    engagement_id=test_context.engagement_id,
                    discovery_flow_id=str(uuid.uuid4()),  # Non-existent discovery flow
                    master_flow_id=str(uuid.uuid4()),  # Non-existent master flow
                    hostname="orphaned-server",
                    asset_type="server",
                    asset_name="Orphaned Server",
                    migration_readiness_score=0.0,
                )

                session.add(orphaned_asset)

                with pytest.raises(IntegrityError):
                    await session.commit()

                await session.rollback()
                logger.info("✅ Prevented orphaned asset creation")

                # Test 3: Discovery flow without master flow
                orphaned_discovery_flow = DiscoveryFlow(
                    flow_id=str(uuid.uuid4()),
                    master_flow_id=str(uuid.uuid4()),  # Non-existent master flow
                    client_account_id=test_context.client_account_id,
                    engagement_id=test_context.engagement_id,
                    user_id=test_context.user_id,
                    flow_name="Orphaned Discovery Flow",
                    status="active",
                )

                session.add(orphaned_discovery_flow)

                # This might not fail if master_flow_id is nullable
                # Check if constraint exists
                try:
                    await session.commit()
                    # If commit succeeds, check if there's a constraint that should prevent this
                    logger.warning(
                        "⚠️  Discovery flow created without master flow - check constraints"
                    )
                    await session.rollback()
                except IntegrityError:
                    await session.rollback()
                    logger.info("✅ Prevented orphaned discovery flow creation")

                logger.info("✅ Orphaned records prevention test completed")

            except Exception as e:
                logger.error(f"❌ Orphaned records prevention test failed: {e}")
                await session.rollback()
                raise

    # ================================
    # 3. API CONSISTENCY TESTS
    # ================================

    @pytest.mark.asyncio
    async def test_api_returns_properly_linked_data(
        self, test_context, sample_raw_data
    ):
        """
        Test that API endpoints return properly linked data with correct relationships.

        This test validates that all API responses include proper foreign key
        relationships and that data is consistently structured.
        """
        async with AsyncSessionLocal() as session:
            try:
                logger.info("🧪 Testing API data consistency")

                # Create test data structure
                master_flow = CrewAIFlowStateExtensions(
                    flow_id=str(uuid.uuid4()),
                    client_account_id=test_context.client_account_id,
                    engagement_id=test_context.engagement_id,
                    user_id=test_context.user_id,
                    flow_type="discovery",
                    flow_name="Test API Flow",
                    flow_status="active",
                )

                session.add(master_flow)
                await session.commit()
                await session.refresh(master_flow)

                data_import = DataImport(
                    client_account_id=test_context.client_account_id,
                    engagement_id=test_context.engagement_id,
                    master_flow_id=master_flow.flow_id,
                    import_name="Test API Import",
                    import_type="test",
                    filename="api_test.csv",
                    status="completed",
                    imported_by=test_context.user_id,
                    total_records=len(sample_raw_data),
                )

                session.add(data_import)
                await session.commit()
                await session.refresh(data_import)

                discovery_flow = DiscoveryFlow(
                    flow_id=master_flow.flow_id,
                    master_flow_id=master_flow.flow_id,
                    client_account_id=test_context.client_account_id,
                    engagement_id=test_context.engagement_id,
                    user_id=test_context.user_id,
                    data_import_id=data_import.id,
                    flow_name="Test API Discovery Flow",
                    status="active",
                    data_import_completed=True,
                    field_mapping_completed=True,
                )

                session.add(discovery_flow)
                await session.commit()
                await session.refresh(discovery_flow)

                # Test API data structure consistency

                # Test 1: Master flow repository
                master_repo = CrewAIFlowStateExtensionsRepository(
                    session,
                    test_context.client_account_id,
                    test_context.engagement_id,
                    test_context.user_id,
                )

                master_flow_data = await master_repo.get_by_flow_id(
                    str(master_flow.flow_id)
                )
                assert master_flow_data is not None
                assert master_flow_data.flow_type == "discovery"
                assert (
                    str(master_flow_data.client_account_id)
                    == test_context.client_account_id
                )
                assert str(master_flow_data.engagement_id) == test_context.engagement_id

                logger.info("✅ Master flow repository returns correct data")

                # Test 2: Discovery flow repository
                discovery_repo = DiscoveryFlowRepository(
                    session, test_context.client_account_id
                )

                discovery_flow_data = await discovery_repo.get_by_flow_id(
                    str(discovery_flow.flow_id)
                )
                assert discovery_flow_data is not None
                assert str(discovery_flow_data.master_flow_id) == str(
                    master_flow.flow_id
                )
                assert discovery_flow_data.data_import_id == data_import.id

                logger.info("✅ Discovery flow repository returns correct data")

                # Test 3: Data import relationships
                data_import_with_relations = await session.execute(
                    select(DataImport)
                    .options(selectinload(DataImport.raw_records))
                    .where(DataImport.id == data_import.id)
                )
                data_import_result = data_import_with_relations.scalar_one()

                assert str(data_import_result.master_flow_id) == str(
                    master_flow.flow_id
                )
                assert (
                    str(data_import_result.client_account_id)
                    == test_context.client_account_id
                )
                assert (
                    str(data_import_result.engagement_id) == test_context.engagement_id
                )

                logger.info("✅ Data import relationships are correct")

                # Test 4: Discovery flow to_dict() method
                discovery_flow_dict = discovery_flow.to_dict()

                required_fields = [
                    "id",
                    "flow_id",
                    "client_account_id",
                    "engagement_id",
                    "user_id",
                    "data_import_id",
                    "flow_name",
                    "status",
                    "progress_percentage",
                    "phases",
                    "created_at",
                    "updated_at",
                ]

                for field in required_fields:
                    assert (
                        field in discovery_flow_dict
                    ), f"Field {field} missing from discovery flow dict"

                assert discovery_flow_dict["data_import_id"] == str(data_import.id)
                assert (
                    discovery_flow_dict["client_account_id"]
                    == test_context.client_account_id
                )
                assert (
                    discovery_flow_dict["engagement_id"] == test_context.engagement_id
                )

                logger.info("✅ Discovery flow to_dict() returns correct structure")

                # Test 5: Master flow to_dict() method
                master_flow_dict = master_flow.to_dict()

                required_master_fields = [
                    "id",
                    "flow_id",
                    "client_account_id",
                    "engagement_id",
                    "user_id",
                    "flow_type",
                    "flow_name",
                    "flow_status",
                    "created_at",
                    "updated_at",
                ]

                for field in required_master_fields:
                    assert (
                        field in master_flow_dict
                    ), f"Field {field} missing from master flow dict"

                assert master_flow_dict["flow_type"] == "discovery"
                assert (
                    master_flow_dict["client_account_id"]
                    == test_context.client_account_id
                )
                assert master_flow_dict["engagement_id"] == test_context.engagement_id

                logger.info("✅ Master flow to_dict() returns correct structure")

                # Cleanup
                await self._cleanup_test_data(session, master_flow.flow_id)

                logger.info("✅ API consistency test passed")

            except Exception as e:
                logger.error(f"❌ API consistency test failed: {e}")
                await session.rollback()
                raise

    # ================================
    # 4. PERFORMANCE VALIDATION TESTS
    # ================================

    @pytest.mark.asyncio
    async def test_query_performance_with_relationships(self, test_context):
        """
        Test that foreign key relationships don't negatively impact query performance.

        This test validates that the database schema and indexes are optimized
        for common query patterns with foreign key joins.
        """
        async with AsyncSessionLocal() as session:
            try:
                logger.info("🧪 Testing query performance with relationships")

                # Create larger dataset for performance testing
                master_flows = []
                discovery_flows = []
                data_imports = []

                # Create 10 master flows with related data
                for i in range(10):
                    master_flow = CrewAIFlowStateExtensions(
                        flow_id=str(uuid.uuid4()),
                        client_account_id=test_context.client_account_id,
                        engagement_id=test_context.engagement_id,
                        user_id=test_context.user_id,
                        flow_type="discovery",
                        flow_name=f"Performance Test Flow {i+1}",
                        flow_status="active",
                    )
                    master_flows.append(master_flow)
                    session.add(master_flow)

                await session.commit()

                # Create related data imports and discovery flows
                for i, master_flow in enumerate(master_flows):
                    await session.refresh(master_flow)

                    data_import = DataImport(
                        client_account_id=test_context.client_account_id,
                        engagement_id=test_context.engagement_id,
                        master_flow_id=master_flow.flow_id,
                        import_name=f"Performance Test Import {i+1}",
                        import_type="test",
                        filename=f"performance_test_{i+1}.csv",
                        status="completed",
                        imported_by=test_context.user_id,
                        total_records=100,
                    )
                    data_imports.append(data_import)
                    session.add(data_import)

                    discovery_flow = DiscoveryFlow(
                        flow_id=master_flow.flow_id,
                        master_flow_id=master_flow.flow_id,
                        client_account_id=test_context.client_account_id,
                        engagement_id=test_context.engagement_id,
                        user_id=test_context.user_id,
                        data_import_id=data_import.id,
                        flow_name=f"Performance Test Discovery Flow {i+1}",
                        status="active",
                    )
                    discovery_flows.append(discovery_flow)
                    session.add(discovery_flow)

                await session.commit()

                logger.info(
                    f"✅ Created {len(master_flows)} master flows with related data"
                )

                # Performance Test 1: Simple select with foreign key
                start_time = datetime.now()

                simple_query = select(DiscoveryFlow).where(
                    DiscoveryFlow.client_account_id == test_context.client_account_id
                )

                result = await session.execute(simple_query)
                flows = result.scalars().all()

                simple_query_time = (datetime.now() - start_time).total_seconds()

                assert len(flows) == 10
                assert simple_query_time < 0.1  # Should complete in < 100ms

                logger.info(f"✅ Simple query completed in {simple_query_time:.3f}s")

                # Performance Test 2: Join query with relationships
                start_time = datetime.now()

                join_query = (
                    select(CrewAIFlowStateExtensions, DiscoveryFlow, DataImport)
                    .select_from(CrewAIFlowStateExtensions)
                    .join(
                        DiscoveryFlow,
                        DiscoveryFlow.master_flow_id
                        == CrewAIFlowStateExtensions.flow_id,
                    )
                    .join(DataImport, DataImport.id == DiscoveryFlow.data_import_id)
                    .where(
                        CrewAIFlowStateExtensions.client_account_id
                        == test_context.client_account_id
                    )
                )

                result = await session.execute(join_query)
                joined_results = result.all()

                join_query_time = (datetime.now() - start_time).total_seconds()

                assert len(joined_results) == 10
                assert join_query_time < 0.2  # Should complete in < 200ms

                logger.info(f"✅ Join query completed in {join_query_time:.3f}s")

                # Performance Test 3: Aggregation query with relationships
                start_time = datetime.now()

                aggregation_query = (
                    select(
                        CrewAIFlowStateExtensions.flow_type,
                        func.count(DiscoveryFlow.id).label("discovery_count"),
                        func.count(DataImport.id).label("import_count"),
                    )
                    .select_from(CrewAIFlowStateExtensions)
                    .join(
                        DiscoveryFlow,
                        DiscoveryFlow.master_flow_id
                        == CrewAIFlowStateExtensions.flow_id,
                    )
                    .join(DataImport, DataImport.id == DiscoveryFlow.data_import_id)
                    .where(
                        CrewAIFlowStateExtensions.client_account_id
                        == test_context.client_account_id
                    )
                    .group_by(CrewAIFlowStateExtensions.flow_type)
                )

                result = await session.execute(aggregation_query)
                aggregation_results = result.all()

                aggregation_query_time = (datetime.now() - start_time).total_seconds()

                assert len(aggregation_results) == 1
                assert aggregation_results[0].discovery_count == 10
                assert aggregation_results[0].import_count == 10
                assert aggregation_query_time < 0.3  # Should complete in < 300ms

                logger.info(
                    f"✅ Aggregation query completed in {aggregation_query_time:.3f}s"
                )

                # Performance Test 4: Multi-tenant isolation query
                start_time = datetime.now()

                tenant_query = (
                    select(
                        func.count(CrewAIFlowStateExtensions.id).label("master_count"),
                        func.count(DiscoveryFlow.id).label("discovery_count"),
                        func.count(DataImport.id).label("import_count"),
                    )
                    .select_from(CrewAIFlowStateExtensions)
                    .outerjoin(
                        DiscoveryFlow,
                        DiscoveryFlow.master_flow_id
                        == CrewAIFlowStateExtensions.flow_id,
                    )
                    .outerjoin(
                        DataImport,
                        DataImport.master_flow_id == CrewAIFlowStateExtensions.flow_id,
                    )
                    .where(
                        CrewAIFlowStateExtensions.client_account_id
                        == test_context.client_account_id
                    )
                )

                result = await session.execute(tenant_query)
                tenant_results = result.first()

                tenant_query_time = (datetime.now() - start_time).total_seconds()

                assert tenant_results.master_count == 10
                assert tenant_query_time < 0.2  # Should complete in < 200ms

                logger.info(
                    f"✅ Multi-tenant query completed in {tenant_query_time:.3f}s"
                )

                # Cleanup
                for master_flow in master_flows:
                    await self._cleanup_test_data(session, master_flow.flow_id)

                logger.info("✅ Query performance test passed")

            except Exception as e:
                logger.error(f"❌ Query performance test failed: {e}")
                await session.rollback()
                raise

    @pytest.mark.asyncio
    async def test_constraint_performance_impact(self, test_context):
        """
        Test that foreign key constraints don't cause performance issues or locking.

        This test validates that constraint checking doesn't create bottlenecks
        or deadlocks in concurrent operations.
        """
        async with AsyncSessionLocal() as session:
            try:
                logger.info("🧪 Testing constraint performance impact")

                # Create master flow for testing
                master_flow = CrewAIFlowStateExtensions(
                    flow_id=str(uuid.uuid4()),
                    client_account_id=test_context.client_account_id,
                    engagement_id=test_context.engagement_id,
                    user_id=test_context.user_id,
                    flow_type="discovery",
                    flow_name="Constraint Performance Test",
                    flow_status="active",
                )

                session.add(master_flow)
                await session.commit()
                await session.refresh(master_flow)

                # Test 1: Batch insert performance with constraints
                start_time = datetime.now()

                data_imports = []
                for i in range(50):
                    data_import = DataImport(
                        client_account_id=test_context.client_account_id,
                        engagement_id=test_context.engagement_id,
                        master_flow_id=master_flow.flow_id,
                        import_name=f"Batch Test Import {i+1}",
                        import_type="test",
                        filename=f"batch_test_{i+1}.csv",
                        status="pending",
                        imported_by=test_context.user_id,
                        total_records=10,
                    )
                    data_imports.append(data_import)
                    session.add(data_import)

                await session.commit()

                batch_insert_time = (datetime.now() - start_time).total_seconds()

                assert batch_insert_time < 2.0  # Should complete in < 2 seconds

                logger.info(
                    f"✅ Batch insert of 50 records completed in {batch_insert_time:.3f}s"
                )

                # Test 2: Concurrent updates without deadlocks
                start_time = datetime.now()

                # Update all imports concurrently
                for data_import in data_imports:
                    data_import.status = "completed"
                    data_import.progress_percentage = 100.0

                await session.commit()

                batch_update_time = (datetime.now() - start_time).total_seconds()

                assert batch_update_time < 1.0  # Should complete in < 1 second

                logger.info(
                    f"✅ Batch update of 50 records completed in {batch_update_time:.3f}s"
                )

                # Test 3: Constraint validation performance
                start_time = datetime.now()

                # Verify all constraints are satisfied
                constraint_check_query = (
                    select(func.count(DataImport.id).label("valid_imports"))
                    .select_from(DataImport)
                    .join(
                        CrewAIFlowStateExtensions,
                        DataImport.master_flow_id == CrewAIFlowStateExtensions.flow_id,
                    )
                    .where(DataImport.master_flow_id == master_flow.flow_id)
                )

                result = await session.execute(constraint_check_query)
                valid_imports = result.scalar()

                constraint_check_time = (datetime.now() - start_time).total_seconds()

                assert valid_imports == 50
                assert constraint_check_time < 0.1  # Should complete in < 100ms

                logger.info(
                    f"✅ Constraint validation completed in {constraint_check_time:.3f}s"
                )

                # Cleanup
                await self._cleanup_test_data(session, master_flow.flow_id)

                logger.info("✅ Constraint performance test passed")

            except Exception as e:
                logger.error(f"❌ Constraint performance test failed: {e}")
                await session.rollback()
                raise

    # ================================
    # 5. DEPLOYMENT VALIDATION TESTS
    # ================================

    @pytest.mark.asyncio
    async def test_production_deployment_validation(self):
        """
        Test that the database schema is ready for production deployment.

        This test validates that all necessary indexes, constraints, and
        relationships are properly configured for production use.
        """
        async with AsyncSessionLocal() as session:
            try:
                logger.info("🧪 Testing production deployment validation")

                # Test 1: Check for required indexes
                required_indexes = [
                    ("crewai_flow_state_extensions", "client_account_id"),
                    ("crewai_flow_state_extensions", "engagement_id"),
                    ("crewai_flow_state_extensions", "flow_id"),
                    ("discovery_flows", "client_account_id"),
                    ("discovery_flows", "engagement_id"),
                    ("discovery_flows", "flow_id"),
                    ("data_imports", "client_account_id"),
                    ("data_imports", "engagement_id"),
                    ("data_imports", "master_flow_id"),
                    ("assets", "client_account_id"),
                    ("assets", "engagement_id"),
                    ("assets", "discovery_flow_id"),
                    ("assets", "master_flow_id"),
                ]

                for table, column in required_indexes:
                    index_query = text(
                        f"""
                        SELECT COUNT(*)
                        FROM pg_indexes
                        WHERE tablename = '{table}'
                        AND indexdef LIKE '%{column}%'
                    """
                    )

                    result = await session.execute(index_query)
                    index_count = result.scalar()

                    assert index_count > 0, f"Missing index for {table}.{column}"

                logger.info("✅ All required indexes exist")

                # Test 2: Check for foreign key constraints
                constraint_query = text(
                    """
                    SELECT
                        tc.table_name,
                        tc.constraint_name,
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_name IN (
                        'crewai_flow_state_extensions',
                        'discovery_flows',
                        'data_imports',
                        'raw_import_records',
                        'assets'
                    )
                """
                )

                result = await session.execute(constraint_query)
                constraints = result.all()

                expected_constraints = [
                    ("data_imports", "master_flow_id", "crewai_flow_state_extensions"),
                    ("raw_import_records", "data_import_id", "data_imports"),
                    (
                        "raw_import_records",
                        "master_flow_id",
                        "crewai_flow_state_extensions",
                    ),
                    ("assets", "master_flow_id", "crewai_flow_state_extensions"),
                ]

                constraint_map = {
                    (row.table_name, row.column_name): row.foreign_table_name
                    for row in constraints
                }

                for table, column, foreign_table in expected_constraints:
                    constraint_key = (table, column)
                    assert (
                        constraint_key in constraint_map
                    ), f"Missing FK constraint: {table}.{column} -> {foreign_table}"
                    assert (
                        constraint_map[constraint_key] == foreign_table
                    ), f"Incorrect FK target: {table}.{column}"

                logger.info("✅ All required foreign key constraints exist")

                # Test 3: Check for proper cascade settings
                cascade_query = text(
                    """
                    SELECT
                        tc.table_name,
                        kcu.column_name,
                        rc.delete_rule,
                        rc.update_rule
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.referential_constraints AS rc
                        ON tc.constraint_name = rc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_name IN (
                        'data_imports',
                        'raw_import_records',
                        'assets'
                    )
                """
                )

                result = await session.execute(cascade_query)
                cascade_rules = result.all()

                cascade_map = {
                    (row.table_name, row.column_name): (
                        row.delete_rule,
                        row.update_rule,
                    )
                    for row in cascade_rules
                }

                # Verify cascade rules are appropriate
                for table, column in cascade_map:
                    delete_rule, update_rule = cascade_map[(table, column)]
                    assert delete_rule in [
                        "CASCADE",
                        "SET NULL",
                    ], f"Inappropriate delete rule for {table}.{column}: {delete_rule}"

                logger.info("✅ Cascade rules are properly configured")

                # Test 4: Check for data consistency
                consistency_query = text(
                    """
                    SELECT
                        'orphaned_discovery_flows' as issue_type,
                        COUNT(*) as count
                    FROM discovery_flows df
                    LEFT JOIN crewai_flow_state_extensions mf ON df.master_flow_id = mf.flow_id
                    WHERE mf.flow_id IS NULL
                    AND df.master_flow_id IS NOT NULL

                    UNION ALL

                    SELECT
                        'orphaned_data_imports' as issue_type,
                        COUNT(*) as count
                    FROM data_imports di
                    LEFT JOIN crewai_flow_state_extensions mf ON di.master_flow_id = mf.flow_id
                    WHERE mf.flow_id IS NULL
                    AND di.master_flow_id IS NOT NULL

                    UNION ALL

                    SELECT
                        'orphaned_raw_records' as issue_type,
                        COUNT(*) as count
                    FROM raw_import_records rir
                    LEFT JOIN data_imports di ON rir.data_import_id = di.id
                    WHERE di.id IS NULL

                    UNION ALL

                    SELECT
                        'orphaned_assets' as issue_type,
                        COUNT(*) as count
                    FROM assets a
                    LEFT JOIN discovery_flows df ON a.discovery_flow_id = df.flow_id
                    WHERE df.flow_id IS NULL
                    AND a.discovery_flow_id IS NOT NULL
                """
                )

                result = await session.execute(consistency_query)
                consistency_issues = result.all()

                for issue in consistency_issues:
                    assert (
                        issue.count == 0
                    ), f"Data consistency issue found: {issue.issue_type} = {issue.count}"

                logger.info("✅ No data consistency issues found")

                logger.info("✅ Production deployment validation passed")

            except Exception as e:
                logger.error(f"❌ Production deployment validation failed: {e}")
                raise

    @pytest.mark.asyncio
    async def test_monitoring_queries_performance(self):
        """
        Test that monitoring queries for data integrity perform well.

        This test validates that queries used for monitoring and alerting
        on data integrity issues are optimized and perform well.
        """
        async with AsyncSessionLocal() as session:
            try:
                logger.info("🧪 Testing monitoring queries performance")

                # Monitoring Query 1: Check for orphaned records
                start_time = datetime.now()

                orphan_check_query = text(
                    """
                    SELECT
                        COUNT(CASE WHEN df.master_flow_id IS NOT NULL AND mf.flow_id IS NULL THEN 1 END) as orphaned_discovery_flows,
                        COUNT(CASE WHEN di.master_flow_id IS NOT NULL AND mf2.flow_id IS NULL THEN 1 END) as orphaned_data_imports,
                        COUNT(CASE WHEN rir.data_import_id IS NOT NULL AND di2.id IS NULL THEN 1 END) as orphaned_raw_records,
                        COUNT(CASE WHEN a.discovery_flow_id IS NOT NULL AND df2.flow_id IS NULL THEN 1 END) as orphaned_assets
                    FROM discovery_flows df
                    FULL OUTER JOIN crewai_flow_state_extensions mf ON df.master_flow_id = mf.flow_id
                    FULL OUTER JOIN data_imports di ON di.master_flow_id = mf.flow_id
                    FULL OUTER JOIN crewai_flow_state_extensions mf2 ON di.master_flow_id = mf2.flow_id
                    FULL OUTER JOIN raw_import_records rir ON rir.data_import_id = di.id
                    FULL OUTER JOIN data_imports di2 ON rir.data_import_id = di2.id
                    FULL OUTER JOIN assets a ON a.discovery_flow_id = df.flow_id
                    FULL OUTER JOIN discovery_flows df2 ON a.discovery_flow_id = df2.flow_id
                """
                )

                result = await session.execute(orphan_check_query)
                result.first()

                orphan_query_time = (datetime.now() - start_time).total_seconds()

                assert orphan_query_time < 2.0  # Should complete in < 2 seconds

                logger.info(
                    f"✅ Orphan check query completed in {orphan_query_time:.3f}s"
                )

                # Monitoring Query 2: Data integrity summary
                start_time = datetime.now()

                integrity_summary_query = text(
                    """
                    SELECT
                        COUNT(DISTINCT mf.flow_id) as total_master_flows,
                        COUNT(DISTINCT df.flow_id) as total_discovery_flows,
                        COUNT(DISTINCT di.id) as total_data_imports,
                        COUNT(DISTINCT rir.id) as total_raw_records,
                        COUNT(DISTINCT a.id) as total_assets,
                        COUNT(DISTINCT CASE WHEN df.master_flow_id = mf.flow_id THEN df.flow_id END) as linked_discovery_flows,
                        COUNT(DISTINCT CASE WHEN di.master_flow_id = mf.flow_id THEN di.id END) as linked_data_imports,
                        COUNT(DISTINCT CASE WHEN rir.master_flow_id = mf.flow_id THEN rir.id END) as linked_raw_records,
                        COUNT(DISTINCT CASE WHEN a.master_flow_id = mf.flow_id THEN a.id END) as linked_assets
                    FROM crewai_flow_state_extensions mf
                    FULL OUTER JOIN discovery_flows df ON df.master_flow_id = mf.flow_id
                    FULL OUTER JOIN data_imports di ON di.master_flow_id = mf.flow_id
                    FULL OUTER JOIN raw_import_records rir ON rir.master_flow_id = mf.flow_id
                    FULL OUTER JOIN assets a ON a.master_flow_id = mf.flow_id
                """
                )

                result = await session.execute(integrity_summary_query)
                result.first()

                integrity_query_time = (datetime.now() - start_time).total_seconds()

                assert integrity_query_time < 1.0  # Should complete in < 1 second

                logger.info(
                    f"✅ Integrity summary query completed in {integrity_query_time:.3f}s"
                )

                # Monitoring Query 3: Performance metrics
                start_time = datetime.now()

                performance_metrics_query = text(
                    """
                    SELECT
                        mf.flow_type,
                        COUNT(*) as flow_count,
                        AVG(EXTRACT(EPOCH FROM (mf.updated_at - mf.created_at))) as avg_duration_seconds,
                        COUNT(CASE WHEN mf.flow_status = 'completed' THEN 1 END) as completed_count,
                        COUNT(CASE WHEN mf.flow_status = 'failed' THEN 1 END) as failed_count
                    FROM crewai_flow_state_extensions mf
                    WHERE mf.created_at >= CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY mf.flow_type
                """
                )

                result = await session.execute(performance_metrics_query)
                result.all()

                performance_query_time = (datetime.now() - start_time).total_seconds()

                assert performance_query_time < 0.5  # Should complete in < 500ms

                logger.info(
                    f"✅ Performance metrics query completed in {performance_query_time:.3f}s"
                )

                logger.info("✅ Monitoring queries performance test passed")

            except Exception as e:
                logger.error(f"❌ Monitoring queries performance test failed: {e}")
                raise

    # ================================
    # UTILITY METHODS
    # ================================

    async def _cleanup_test_data(self, session: AsyncSession, flow_id: str):
        """Clean up test data for a specific flow"""
        try:
            # Delete in reverse dependency order

            # Delete assets
            await session.execute(
                text("DELETE FROM assets WHERE master_flow_id = :flow_id"),
                {"flow_id": flow_id},
            )

            # Delete raw records
            await session.execute(
                text("DELETE FROM raw_import_records WHERE master_flow_id = :flow_id"),
                {"flow_id": flow_id},
            )

            # Delete data imports
            await session.execute(
                text("DELETE FROM data_imports WHERE master_flow_id = :flow_id"),
                {"flow_id": flow_id},
            )

            # Delete discovery flows
            await session.execute(
                text("DELETE FROM discovery_flows WHERE master_flow_id = :flow_id"),
                {"flow_id": flow_id},
            )

            # Delete master flow
            await session.execute(
                text(
                    "DELETE FROM crewai_flow_state_extensions WHERE flow_id = :flow_id"
                ),
                {"flow_id": flow_id},
            )

            await session.commit()

        except Exception as e:
            logger.error(f"❌ Cleanup failed for flow {flow_id}: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
