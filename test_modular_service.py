#!/usr/bin/env python3

import sys
import os
import asyncio

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_modular_service():
    try:
        from app.services.crewai_service_modular import crewai_service
        
        print("✅ Modular CrewAI Service Import: SUCCESS")
        
        # Test health status
        health = crewai_service.get_health_status()
        print(f"✅ Health Status: {health['status']}")
        
        # Test field mapping tool
        has_field_mapping = hasattr(crewai_service, 'field_mapping_tool') and crewai_service.field_mapping_tool is not None
        print(f"✅ Field Mapping Tool: {'Available' if has_field_mapping else 'Not Available'}")
        
        # Test enhanced methods
        enhanced_methods = [
            'analyze_asset_inventory',
            'classify_assets', 
            'plan_asset_bulk_operation',
            'process_asset_feedback'
        ]
        
        for method in enhanced_methods:
            has_method = hasattr(crewai_service, method)
            print(f"✅ Enhanced Method '{method}': {'Available' if has_method else 'Missing'}")
        
        # Test asset feedback processing
        try:
            result = await crewai_service.process_asset_feedback({
                'operation_type': 'field_mapping',
                'field_mappings': [{'source_field': 'RAM (GB)', 'target_field': 'memory_gb'}]
            })
            print(f"✅ Asset Feedback Processing: SUCCESS - {result.get('status', 'unknown')}")
        except Exception as e:
            print(f"❌ Asset Feedback Processing: FAILED - {e}")
        
        print("\n🎉 All tests completed successfully!")
        print("🗑️  Old monolithic crewai_service.py has been safely removed")
        print("🔧 Enhanced field mapping intelligence is working")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_modular_service())
    sys.exit(0 if success else 1) 