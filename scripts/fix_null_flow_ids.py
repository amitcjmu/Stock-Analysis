#!/usr/bin/env python3
"""
Script to find and fix DiscoveryFlow records with null flow_id values.
This addresses the root cause of undefined flow IDs in the frontend.
"""

import asyncio
import sys
import os
import uuid
from typing import List, Optional

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

# Import from backend
from app.core.database import AsyncSessionLocal
from app.models.discovery_flow import DiscoveryFlow

async def find_and_fix_null_flow_ids():
    """Find flows with null flow_id and either fix or report them"""
    
    async with AsyncSessionLocal() as db:
        print("🔍 Searching for DiscoveryFlow records with null flow_id...")
        
        # Find flows with null flow_id
        null_flow_id_stmt = select(DiscoveryFlow).where(DiscoveryFlow.flow_id.is_(None))
        result = await db.execute(null_flow_id_stmt)
        null_flows = result.scalars().all()
        
        if not null_flows:
            print("✅ No flows with null flow_id found. Database integrity is good!")
            return True
        
        print(f"❌ CRITICAL: Found {len(null_flows)} flows with null flow_id:")
        
        # Display the problematic flows
        for flow in null_flows:
            print(f"  - DB ID: {flow.id}")
            print(f"    Name: {flow.flow_name}")
            print(f"    Status: {flow.status}")
            print(f"    Client: {flow.client_account_id}")
            print(f"    Engagement: {flow.engagement_id}")
            print(f"    Created: {flow.created_at}")
            print("    ---")
        
        # For now, we'll report but not automatically fix to avoid data corruption
        print("⚠️  RECOMMENDED ACTION:")
        print("   These flows should be investigated to understand how they were created")
        print("   without proper flow_id values. Consider:")
        print("   1. Check if they can be safely deleted")
        print("   2. Or assign new UUIDs if they contain valuable data")
        print("   3. Investigate the code path that created them")
        
        # Optional: Add a flag to automatically fix (commented out for safety)
        # fix_flows = input("Do you want to assign new UUIDs to these flows? (y/N): ")
        # if fix_flows.lower() == 'y':
        #     await fix_null_flow_ids(db, null_flows)
        
        return False

async def fix_null_flow_ids(db: AsyncSession, flows: List[DiscoveryFlow]):
    """Fix flows by assigning new UUIDs (DANGEROUS - use with caution)"""
    print("🔧 Fixing flows with null flow_id...")
    
    for flow in flows:
        new_flow_id = uuid.uuid4()
        print(f"  - Assigning UUID {new_flow_id} to flow {flow.id} ({flow.flow_name})")
        
        # Update the flow with new UUID
        await db.execute(
            update(DiscoveryFlow)
            .where(DiscoveryFlow.id == flow.id)
            .values(flow_id=new_flow_id)
        )
    
    await db.commit()
    print(f"✅ Fixed {len(flows)} flows with new UUIDs")

async def main():
    """Main function"""
    try:
        await find_and_fix_null_flow_ids()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())