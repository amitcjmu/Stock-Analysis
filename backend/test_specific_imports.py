#!/usr/bin/env python3
"""
Focused test for specific import issues
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_collection_specific():
    """Test collection imports specifically"""
    try:
        print("Testing collection_crud import...")
        from app.api.v1.endpoints import collection_crud
        print("✅ collection_crud imported successfully")
        
        print("Testing collection_validators import...")
        from app.api.v1.endpoints import collection_validators
        print("✅ collection_validators imported successfully")
        
        print("Testing collection_serializers import...")
        from app.api.v1.endpoints import collection_serializers
        print("✅ collection_serializers imported successfully")
        
        print("Testing collection_utils import...")
        from app.api.v1.endpoints import collection_utils
        print("✅ collection_utils imported successfully")
        
        print("Testing main collection import...")
        from app.api.v1.endpoints.collection import router
        print("✅ collection main module imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Collection import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_azure_adapter_specific():
    """Test Azure adapter imports specifically"""
    try:
        print("Testing Azure adapter components...")
        
        from app.services.adapters import azure_adapter_auth
        print("✅ azure_adapter_auth imported successfully")
        
        from app.services.adapters import azure_adapter_storage
        print("✅ azure_adapter_storage imported successfully")
        
        from app.services.adapters import azure_adapter_compute  
        print("✅ azure_adapter_compute imported successfully")
        
        from app.services.adapters import azure_adapter_data
        print("✅ azure_adapter_data imported successfully")
        
        from app.services.adapters import azure_adapter_utils
        print("✅ azure_adapter_utils imported successfully")
        
        print("Testing main Azure adapter...")
        # Import the class without instantiating
        from app.services.adapters.azure_adapter import AzureAdapter
        print("✅ AzureAdapter class imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Azure adapter import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_crewai_service_specific():
    """Test CrewAI service imports specifically"""
    try:
        print("Testing CrewAI service components...")
        
        from app.services import crewai_flow_state_manager
        print("✅ crewai_flow_state_manager imported successfully")
        
        from app.services import crewai_flow_executor
        print("✅ crewai_flow_executor imported successfully")
        
        from app.services import crewai_flow_lifecycle
        print("✅ crewai_flow_lifecycle imported successfully")
        
        from app.services import crewai_flow_monitoring
        print("✅ crewai_flow_monitoring imported successfully")
        
        from app.services import crewai_flow_utils
        print("✅ crewai_flow_utils imported successfully")
        
        print("Testing main CrewAI service...")
        from app.services.crewai_flow_service import CrewAIFlowService
        print("✅ CrewAIFlowService class imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ CrewAI service import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("FOCUSED IMPORT TESTING")
    print("=" * 60)
    
    results = []
    
    print("\n1. Testing Collection Components:")
    results.append(test_collection_specific())
    
    print("\n2. Testing Azure Adapter Components:")  
    results.append(test_azure_adapter_specific())
    
    print("\n3. Testing CrewAI Service Components:")
    results.append(test_crewai_service_specific())
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Import tests passed: {passed}/{total}")
    
    if all(results):
        print("✅ All focused import tests PASSED!")
    else:
        print("❌ Some focused import tests FAILED!")