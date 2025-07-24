#!/usr/bin/env python3
"""
Test script for master flow linkage and smart discovery functionality
Tests both Phase 1 (retroactive updates) and Phase 2 (smart discovery)
"""

import asyncio
import os
import sys

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import uuid

from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.models.data_import import DataImport, ImportFieldMapping, RawImportRecord
from app.services.data_import.storage_manager import ImportStorageManager
from app.services.master_flow_orchestrator import MasterFlowOrchestrator
from sqlalchemy import and_, func, select

# Test configuration using real orphaned data
TEST_FLOW_ID = "914ebf01-5174-4efa-9a81-5deb968dac60"  # Known orphaned flow
TEST_CLIENT_ACCOUNT_ID = (
    "21990f3a-abb6-4862-be06-cb6f854e167b"  # Real client with orphaned data
)
TEST_ENGAGEMENT_ID = (
    "58467010-6a72-44e8-ba37-cc0238724455"  # Real engagement with orphaned data
)
TEST_USER_ID = "demo-user-555"


async def test_orphaned_data_discovery():
    """Test discovery of orphaned data for a known flow ID"""
    print(f"\n🔍 Testing orphaned data discovery for flow: {TEST_FLOW_ID}")

    async with AsyncSessionLocal() as db:
        # Create test context
        context = RequestContext(
            client_account_id=TEST_CLIENT_ACCOUNT_ID,
            engagement_id=TEST_ENGAGEMENT_ID,
            user_id=TEST_USER_ID,
        )

        # Initialize Master Flow Orchestrator
        orchestrator = MasterFlowOrchestrator(db, context)

        try:
            # Test primary flow status (should fail for orphaned flow)
            print("📊 Testing primary flow status lookup...")
            try:
                status = await orchestrator.get_flow_status(
                    TEST_FLOW_ID, include_details=True
                )
                print(f"✅ Primary lookup succeeded: {status['status']}")

                # Check for orphaned data enhancement
                if status.get("metadata", {}).get("orphaned_data_found"):
                    print(
                        f"🔍 Orphaned data detected: {status['metadata']['orphaned_data_summary']}"
                    )

            except ValueError as e:
                print(f"❌ Primary lookup failed as expected: {e}")
                print("🔄 This will trigger smart discovery...")

                # The smart discovery should be triggered automatically
                # Let's test it directly
                smart_status = await orchestrator._smart_flow_discovery(
                    TEST_FLOW_ID, include_details=True
                )
                if smart_status:
                    print("✅ Smart discovery succeeded!")
                    print(
                        f"📊 Discovery method: {smart_status.get('discovery_method')}"
                    )
                    print(f"🎯 Confidence: {smart_status.get('confidence')}")

                    if "repair_options" in smart_status:
                        print(
                            f"🔧 Repair options available: {len(smart_status['repair_options'])}"
                        )
                        for option in smart_status["repair_options"]:
                            print(f"   - {option['title']}: {option['description']}")
                else:
                    print("❌ Smart discovery failed to find data")

        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback

            traceback.print_exc()


async def test_orphaned_data_repair():
    """Test repair of orphaned data"""
    print(f"\n🔧 Testing orphaned data repair for flow: {TEST_FLOW_ID}")

    async with AsyncSessionLocal() as db:
        # Create test context
        context = RequestContext(
            client_account_id=TEST_CLIENT_ACCOUNT_ID,
            engagement_id=TEST_ENGAGEMENT_ID,
            user_id=TEST_USER_ID,
        )

        # Initialize Master Flow Orchestrator
        orchestrator = MasterFlowOrchestrator(db, context)

        try:
            # First, find orphaned data to repair
            discovered_data = await orchestrator._find_related_data_by_context(
                TEST_FLOW_ID
            )
            if not discovered_data:
                discovered_data = await orchestrator._find_related_data_by_timestamp(
                    TEST_FLOW_ID
                )

            if discovered_data and "data_import" in discovered_data:
                data_import = discovered_data["data_import"]
                print(
                    f"📦 Found orphaned data import: {data_import.id} ({data_import.filename})"
                )

                # Test repair option
                repair_result = await orchestrator.repair_orphaned_data(
                    flow_id=TEST_FLOW_ID,
                    repair_option_id="link_orphaned_data",
                    data_import_id=str(data_import.id),
                )

                if repair_result["success"]:
                    print(f"✅ Repair succeeded: {repair_result['message']}")
                    print(f"📊 Details: {repair_result['details']}")
                else:
                    print(f"❌ Repair failed: {repair_result['message']}")
            else:
                print("❌ No orphaned data found to repair")

        except Exception as e:
            print(f"❌ Repair test failed with error: {e}")
            import traceback

            traceback.print_exc()


