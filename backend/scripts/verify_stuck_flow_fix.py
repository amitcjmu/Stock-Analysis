"""
Verify that stuck flows are properly detected and handled
"""

import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func
from app.core.database import AsyncSessionLocal
from app.models.discovery_flow import DiscoveryFlow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_stuck_flows():
    """Check for flows that are stuck at 0% progress"""
    async with AsyncSessionLocal() as db:
        try:
            # Count all flows by status
            logger.info("\n📊 Flow Status Summary:")
            statuses = ['active', 'initialized', 'running', 'complete', 'failed', 'waiting_for_approval']
            
            for status in statuses:
                stmt = select(func.count()).where(DiscoveryFlow.status == status)
                result = await db.execute(stmt)
                count = result.scalar() or 0
                logger.info(f"  {status}: {count}")
            
            # Find stuck flows (active/initialized/running with 0% progress for > 1 hour)
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            
            stmt = select(DiscoveryFlow).where(
                and_(
                    DiscoveryFlow.status.in_(['active', 'initialized', 'running']),
                    DiscoveryFlow.progress_percentage == 0.0,
                    DiscoveryFlow.created_at < cutoff_time
                )
            )
            
            result = await db.execute(stmt)
            stuck_flows = result.scalars().all()
            
            logger.info(f"\n⚠️ Found {len(stuck_flows)} stuck flows:")
            
            for flow in stuck_flows:
                hours_stuck = (datetime.utcnow() - flow.created_at).total_seconds() / 3600
                logger.info(f"  - Flow {flow.flow_id}: {flow.flow_name}")
                logger.info(f"    Status: {flow.status}, Progress: {flow.progress_percentage}%")
                logger.info(f"    Stuck for: {hours_stuck:.2f} hours")
                logger.info(f"    Current phase: {flow.current_phase}")
                
                # Check if it has timeout metadata
                if flow.crewai_state_data and 'metadata' in flow.crewai_state_data:
                    timeout_at = flow.crewai_state_data['metadata'].get('timeout_at')
                    logger.info(f"    Timeout at: {timeout_at}")
            
            # Check for failed flows with timeout reason
            stmt = select(DiscoveryFlow).where(
                and_(
                    DiscoveryFlow.status == 'failed',
                    DiscoveryFlow.error_phase == 'timeout'
                )
            )
            
            result = await db.execute(stmt)
            timeout_flows = result.scalars().all()
            
            logger.info(f"\n⏰ Found {len(timeout_flows)} timed out flows:")
            
            for flow in timeout_flows:
                logger.info(f"  - Flow {flow.flow_id}: {flow.flow_name}")
                logger.info(f"    Error: {flow.error_message}")
                if flow.error_details:
                    logger.info(f"    Details: {flow.error_details}")
                    
        except Exception as e:
            logger.error(f"❌ Error checking stuck flows: {e}")


async def check_flow_uuid_handling():
    """Verify that UUID handling is working correctly"""
    async with AsyncSessionLocal() as db:
        try:
            # Get a sample flow
            stmt = select(DiscoveryFlow).limit(1)
            result = await db.execute(stmt)
            flow = result.scalar_one_or_none()
            
            if flow:
                logger.info(f"\n🔍 Testing UUID handling with flow {flow.flow_id}")
                logger.info(f"  Flow ID type: {type(flow.flow_id)}")
                logger.info(f"  Flow ID string: {str(flow.flow_id)}")
                
                # Test that we can query by UUID
                stmt = select(DiscoveryFlow).where(
                    DiscoveryFlow.flow_id == flow.flow_id
                )
                result = await db.execute(stmt)
                found_flow = result.scalar_one_or_none()
                
                if found_flow:
                    logger.info("  ✅ UUID query successful")
                else:
                    logger.error("  ❌ UUID query failed")
                    
        except Exception as e:
            logger.error(f"❌ Error testing UUID handling: {e}")


async def main():
    """Run all checks"""
    logger.info("🚀 Verifying stuck flow detection and fixes...")
    
    await check_stuck_flows()
    await check_flow_uuid_handling()
    
    logger.info("\n✅ Verification complete!")


if __name__ == "__main__":
    asyncio.run(main())