#!/usr/bin/env python3
"""
Fix duplicate master_flow_id entries in discovery flows.

This script identifies and resolves cases where multiple discovery flows
have the same master_flow_id, which violates the expected one-to-one relationship
and causes "Multiple rows were found when one or none was required" errors.
"""

import asyncio
import logging
from datetime import datetime

from sqlalchemy import and_, func, select, update

from app.core.database import AsyncSessionLocal
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.discovery_flow import DiscoveryFlow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_duplicate_master_flow_ids():
    """Fix duplicate master_flow_id entries in discovery flows."""
    async with AsyncSessionLocal() as db:
        # Find master_flow_ids that have multiple discovery flows
        stmt = select(
            DiscoveryFlow.master_flow_id,
            func.count(DiscoveryFlow.id).label('count')
        ).where(
            DiscoveryFlow.master_flow_id.isnot(None)
        ).group_by(
            DiscoveryFlow.master_flow_id
        ).having(
            func.count(DiscoveryFlow.id) > 1
        )
        
        result = await db.execute(stmt)
        duplicates = result.fetchall()
        
        logger.info(f'Found {len(duplicates)} master flows with multiple discovery flows')
        
        for row in duplicates:
            master_flow_id = row[0]
            count = row[1]
            
            logger.info(f'Processing master flow {master_flow_id} with {count} discovery flows')
            
            # Get all discovery flows for this master flow
            detail_stmt = select(DiscoveryFlow).where(
                DiscoveryFlow.master_flow_id == master_flow_id
            ).order_by(DiscoveryFlow.created_at.desc())
            
            detail_result = await db.execute(detail_stmt)
            flows = detail_result.scalars().all()
            
            # Keep the most recent flow, mark others as orphaned
            primary_flow = flows[0]  # Most recent
            orphaned_flows = flows[1:]  # All others
            
            logger.info(f'  Primary flow: {primary_flow.flow_id} (status: {primary_flow.status}, created: {primary_flow.created_at})')
            
            for orphaned_flow in orphaned_flows:
                logger.info(f'  Orphaning flow: {orphaned_flow.flow_id} (status: {orphaned_flow.status}, created: {orphaned_flow.created_at})')
                
                # Clear the master_flow_id for orphaned flows
                orphaned_flow.master_flow_id = None
                orphaned_flow.status = 'orphaned'
                orphaned_flow.updated_at = datetime.utcnow()
                
                # Add a note about the orphaning
                if not orphaned_flow.error_details:
                    orphaned_flow.error_details = {}
                orphaned_flow.error_details['orphaned_reason'] = 'Duplicate master_flow_id resolved'
                orphaned_flow.error_details['orphaned_at'] = datetime.utcnow().isoformat()
                orphaned_flow.error_details['primary_flow_id'] = str(primary_flow.flow_id)
        
        await db.commit()
        logger.info('✅ Fixed duplicate master_flow_id entries')

async def verify_fix():
    """Verify that the fix worked."""
    async with AsyncSessionLocal() as db:
        # Check for remaining duplicates
        stmt = select(
            DiscoveryFlow.master_flow_id,
            func.count(DiscoveryFlow.id).label('count')
        ).where(
            DiscoveryFlow.master_flow_id.isnot(None)
        ).group_by(
            DiscoveryFlow.master_flow_id
        ).having(
            func.count(DiscoveryFlow.id) > 1
        )
        
        result = await db.execute(stmt)
        remaining_duplicates = result.fetchall()
        
        if remaining_duplicates:
            logger.error(f'❌ Still have {len(remaining_duplicates)} duplicate master_flow_ids')
            for row in remaining_duplicates:
                logger.error(f'  Master Flow ID: {row[0]} has {row[1]} discovery flows')
        else:
            logger.info('✅ All duplicate master_flow_ids have been resolved')

async def main():
    logger.info('🔧 Starting duplicate master_flow_id fix...')
    await fix_duplicate_master_flow_ids()
    await verify_fix()
    logger.info('✅ Fix completed')

if __name__ == '__main__':
    asyncio.run(main())