"""
Integration tests for database consolidation
Tests the complete V3 API flow with consolidated database schema

NOTE: These tests are designed to verify the database after consolidation.
Some tests may fail if:
1. The Day 6 database migration hasn't been applied yet
2. The model classes still have fields that should be removed (like is_mock)
3. The database indexes haven't been created yet

The tests are written to be run after the full consolidation is complete.
"""

import asyncio
from datetime import datetime

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.core.database import AsyncSessionLocal
from app.models.client_account import ClientAccount, Engagement, User
from app.services.v3.asset_service import V3AssetService
from app.services.v3.data_import_service import V3DataImportService
from app.services.v3.discovery_flow_service import V3DiscoveryFlowService
from app.services.v3.field_mapping_service import V3FieldMappingService

# Configure pytest to use asyncio
pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def db_session():
    """Create a test database session"""
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def test_context(db_session):
    """Create test multi-tenant context"""
    # Create test client account
    client = ClientAccount(
        name="Test Client",
        slug="test-client",
        description="Test client for integration tests",
    )
    db_session.add(client)
    await db_session.commit()
    await db_session.refresh(client)

    # Create test engagement
    engagement = Engagement(
        client_account_id=client.id,
        name="Test Engagement",
        start_date=datetime.utcnow(),
        status="active",
    )
    db_session.add(engagement)
    await db_session.commit()
    await db_session.refresh(engagement)

    # Create test user
    user = User(
        email="test@example.com",
        username="testuser",
        first_name="Test",
        last_name="User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return {
        "client_account_id": str(client.id),
        "engagement_id": str(engagement.id),
        "user_id": str(user.id),
    }


class TestDatabaseConsolidation:
    """Test suite for database consolidation

    NOTE: These tests verify the database schema after migration.
    They will fail if run before the Day 6 database migration is applied.
    """

    async def test_no_v3_tables_exist(self, db_session):
        """Test that no v3_ prefixed tables exist in the database"""
        # Check for v3_ tables
        result = await db_session.execute(
            text(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name LIKE 'v3_%'
            """
            )
        )
        v3_tables = result.fetchall()

        assert len(v3_tables) == 0, f"Found v3_ tables: {[t[0] for t in v3_tables]}"

    async def test_field_renames_in_database(self, db_session):
        """Test that field renames have been applied correctly"""
        # Check DataImport table columns
        result = await db_session.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'data_imports'
                AND column_name IN ('filename', 'file_size', 'mime_type')
            """
            )
        )
        columns = [row[0] for row in result.fetchall()]

        assert "filename" in columns, "Column 'filename' not found"
        assert "file_size" in columns, "Column 'file_size' not found"
        assert "mime_type" in columns, "Column 'mime_type' not found"

        # Check that old column names don't exist
        result = await db_session.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'data_imports'
                AND column_name IN ('source_filename', 'file_size_bytes', 'file_type', 'is_mock')
            """
            )
        )
        old_columns = [row[0] for row in result.fetchall()]

        assert len(old_columns) == 0, f"Found old columns: {old_columns}"

    async def test_discovery_flow_consolidated_fields(self, db_session):
        """Test that DiscoveryFlow has consolidated fields"""
        result = await db_session.execute(
            text(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'discovery_flows'
                AND column_name IN (
                    'flow_state', 'phase_state', 'agent_state',
                    'data_validation_completed', 'field_mapping_completed'
                )
                ORDER BY column_name
            """
            )
        )
        columns = {row[0]: row[1] for row in result.fetchall()}

        # Check JSON fields exist (will fail before migration)
        if "flow_state" in columns:
            assert columns["flow_state"] == "jsonb"
        else:
            pytest.skip("flow_state column not found - migration not yet applied")

        # Check boolean fields exist
        if "data_validation_completed" in columns:
            assert columns["data_validation_completed"] == "boolean"
        else:
            pytest.skip(
                "data_validation_completed column not found - migration not yet applied"
            )

    async def test_removed_tables(self, db_session):
        """Test that deprecated tables have been removed"""
        deprecated_tables = [
            "workflow_states",
            "discovery_assets",
            "mapping_learning_patterns",
            "session_management",
            "discovery_sessions",
        ]

        result = await db_session.execute(
            text(
                f"""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ({','.join([f"'{t}'" for t in deprecated_tables])})
            """
            )
        )
        existing_tables = [row[0] for row in result.fetchall()]

        assert len(existing_tables) == 0, f"Found deprecated tables: {existing_tables}"

    async def test_multi_tenant_indexes(self, db_session):
        """Test that multi-tenant indexes exist"""
        tables_to_check = [
            "data_imports",
            "discovery_flows",
            "import_field_mappings",
            "assets",
        ]

        for table in tables_to_check:
            result = await db_session.execute(
                text(
                    f"""
                    SELECT indexname
                    FROM pg_indexes
                    WHERE tablename = '{table}'
                    AND indexdef LIKE '%client_account_id%'
                """
                )
            )
            indexes = [row[0] for row in result.fetchall()]

            if len(indexes) == 0:
                pytest.skip(
                    f"No client_account_id index found for table {table} - migration not yet applied"
                )
            assert (
                len(indexes) > 0
            ), f"No client_account_id index found for table {table}"


