#!/usr/bin/env python3
"""
Test script to verify Discovery flow with CrewAI execution
"""
import asyncio
import sys
import os
import json
sys.path.insert(0, '/app')

os.environ['DEEPINFRA_BASE_URL'] = 'https://api.deepinfra.com/v1/openai'

from app.core.context import RequestContext
from app.services.crewai_flow_service import CrewAIFlowService
from app.services.crewai_flows.unified_discovery_flow import UnifiedDiscoveryFlow
from app.services.crewai_flows.unified_discovery_flow.phase_controller import PhaseController, FlowPhase
from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState

async def test_field_mapping_phase():
    """Test field mapping phase with CrewAI execution"""

    print("=" * 60)
    print("DISCOVERY FLOW FIELD MAPPING TEST")
    print("=" * 60)

    # Create mock context
    context = RequestContext(
        client_account_id="test-client",
        engagement_id="test-engagement",
        user_id="test-user"
    )

    # Create service and flow
    crewai_service = CrewAIFlowService()

    # Create test data
    test_data = [
        {
            "Asset_ID": "A001",
            "Asset_Name": "Web Server 1",
            "IP_Address": "192.168.1.10",
            "Operating_System": "Ubuntu 20.04",
            "CPU_Cores": "8",
            "RAM_GB": "16",
            "Storage_GB": "500"
        },
        {
            "Asset_ID": "A002",
            "Asset_Name": "Database Server",
            "IP_Address": "192.168.1.20",
            "Operating_System": "Red Hat 8",
            "CPU_Cores": "16",
            "RAM_GB": "64",
            "Storage_GB": "2000"
        }
    ]

    # Create flow with initial state
    initial_state = {
        "raw_data": test_data,
        "flow_id": "test-flow-123"
    }

    flow_instance = UnifiedDiscoveryFlow(
        crewai_service,
        context=context,
        flow_id="test-flow-123",
        initial_state=initial_state
    )

    # Set raw data in state
    flow_instance.state.raw_data = test_data

    # Create phase controller
    phase_controller = PhaseController(flow_instance)

    print("\n" + "=" * 60)
    print("Testing Field Mapping Phase Execution")
    print("=" * 60)

    try:
        # Force run field mapping phase
        result = await phase_controller.force_rerun_phase(
            phase=FlowPhase.FIELD_MAPPING_SUGGESTIONS,
            use_existing_data=True
        )

        print(f"\n✅ Phase execution successful!")
        print(f"Phase: {result.phase.value}")
        print(f"Status: {result.status}")
        print(f"Data keys: {list(result.data.keys()) if result.data else 'None'}")

        if result.data and 'result' in result.data:
            result_data = result.data['result']
            if isinstance(result_data, dict):
                print(f"\nMappings found:")
                mappings = result_data.get('mappings', {})
                for source, target in list(mappings.items())[:5]:
                    print(f"  {source} -> {target}")

    except Exception as e:
        print(f"❌ Phase execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_field_mapping_phase())
