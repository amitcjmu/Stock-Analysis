#!/usr/bin/env python
"""
Reset flow back to field_mapping phase for testing
"""
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, update

from app.core.database import AsyncSessionLocal
from app.models import CrewAIFlowStateExtensions
from app.models.discovery_flow import DiscoveryFlow


async def reset_flow():
    """Reset flow to field_mapping phase"""
    
    flow_id = "77e32363-c719-4c7d-89a6-81a104f8b8ac"
    
    async with AsyncSessionLocal() as db:
        # Update DiscoveryFlow table
        await db.execute(
            update(DiscoveryFlow)
            .where(DiscoveryFlow.flow_id == flow_id)
            .values({
                'current_phase': 'field_mapping',
                'field_mapping_completed': False,
                'data_cleansing_completed': False,
                'status': 'waiting_for_approval'
            })
        )
        
        # Update CrewAI extensions
        result = await db.execute(
            select(CrewAIFlowStateExtensions)
            .where(CrewAIFlowStateExtensions.flow_id == flow_id)
        )
        ext = result.scalar_one_or_none()
        
        if ext and ext.flow_persistence_data:
            # Update the persistence data
            ext.flow_persistence_data['current_phase'] = 'field_mapping'
            ext.flow_persistence_data['status'] = 'waiting_for_approval'
            ext.flow_persistence_data['phase_completion']['field_mapping'] = False
            ext.flow_persistence_data['phase_completion']['data_cleansing'] = False
            
            # Clear field mappings to force regeneration
            ext.flow_persistence_data['field_mappings'] = {
                'mappings': {},
                'agent_insights': {},
                'unmapped_fields': [],
                'confidence_scores': {},
                'validation_results': {}
            }
            
            # Mark for update
            db.add(ext)
        
        await db.commit()
        print(f"✅ Flow {flow_id} reset to field_mapping phase")

if __name__ == "__main__":
    asyncio.run(reset_flow())