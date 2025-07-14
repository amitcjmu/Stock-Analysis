#!/usr/bin/env python3
"""
Fix stuck flows and stop runaway polling

This script:
1. Marks old stuck flows as failed
2. Stops flows that have been processing too long
3. Cleans up orphaned data
"""

import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import text

from app.core.database import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fix_stuck_flows():
    """Fix flows stuck in processing state"""
    async with AsyncSessionLocal() as db:
        try:
            # Find flows stuck in processing for more than 30 minutes
            result = await db.execute(text("""
                UPDATE discovery_flows
                SET status = 'failed',
                    updated_at = NOW()
                WHERE status IN ('processing', 'active')
                  AND updated_at < NOW() - INTERVAL '30 minutes'
                RETURNING flow_id, current_phase, 
                  EXTRACT(EPOCH FROM (NOW() - updated_at)) as seconds_stuck
            """))
            
            stuck_flows = result.fetchall()
            
            if stuck_flows:
                logger.info(f"✅ Fixed {len(stuck_flows)} stuck discovery flows:")
                for flow in stuck_flows:
                    logger.info(f"  - Flow {str(flow.flow_id)[:8]}... was stuck in {flow.current_phase} for {int(flow.seconds_stuck)}s")
            else:
                logger.info("No stuck discovery flows found")
                
            # Also update master flows
            result = await db.execute(text("""
                UPDATE crewai_flow_state_extensions
                SET flow_status = 'failed',
                    updated_at = NOW()
                WHERE flow_status IN ('processing', 'active', 'running')
                  AND updated_at < NOW() - INTERVAL '30 minutes'
                RETURNING flow_id, flow_type
            """))
            
            stuck_master_flows = result.fetchall()
            
            if stuck_master_flows:
                logger.info(f"✅ Fixed {len(stuck_master_flows)} stuck master flows")
            
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error fixing stuck flows: {e}")
            await db.rollback()
            

async def cleanup_orphaned_data():
    """Clean up orphaned data imports with no associated flow"""
    async with AsyncSessionLocal() as db:
        try:
            # Find data imports not linked to any flow
            result = await db.execute(text("""
                DELETE FROM data_imports
                WHERE id NOT IN (
                    SELECT DISTINCT data_import_id 
                    FROM discovery_flows 
                    WHERE data_import_id IS NOT NULL
                )
                AND created_at < NOW() - INTERVAL '1 hour'
                RETURNING id, filename
            """))
            
            orphaned_imports = result.fetchall()
            
            if orphaned_imports:
                logger.info(f"✅ Cleaned up {len(orphaned_imports)} orphaned data imports")
                
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error cleaning orphaned data: {e}")
            await db.rollback()


async def reset_waiting_flows():
    """Reset flows stuck in waiting_for_approval state"""
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(text("""
                UPDATE crewai_flow_state_extensions
                SET flow_status = 'failed',
                    updated_at = NOW()
                WHERE flow_status = 'waiting_for_approval'
                  AND updated_at < NOW() - INTERVAL '2 hours'
                RETURNING flow_id
            """))
            
            waiting_flows = result.fetchall()
            
            if waiting_flows:
                logger.info(f"✅ Reset {len(waiting_flows)} flows stuck waiting for approval")
                
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error resetting waiting flows: {e}")
            await db.rollback()


async def main():
    logger.info("🔧 Starting flow cleanup...")
    
    await fix_stuck_flows()
    await cleanup_orphaned_data()
    await reset_waiting_flows()
    
    logger.info("✅ Flow cleanup completed")
    

if __name__ == "__main__":
    asyncio.run(main())