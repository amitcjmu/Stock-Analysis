"""
Test script to validate multi-tenant isolation fixes

Run this to ensure Client 2 cannot access Client 1's data.
"""

import asyncio
import uuid

from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository


async def test_tenant_isolation():
    """Test that tenant isolation is properly enforced"""
    async with AsyncSessionLocal() as db:
        # Create contexts for two different clients
        client1_context = RequestContext(
            client_account_id="11111111-def0-def0-def0-111111111111",
            engagement_id="22222222-def0-def0-def0-222222222222",
            user_id="33333333-def0-def0-def0-333333333333",
        )

        client2_context = RequestContext(
            client_account_id="44444444-def0-def0-def0-444444444444",
            engagement_id="55555555-def0-def0-def0-555555555555",
            user_id="66666666-def0-def0-def0-666666666666",
        )

        print("\n🔒 TESTING MULTI-TENANT ISOLATION")
        print("=" * 50)

        # Test 1: Repository creation requires context
        print("\n1. Testing repository context requirement...")
        try:
            # This should fail with new security enforcement
            DiscoveryFlowRepository(db=db, client_account_id=None, engagement_id=None)
            print("❌ FAILED: Repository allowed creation without client context!")
        except ValueError as e:
            if "SECURITY" in str(e):
                print("✅ PASSED: Repository correctly requires client context")
            else:
                print(f"❌ FAILED: Wrong error type: {e}")

        # Test 2: Create repositories for each client
        print("\n2. Creating client-specific repositories...")
        client1_discovery = DiscoveryFlowRepository(
            db=db,
            client_account_id=client1_context.client_account_id,
            engagement_id=client1_context.engagement_id,
        )

        client2_discovery = DiscoveryFlowRepository(
            db=db,
            client_account_id=client2_context.client_account_id,
            engagement_id=client2_context.engagement_id,
        )

        client1_master = CrewAIFlowStateExtensionsRepository(
            db=db,
            client_account_id=client1_context.client_account_id,
            engagement_id=client1_context.engagement_id,
        )

        client2_master = CrewAIFlowStateExtensionsRepository(
            db=db,
            client_account_id=client2_context.client_account_id,
            engagement_id=client2_context.engagement_id,
        )

        print("✅ Repositories created successfully")

        # Test 3: Create flows for each client
        print("\n3. Creating test flows...")

        # Create Client 1 flows
        flow1_id = str(uuid.uuid4())
        try:
            await client1_discovery.create_discovery_flow(
                flow_id=flow1_id, flow_type="primary", description="Client 1 Test Flow"
            )
            print(f"✅ Created Client 1 discovery flow: {flow1_id}")
        except Exception as e:
            print(f"❌ Failed to create Client 1 flow: {e}")
            return

        master1_id = str(uuid.uuid4())
        try:
            await client1_master.create_master_flow(
                flow_id=master1_id,
                flow_type="discovery",
                flow_name="Client 1 Master Flow",
            )
            print(f"✅ Created Client 1 master flow: {master1_id}")
        except Exception as e:
            print(f"❌ Failed to create Client 1 master flow: {e}")
            return

        # Create Client 2 flows
        flow2_id = str(uuid.uuid4())
        try:
            await client2_discovery.create_discovery_flow(
                flow_id=flow2_id, flow_type="primary", description="Client 2 Test Flow"
            )
            print(f"✅ Created Client 2 discovery flow: {flow2_id}")
        except Exception as e:
            print(f"❌ Failed to create Client 2 flow: {e}")
            return

        # Test 4: Verify isolation - Client 2 cannot see Client 1's flows
        print("\n4. Testing cross-client access (should be blocked)...")

        # Client 2 tries to access Client 1's discovery flow
        client1_flow_from_client2 = await client2_discovery.get_by_flow_id(flow1_id)
        if client1_flow_from_client2 is None:
            print("✅ PASSED: Client 2 cannot access Client 1's discovery flow")
        else:
            print("❌ FAILED: Client 2 can access Client 1's discovery flow!")

        # Client 2 tries to access Client 1's master flow
        client1_master_from_client2 = await client2_master.get_by_flow_id(master1_id)
        if client1_master_from_client2 is None:
            print("✅ PASSED: Client 2 cannot access Client 1's master flow")
        else:
            print("❌ FAILED: Client 2 can access Client 1's master flow!")

        # Test 5: Verify clients can only see their own flows
        print("\n5. Testing flow listing...")

        client1_flows = await client1_discovery.get_active_flows()
        client2_flows = await client2_discovery.get_active_flows()

        print(f"Client 1 sees {len(client1_flows)} flows")
        print(f"Client 2 sees {len(client2_flows)} flows")

        # Check no cross-contamination
        client1_ids = {str(f.flow_id) for f in client1_flows}
        client2_ids = {str(f.flow_id) for f in client2_flows}

        if flow1_id in client1_ids and flow1_id not in client2_ids:
            print("✅ PASSED: Client 1 can only see their own flows")
        else:
            print("❌ FAILED: Flow visibility issue detected")

        if flow2_id in client2_ids and flow2_id not in client1_ids:
            print("✅ PASSED: Client 2 can only see their own flows")
        else:
            print("❌ FAILED: Flow visibility issue detected")

        # Test 6: Test global query security
        print("\n6. Testing global query method security...")

        # Client 2 tries global query for Client 1's flow
        global_result = await client2_discovery.flow_queries.get_by_flow_id_global(
            flow1_id
        )
        if global_result is None:
            print("✅ PASSED: Global query properly secured - access denied")
        else:
            print("❌ FAILED: Global query allowed cross-tenant access!")

        # Clean up test data
        print("\n7. Cleaning up test data...")
        try:
            await client1_discovery.delete_flow(flow1_id)
            await client2_discovery.delete_flow(flow2_id)
            await client1_master.delete_master_flow(master1_id)
            print("✅ Test data cleaned up")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")

        print("\n" + "=" * 50)
        print("🔒 TENANT ISOLATION TEST COMPLETE")
        print("=" * 50)


if __name__ == "__main__":
    print("🔒 Multi-Tenant Security Validation Test")
    print("Testing Production Blocker #2 Fix")
    asyncio.run(test_tenant_isolation())
