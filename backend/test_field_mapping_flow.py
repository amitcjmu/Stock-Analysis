#!/usr/bin/env python3
"""
Test the field mapping in a mock discovery flow scenario
"""

import asyncio
from app.services.field_mapping_executor.agent_operations import AgentOperations
from app.schemas.unified_discovery_flow_state import UnifiedDiscoveryFlowState
from uuid import uuid4


async def test_field_mapping_flow():
    """Test field mapping with mock discovery flow data"""

    # Create a mock state with sample CMDB data
    state = UnifiedDiscoveryFlowState(
        flow_id=str(uuid4()),
        client_account_id="test-client",
        engagement_id="test-engagement",
        current_phase="field_mapping",
        raw_data=[
            {
                "Device_Name": "SERVER01",
                "Device_Type": "Server",
                "IP": "192.168.1.10",
                "CPU": 8,
                "Memory": 32,
                "OS": "Windows Server 2019",
                "Owner": "IT Department",
                "Environment": "Production",
                "Datacenter": "DC-East",
                "cpu_utilization": 45.5,  # Should be UNMAPPED
                "memory_utilization": 78.2,  # Should be UNMAPPED
                "aws_readiness": "High",  # Should be UNMAPPED
            }
        ],
        metadata={
            "detected_columns": [
                "Device_Name",
                "Device_Type",
                "IP",
                "CPU",
                "Memory",
                "OS",
                "Owner",
                "Environment",
                "Datacenter",
                "cpu_utilization",
                "memory_utilization",
                "aws_readiness",
            ]
        },
    )

    # Create agent operations instance
    agent_ops = AgentOperations(
        agent_pool=None,  # Will use mock response
        client_account_id="test-client",
        engagement_id="test-engagement",
    )

    print("Testing field mapping with mock CMDB data...")
    print("-" * 60)

    # Execute field mapping (will use mock response)
    response = await agent_ops.execute_field_mapping_agent(state)

    # Parse the mock response to extract mappings
    print("\n📝 Agent Response (first 500 chars):")
    print(response[:500])

    # Extract mappings from response
    mappings_start = response.find("MAPPINGS:")
    mappings_end = response.find("CLARIFICATIONS:")

    if mappings_start > 0 and mappings_end > 0:
        mappings_text = response[mappings_start + 9 : mappings_end].strip()
        try:
            # Parse the mappings list
            import ast

            mappings = ast.literal_eval(mappings_text)

            print("\n✅ Field Mappings Generated:")
            print("-" * 60)
            for mapping in mappings:
                source = mapping.get("source_field", "")
                target = mapping.get("target_field", "")
                confidence = mapping.get("confidence", 0)

                # Determine status icon
                if target == "UNMAPPED":
                    icon = "❌"
                elif confidence >= 0.8:
                    icon = "✅"
                elif confidence >= 0.5:
                    icon = "⚠️"
                else:
                    icon = "❓"

                print(
                    f"{icon} {source:25} -> {target:25} (confidence: {confidence:.2f})"
                )

            # Count statistics
            total = len(mappings)
            unmapped = sum(1 for m in mappings if m.get("target_field") == "UNMAPPED")
            mapped = total - unmapped

            print("-" * 60)
            print("\n📊 Statistics:")
            print(f"  Total fields: {total}")
            print(f"  Mapped fields: {mapped}")
            print(f"  Unmapped fields: {unmapped}")
            print(f"  Mapping rate: {(mapped/total*100):.1f}%")

            # Verify specific mappings
            print("\n🔍 Verification of Key Mappings:")
            expected_mappings = {
                "Device_Name": "name",
                "Device_Type": "asset_type",
                "IP": "ip_address",
                "CPU": "cpu_cores",
                "Memory": "memory_gb",
                "OS": "operating_system",
                "Owner": "business_owner",
                "Environment": "environment",
                "Datacenter": "datacenter",
                "cpu_utilization": "UNMAPPED",
                "memory_utilization": "UNMAPPED",
                "aws_readiness": "UNMAPPED",
            }

            actual_mappings = {m["source_field"]: m["target_field"] for m in mappings}

            all_correct = True
            for source, expected_target in expected_mappings.items():
                actual_target = actual_mappings.get(source, "NOT_FOUND")
                if actual_target == expected_target:
                    print(f"  ✅ {source} correctly mapped to {actual_target}")
                else:
                    print(
                        f"  ❌ {source} incorrectly mapped to {actual_target} (expected {expected_target})"
                    )
                    all_correct = False

            if all_correct:
                print("\n🎉 All field mappings are correct!")
            else:
                print("\n⚠️ Some field mappings need correction")

        except Exception as e:
            print(f"\n❌ Error parsing mappings: {e}")
    else:
        print("\n❌ Could not extract mappings from response")


if __name__ == "__main__":
    asyncio.run(test_field_mapping_flow())
