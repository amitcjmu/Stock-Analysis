"""
Activate a paused flow so it can be properly resumed
"""
import asyncio
from sqlalchemy import select, update
from app.core.database import AsyncSessionLocal
from app.models.discovery_flow import DiscoveryFlow
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
import json

async def activate_paused_flow():
    flow_id = '77e32363-c719-4c7d-89a6-81a104f8b8ac'
    
    async with AsyncSessionLocal() as db:
        # Get the flow
        result = await db.execute(
            select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_id)
        )
        flow = result.scalar()
        
        if not flow:
            print(f"Flow {flow_id} not found")
            return
            
        print(f"Current flow status: {flow.status}")
        print(f"Current phase: {flow.current_phase}")
        
        if flow.status == 'paused':
            print("Flow is paused. Changing to 'active' status...")
            
            # Update flow status to active
            await db.execute(
                update(DiscoveryFlow)
                .where(DiscoveryFlow.flow_id == flow_id)
                .values({
                    'status': 'active'
                })
            )
            
            # Also update CrewAI extensions
            await db.execute(
                update(CrewAIFlowStateExtensions)
                .where(CrewAIFlowStateExtensions.flow_id == flow_id)
                .values({
                    'flow_status': 'active'
                })
            )
            
            await db.commit()
            print("✅ Flow status changed to 'active'")
            print("The flow should now be resumable from the frontend")
        else:
            print(f"Flow is already in {flow.status} status")

if __name__ == "__main__":
    asyncio.run(activate_paused_flow())