async def test_comprehensive_linkage():
    """Test comprehensive linkage for new flow creation"""
    print("\n🔗 Testing comprehensive master_flow_id linkage")

    async with AsyncSessionLocal() as db:
        # Create test context
        RequestContext(
            client_account_id=TEST_CLIENT_ACCOUNT_ID,
            engagement_id=TEST_ENGAGEMENT_ID,
            user_id=TEST_USER_ID,
        )

        # Create storage manager
        storage_manager = ImportStorageManager(db, TEST_CLIENT_ACCOUNT_ID)

        try:
            # Create a test data import
            test_import_id = uuid.uuid4()
            print(f"📦 Creating test data import: {test_import_id}")

            data_import = await storage_manager.find_or_create_import(
                import_id=test_import_id,
                engagement_id=TEST_ENGAGEMENT_ID,
                user_id=TEST_USER_ID,
                filename="test_linkage.csv",
                file_size=1024,
                file_type="text/csv",
                intended_type="servers",
            )

            # Create some test raw records
            test_data = [
                {"server_name": "test-server-1", "ip_address": "192.168.1.1"},
                {"server_name": "test-server-2", "ip_address": "192.168.1.2"},
            ]

            records_stored = await storage_manager.store_raw_records(
                data_import=data_import,
                file_data=test_data,
                engagement_id=TEST_ENGAGEMENT_ID,
            )
            print(f"📊 Stored {records_stored} test records")

            # Create field mappings
            mappings_created = await storage_manager.create_field_mappings(
                data_import=data_import, file_data=test_data
            )
            print(f"🗺️ Created {mappings_created} field mappings")

            # Test comprehensive linkage
            test_flow_id = str(uuid.uuid4())
            print(f"🔗 Testing comprehensive linkage with flow: {test_flow_id}")

            # First, we need to create a master flow record
            from app.models.crewai_flow_state_extensions import (
                CrewAIFlowStateExtensions,
            )

            master_flow = CrewAIFlowStateExtensions(
                flow_id=test_flow_id,
                client_account_id=TEST_CLIENT_ACCOUNT_ID,
                engagement_id=TEST_ENGAGEMENT_ID,
                user_id=TEST_USER_ID,
                flow_type="discovery",
                flow_name="Test Discovery Flow",
                flow_status="active",
                flow_configuration={"test": True},
            )
            db.add(master_flow)
            await db.flush()

            # Now test comprehensive linkage
            linkage_results = await storage_manager.update_all_records_with_flow(
                data_import_id=data_import.id, master_flow_id=test_flow_id
            )

            print(f"🎯 Linkage results: {linkage_results}")

            if linkage_results["success"]:
                print("✅ Comprehensive linkage test passed!")
                print(
                    f"   📦 DataImport updated: {linkage_results['data_import_updated']}"
                )
                print(
                    f"   📋 RawImportRecords updated: {linkage_results['raw_import_records_updated']}"
                )
                print(
                    f"   🗺️ FieldMappings updated: {linkage_results['field_mappings_updated']}"
                )
            else:
                print(f"❌ Comprehensive linkage failed: {linkage_results['error']}")

            # Clean up test data
            await db.commit()
            print("🧹 Test completed (data committed for inspection)")

        except Exception as e:
            print(f"❌ Comprehensive linkage test failed: {e}")
            import traceback

            traceback.print_exc()
            await db.rollback()


async def check_orphaned_data_status():
    """Check current status of orphaned data"""
    print("\n📊 Checking current orphaned data status")

    async with AsyncSessionLocal() as db:
        try:
            # Check orphaned DataImports
            orphaned_imports_query = select(DataImport).where(
                and_(
                    DataImport.client_account_id == TEST_CLIENT_ACCOUNT_ID,
                    DataImport.master_flow_id.is_(None),
                )
            )
            result = await db.execute(orphaned_imports_query)
            orphaned_imports = result.scalars().all()

            print(f"📦 Orphaned DataImports: {len(orphaned_imports)}")
            for import_record in orphaned_imports:
                print(
                    f"   - {import_record.id}: {import_record.filename} ({import_record.status})"
                )

            # Check orphaned RawImportRecords
            orphaned_raw_query = select(func.count(RawImportRecord.id)).where(
                and_(
                    RawImportRecord.client_account_id == TEST_CLIENT_ACCOUNT_ID,
                    RawImportRecord.master_flow_id.is_(None),
                )
            )
            result = await db.execute(orphaned_raw_query)
            orphaned_raw_count = result.scalar() or 0

            print(f"📋 Orphaned RawImportRecords: {orphaned_raw_count}")

            # Check orphaned ImportFieldMappings
            orphaned_mappings_query = select(func.count(ImportFieldMapping.id)).where(
                ImportFieldMapping.master_flow_id.is_(None)
            )
            result = await db.execute(orphaned_mappings_query)
            orphaned_mappings_count = result.scalar() or 0

            print(f"🗺️ Orphaned ImportFieldMappings: {orphaned_mappings_count}")

        except Exception as e:
            print(f"❌ Status check failed: {e}")
            import traceback

            traceback.print_exc()


async def main():
    """Run all tests"""
    print("🚀 Starting Master Flow Linkage Tests")
    print("=" * 60)

    await check_orphaned_data_status()
    await test_orphaned_data_discovery()
    await test_comprehensive_linkage()
    await test_orphaned_data_repair()

    print("\n" + "=" * 60)
    print("🏁 All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
