import asyncio

from app.services.crewai_service_modular import crewai_service


async def test_analysis():
    print("Testing CrewAI CMDB analysis...")
    test_data = {
        "filename": "test.csv",
        "headers": ["name", "type", "os"],
        "sample_data": [["server1", "server", "linux"]],
    }

    try:
        result = await crewai_service.analyze_cmdb_data(test_data)
        print("Analysis result type:", result.get("analysis_type", "unknown"))
        print("Success:", "asset_type" in result)
        print("Asset type detected:", result.get("asset_type", "none"))
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_analysis())
    print(f"Test {'PASSED' if success else 'FAILED'}")
