#!/usr/bin/env python3
"""
Test if the real CrewAI field_mapper agent can be executed
"""

import asyncio
import logging
from uuid import uuid4

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_agent_execution():
    """Test real agent execution"""

    try:
        # Import required modules
        from app.services.persistent_agents.tenant_scoped_agent_pool import (
            TenantScopedAgentPool,
        )

        client_id = "test-client-123"
        engagement_id = "test-engagement-456"

        print("=" * 60)
        print("Testing CrewAI Field Mapper Agent Execution")
        print("=" * 60)

        # Initialize tenant pool
        print("\n1. Initializing tenant pool...")
        await TenantScopedAgentPool.initialize_tenant_pool(
            client_id=client_id, engagement_id=engagement_id
        )
        print("   ✅ Tenant pool initialized")

        # Create field_mapper agent
        print("\n2. Creating field_mapper agent...")
        agent = await TenantScopedAgentPool.get_or_create_agent(
            client_id=client_id,
            engagement_id=engagement_id,
            agent_type="field_mapper",
            context_info={"flow_id": str(uuid4())},
        )
        print(f"   ✅ Agent created: {type(agent).__name__}")

        # Check agent attributes
        print("\n3. Checking agent configuration...")
        if hasattr(agent, "_agent"):
            inner_agent = agent._agent
            print(f"   - Role: {getattr(inner_agent, 'role', 'N/A')}")
            print(f"   - Goal: {getattr(inner_agent, 'goal', 'N/A')[:100]}...")
            print(f"   - Has execute_async: {hasattr(agent, 'execute_async')}")
            print(f"   - Has tools: {len(getattr(inner_agent, 'tools', [])) > 0}")

        # Try to execute a simple task
        print("\n4. Testing agent execution...")
        test_input = {
            "task": "Analyze these sample fields and suggest mappings to Asset model: Device_Name, IP, CPU, Memory",
            "flow_state": {
                "flow_id": str(uuid4()),
                "sample_data": [
                    {
                        "Device_Name": "SERVER01",
                        "IP": "192.168.1.10",
                        "CPU": 8,
                        "Memory": 32,
                    }
                ],
                "detected_columns": ["Device_Name", "IP", "CPU", "Memory"],
            },
            "mapping_context": {
                "target_schema": "Asset model with fields: name, hostname, ip_address, cpu_cores, memory_gb"
            },
        }

        try:
            # Execute with timeout
            print("   Executing agent task (30 second timeout)...")
            response = await asyncio.wait_for(
                agent.execute_async(inputs=test_input), timeout=30.0
            )

            print("\n   ✅ Agent executed successfully!")
            print(f"   Response type: {type(response)}")

            # Show response preview
            if isinstance(response, dict):
                print("\n   Response keys:", list(response.keys()))
                if "result" in response:
                    result_preview = str(response["result"])[:500]
                    print(f"\n   Result preview:\n   {result_preview}")
            else:
                response_preview = str(response)[:500]
                print(f"\n   Response preview:\n   {response_preview}")

        except asyncio.TimeoutError:
            print(
                "   ⏱️ Agent execution timed out (this might be normal for complex tasks)"
            )
        except Exception as e:
            print(f"   ❌ Agent execution failed: {e}")
            import traceback

            traceback.print_exc()

        # Get pool statistics
        print("\n5. Agent pool statistics:")
        stats = await TenantScopedAgentPool.get_pool_statistics()
        for stat in stats:
            if stat.client_account_id == client_id:
                print(f"   - Agent count: {stat.agent_count}")
                print(f"   - Total requests: {stat.total_requests}")
                print(f"   - Error count: {stat.error_count}")

        print("\n" + "=" * 60)
        print("Test completed!")
        print("=" * 60)

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   CrewAI or required modules not available")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_agent_execution())
