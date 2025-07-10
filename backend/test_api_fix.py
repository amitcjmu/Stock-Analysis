#!/usr/bin/env python3
"""
Test script to verify the master-flows/active API endpoint fix
This tests the endpoint directly from inside the backend container
"""

import asyncio
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.api.v1.master_flows import get_active_master_flows

async def test_get_active_flows():
    """Test the get_active_master_flows function directly"""
    
    # Mock user context for demo client
    mock_user_context = {
        "client_account_id": "11111111-1111-1111-1111-111111111111",
        "engagement_id": "22222222-2222-2222-2222-222222222222",
        "user_id": "demo_user"
    }
    
    async with AsyncSessionLocal() as db:
        try:
            # Test without flowType filter
            print("🔍 Testing without flowType filter...")
            all_flows = await get_active_master_flows(
                flowType=None,
                db=db,
                current_user=mock_user_context
            )
            print(f"✅ Found {len(all_flows)} total active flows")
            for flow in all_flows:
                print(f"  - {flow['master_flow_id']}: {flow['flow_type']} ({flow['status']})")
            
            # Test with discovery flowType filter
            print("\n🔍 Testing with flowType=discovery filter...")
            discovery_flows = await get_active_master_flows(
                flowType="discovery",
                db=db,
                current_user=mock_user_context
            )
            print(f"✅ Found {len(discovery_flows)} discovery flows")
            for flow in discovery_flows:
                print(f"  - {flow['master_flow_id']}: {flow['flow_type']} ({flow['status']})")
            
            # Test with non-existent flowType filter
            print("\n🔍 Testing with flowType=nonexistent filter...")
            no_flows = await get_active_master_flows(
                flowType="nonexistent",
                db=db,
                current_user=mock_user_context
            )
            print(f"✅ Found {len(no_flows)} nonexistent flows (should be 0)")
            
            # Verify the filtering is working
            discovery_count = len(discovery_flows)
            expected_discovery = sum(1 for flow in all_flows if flow['flow_type'] == 'discovery')
            
            if discovery_count == expected_discovery:
                print(f"\n✅ SUCCESS: Filtering is working correctly!")
                print(f"   - All flows: {len(all_flows)}")
                print(f"   - Discovery flows (filtered): {discovery_count}")
                print(f"   - Discovery flows (expected): {expected_discovery}")
                return True
            else:
                print(f"\n❌ FAILURE: Filtering mismatch!")
                print(f"   - Discovery flows (filtered): {discovery_count}")
                print(f"   - Discovery flows (expected): {expected_discovery}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing API: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    result = asyncio.run(test_get_active_flows())
    sys.exit(0 if result else 1)