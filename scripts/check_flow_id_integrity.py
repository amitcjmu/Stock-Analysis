#!/usr/bin/env python3
"""
Script to check for DiscoveryFlow records with null or invalid flow_id values.
This helps diagnose the root cause of undefined flow IDs in the API.
"""

import asyncio
import sys
import os
from typing import List, Optional

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession

# Import from backend
from app.core.database import AsyncSessionLocal
from app.models.discovery_flow import DiscoveryFlow

async def check_flow_id_integrity():
    """Check for flows with null or invalid flow_id values"""
    
    # Get database session
    SessionMaker = AsyncSessionLocal
    
    async with SessionMaker() as db:
        print("🔍 Checking DiscoveryFlow table for flow_id integrity issues...")
        
        # Check for flows with null flow_id
        null_flow_id_stmt = select(func.count()).where(DiscoveryFlow.flow_id.is_(None))
        null_count_result = await db.execute(null_flow_id_stmt)
        null_count = null_count_result.scalar()
        
        print(f"📊 Flows with null flow_id: {null_count}")
        
        # Get some examples of flows with null flow_id
        if null_count > 0:
            examples_stmt = select(DiscoveryFlow).where(DiscoveryFlow.flow_id.is_(None)).limit(5)
            examples_result = await db.execute(examples_stmt)
            null_flows = examples_result.scalars().all()
            
            print("🔍 Example flows with null flow_id:")
            for flow in null_flows:
                print(f"  - ID: {flow.id}, Name: {flow.flow_name}, Status: {flow.status}, Created: {flow.created_at}")
        
        # Check total flows for comparison
        total_stmt = select(func.count()).select_from(DiscoveryFlow)
        total_result = await db.execute(total_stmt)
        total_count = total_result.scalar()
        
        print(f"📊 Total flows in database: {total_count}")
        
        # Check for flows with valid flow_id
        valid_flow_id_stmt = select(func.count()).where(DiscoveryFlow.flow_id.is_not(None))
        valid_count_result = await db.execute(valid_flow_id_stmt)
        valid_count = valid_count_result.scalar()
        
        print(f"📊 Flows with valid flow_id: {valid_count}")
        
        # Get some examples of recent flows to see their structure
        print("\n🔍 Recent flows (last 10):")
        recent_stmt = select(DiscoveryFlow).order_by(DiscoveryFlow.created_at.desc()).limit(10)
        recent_result = await db.execute(recent_stmt)
        recent_flows = recent_result.scalars().all()
        
        for flow in recent_flows:
            print(f"  - ID: {flow.id}")
            print(f"    flow_id: {flow.flow_id}")
            print(f"    Name: {flow.flow_name}")
            print(f"    Status: {flow.status}")
            print(f"    Created: {flow.created_at}")
            print(f"    Client: {flow.client_account_id}")
            print(f"    Engagement: {flow.engagement_id}")
            print("    ---")
        
        # Check for flows with empty string flow_id (shouldn't happen but worth checking)
        empty_string_stmt = select(func.count()).where(
            and_(
                DiscoveryFlow.flow_id.is_not(None),
                func.char_length(DiscoveryFlow.flow_id.cast(text("TEXT"))) == 0
            )
        )
        try:
            empty_result = await db.execute(empty_string_stmt)
            empty_count = empty_result.scalar()
            print(f"📊 Flows with empty string flow_id: {empty_count}")
        except Exception as e:
            print(f"⚠️ Could not check for empty string flow_ids: {e}")
        
        print("\n✅ Flow ID integrity check completed!")
        
        if null_count > 0:
            print(f"❌ CRITICAL: Found {null_count} flows with null flow_id values!")
            print("   This is likely the root cause of 'undefined' flow IDs in the API.")
            return False
        else:
            print("✅ All flows have valid flow_id values.")
            return True

async def main():
    """Main function"""
    try:
        integrity_ok = await check_flow_id_integrity()
        if not integrity_ok:
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error checking flow ID integrity: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())