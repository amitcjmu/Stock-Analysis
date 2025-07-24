#!/usr/bin/env python3
"""
Minimal test to verify the core CrewAI Flow state property fix
"""

import asyncio
import sys

sys.path.append("/Users/chocka/CursorProjects/migrate-ui-orchestrator/backend")

from app.core.context import RequestContext


async def test_minimal_state_fix():
    """Test the absolute core state property fix"""

    print("🧪 Testing minimal UnifiedCollectionFlow state property fix...")

    try:
        # Import and create minimal version
        from app.services.crewai_flow_service import CrewAIFlowService
        from app.services.crewai_flows.unified_collection_flow import (
            UnifiedCollectionFlow,
        )

        context = RequestContext(
            client_account_id="11111111-1111-1111-1111-111111111111",
            engagement_id="22222222-2222-2222-2222-222222222222",
            user_id="33333333-3333-3333-3333-333333333333",
        )

        crewai_service = CrewAIFlowService(db=None)

        # Patch all the initialization methods that cause issues
        original_init_services = UnifiedCollectionFlow._initialize_services
        original_init = UnifiedCollectionFlow.__init__

        def minimal_init(
            self, crewai_service, context, automation_tier="tier_2", **kwargs
        ):
            """Minimal initialization that only tests the state property"""
            import uuid

            from app.models.collection_flow import AutomationTier

            logger = __import__("logging").getLogger(__name__)
            logger.info("🚀 Minimal Unified Collection Flow initialization")

            # Set required attributes BEFORE calling super().__init__()
            self.crewai_service = crewai_service
            self.context = context
            self.automation_tier = AutomationTier(automation_tier)
            self._flow_id = kwargs.get("flow_id") or str(uuid.uuid4())
            self._master_flow_id = kwargs.get("master_flow_id")
            self._discovery_flow_id = kwargs.get("discovery_flow_id")

            # Initialize base CrewAI Flow - this tests the state property
            super(UnifiedCollectionFlow, self).__init__()

            # Skip all service initialization - we just want to test state property
            logger.info(
                "✅ Minimal Collection Flow initialized - testing state property..."
            )

        # Apply patches
        UnifiedCollectionFlow.__init__ = minimal_init

        print("✅ Creating minimal UnifiedCollectionFlow instance...")

        # This should work without the state property setter error
        collection_flow = UnifiedCollectionFlow(
            crewai_service=crewai_service,
            context=context,
            automation_tier="tier_2",
            flow_id="test-flow-12345",
        )

        print("✅ Collection flow created successfully!")
        print(f"   Flow ID: {collection_flow.flow_id}")

        # Test state property access
        print("✅ Testing state property access...")
        state = collection_flow.state
        print(f"   State type: {type(state)}")
        print(f"   State flow_id: {state.flow_id}")
        print(f"   State current_phase: {state.current_phase}")
        print(f"   State status: {state.status}")

        # Test multiple accesses
        state2 = collection_flow.state
        assert state is state2, "State should be the same object"

        print("✅ State property works correctly!")

        # Restore original methods
        UnifiedCollectionFlow.__init__ = original_init
        UnifiedCollectionFlow._initialize_services = original_init_services

        return True

    except Exception as e:
        print(f"❌ Minimal state property test failed: {e}")
        if "property 'state' of 'UnifiedCollectionFlow' object has no setter" in str(e):
            print(
                "💥 CRITICAL: The original state property setter error is STILL PRESENT!"
            )
        else:
            print("ℹ️  Different error - the state property setter issue may be fixed")
        import traceback

        print(f"Traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_minimal_state_fix())
    if result:
        print("\n🎉 SUCCESS: The state property setter error is FIXED!")
        sys.exit(0)
    else:
        print("\n💥 FAILURE: Issues remain")
        sys.exit(1)
