#!/usr/bin/env python3
"""
Manual test script for Bug #21 - Batched LLM Processing in Collection Flow
Tests the questionnaire generation with batched asset processing
"""

import asyncio
import sys
import time
from datetime import datetime

# Add backend to path
sys.path.insert(0, '/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend')

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from uuid import UUID

from app.models.collection_flow.collection_flow_model import CollectionFlow
from app.services.collection.gap_analysis.gap_persistence import GapPersistenceService
from app.services.collection.gap_analysis.data_awareness_agent import DataAwarenessAgent
from app.core.context import RequestContext


async def main():
    print("=" * 80)
    print("Bug #21 Test: Batched LLM Processing in Gap Analysis")
    print("=" * 80)
    print()

    # Database connection
    DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/migration_db"
    engine = create_async_engine(DATABASE_URL, echo=False)

    flow_id = "220b9eb7-5ff4-46f3-9608-bbad9d3335b3"

    async with AsyncSession(engine) as session:
        print(f"🔍 Looking up flow: {flow_id}")

        # Get the collection flow
        stmt = select(CollectionFlow).where(CollectionFlow.id == UUID(flow_id))
        result = await session.execute(stmt)
        flow = result.scalar_one_or_none()

        if not flow:
            print(f"❌ Flow not found: {flow_id}")
            return

        print(f"✅ Found flow: {flow.flow_name}")
        print(f"   Status: {flow.status}")
        print(f"   Current Phase: {flow.current_phase}")
        print(f"   Client: {flow.client_account_id}")
        print(f"   Engagement: {flow.engagement_id}")
        print()

        # Count assets
        count_stmt = text("""
            SELECT COUNT(*)
            FROM migration.assets
            WHERE client_account_id = :client_id
            AND engagement_id = :engagement_id
        """)
        result = await session.execute(
            count_stmt,
            {
                "client_id": str(flow.client_account_id),
                "engagement_id": str(flow.engagement_id)
            }
        )
        asset_count = result.scalar()
        print(f"📊 Total assets in engagement: {asset_count}")
        print()

        # Create context
        context = RequestContext(
            user_id=str(flow.user_id),
            client_account_id=flow.client_account_id,
            engagement_id=flow.engagement_id,
            user_email="demo@demo-corp.com",
            is_admin=False
        )

        # Initialize services
        print("🚀 Initializing Gap Analysis services...")
        gap_service = GapPersistenceService(session)
        data_awareness_agent = DataAwarenessAgent(session, gap_service)

        print("⏱️  Starting questionnaire generation with batched processing...")
        print("   (This may take 60-90 seconds for 50 assets)")
        print()

        start_time = time.time()

        try:
            # This should trigger the batched processing
            result = await data_awareness_agent.create_data_map(context)

            elapsed = time.time() - start_time
            print()
            print(f"✅ Questionnaire generation completed in {elapsed:.1f}s")
            print()

            if result:
                print("📋 Result summary:")
                if isinstance(result, dict):
                    print(f"   Sections: {len(result.get('sections', []))}")
                    print(f"   Total questions: {sum(len(s.get('questions', [])) for s in result.get('sections', []))}")
                else:
                    print(f"   Result type: {type(result)}")
            else:
                print("⚠️  No result returned (may be normal)")

        except Exception as e:
            elapsed = time.time() - start_time
            print()
            print(f"❌ Error after {elapsed:.1f}s:")
            print(f"   {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return

    print()
    print("=" * 80)
    print("Test complete. Check backend logs for batch processing indicators:")
    print("  - Look for: '📦 Processing batch X/Y'")
    print("  - Look for: '✅ Batch X/Y complete'")
    print("  - Look for: '✅ DataAwarenessAgent: Created data map'")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
