#!/usr/bin/env python3
"""
Test script to verify the UnifiedCollectionFlow state property fix
"""

import asyncio
import os
import sys

sys.path.append('/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend')

from app.core.context import RequestContext
from app.services.crewai_flow_service import CrewAIFlowService
from app.services.crewai_flows.unified_collection_flow import UnifiedCollectionFlow


async def test_collection_flow_initialization():
    """Test that UnifiedCollectionFlow can be initialized without state setter error"""
    
    print("🧪 Testing UnifiedCollectionFlow state property fix...")
    
    try:
        # Create a mock context
        context = RequestContext(
            client_account_id="11111111-1111-1111-1111-111111111111",
            engagement_id="22222222-2222-2222-2222-222222222222", 
            user_id="33333333-3333-3333-3333-333333333333"
        )
        
        # Create a mock CrewAI service
        crewai_service = CrewAIFlowService(db=None)
        
        print("✅ Creating UnifiedCollectionFlow instance...")
        
        # This should NOT fail with "property 'state' of 'UnifiedCollectionFlow' object has no setter"
        collection_flow = UnifiedCollectionFlow(
            crewai_service=crewai_service,
            context=context,
            automation_tier="tier_2",
            flow_id="test-flow-12345"
        )
        
        print("✅ UnifiedCollectionFlow created successfully!")
        print(f"   Flow ID: {collection_flow.flow_id}")
        print(f"   State type: {type(collection_flow.state)}")
        print(f"   State flow_id: {collection_flow.state.flow_id}")
        print(f"   State current_phase: {collection_flow.state.current_phase}")
        print(f"   State status: {collection_flow.state.status}")
        
        # Test that we can access state properties
        print("✅ State property access works correctly!")
        
        # Test that kickoff method would work (without actually running it)
        print("✅ UnifiedCollectionFlow initialization test passed!")
        
        return True
        
    except Exception as e:
        print(f"❌ UnifiedCollectionFlow initialization failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_collection_flow_initialization())
    if result:
        print("\n🎉 SUCCESS: UnifiedCollectionFlow state property fix is working!")
        sys.exit(0)
    else:
        print("\n💥 FAILURE: UnifiedCollectionFlow still has state property issues")
        sys.exit(1)