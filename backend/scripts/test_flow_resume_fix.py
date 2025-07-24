#!/usr/bin/env python
"""
Test script to verify flow state persistence fix
"""
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.models.discovery_flow import DiscoveryFlow
from app.services.crewai_flow_service import CrewAIFlowService
from sqlalchemy import select


async def test_flow_resume():
    """Test that flow state is properly loaded when resuming"""

    # Test context
    context = RequestContext(
        client_account_id="21990f3a-abb6-4862-be06-cb6f854e167b",
        engagement_id="58467010-6a72-44e8-ba37-cc0238724455",
        user_id="77b30e13-c331-40eb-a0ec-ed0717f72b22",
    )

    # Get the existing flow
    flow_id = "77e32363-c719-4c7d-89a6-81a104f8b8ac"

    async with AsyncSessionLocal() as db:
        # Check current state
        result = await db.execute(
            select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_id)
        )
        flow = result.scalar_one_or_none()

        if not flow:
            print(f"❌ Flow {flow_id} not found")
            return

        print("📋 Current flow state:")
        print(f"   - Status: {flow.status}")
        print(f"   - Phase: {flow.current_phase}")
        print(f"   - Progress: {flow.progress_percentage}%")

        # Simulate resuming the flow
        print("\n🔄 Testing flow resume...")

        service = CrewAIFlowService(db)
        resume_context = {
            "client_account_id": str(context.client_account_id),
            "engagement_id": str(context.engagement_id),
            "approved_by": str(context.user_id),
            "user_approval": True,
            "approval_timestamp": "2025-07-06T14:38:00Z",
            "notes": "Testing flow resume with state persistence fix",
        }

        # This should load existing state, not create new one
        result = await service.resume_flow(flow_id, resume_context)

        print("\n✅ Resume result:")
        print(f"   - Status: {result.get('status')}")
        print(f"   - Method: {result.get('method')}")
        if "execution_result" in result:
            print(f"   - Execution result: {result['execution_result']}")
        if "error" in result:
            print(f"   - Error: {result['error']}")


if __name__ == "__main__":
    asyncio.run(test_flow_resume())
