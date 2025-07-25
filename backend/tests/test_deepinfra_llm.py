#!/usr/bin/env python3
"""
Test script for DeepInfra Llama 4 Maverick LLM integration.
"""

import asyncio
import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.services.deepinfra_llm import create_deepinfra_llm


async def test_deepinfra_llm():
    """Test the DeepInfra LLM integration."""
    print("🧠 Testing DeepInfra Llama 4 Maverick LLM Integration")
    print("=" * 60)

    # Check API key
    if not settings.DEEPINFRA_API_KEY:
        print("❌ Error: DEEPINFRA_API_KEY not found in environment")
        return False

    print(f"✅ API Key: {settings.DEEPINFRA_API_KEY[:10]}...")
    print(f"✅ Model: {settings.DEEPINFRA_MODEL}")
    print(f"✅ Base URL: {settings.DEEPINFRA_BASE_URL}")

    try:
        # Create LLM instance
        llm = create_deepinfra_llm()
        print("✅ LLM instance created successfully")

        # Test simple prompt
        print("\n🔄 Testing simple prompt...")
        test_prompt = "Hello! Please respond with a brief greeting."

        response = llm._call(test_prompt)
        print(f"✅ Response: {response[:100]}...")

        # Test CMDB analysis prompt
        print("\n🔄 Testing CMDB analysis prompt...")
        cmdb_prompt = """
        Analyze this CMDB data and determine the asset type:

        Data: Name=WebServer01, CI_Type=Server, Environment=Production, CPU=4, Memory=8GB

        Return JSON format: {"asset_type": "server", "confidence": 0.9}
        """

        cmdb_response = llm._call(cmdb_prompt)
        print(f"✅ CMDB Analysis Response: {cmdb_response[:200]}...")

        # Test usage stats
        stats = llm.get_usage_stats()
        print(f"✅ Usage Stats: {stats}")

        print("\n🎉 All tests passed! DeepInfra LLM is working correctly.")
        return True

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False


async def test_crewai_integration():
    """Test CrewAI integration with DeepInfra LLM."""
    print("\n🤖 Testing CrewAI Integration")
    print("=" * 40)

    try:
        from app.services.crewai_service_modular import CrewAIService

        # Initialize service
        service = CrewAIService()

        if service.llm is None:
            print("❌ CrewAI service LLM not initialized")
            return False

        print("✅ CrewAI service initialized with DeepInfra LLM")

        # Check agents
        if service.agents:
            print(f"✅ Agents available: {list(service.agents.keys())}")
        else:
            print("⚠️  No agents available (may be expected in some configurations)")

        # Check crews
        if service.crews:
            print(f"✅ Crews available: {list(service.crews.keys())}")
        else:
            print("⚠️  No crews available (may be expected in some configurations)")

        print("✅ CrewAI integration test completed")
        return True

    except Exception as e:
        print(f"❌ Error in CrewAI integration: {e}")
        return False


if __name__ == "__main__":

    async def main():
        print("🚀 Starting DeepInfra LLM Tests\n")

        # Test basic LLM functionality
        llm_success = await test_deepinfra_llm()

        # Test CrewAI integration
        crewai_success = await test_crewai_integration()

        print("\n" + "=" * 60)
        if llm_success and crewai_success:
            print("🎉 All tests passed! System is ready for DeepInfra-only operation.")
        else:
            print("❌ Some tests failed. Please check the configuration.")

        return llm_success and crewai_success

    # Run the tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
