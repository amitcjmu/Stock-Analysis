#!/usr/bin/env python3
"""
Test the updated CrewAI service with LiteLLM configuration.
"""

import asyncio
import time
import sys
import os
import gc

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.services.crewai_service_modular import CrewAIService

async def test_updated_crewai_service():
    """Test the updated CrewAI service with LiteLLM."""
    print("🧪 Testing Updated CrewAI Service with LiteLLM")
    print("=" * 60)
    
    # Force garbage collection
    gc.collect()
    
    try:
        # Initialize the service
        service = CrewAIService()
        
        print(f"✅ CrewAI service initialized")
        print(f"   LLM configured: {service.llm is not None}")
        print(f"   Available agents: {len(service.agents)}")
        
        if service.llm:
            print(f"   LLM model: {service.llm.model}")
            print(f"   LLM temperature: {service.llm.temperature}")
            print(f"   LLM max tokens: {service.llm.max_tokens}")
        
        # Test agent availability
        if service.agents:
            print(f"   Agent list: {list(service.agents.keys())}")
        else:
            print("   No agents available - service in placeholder mode")
            return False
        
        # Test CMDB analysis
        print("\n🔍 Testing CMDB Analysis")
        
        test_cmdb_data = {
            'filename': 'test_litellm.csv',
            'structure': {
                'columns': ['Name', 'Type', 'Environment'],
                'total_rows': 3
            },
            'sample_data': [
                {'Name': 'WebApp1', 'Type': 'Application', 'Environment': 'Prod'},
                {'Name': 'Server1', 'Type': 'Server', 'Environment': 'Prod'},
                {'Name': 'DB1', 'Type': 'Database', 'Environment': 'Prod'}
            ]
        }
        
        start_time = time.time()
        analysis_result = await service.analyze_cmdb_data(test_cmdb_data)
        duration = time.time() - start_time
        
        print(f"✅ CMDB Analysis completed in {duration:.2f}s")
        print(f"   Asset type detected: {analysis_result.get('asset_type_detected', 'unknown')}")
        print(f"   Confidence: {analysis_result.get('confidence_level', 0)}")
        print(f"   Quality score: {analysis_result.get('data_quality_score', 0)}")
        
        if duration < 20:
            print("🎉 SUCCESS: CMDB analysis executed quickly with LiteLLM!")
            return True
        else:
            print(f"⚠️  Analysis took {duration:.2f}s - might still have issues")
            return False
            
    except Exception as e:
        print(f"❌ Service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_service_reinitialization():
    """Test service reinitialization."""
    print("\n🔄 Testing Service Reinitialization")
    print("=" * 50)
    
    try:
        # Initialize service
        service = CrewAIService()
        
        print("✅ Initial service created")
        
        # Reinitialize with fresh LLM
        service.reinitialize_with_fresh_llm()
        
        print("✅ Service reinitialized with fresh LiteLLM")
        print(f"   Available agents: {len(service.agents)}")
        
        # Test a quick analysis after reinitialization
        test_data = {
            'filename': 'test_reinit.csv',
            'structure': {'columns': ['Name', 'Type'], 'total_rows': 1},
            'sample_data': [{'Name': 'TestApp', 'Type': 'Application'}]
        }
        
        start_time = time.time()
        result = await service.analyze_cmdb_data(test_data)
        duration = time.time() - start_time
        
        print(f"✅ Post-reinit analysis completed in {duration:.2f}s")
        
        if duration < 15:
            print("🎉 SUCCESS: Reinitialization works correctly!")
            return True
        else:
            print(f"⚠️  Post-reinit analysis took {duration:.2f}s")
            return False
            
    except Exception as e:
        print(f"❌ Reinitialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    async def main():
        print("🔬 Updated CrewAI Service Test Suite")
        print("=" * 50)
        
        # Test 1: Basic service functionality
        test1_success = await test_updated_crewai_service()
        
        if test1_success:
            # Test 2: Service reinitialization
            test2_success = await test_service_reinitialization()
            
            if test1_success and test2_success:
                print("\n🎉 ALL TESTS PASSED! Updated CrewAI service works with LiteLLM!")
                print("✅ CMDB analysis works quickly")
                print("✅ Service reinitialization works")
                print("✅ Ready for production use")
            else:
                print("\n⚠️  Basic functionality works but reinitialization has issues")
        else:
            print("\n❌ Basic service test failed. Check the LiteLLM configuration.")
    
    asyncio.run(main()) 