"""
Test script to verify stuck flow fixes
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta

from sqlalchemy import update

from app.core.database import AsyncSessionLocal
from app.models.discovery_flow import DiscoveryFlow
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_test_stuck_flow():
    """Create a test flow that's stuck at 0% progress"""
    async with AsyncSessionLocal() as db:
        try:
            # Create a stuck flow
            flow_id = uuid.uuid4()
            client_account_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
            engagement_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
            user_id = "test-user"

            repo = DiscoveryFlowRepository(
                db,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                user_id=user_id,
            )

            # Create flow with proper UUID handling
            flow = await repo.flow_commands.create_discovery_flow(
                flow_id=str(flow_id),
                flow_type="primary",
                description="Test Stuck Flow",
                initial_state_data={
                    "status": "active",
                    "current_phase": "initialization",
                    "progress_percentage": 0.0,
                },
                user_id=user_id,
                raw_data=[{"test": "data"}],
            )

            logger.info(f"✅ Created test stuck flow: {flow.flow_id}")

            # Make it look stuck by backdating creation time
            stmt = (
                update(DiscoveryFlow)
                .where(DiscoveryFlow.flow_id == flow_id)
                .values(created_at=datetime.utcnow() - timedelta(hours=2))
            )
            await db.execute(stmt)
            await db.commit()

            logger.info("✅ Backdated flow to appear stuck")

            return str(flow_id)

        except Exception as e:
            logger.error(f"❌ Error creating test flow: {e}")
            await db.rollback()
            raise


async def test_flow_updates():
    """Test that flow updates work with UUID handling"""
    async with AsyncSessionLocal() as db:
        try:
            client_account_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
            engagement_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
            user_id = "test-user"

            repo = DiscoveryFlowRepository(
                db,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                user_id=user_id,
            )

            # Get active flows
            flows = await repo.flow_queries.get_active_flows()
            logger.info(f"Found {len(flows)} active flows")

            for flow in flows:
                try:
                    # Test updating phase completion
                    updated_flow = await repo.flow_commands.update_phase_completion(
                        flow_id=str(flow.flow_id),
                        phase="data_import",
                        data={"test": "update"},
                        completed=False,
                        agent_insights=[{"test": "insight"}],
                    )

                    if updated_flow:
                        logger.info(f"✅ Successfully updated flow {flow.flow_id}")
                    else:
                        logger.warning(f"⚠️ No update returned for flow {flow.flow_id}")

                except Exception as e:
                    logger.error(f"❌ Error updating flow {flow.flow_id}: {e}")

        except Exception as e:
            logger.error(f"❌ Error in test_flow_updates: {e}")


async def test_cleanup_stuck_flows():
    """Test the cleanup function"""
    async with AsyncSessionLocal() as db:
        try:
            client_account_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
            engagement_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
            user_id = "test-user"

            repo = DiscoveryFlowRepository(
                db,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                user_id=user_id,
            )

            # Run cleanup with 1 hour threshold
            count = await repo.flow_commands.cleanup_stuck_flows(hours_threshold=1)
            logger.info(f"🧹 Cleaned up {count} stuck flows")

        except Exception as e:
            logger.error(f"❌ Error in cleanup: {e}")


async def main():
    """Run all tests"""
    logger.info("🚀 Starting stuck flow fix tests...")

    # Test 1: Create a stuck flow
    logger.info("\n📝 Test 1: Creating stuck flow...")
    await create_test_stuck_flow()

    # Test 2: Test flow updates work
    logger.info("\n📝 Test 2: Testing flow updates...")
    await test_flow_updates()

    # Test 3: Test cleanup
    logger.info("\n📝 Test 3: Testing cleanup...")
    await test_cleanup_stuck_flows()

    logger.info("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
