#!/usr/bin/env python3
"""
Test Flow Processing Fix
"""

import asyncio
import sys

sys.path.append("/app")


async def test_flow_processing_fix():
    from app.api.v1.endpoints.flow_processing import (
        FlowContinuationRequest,
        continue_flow_processing,
    )
    from app.core.context import RequestContext
    from app.core.database import AsyncSessionLocal

    try:
        # Test with a real flow ID that exists in both discovery_flows and master orchestrator
        flow_id = "23678d88-f4bd-49f4-bca8-b93c7b2b9ef2"

        # Create context with ACTUAL tenant values from the database
        context = RequestContext(
            client_account_id="21990f3a-abb6-4862-be06-cb6f854e167b",
            engagement_id="58467010-6a72-44e8-ba37-cc0238724455",
            user_id="77b30e13-c331-40eb-a0ec-ed0717f72b22",
        )

        # Create request
        request = FlowContinuationRequest(user_context={})

        async with AsyncSessionLocal() as db:
            result = await continue_flow_processing(flow_id, request, context, db)
            print("✅ Flow processing test successful:")
            print(f"   Flow ID: {result.flow_id}")
            print(f"   Success: {result.success}")
            print(f"   Current Phase: {result.current_phase}")
            print(f"   Routing: {result.routing_context.target_page}")
            print(f"   Guidance: {result.user_guidance.primary_message}")

            # Check if the result indicates the flow was found
            if result.current_phase != "not_found":
                print("🎉 SUCCESS: Flow was found using Master Flow Orchestrator!")
                return True
            else:
                print("❌ Flow still not found even with Master Flow Orchestrator")
                return False

    except Exception as e:
        print(f"❌ Flow processing test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_flow_processing_fix())
    sys.exit(0 if result else 1)
