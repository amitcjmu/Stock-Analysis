#!/usr/bin/env python3
"""
Direct test of CrewAI field mapping crew execution
"""
import asyncio
import sys
import os
sys.path.insert(0, '/app')

os.environ['DEEPINFRA_BASE_URL'] = 'https://api.deepinfra.com/v1/openai'

async def test_direct_crew_execution():
    """Test field mapping crew directly without the full flow infrastructure"""

    print("=" * 60)
    print("DIRECT CREWAI FIELD MAPPING TEST")
    print("=" * 60)

    # Import after path setup
    from app.services.crewai_flow_service import CrewAIFlowService
    from app.services.crewai_flows.crews.field_mapping_crew_fast import create_fast_field_mapping_crew
    from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState

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

    # Create minimal state
    state = UnifiedDiscoveryFlowState()
    state.raw_data = test_data

    # Create service
    crewai_service = CrewAIFlowService()

    print("\n" + "=" * 60)
    print("Creating Field Mapping Crew")
    print("=" * 60)

    # Create crew
    crew = create_fast_field_mapping_crew(crewai_service, state)
    print(f"✅ Crew created: {crew}")

    # Prepare input
    crew_input = {
        "columns": list(test_data[0].keys()),
        "sample_data": test_data[:2],
        "mapping_type": "comprehensive_field_mapping"
    }

    print(f"\nInput columns: {crew_input['columns']}")
    print(f"Sample data count: {len(crew_input['sample_data'])}")

    print("\n" + "=" * 60)
    print("Executing Crew with Async Method")
    print("=" * 60)

    try:
        # Test async execution
        if hasattr(crew, 'kickoff_async'):
            print("🚀 Using kickoff_async method")
            result = await crew.kickoff_async(inputs=crew_input)
        else:
            print("🔄 Using asyncio.to_thread wrapper")
            result = await asyncio.to_thread(crew.kickoff, inputs=crew_input)

        print(f"\n✅ Crew execution successful!")
        print(f"Result type: {type(result)}")
        print(f"Result output: {result}")

        # Parse the result to extract mappings
        if result:
            output_text = str(result)
            print("\n" + "=" * 60)
            print("Extracted Mappings:")
            print("=" * 60)

            # Look for mapping patterns in the output
            lines = output_text.split('\n')
            for line in lines:
                if '->' in line:
                    print(f"  {line.strip()}")

    except Exception as e:
        print(f"❌ Crew execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct_crew_execution())
