#!/usr/bin/env python3
"""
Check all discovery flows in the database to understand what's there.
"""

import asyncio
import json
from datetime import datetime
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent directory to Python path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.discovery_flow import DiscoveryFlow
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions


async def check_all_flows():
    """Check all discovery flows in the database."""
    
    print(f"\n{'='*80}")
    print(f"ALL DISCOVERY FLOWS IN DATABASE")
    print(f"Check Time: {datetime.utcnow().isoformat()}")
    print(f"{'='*80}\n")
    
    async with AsyncSessionLocal() as session:
        # Count total discovery flows
        count_result = await session.execute(
            select(text("COUNT(*)")).select_from(DiscoveryFlow)
        )
        total_count = count_result.scalar()
        
        print(f"Total Discovery Flows in database: {total_count}")
        print("-" * 40)
        
        if total_count == 0:
            print("❌ No discovery flows found in database!")
            
            # Check CrewAI extensions for any discovery flows
            print("\nChecking CrewAI Flow State Extensions for discovery flows...")
            crewai_flows = await session.execute(
                select(CrewAIFlowStateExtensions).where(
                    CrewAIFlowStateExtensions.flow_type == "discovery"
                )
            )
            crewai_flows = crewai_flows.scalars().all()
            
            if crewai_flows:
                print(f"\nFound {len(crewai_flows)} discovery flows in CrewAI extensions:")
                for flow in crewai_flows:
                    print(f"\n  Flow ID: {flow.flow_id}")
                    print(f"  Extension ID: {flow.id}")
                    print(f"  Is Active: {flow.is_active}")
                    print(f"  Created At: {flow.created_at}")
                    print(f"  Master Flow ID: {flow.master_flow_id}")
            else:
                print("❌ No discovery flows found in CrewAI extensions either!")
            
            return
        
        # Get all discovery flows
        flows = await session.execute(
            select(DiscoveryFlow).order_by(DiscoveryFlow.created_at.desc())
        )
        flows = flows.scalars().all()
        
        for i, flow in enumerate(flows, 1):
            print(f"\n{i}. Discovery Flow")
            print("   " + "-" * 35)
            print(f"   Flow ID: {flow.id}")
            print(f"   Client Account ID: {flow.client_account_id}")
            print(f"   Engagement ID: {flow.engagement_id}")
            print(f"   User ID: {flow.user_id}")
            print(f"   Current Phase: {flow.current_phase}")
            print(f"   Progress: {flow.progress_percentage}%")
            print(f"   Status: {flow.status}")
            print(f"   Master Flow ID: {flow.master_flow_id}")
            print(f"   Created At: {flow.created_at}")
            print(f"   Updated At: {flow.updated_at}")
            
            # Check CrewAI extension
            crewai_ext = await session.execute(
                select(CrewAIFlowStateExtensions).where(
                    CrewAIFlowStateExtensions.flow_id == flow.id
                )
            )
            crewai_ext = crewai_ext.scalar_one_or_none()
            
            if crewai_ext:
                print(f"   ✅ Has CrewAI Extension (Active: {crewai_ext.is_active})")
            else:
                print(f"   ❌ Missing CrewAI Extension")
        
        # Also check for the specific flow ID we're looking for
        print(f"\n\nSearching specifically for flow ID: 582b87c4-0df1-4c2f-aa3b-e4b5a287d725")
        print("-" * 40)
        
        # Direct SQL query to be absolutely sure
        result = await session.execute(
            text("SELECT id, current_phase, status FROM discovery_flows WHERE id = :flow_id"),
            {"flow_id": "582b87c4-0df1-4c2f-aa3b-e4b5a287d725"}
        )
        row = result.fetchone()
        
        if row:
            print(f"✅ Found in direct SQL query: {row}")
        else:
            print(f"❌ Not found in direct SQL query either")


async def main():
    """Main function."""
    try:
        await check_all_flows()
    except Exception as e:
        print(f"\n❌ Check failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())