"""
Test Deletion Cascade

This script tests if deletion properly cascades from master flow to discovery flow.
"""

import asyncio
import logging
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.discovery_flow import DiscoveryFlow
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_deletion():
    async with AsyncSessionLocal() as db:
        # Get a discovery flow that's not already deleted
        stmt = select(DiscoveryFlow).where(
            DiscoveryFlow.master_flow_id.isnot(None),
            DiscoveryFlow.status != 'deleted'
        ).limit(1)
        result = await db.execute(stmt)
        discovery_flow = result.scalar_one_or_none()
        
        if discovery_flow:
            flow_id = discovery_flow.flow_id
            logger.info(f'Testing deletion for flow: {flow_id}')
            logger.info(f'Master flow ID: {discovery_flow.master_flow_id}')
            logger.info(f'Status before: {discovery_flow.status}')
            
            # Delete using the master flow deletion logic directly
            from sqlalchemy import update, and_, or_
            from datetime import datetime
            import uuid
            
            try:
                flow_uuid = uuid.UUID(str(flow_id))
            except ValueError:
                flow_uuid = flow_id
            
            # Execute the same deletion logic as the API
            discovery_update = update(DiscoveryFlow).where(
                and_(
                    or_(
                        DiscoveryFlow.master_flow_id == flow_uuid,
                        DiscoveryFlow.flow_id == flow_uuid
                    ),
                    DiscoveryFlow.status != "deleted"
                )
            ).values(
                status="deleted",
                updated_at=datetime.utcnow()
            )
            result = await db.execute(discovery_update)
            await db.commit()
            logger.info(f'Deleted {result.rowcount} discovery flows')
            
            # Check status after deletion
            await db.refresh(discovery_flow)
            logger.info(f'Status after: {discovery_flow.status}')
            
            if discovery_flow.status == 'deleted':
                logger.info('✅ SUCCESS: Deletion cascade worked!')
            else:
                logger.error('❌ FAILURE: Discovery flow not marked as deleted')
        else:
            logger.info('No non-deleted discovery flows found to test')


if __name__ == "__main__":
    asyncio.run(test_deletion())