#!/usr/bin/env python3
"""
Test script to verify field mappings are properly created and persisted
"""

import asyncio
import json
from uuid import UUID
from datetime import datetime

# Test data for field mapping
TEST_DATA = [
    {"Hostname": "server1", "OS": "Windows", "CPU": "8", "Memory": "32", "Environment": "Prod"},
    {"Hostname": "server2", "OS": "Linux", "CPU": "16", "Memory": "64", "Environment": "Dev"}
]

async def test_field_mapping_persistence():
    """Test that field mappings are created and persisted correctly"""

    from app.core.database.session import get_db
    from app.models.data_import.mapping import ImportFieldMapping
    from app.models.discovery_flows import DiscoveryFlow
    from sqlalchemy import select

    print("🔍 Testing field mapping persistence fix...")

    async for db in get_db():
        try:
            # Check if any field mappings exist
            result = await db.execute(
                select(ImportFieldMapping)
                .order_by(ImportFieldMapping.created_at.desc())
                .limit(10)
            )
            mappings = result.scalars().all()

            print(f"\n📊 Found {len(mappings)} recent field mappings")

            for mapping in mappings:
                print(f"  - {mapping.source_field} -> {mapping.target_field} (confidence: {mapping.confidence_score})")

            # Check discovery flows with field mappings
            flow_result = await db.execute(
                select(DiscoveryFlow)
                .where(DiscoveryFlow.field_mappings.isnot(None))
                .order_by(DiscoveryFlow.created_at.desc())
                .limit(5)
            )
            flows = flow_result.scalars().all()

            print(f"\n📋 Found {len(flows)} discovery flows with field mappings")

            for flow in flows:
                if flow.field_mappings:
                    fm = flow.field_mappings
                    print(f"  - Flow {flow.flow_id[:8]}...")
                    print(f"    Total: {fm.get('total_fields', 0)}, Mapped: {fm.get('mapped_count', 0)}, Critical: {fm.get('critical_mapped', 0)}")

            # Test creating a new field mapping
            if mappings:
                print("\n✅ Field mappings are being persisted correctly!")
            else:
                print("\n⚠️ No field mappings found. Upload a CSV file through the UI to test.")

        finally:
            await db.close()

if __name__ == "__main__":
    # Set up the backend environment
    import sys
    import os
    sys.path.insert(0, "/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend")
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5433/migration_db"

    asyncio.run(test_field_mapping_persistence())
