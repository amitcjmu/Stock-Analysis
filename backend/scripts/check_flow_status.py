#!/usr/bin/env python3
"""
Script to check the current status of a Discovery Flow
"""

import asyncio
import logging
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Flow ID to check
FLOW_ID = "582b87c4-0df1-4c2f-aa3b-e4b5a287d725"


async def check_flow_status():
    """Check the current status of the flow"""
    async with AsyncSessionLocal() as db:
        try:
            # Check discovery flow
            discovery_query = text('''
                SELECT flow_id, flow_name, current_phase, status, 
                       progress_percentage, field_mapping_completed,
                       data_cleansing_completed, asset_inventory_completed
                FROM discovery_flows 
                WHERE flow_id = :flow_id
            ''')
            
            result = await db.execute(discovery_query, {'flow_id': FLOW_ID})
            flow = result.fetchone()
            
            if flow:
                logger.info("📊 Discovery Flow Status:")
                logger.info(f"   Name: {flow.flow_name}")
                logger.info(f"   Status: {flow.status}")
                logger.info(f"   Current Phase: {flow.current_phase}")
                logger.info(f"   Progress: {flow.progress_percentage}%")
                logger.info(f"   Field Mapping Completed: {flow.field_mapping_completed}")
                logger.info(f"   Data Cleansing Completed: {flow.data_cleansing_completed}")
                logger.info(f"   Asset Inventory Completed: {flow.asset_inventory_completed}")
            
            # Check CrewAI state
            state_query = text('''
                SELECT flow_status,
                       flow_persistence_data->>'current_phase' as current_phase,
                       flow_persistence_data->>'completion' as completion,
                       flow_persistence_data->>'progress_percentage' as progress,
                       flow_persistence_data->>'data_import_id' as data_import_id
                FROM crewai_flow_state_extensions 
                WHERE flow_id = :flow_id
            ''')
            
            state_result = await db.execute(state_query, {'flow_id': FLOW_ID})
            state = state_result.fetchone()
            
            if state:
                logger.info("\n🤖 CrewAI Flow State:")
                logger.info(f"   Status: {state.flow_status}")
                logger.info(f"   Current Phase: {state.current_phase}")
                logger.info(f"   Completion: {state.completion}")
                logger.info(f"   Progress: {state.progress}%")
                logger.info(f"   Data Import ID: {state.data_import_id}")
            
            # Check field mappings
            if state and state.data_import_id:
                mapping_query = text('''
                    SELECT COUNT(*) as total,
                           COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved,
                           COUNT(CASE WHEN status = 'suggested' THEN 1 END) as pending
                    FROM import_field_mappings
                    WHERE data_import_id = :import_id
                ''')
                
                mapping_result = await db.execute(mapping_query, {'import_id': state.data_import_id})
                mappings = mapping_result.fetchone()
                
                if mappings:
                    logger.info("\n📋 Field Mappings:")
                    logger.info(f"   Total: {mappings.total}")
                    logger.info(f"   Approved: {mappings.approved}")
                    logger.info(f"   Pending: {mappings.pending}")
            
        except Exception as e:
            logger.error(f"❌ Error: {str(e)}")
            raise


if __name__ == "__main__":
    asyncio.run(check_flow_status())