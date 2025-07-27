"""
Test Discovery Flow Linkage

This script tests if discovery flows are properly linked to master flows.
"""

import asyncio
import logging

from sqlalchemy import select

from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.discovery_flow import DiscoveryFlow
from app.services.master_flow_orchestrator import MasterFlowOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_discovery_flow_linkage():
    """Test if discovery flows are properly linked to master flows"""

    async with AsyncSessionLocal() as db:
        try:
            # Initialize flow configs first
            from app.services.flow_configs import initialize_all_flows

            initialize_all_flows()

            # Create test context
            context = RequestContext(
                client_account_id="11111111-1111-1111-1111-111111111111",
                engagement_id="22222222-2222-2222-2222-222222222222",
                user_id="test-user",
            )

            # Create Master Flow Orchestrator
            orchestrator = MasterFlowOrchestrator(db, context)

            # Create a test discovery flow
            logger.info("Creating test discovery flow...")
            flow_result = await orchestrator.create_flow(
                flow_type="discovery",
                flow_name="Test Discovery Flow Linkage",
                configuration={"test": True, "purpose": "testing_linkage"},
                initial_state={
                    "raw_data": [{"test": "data"}],
                    "metadata": {"test_run": True},
                },
            )

            flow_id = flow_result[0]
            logger.info(f"Created flow with ID: {flow_id}")

            # Wait a bit for async operations
            await asyncio.sleep(2)

            # Check if discovery flow has master_flow_id
            discovery_query = select(DiscoveryFlow).where(
                DiscoveryFlow.flow_id == flow_id
            )
            discovery_result = await db.execute(discovery_query)
            discovery_flow = discovery_result.scalar_one_or_none()

            if discovery_flow:
                logger.info("✅ Discovery flow found!")
                logger.info(f"   - Flow ID: {discovery_flow.flow_id}")
                logger.info(f"   - Master Flow ID: {discovery_flow.master_flow_id}")
                logger.info(f"   - Status: {discovery_flow.status}")

                if discovery_flow.master_flow_id:
                    logger.info(
                        "✅ SUCCESS: Discovery flow is properly linked to master flow!"
                    )
                else:
                    logger.error("❌ FAILURE: Discovery flow has NO master_flow_id!")
            else:
                logger.error("❌ Discovery flow not found in database!")

            # Check master flow
            master_query = select(CrewAIFlowStateExtensions).where(
                CrewAIFlowStateExtensions.flow_id == flow_id
            )
            master_result = await db.execute(master_query)
            master_flow = master_result.scalar_one_or_none()

            if master_flow:
                logger.info("✅ Master flow found!")
                logger.info(f"   - Flow ID: {master_flow.flow_id}")
                logger.info(f"   - Status: {master_flow.flow_status}")
                logger.info(f"   - Type: {master_flow.flow_type}")

            # Test deletion cascade
            logger.info("\nTesting deletion cascade...")
            await orchestrator.delete_flow(flow_id)

            # Check if discovery flow was marked as deleted
            await db.refresh(discovery_flow)
            logger.info(
                f"After deletion - Discovery flow status: {discovery_flow.status}"
            )

            if discovery_flow.status == "deleted":
                logger.info("✅ SUCCESS: Deletion cascade worked properly!")
            else:
                logger.error("❌ FAILURE: Discovery flow not marked as deleted!")

        except Exception as e:
            logger.error(f"Test failed: {e}")
            import traceback

            logger.error(traceback.format_exc())


async def main():
    """Main entry point"""
    logger.info("Starting discovery flow linkage test...")
    await test_discovery_flow_linkage()
    logger.info("Test complete!")


if __name__ == "__main__":
    asyncio.run(main())
