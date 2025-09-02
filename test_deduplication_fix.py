#!/usr/bin/env python3
"""
Test script to verify the deduplication service fix is working.
This script simulates the collection flow application selection process.
"""

import asyncio
import uuid
from datetime import datetime, timezone

# We'll need to import from the backend modules
import sys
sys.path.append('/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend')

from app.models.asset import Asset
from app.services.application_deduplication_service import create_deduplication_service
from app.core.database import get_db_session
from app.models.collection_flow import CollectionFlow
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def test_deduplication_fix():
    """Test that the deduplication service actually creates normalized records"""

    async with get_db_session() as db:
        # Get an existing collection flow
        flow_result = await db.execute(
            select(CollectionFlow).limit(1)
        )
        collection_flow = flow_result.scalar_one_or_none()

        if not collection_flow:
            print("❌ No collection flows found")
            return False

        print(f"✅ Found collection flow: {collection_flow.id}")

        # Get an existing asset
        asset_result = await db.execute(
            select(Asset).where(Asset.id == '01b06238-7dd4-4d83-afb5-064ad9ecb5e4')
        )
        asset = asset_result.scalar_one_or_none()

        if not asset:
            print("❌ Asset not found")
            return False

        print(f"✅ Found asset: {asset.name}")

        # Initialize deduplication service
        dedup_service = create_deduplication_service()

        # Test the deduplication process
        try:
            dedup_result = await dedup_service.deduplicate_application(
                db=db,
                application_name=asset.name,
                client_account_id=collection_flow.client_account_id,
                engagement_id=collection_flow.engagement_id,
                user_id=collection_flow.user_id,
                collection_flow_id=collection_flow.id,
                additional_metadata={
                    "asset_id": str(asset.id),
                    "source": "test_script",
                }
            )

            print(f"✅ Deduplication successful!")
            print(f"   - Canonical app: {dedup_result.canonical_application.canonical_name}")
            print(f"   - Method: {dedup_result.match_method.value}")
            print(f"   - Score: {dedup_result.similarity_score:.3f}")
            print(f"   - New canonical: {dedup_result.is_new_canonical}")

            return True

        except Exception as e:
            print(f"❌ Deduplication failed: {str(e)}")
            return False


async def check_normalized_tables():
    """Check if records were created in normalized tables"""

    async with get_db_session() as db:
        # Check collection_flow_applications
        result = await db.execute(
            select(db.sql_text("SELECT COUNT(*) as count FROM migration.collection_flow_applications"))
        )
        app_count = result.scalar()
        print(f"📊 collection_flow_applications records: {app_count}")

        # Check canonical_applications
        result = await db.execute(
            select(db.sql_text("SELECT COUNT(*) as count FROM migration.canonical_applications"))
        )
        canonical_count = result.scalar()
        print(f"📊 canonical_applications records: {canonical_count}")

        return app_count > 0


async def main():
    """Main test function"""
    print("🚀 Testing deduplication service fix...")

    # Check initial state
    await check_normalized_tables()

    # Test the deduplication
    success = await test_deduplication_fix()

    if success:
        print("\n🎉 Test completed successfully!")
        # Check final state
        await check_normalized_tables()
    else:
        print("\n💥 Test failed!")


if __name__ == "__main__":
    asyncio.run(main())