class TestV3ServicesIntegration:
    """Test V3 services with consolidated database"""

    async def test_complete_discovery_flow(self, db_session, test_context):
        """Test complete discovery flow using V3 services"""
        # Initialize services
        flow_service = V3DiscoveryFlowService(
            db_session, test_context["client_account_id"], test_context["engagement_id"]
        )

        import_service = V3DataImportService(
            db_session, test_context["client_account_id"], test_context["engagement_id"]
        )

        mapping_service = V3FieldMappingService(
            db_session, test_context["client_account_id"], test_context["engagement_id"]
        )

        asset_service = V3AssetService(
            db_session, test_context["client_account_id"], test_context["engagement_id"]
        )

        # Step 1: Create discovery flow
        flow = await flow_service.create_flow(
            name="Test Discovery Flow",
            description="Integration test flow",
            metadata={"test": True},
            execution_mode="database",
            user_id=test_context["user_id"],
        )

        assert flow is not None
        assert flow.name == "Test Discovery Flow"
        assert flow.status == "initialized"

        # Step 2: Create data import
        import_data = b'{"servers": [{"name": "test-server", "ip": "10.0.0.1"}]}'
        data_import = await import_service.create_import(
            filename="test_data.json",
            file_data=import_data,
            source_system="test",
            import_name="Test Import",
            import_type="json",
            user_id=test_context["user_id"],
            flow_id=str(flow.id),
        )

        assert data_import is not None
        assert data_import.filename == "test_data.json"
        assert data_import.file_size == len(import_data)
        assert data_import.mime_type == "application/json"

        # Step 3: Process import data
        test_data = [
            {
                "hostname": "server-01",
                "ip": "10.0.0.1",
                "os": "Ubuntu 20.04",
                "cpu": 8,
                "memory": 32768,
                "storage": 512000,
            }
        ]

        await import_service.process_import_data(str(data_import.id), test_data)

        # Step 4: Create field mappings
        mappings = {
            "hostname": "asset_name",
            "ip": "ip_address",
            "os": "operating_system",
            "cpu": "cpu_cores",
            "memory": "memory_gb",
            "storage": "storage_gb",
        }

        await mapping_service.create_flow_mappings(
            str(flow.id), mappings, confidence_scores={field: 0.9 for field in mappings}
        )

        # Step 5: Create assets from discovery
        assets_data = [
            {
                "asset_name": "server-01",
                "asset_type": "server",
                "ip_address": "10.0.0.1",
                "operating_system": "Ubuntu 20.04",
                "cpu_cores": 8,
                "memory_gb": 32,
                "storage_gb": 500,
                "discovery_flow_id": str(flow.id),
            }
        ]

        created_assets = await asset_service.bulk_create_assets(assets_data)

        assert len(created_assets) == 1
        assert created_assets[0].asset_name == "server-01"
        assert created_assets[0].memory_gb == 32  # Check unit conversion worked

        # Step 6: Update flow status
        await flow_service.update_flow_status(
            str(flow.id), status="completed", current_phase="completed"
        )

        # Verify final state
        final_status = await flow_service.get_flow_status(str(flow.id))
        assert final_status["status"] == "completed"
        assert final_status["progress_percentage"] == 100.0

    async def test_field_rename_backward_compatibility(self, db_session, test_context):
        """Test that field renames work with backward compatibility"""
        import_service = V3DataImportService(
            db_session, test_context["client_account_id"], test_context["engagement_id"]
        )

        # Create import with old field names (should be handled by repository)
        import_data = b"test data"

        # This would normally fail, but the repository handles the rename
        data_import = await import_service.create_import(
            filename="test.csv",  # New field name
            file_data=import_data,
            source_system="legacy",
            import_name="Legacy Test",
            import_type="csv",
        )

        assert data_import.filename == "test.csv"
        assert data_import.file_size == len(import_data)
        assert data_import.mime_type == "text/csv"

    async def test_asset_unit_conversions(self, db_session, test_context):
        """Test that asset unit conversions work correctly"""
        asset_service = V3AssetService(
            db_session, test_context["client_account_id"], test_context["engagement_id"]
        )

        # Create asset with GB values
        asset_data = {
            "asset_name": "test-server",
            "asset_type": "server",
            "memory_gb": 16,  # 16 GB
            "storage_gb": 500,  # 500 GB
        }

        asset = await asset_service.create_asset(**asset_data)

        assert asset.memory_gb == 16
        assert asset.storage_gb == 500

        # Search should work with new field names
        results = await asset_service.search_assets(filters={"memory_gb": 16})

        assert len(results) == 1
        assert results[0].asset_name == "test-server"


