#!/usr/bin/env python3
"""
Manual Discovery Flow Completion Script
Completes any active discovery flows in the database to stop frontend polling.
"""

import asyncio
import logging
import os
import sys

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.discovery_flow import DiscoveryFlow
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def complete_active_flows():
    """Complete all active discovery flows to stop frontend polling"""
    try:
        async with AsyncSessionLocal() as db_session:
            logger.info("🔍 Checking for active discovery flows...")

            # Get all active flows across all clients
            stmt = select(DiscoveryFlow).where(
                DiscoveryFlow.status.in_(["active", "running", "paused"])
            )

            result = await db_session.execute(stmt)
            active_flows = result.scalars().all()

            if not active_flows:
                logger.info("✅ No active flows found - frontend should not be polling")
                return

            logger.info(f"📊 Found {len(active_flows)} active flows to complete:")

            for flow in active_flows:
                logger.info(f"   - Flow ID: {flow.flow_id}")
                logger.info(f"     Client: {flow.client_account_id}")
                logger.info(f"     Engagement: {flow.engagement_id}")
                logger.info(f"     Status: {flow.status}")
                logger.info(f"     Progress: {flow.progress_percentage}%")
                logger.info(f"     Created: {flow.created_at}")

                # Create repository for this flow's context
                flow_repo = DiscoveryFlowRepository(
                    db_session, str(flow.client_account_id), str(flow.engagement_id)
                )

                try:
                    # Complete the flow
                    completed_flow = await flow_repo.complete_discovery_flow(
                        str(flow.flow_id)
                    )
                    logger.info(f"✅ Completed flow: {completed_flow.flow_id}")
                    logger.info(f"   Status updated to: {completed_flow.status}")
                    logger.info(f"   Progress: {completed_flow.progress_percentage}%")

                except Exception as e:
                    logger.error(f"❌ Failed to complete flow {flow.flow_id}: {e}")
                    continue

            logger.info("🎯 All active flows have been completed")
            logger.info("✅ Frontend should stop polling for active flows")

    except Exception as e:
        logger.error(f"❌ Error completing active flows: {e}")
        raise


async def verify_no_active_flows():
    """Verify that no active flows remain"""
    try:
        async with AsyncSessionLocal() as db_session:
            stmt = select(DiscoveryFlow).where(
                DiscoveryFlow.status.in_(["active", "running", "paused"])
            )

            result = await db_session.execute(stmt)
            remaining_active = result.scalars().all()

            if remaining_active:
                logger.warning(f"⚠️ Still have {len(remaining_active)} active flows:")
                for flow in remaining_active:
                    logger.warning(f"   - {flow.flow_id}: {flow.status}")
                return False
            else:
                logger.info(
                    "✅ No active flows remaining - frontend polling should stop"
                )
                return True

    except Exception as e:
        logger.error(f"❌ Error verifying flows: {e}")
        return False


if __name__ == "__main__":

    async def main():
        logger.info("🚀 Starting discovery flow completion script...")

        # Complete active flows
        await complete_active_flows()

        # Verify completion
        success = await verify_no_active_flows()

        if success:
            logger.info("🎉 Success! All flows completed. Frontend should stop polling.")
        else:
            logger.error("❌ Some flows may still be active. Check the logs above.")

    asyncio.run(main())
