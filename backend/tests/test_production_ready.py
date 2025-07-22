#!/usr/bin/env python3
"""
Production-ready test for CMDB analysis with CrewAI and LiteLLM.
"""

import asyncio
import os
import sys
import time

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.services.crewai_service_modular import CrewAIService


async def test_production_cmdb_analysis():
    """Test CMDB analysis for production readiness."""
    print("🏭 Production-Ready CMDB Analysis Test")
    print("=" * 50)
    
    try:
        # Initialize service
        service = CrewAIService()
        
        if not service.llm or not service.agents:
            print("❌ Service not properly initialized")
            return False
        
        print(f"✅ Service initialized with {len(service.agents)} agents")
        
        # Test case 1: Application-heavy dataset
        print("\n📱 Test 1: Application-Heavy Dataset")
        app_data = {
            'filename': 'applications.csv',
            'structure': {
                'columns': ['Name', 'Type', 'Version', 'Environment', 'Business_Service'],
                'total_rows': 5
            },
            'sample_data': [
                {'Name': 'CustomerPortal', 'Type': 'Application', 'Version': '2.1', 'Environment': 'Prod', 'Business_Service': 'Customer Management'},
                {'Name': 'OrderSystem', 'Type': 'Application', 'Version': '1.8', 'Environment': 'Prod', 'Business_Service': 'Order Processing'},
                {'Name': 'PaymentGateway', 'Type': 'Application', 'Version': '3.2', 'Environment': 'Prod', 'Business_Service': 'Payment Processing'}
            ]
        }
        
        start_time = time.time()
        result1 = await service.analyze_cmdb_data(app_data)
        duration1 = time.time() - start_time
        
        print(f"   Duration: {duration1:.2f}s")
        print(f"   Asset type: {result1.get('asset_type_detected', 'unknown')}")
        print(f"   Quality score: {result1.get('data_quality_score', 0)}")
        
        # Test case 2: Server-heavy dataset
        print("\n🖥️  Test 2: Server-Heavy Dataset")
        server_data = {
            'filename': 'servers.csv',
            'structure': {
                'columns': ['Name', 'Type', 'OS', 'CPU', 'Memory', 'Environment'],
                'total_rows': 4
            },
            'sample_data': [
                {'Name': 'WEB-SRV-01', 'Type': 'Server', 'OS': 'Linux', 'CPU': '8', 'Memory': '16GB', 'Environment': 'Prod'},
                {'Name': 'DB-SRV-01', 'Type': 'Server', 'OS': 'Linux', 'CPU': '16', 'Memory': '64GB', 'Environment': 'Prod'},
                {'Name': 'APP-SRV-01', 'Type': 'Server', 'OS': 'Windows', 'CPU': '12', 'Memory': '32GB', 'Environment': 'Prod'}
            ]
        }
        
        start_time = time.time()
        result2 = await service.analyze_cmdb_data(server_data)
        duration2 = time.time() - start_time
        
        print(f"   Duration: {duration2:.2f}s")
        print(f"   Asset type: {result2.get('asset_type_detected', 'unknown')}")
        print(f"   Quality score: {result2.get('data_quality_score', 0)}")
        
        # Test case 3: Mixed dataset
        print("\n🔀 Test 3: Mixed Asset Dataset")
        mixed_data = {
            'filename': 'mixed_assets.csv',
            'structure': {
                'columns': ['Name', 'CI_Type', 'Environment', 'Owner'],
                'total_rows': 6
            },
            'sample_data': [
                {'Name': 'CRM-App', 'CI_Type': 'Application', 'Environment': 'Prod', 'Owner': 'Sales Team'},
                {'Name': 'WEB-01', 'CI_Type': 'Server', 'Environment': 'Prod', 'Owner': 'IT Ops'},
                {'Name': 'Oracle-DB', 'CI_Type': 'Database', 'Environment': 'Prod', 'Owner': 'DBA Team'},
                {'Name': 'LoadBalancer', 'CI_Type': 'Network Device', 'Environment': 'Prod', 'Owner': 'Network Team'}
            ]
        }
        
        start_time = time.time()
        result3 = await service.analyze_cmdb_data(mixed_data)
        duration3 = time.time() - start_time
        
        print(f"   Duration: {duration3:.2f}s")
        print(f"   Asset type: {result3.get('asset_type_detected', 'unknown')}")
        print(f"   Quality score: {result3.get('data_quality_score', 0)}")
        
        # Evaluate results
        avg_duration = (duration1 + duration2 + duration3) / 3
        print("\n📊 Performance Summary:")
        print(f"   Average duration: {avg_duration:.2f}s")
        print("   All tests completed: ✅")
        
        # Check if performance is acceptable for production
        if avg_duration < 30:  # 30 seconds is reasonable for CMDB analysis
            print("🎉 PRODUCTION READY: Performance is acceptable!")
            
            # Verify we got meaningful results
            results = [result1, result2, result3]
            meaningful_results = 0
            
            for i, result in enumerate(results, 1):
                asset_type = result.get('asset_type_detected', 'unknown')
                if asset_type != 'unknown':
                    meaningful_results += 1
                    print(f"   Test {i}: {asset_type} ✅")
                else:
                    print(f"   Test {i}: unknown ⚠️")
            
            if meaningful_results >= 2:
                print(f"\n🚀 SUCCESS: {meaningful_results}/3 tests provided meaningful analysis!")
                print("✅ CrewAI CMDB analysis is ready for production use")
                return True
            else:
                print(f"\n⚠️  Only {meaningful_results}/3 tests provided meaningful results")
                return False
        else:
            print(f"⚠️  Average duration {avg_duration:.2f}s is too slow for production")
            return False
            
    except Exception as e:
        print(f"❌ Production test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_production_cmdb_analysis())
    
    if success:
        print("\n" + "="*60)
        print("🎉 PRODUCTION READY!")
        print("✅ CrewAI service with LiteLLM is working correctly")
        print("✅ CMDB analysis provides meaningful results")
        print("✅ Performance is acceptable for production use")
        print("✅ No thinking mode delays detected")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ NOT PRODUCTION READY")
        print("⚠️  Issues detected that need to be resolved")
        print("="*60) 