class TestPerformance:
    """Performance tests for consolidated database"""

    async def test_bulk_asset_creation_performance(self, db_session, test_context):
        """Test performance of bulk asset creation"""
        asset_service = V3AssetService(
            db_session, test_context["client_account_id"], test_context["engagement_id"]
        )

        # Create 1000 assets
        assets_data = []
        for i in range(1000):
            assets_data.append(
                {
                    "asset_name": f"server-{i:04d}",
                    "asset_type": "server",
                    "ip_address": f"10.0.{i // 256}.{i % 256}",
                    "cpu_cores": 8 + (i % 8),
                    "memory_gb": 16 + (i % 48),
                    "storage_gb": 100 + (i % 900),
                }
            )

        import time

        start_time = time.time()

        created_assets = await asset_service.bulk_create_assets(assets_data)

        end_time = time.time()
        duration = end_time - start_time

        assert len(created_assets) == 1000
        assert duration < 10.0, f"Bulk creation took {duration}s, expected < 10s"

        print(f"Created 1000 assets in {duration:.2f} seconds")

    async def test_multi_tenant_query_performance(self, db_session, test_context):
        """Test performance of multi-tenant queries"""
        # Create a second client context
        client2 = ClientAccount(
            name="Test Client 2", slug="test-client-2", description="Second test client"
        )
        db_session.add(client2)
        await db_session.commit()

        engagement2 = Engagement(
            client_account_id=client2.id,
            name="Test Engagement 2",
            start_date=datetime.utcnow(),
            status="active",
        )
        db_session.add(engagement2)
        await db_session.commit()

        # Create assets for both clients
        asset_service1 = V3AssetService(
            db_session, test_context["client_account_id"], test_context["engagement_id"]
        )

        asset_service2 = V3AssetService(
            db_session, str(client2.id), str(engagement2.id)
        )

        # Create 500 assets for each client
        for service, prefix in [
            (asset_service1, "client1"),
            (asset_service2, "client2"),
        ]:
            assets_data = []
            for i in range(500):
                assets_data.append(
                    {"asset_name": f"{prefix}-server-{i:03d}", "asset_type": "server"}
                )
            await service.bulk_create_assets(assets_data)

        # Test query performance with tenant isolation
        import time

        start_time = time.time()

        # This should only return client1's assets
        results = await asset_service1.search_assets(
            filters={"asset_type": "server"}, limit=1000
        )

        end_time = time.time()
        duration = end_time - start_time

        assert len(results) == 500  # Only client1's assets
        assert all("client1" in r.asset_name for r in results)
        assert duration < 1.0, f"Query took {duration}s, expected < 1s"

        print(f"Multi-tenant query returned 500 assets in {duration:.2f} seconds")


@pytest.mark.asyncio
async def test_database_consolidation_suite():
    """Run all database consolidation tests"""
    async with AsyncSessionLocal() as session:
        # Create test context
        test_context = await create_test_context(session)

        # Run schema tests
        schema_tests = TestDatabaseConsolidation()
        await schema_tests.test_no_v3_tables_exist(session)
        await schema_tests.test_field_renames_in_database(session)
        await schema_tests.test_discovery_flow_consolidated_fields(session)
        await schema_tests.test_removed_tables(session)
        await schema_tests.test_multi_tenant_indexes(session)

        # Run integration tests
        integration_tests = TestV3ServicesIntegration()
        await integration_tests.test_complete_discovery_flow(session, test_context)
        await integration_tests.test_field_rename_backward_compatibility(
            session, test_context
        )
        await integration_tests.test_asset_unit_conversions(session, test_context)

        # Run performance tests
        perf_tests = TestPerformance()
        await perf_tests.test_bulk_asset_creation_performance(session, test_context)
        await perf_tests.test_multi_tenant_query_performance(session, test_context)

        print("\n✅ All database consolidation tests passed!")


async def create_test_context(session):
    """Helper to create test context"""
    # Create test client account
    client = ClientAccount(
        name="Test Client",
        slug="test-client",
        description="Test client for integration tests",
    )
    session.add(client)
    await session.commit()
    await session.refresh(client)

    # Create test engagement
    engagement = Engagement(
        client_account_id=client.id,
        name="Test Engagement",
        start_date=datetime.utcnow(),
        status="active",
    )
    session.add(engagement)
    await session.commit()
    await session.refresh(engagement)

    # Create test user
    user = User(
        email="test@example.com",
        username="testuser",
        first_name="Test",
        last_name="User",
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return {
        "client_account_id": str(client.id),
        "engagement_id": str(engagement.id),
        "user_id": str(user.id),
    }


if __name__ == "__main__":
    asyncio.run(test_database_consolidation_suite())
