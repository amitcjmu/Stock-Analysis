#!/usr/bin/env python3
"""
Check the master flow and its relationship to discovery flows.
"""

import asyncio
import json
import os

# Add parent directory to Python path
import sys
from datetime import datetime

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.asset import Asset
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.data_import.core import DataImport
from app.models.discovery_flow import DiscoveryFlow


async def check_master_flow():
    """Check the master flow and related discovery flows."""
    
    master_flow_id = "582b87c4-0df1-4c2f-aa3b-e4b5a287d725"
    
    print(f"\n{'='*80}")
    print("MASTER FLOW AND DISCOVERY FLOW INVESTIGATION")
    print(f"Investigation Time: {datetime.utcnow().isoformat()}")
    print(f"{'='*80}\n")
    
    async with AsyncSessionLocal() as session:
        # 1. Check if this is a master flow in CrewAI extensions
        print("1. CHECKING CREWAI FLOW STATE EXTENSIONS")
        print("-" * 40)
        
        master_flow = await session.execute(
            select(CrewAIFlowStateExtensions).where(
                CrewAIFlowStateExtensions.id == master_flow_id
            )
        )
        master_flow = master_flow.scalar_one_or_none()
        
        if master_flow:
            print("✅ Found flow in CrewAI extensions!")
            print(f"  Extension ID: {master_flow.id}")
            print(f"  Flow ID: {master_flow.flow_id}")
            print(f"  Flow Type: {master_flow.flow_type}")
            print(f"  Is Active: {master_flow.is_active}")
            print(f"  State Version: {master_flow.state_version}")
            print(f"  Created At: {master_flow.created_at}")
            print(f"  Updated At: {master_flow.updated_at}")
            
            if master_flow.execution_state:
                print("\n  Execution State:")
                print(json.dumps(master_flow.execution_state, indent=4))
        else:
            print("❌ Flow not found in CrewAI extensions!")
        
        # 2. Find all discovery flows that reference this master flow
        print("\n\n2. DISCOVERY FLOWS LINKED TO THIS MASTER FLOW")
        print("-" * 40)
        
        linked_flows = await session.execute(
            select(DiscoveryFlow).where(
                DiscoveryFlow.master_flow_id == master_flow_id
            )
        )
        linked_flows = linked_flows.scalars().all()
        
        if linked_flows:
            print(f"Found {len(linked_flows)} discovery flow(s) linked to this master flow:")
            
            for flow in linked_flows:
                print(f"\n  Discovery Flow ID: {flow.id}")
                print(f"    Status: {flow.status}")
                print(f"    Current Phase: {flow.current_phase}")
                print(f"    Progress: {flow.progress_percentage}%")
                print(f"    Created At: {flow.created_at}")
                
                # Check if this discovery flow has data imports and assets
                data_imports = await session.execute(
                    select(DataImport).where(
                        DataImport.master_flow_id == flow.master_flow_id
                    )
                )
                data_imports = data_imports.scalars().all()
                
                assets_count = await session.execute(
                    select(text("COUNT(*)")).select_from(Asset).where(
                        Asset.discovery_flow_id == flow.id
                    )
                )
                assets_count = assets_count.scalar()
                
                print(f"    Data Imports: {len(data_imports)}")
                print(f"    Assets: {assets_count}")
                
                # Check CrewAI extension for this discovery flow
                discovery_ext = await session.execute(
                    select(CrewAIFlowStateExtensions).where(
                        CrewAIFlowStateExtensions.flow_id == flow.id
                    )
                )
                discovery_ext = discovery_ext.scalar_one_or_none()
                
                if discovery_ext:
                    print(f"    ✅ Has CrewAI Extension (Active: {discovery_ext.is_active})")
                else:
                    print("    ❌ Missing CrewAI Extension")
        else:
            print("❌ No discovery flows linked to this master flow")
        
        # 3. Check all active discovery flows
        print("\n\n3. CURRENTLY ACTIVE DISCOVERY FLOWS")
        print("-" * 40)
        
        active_flows = await session.execute(
            select(DiscoveryFlow).where(
                DiscoveryFlow.status.in_(["running", "in_progress", "waiting_for_approval"])
            )
        )
        active_flows = active_flows.scalars().all()
        
        if active_flows:
            print(f"Found {len(active_flows)} active discovery flow(s):")
            for flow in active_flows:
                print(f"\n  Flow ID: {flow.id}")
                print(f"    Status: {flow.status}")
                print(f"    Current Phase: {flow.current_phase}")
                print(f"    Progress: {flow.progress_percentage}%")
                print(f"    Master Flow ID: {flow.master_flow_id}")
        else:
            print("❌ No active discovery flows found")
        
        # 4. Summary
        print("\n\n4. SUMMARY")
        print("-" * 40)
        
        if master_flow and master_flow.flow_type == "master":
            print(f"✅ {master_flow_id} is a MASTER flow, not a discovery flow")
            print("   This explains why it's not in the discovery_flows table")
            
            if linked_flows:
                print("\n   The actual discovery flow to check is:")
                for flow in linked_flows:
                    print(f"   • {flow.id} (Status: {flow.status}, Phase: {flow.current_phase})")
            else:
                print("\n   ❌ However, no discovery flows are linked to this master flow")
        else:
            print(f"❌ Unable to determine the nature of flow {master_flow_id}")


async def main():
    """Main function."""
    try:
        await check_master_flow()
    except Exception as e:
        print(f"\n❌ Check failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())