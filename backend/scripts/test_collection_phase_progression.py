#!/usr/bin/env python3
"""
Test script for collection phase progression service

This script tests the new phase progression functionality by:
1. Finding stuck collection flows
2. Analyzing their status
3. Advancing them if possible

Run this script to test the fix for collection flows stuck in platform_detection.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.context import RequestContext
from app.models.collection_flow import CollectionFlow, CollectionPhase
from app.services.collection_phase_progression_service import (
    CollectionPhaseProgressionService,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_phase_progression():
    """Test the collection phase progression service"""

    async with AsyncSessionLocal() as db:
        try:
            # Find collection flows that might be stuck
            stmt = select(CollectionFlow).where(
                CollectionFlow.current_phase == CollectionPhase.PLATFORM_DETECTION.value
            )
            result = await db.execute(stmt)
            flows = result.scalars().all()

            logger.info(f"Found {len(flows)} flows in platform_detection phase")

            if not flows:
                logger.info("No flows found in platform_detection phase")
                return

            # Process each flow
            for flow in flows:
                logger.info(f"\nAnalyzing flow: {flow.flow_id}")
                logger.info(f"  Flow name: {flow.flow_name}")
                logger.info(f"  Status: {flow.status}")
                logger.info(f"  Current phase: {flow.current_phase}")
                logger.info(f"  Master flow ID: {flow.master_flow_id}")
                logger.info(f"  Created: {flow.created_at}")
                logger.info(f"  Updated: {flow.updated_at}")

                # Create a test context
                context = RequestContext(
                    client_account_id=flow.client_account_id,
                    engagement_id=flow.engagement_id,
                    user_id=flow.user_id,
                )

                # Test the progression service
                progression_service = CollectionPhaseProgressionService(db, context)

                # Check if platform detection is complete
                platform_complete = (
                    await progression_service.check_platform_detection_complete(flow)
                )
                logger.info(f"  Platform detection complete: {platform_complete}")

                if platform_complete:
                    logger.info(
                        "  -> This flow can be advanced to automated_collection"
                    )

                    # Uncomment the next line to actually advance the flow
                    # result = await progression_service.advance_to_next_phase(flow, "automated_collection")
                    # logger.info(f"  -> Advancement result: {result}")
                else:
                    logger.info(
                        "  -> This flow is still waiting for platform detection to complete"
                    )

            # Test the batch processing
            logger.info(f"\n{'='*60}")
            logger.info("Testing batch processing...")

            if flows:
                # Use the first flow's context for batch processing
                first_flow = flows[0]
                context = RequestContext(
                    client_account_id=first_flow.client_account_id,
                    engagement_id=first_flow.engagement_id,
                    user_id=first_flow.user_id,
                )

                progression_service = CollectionPhaseProgressionService(db, context)

                # Test finding stuck flows
                stuck_flows = await progression_service.find_stuck_flows()
                logger.info(f"Found {len(stuck_flows)} potentially stuck flows")

                # Uncomment the next lines to actually process stuck flows
                # results = await progression_service.process_stuck_flows()
                # logger.info(f"Batch processing results: {results}")

        except Exception as e:
            logger.error(f"Error testing phase progression: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(test_phase_progression())
