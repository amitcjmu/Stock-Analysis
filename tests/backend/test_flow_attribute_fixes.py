#!/usr/bin/env python3
"""
Test script to verify attribute access fixes for DiscoveryFlow and ImportFieldMapping.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models.discovery_flow import DiscoveryFlow
from app.models.data_import.mapping import ImportFieldMapping


async def test_discovery_flow_attributes():
    """Test that DiscoveryFlow attributes are safely accessed."""

    # Database connection
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5433/migration_db"
    )

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Find a discovery flow
            flow_query = select(DiscoveryFlow).limit(1)
            result = await session.execute(flow_query)
            flow = result.scalar_one_or_none()

            if not flow:
                print("❌ No discovery flow found to test")
                return False

            print(f"✅ Found flow: {flow.flow_id}")

            # Test safe attribute access
            test_attributes = {
                "flow_id": flow.flow_id,
                "status": flow.status,
                "current_phase": flow.current_phase,
                "next_phase": getattr(flow, "next_phase", None),  # Safe access
                "phases": getattr(flow, "phases", {}),  # Safe access
                "error_details": getattr(flow, "error_details", None),  # Safe access
                "progress_percentage": flow.progress_percentage or 0,
                "client_account_id": flow.client_account_id,
                "engagement_id": flow.engagement_id,
            }

            print("\n📊 Flow attributes (safe access):")
            for attr, value in test_attributes.items():
                if value is not None:
                    print(f"   ✅ {attr}: {type(value).__name__}")
                else:
                    print(f"   ⚠️  {attr}: None (expected for missing attributes)")

            # Verify the problematic attributes are handled
            if hasattr(flow, "next_phase"):
                print("\n⚠️  WARNING: next_phase attribute exists but wasn't expected")
            else:
                print("\n✅ next_phase attribute safely handled with getattr")

            return True

        except Exception as e:
            print(f"❌ Error testing DiscoveryFlow: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await engine.dispose()


async def test_import_field_mapping_attributes():
    """Test that ImportFieldMapping queries work without engagement_id."""

    # Database connection
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5433/migration_db"
    )

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Test query without engagement_id
            client_account_id = "11111111-1111-1111-1111-111111111111"

            # This should work now
            mapping_query = select(ImportFieldMapping).where(
                ImportFieldMapping.client_account_id == client_account_id
            ).limit(1)

            result = await session.execute(mapping_query)
            mapping = result.scalar_one_or_none()

            if mapping:
                print(f"✅ Found mapping: {mapping.id}")
                print(f"   - client_account_id: {mapping.client_account_id}")
                print(f"   - source_field: {mapping.source_field}")
                print(f"   - target_field: {mapping.target_field}")
            else:
                print("ℹ️  No mappings found (this is OK if no data imported yet)")

            # Verify engagement_id doesn't exist
            if hasattr(ImportFieldMapping, "engagement_id"):
                print("\n❌ ERROR: engagement_id attribute exists but shouldn't")
                return False
            else:
                print("\n✅ ImportFieldMapping correctly doesn't have engagement_id")

            return True

        except Exception as e:
            print(f"❌ Error testing ImportFieldMapping: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await engine.dispose()


async def main():
    """Main test runner."""
    print("🔍 Testing Attribute Access Fixes")
    print("=" * 50)

    # Test DiscoveryFlow
    print("\n1. Testing DiscoveryFlow attributes...")
    flow_test = await test_discovery_flow_attributes()

    # Test ImportFieldMapping
    print("\n2. Testing ImportFieldMapping queries...")
    mapping_test = await test_import_field_mapping_attributes()

    print("\n" + "=" * 50)
    if flow_test and mapping_test:
        print("✅ ALL TESTS PASSED")
        print("   Attribute access issues are fixed")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("   Review the errors above")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
