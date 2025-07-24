#!/usr/bin/env python3
"""
Test script to verify ONLY the UnifiedCollectionFlow state property fix
This bypasses service initialization to focus on the core state property issue
"""

import asyncio
import sys

sys.path.append("/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend")

from app.core.context import RequestContext
from app.services.crewai_flow_service import CrewAIFlowService


async def test_state_property_fix():
    """Test that UnifiedCollectionFlow state property can be accessed without setter error"""

    print("🧪 Testing UnifiedCollectionFlow state property fix (core issue only)...")

    try:
        # Create a mock context
        context = RequestContext(
            client_account_id="11111111-1111-1111-1111-111111111111",
            engagement_id="22222222-2222-2222-2222-222222222222",
            user_id="33333333-3333-3333-3333-333333333333",
        )

        # Import and patch the service initialization to skip database dependencies
        from app.services.crewai_flows.unified_collection_flow import (
            UnifiedCollectionFlow,
        )

        # Create a mock CrewAI service
        crewai_service = CrewAIFlowService(db=None)

        print("✅ Patching _initialize_services to skip database dependencies...")

        # Temporarily patch the _initialize_services method to avoid database dependencies
        original_init_services = UnifiedCollectionFlow._initialize_services

        def mock_init_services(self):
            print("   (Skipping service initialization for state property test)")
            pass

        UnifiedCollectionFlow._initialize_services = mock_init_services

        print("✅ Creating UnifiedCollectionFlow instance...")

        # This should NOT fail with "property 'state' of 'UnifiedCollectionFlow' object has no setter"
        collection_flow = UnifiedCollectionFlow(
            crewai_service=crewai_service,
            context=context,
            automation_tier="tier_2",
            flow_id="test-flow-12345",
        )

        print("✅ UnifiedCollectionFlow created successfully!")
        print(f"   Flow ID: {collection_flow.flow_id}")
        print(f"   State type: {type(collection_flow.state)}")
        print(f"   State flow_id: {collection_flow.state.flow_id}")
        print(f"   State current_phase: {collection_flow.state.current_phase}")
        print(f"   State status: {collection_flow.state.status}")

        # Test that we can access state properties multiple times
        state1 = collection_flow.state
        state2 = collection_flow.state
        assert state1 is state2, "State property should return the same object"

        print("✅ State property access works correctly!")
        print("✅ State property persistence works correctly!")

        # Restore original method
        UnifiedCollectionFlow._initialize_services = original_init_services

        return True

    except Exception as e:
        print(f"❌ UnifiedCollectionFlow state property test failed: {e}")
        import traceback

        print(f"Traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_state_property_fix())
    if result:
        print("\n🎉 SUCCESS: UnifiedCollectionFlow state property fix is working!")
        print(
            "   The 'property state of UnifiedCollectionFlow object has no setter' error is FIXED!"
        )
        sys.exit(0)
    else:
        print("\n💥 FAILURE: UnifiedCollectionFlow still has state property issues")
        sys.exit(1)
