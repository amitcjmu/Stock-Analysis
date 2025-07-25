import asyncio
import time
from app.services.crewai_flow_service import crewai_service

async def test_cmdb_analysis_with_timeout():
    """Test CMDB analysis with a timeout to detect hanging issues."""
    print("🧪 Testing CrewAI CMDB Analysis with timeout...")

    test_data = {
        'filename': 'test_sample.csv',
        'headers': ['Name', 'CI_Type', 'Environment', 'CPU_Cores', 'Memory_GB'],
        'sample_data': [
            ['WebServer01', 'Server', 'Production', '4', '16'],
            ['AppServer02', 'Server', 'Development', '2', '8'],
            ['Database01', 'Database', 'Production', '8', '32']
        ]
    }

    start_time = time.time()

    try:
        # Set a timeout of 60 seconds
        result = await asyncio.wait_for(
            crewai_service.analyze_cmdb_data(test_data),
            timeout=60.0
        )

        end_time = time.time()
        duration = end_time - start_time

        print(f"✅ Analysis completed in {duration:.2f} seconds")
        print(f"   Analysis type: {result.get('analysis_type', 'unknown')}")
        print(f"   Asset type detected: {result.get('asset_type', 'none')}")
        print(f"   Has recommendations: {'recommendations' in result}")

        return True, result

    except asyncio.TimeoutError:
        end_time = time.time()
        duration = end_time - start_time
        print(f"❌ Analysis timed out after {duration:.2f} seconds")
        return False, {"error": "timeout"}

    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f"❌ Analysis failed after {duration:.2f} seconds: {e}")
        return False, {"error": str(e)}

async def test_simple_agent_call():
    """Test a simple agent call to see if the issue is with the agent or the crew."""
    print("\n🤖 Testing simple agent call...")

    if not crewai_service.agents.get('cmdb_analyst'):
        print("❌ CMDB analyst agent not available")
        return False

    try:
        # Test if we can access the agent
        agent = crewai_service.agents['cmdb_analyst']
        print(f"✅ Agent available: {agent.role}")
        print(f"   Goal: {agent.goal}")
        return True

    except Exception as e:
        print(f"❌ Agent access failed: {e}")
        return False

if __name__ == "__main__":
    async def main():
        print("=" * 60)
        print("CrewAI CMDB Analysis Diagnostic Test")
        print("=" * 60)

        # Test 1: Simple agent access
        agent_ok = await test_simple_agent_call()

        if agent_ok:
            # Test 2: Full CMDB analysis with timeout
            success, result = await test_cmdb_analysis_with_timeout()

            if success:
                print("\n🎉 All tests PASSED! CrewAI CMDB analysis is working.")
            else:
                print(f"\n❌ CMDB analysis FAILED: {result.get('error', 'unknown')}")
        else:
            print("\n❌ Agent setup FAILED")

    asyncio.run(main())
