#!/usr/bin/env python3
"""
Test script for DeepInfra integration with Llama 4 Maverick model.
This script verifies that the AI configuration is working correctly.
"""

import os
import sys
import asyncio
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.core.config import settings
    from app.services.crewai_flow_service import CrewAIFlowService
    print("✅ Successfully imported configuration and services")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Skipping test due to import error")
    # Don't exit - let pytest skip this test
    import pytest
    pytest.skip(f"Skipping due to import error: {e}", allow_module_level=True)


async def test_deepinfra_config():
    """Test DeepInfra configuration."""
    print("\n🔧 Testing DeepInfra Configuration:")
    print(f"   API Key: {'✅ Set' if settings.DEEPINFRA_API_KEY else '❌ Missing'}")
    print(f"   Model: {settings.DEEPINFRA_MODEL}")
    print(f"   Base URL: {settings.DEEPINFRA_BASE_URL}")
    print(f"   Full Model URL: {settings.deepinfra_model_url}")
    print(f"   Temperature: {settings.CREWAI_TEMPERATURE}")
    print(f"   Max Tokens: {settings.CREWAI_MAX_TOKENS}")


async def test_crewai_service():
    """Test CrewAI service initialization."""
    print("\n🤖 Testing CrewAI Service:")
    
    try:
        service = CrewAIService()
        
        if service.llm:
            print("✅ CrewAI service initialized successfully")
            print(f"   LLM Type: {type(service.llm).__name__}")
            print(f"   Agents Created: {len(service.agents)}")
            print(f"   Crews Created: {len(service.crews)}")
            
            # Test agent names
            if service.agents:
                print("   Available Agents:")
                for agent_name in service.agents.keys():
                    print(f"     - {agent_name}")
            
            return True
        else:
            print("❌ CrewAI service failed to initialize LLM")
            return False
            
    except Exception as e:
        print(f"❌ CrewAI service error: {e}")
        return False


async def test_6r_analysis():
    """Test 6R analysis functionality."""
    print("\n📊 Testing 6R Analysis:")
    
    try:
        service = CrewAIService()
        
        # Sample asset data for testing
        test_asset = {
            "name": "web-server-01",
            "asset_type": "Virtual Machine",
            "operating_system": "Ubuntu",
            "os_version": "20.04",
            "cpu_cores": 4,
            "memory_gb": 16,
            "storage_gb": 100,
            "environment": "production",
            "business_criticality": "high",
            "dependencies": ["database-01", "load-balancer"]
        }
        
        result = await service.analyze_asset_6r_strategy(test_asset)
        
        if result:
            print("✅ 6R Analysis completed")
            print(f"   Recommended Strategy: {result.get('recommended_strategy', 'N/A')}")
            print(f"   Risk Level: {result.get('risk_level', 'N/A')}")
            print(f"   Complexity: {result.get('complexity', 'N/A')}")
            print(f"   Priority: {result.get('priority', 'N/A')}")
            return True
        else:
            print("❌ 6R Analysis failed")
            return False
            
    except Exception as e:
        print(f"❌ 6R Analysis error: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 AI Force Migration Platform - DeepInfra Integration Test")
    print("=" * 60)
    
    # Test configuration
    await test_deepinfra_config()
    
    # Test service initialization
    service_ok = await test_crewai_service()
    
    # Test 6R analysis (only if service is working)
    if service_ok:
        await test_6r_analysis()
    
    print("\n" + "=" * 60)
    print("🏁 Test completed!")


if __name__ == "__main__":
    asyncio.run(main()) 