#!/usr/bin/env python3
"""
Test Master Flow Orchestrator Flow Creation
Agent Team Delta - Production Validation Testing
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_HEADERS = {
    "Content-Type": "application/json",
    "X-Client-Account-ID": "1",
    "X-Engagement-ID": "1"
}

# Test data for discovery flow
DISCOVERY_TEST_DATA = {
    "flow_name": f"Test Discovery Flow - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
    "raw_data": [
        {
            "application_name": "TestApp1",
            "business_criticality": "High",
            "technical_complexity": "Medium",
            "dependencies": ["Database", "API Gateway"]
        },
        {
            "application_name": "TestApp2", 
            "business_criticality": "Medium",
            "technical_complexity": "Low",
            "dependencies": ["TestApp1"]
        }
    ],
    "configuration": {
        "source": "test_validation",
        "test_run": True
    }
}

# Test data for assessment flow
ASSESSMENT_TEST_DATA = {
    "flow_name": f"Test Assessment Flow - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
    "flow_type": "assessment",
    "configuration": {
        "source": "test_validation", 
        "test_run": True
    },
    "initial_state": {
        "selected_application_ids": [1, 2, 3]  # Assuming some apps exist
    }
}


async def test_discovery_flow_creation():
    """Test creating a discovery flow through the Master Flow Orchestrator"""
    print("\n" + "="*60)
    print("TEST: Discovery Flow Creation via Master Flow Orchestrator")
    print("="*60)
    
    async with aiohttp.ClientSession() as session:
        # 1. Create Discovery Flow
        print("\n1. Creating Discovery Flow...")
        create_url = f"{BASE_URL}/api/v1/unified-discovery/flow/initialize"
        
        try:
            async with session.post(create_url, json=DISCOVERY_TEST_DATA, headers=TEST_HEADERS) as response:
                result = await response.json()
                print(f"   Status Code: {response.status}")
                print(f"   Response: {json.dumps(result, indent=2)}")
                
                if response.status == 200 and result.get("success"):
                    flow_id = result.get("flow_id")
                    print(f"   ✅ Discovery Flow Created: {flow_id}")
                    
                    # 2. Check Flow Status Multiple Times
                    print(f"\n2. Checking Flow Status (30-second polling)...")
                    status_url = f"{BASE_URL}/api/v1/unified-discovery/flow/{flow_id}/status"
                    
                    for i in range(5):  # Check 5 times over ~2.5 minutes
                        await asyncio.sleep(30)  # 30-second polling interval
                        
                        async with session.get(status_url, headers=TEST_HEADERS) as status_response:
                            if status_response.status == 200:
                                status_data = await status_response.json()
                                print(f"\n   Check #{i+1} at {datetime.now().strftime('%H:%M:%S')}:")
                                print(f"   - Status: {status_data.get('status')}")
                                print(f"   - Current Phase: {status_data.get('current_phase')}")
                                print(f"   - Progress: {status_data.get('progress_percentage', 0)}%")
                                
                                # Check if flow has progressed beyond initialization
                                if status_data.get('status') != 'initialized' or status_data.get('current_phase') != 'initialization':
                                    print(f"   ✅ Flow has progressed beyond initialization!")
                                    return True
                            else:
                                print(f"   ❌ Status check failed: {status_response.status}")
                    
                    print(f"   ⚠️ Flow still in initialization after 2.5 minutes")
                    return False
                else:
                    print(f"   ❌ Flow creation failed: {result}")
                    return False
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False


async def test_assessment_flow_creation():
    """Test creating an assessment flow through the Master Flow Orchestrator"""
    print("\n" + "="*60)
    print("TEST: Assessment Flow Creation via Master Flow Orchestrator")
    print("="*60)
    
    async with aiohttp.ClientSession() as session:
        # 1. Create Assessment Flow
        print("\n1. Creating Assessment Flow...")
        create_url = f"{BASE_URL}/api/v1/flows"
        
        try:
            async with session.post(create_url, json=ASSESSMENT_TEST_DATA, headers=TEST_HEADERS) as response:
                result = await response.json()
                print(f"   Status Code: {response.status}")
                print(f"   Response: {json.dumps(result, indent=2)}")
                
                if response.status == 200 and result.get("success"):
                    flow_id = result.get("flow_id")
                    print(f"   ✅ Assessment Flow Created: {flow_id}")
                    
                    # 2. Check Flow Status
                    print(f"\n2. Checking Flow Status...")
                    status_url = f"{BASE_URL}/api/v1/flows/{flow_id}"
                    
                    await asyncio.sleep(5)  # Wait a bit for initialization
                    
                    async with session.get(status_url, headers=TEST_HEADERS) as status_response:
                        if status_response.status == 200:
                            status_data = await status_response.json()
                            print(f"   Status Response: {json.dumps(status_data, indent=2)}")
                            
                            # Check if we get real assessment data (not placeholder)
                            if "placeholder" not in str(status_data).lower() and status_data.get('flow_type') == 'assessment':
                                print(f"   ✅ Real assessment flow data returned!")
                                return True
                            else:
                                print(f"   ⚠️ Assessment flow may contain placeholder data")
                                return False
                        else:
                            print(f"   ❌ Status check failed: {status_response.status}")
                            return False
                else:
                    print(f"   ❌ Flow creation failed: {result}")
                    return False
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False


async def test_master_flow_list():
    """Test listing all active flows through the Master Flow Orchestrator"""
    print("\n" + "="*60)
    print("TEST: List All Active Flows")
    print("="*60)
    
    async with aiohttp.ClientSession() as session:
        list_url = f"{BASE_URL}/api/v1/master-flows/active"
        
        try:
            async with session.get(list_url, headers=TEST_HEADERS) as response:
                if response.status == 200:
                    flows = await response.json()
                    print(f"\nActive Flows Count: {len(flows)}")
                    
                    for flow in flows[:5]:  # Show first 5 flows
                        print(f"\n   Flow ID: {flow.get('flow_id')}")
                        print(f"   Type: {flow.get('flow_type')}")
                        print(f"   Name: {flow.get('flow_name')}")
                        print(f"   Status: {flow.get('status')}")
                        print(f"   Progress: {flow.get('progress_percentage', 0)}%")
                    
                    return True
                else:
                    print(f"   ❌ Failed to list flows: {response.status}")
                    return False
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False


async def test_api_performance():
    """Test API response times for performance validation"""
    print("\n" + "="*60)
    print("TEST: API Performance (Response Times)")
    print("="*60)
    
    async with aiohttp.ClientSession() as session:
        endpoints = [
            ("POST", "/api/v1/unified-discovery/flow/initialize", DISCOVERY_TEST_DATA),
            ("POST", "/api/v1/flows", ASSESSMENT_TEST_DATA),
            ("GET", "/api/v1/master-flows/active", None),
            ("GET", "/api/v1/health", None)
        ]
        
        for method, endpoint, data in endpoints:
            url = f"{BASE_URL}{endpoint}"
            start_time = time.time()
            
            try:
                if method == "POST":
                    async with session.post(url, json=data, headers=TEST_HEADERS) as response:
                        await response.read()
                        status = response.status
                else:
                    async with session.get(url, headers=TEST_HEADERS) as response:
                        await response.read()
                        status = response.status
                
                response_time = (time.time() - start_time) * 1000  # Convert to ms
                
                print(f"\n   {method} {endpoint}")
                print(f"   Status: {status}")
                print(f"   Response Time: {response_time:.2f}ms")
                
                if response_time > 1000:  # More than 1 second
                    print(f"   ⚠️ Response time exceeds 1 second!")
                else:
                    print(f"   ✅ Good response time")
                    
            except Exception as e:
                print(f"   ❌ Error testing {endpoint}: {e}")


async def main():
    """Run all validation tests"""
    print("\n🚀 MASTER FLOW ORCHESTRATOR VALIDATION SUITE")
    print("="*80)
    print("Agent Team Delta - Production Readiness Testing")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Run tests
    results = []
    
    # Test 1: Discovery Flow Creation
    discovery_result = await test_discovery_flow_creation()
    results.append(("Discovery Flow Creation", discovery_result))
    
    # Test 2: Assessment Flow Creation  
    assessment_result = await test_assessment_flow_creation()
    results.append(("Assessment Flow Creation", assessment_result))
    
    # Test 3: List Active Flows
    list_result = await test_master_flow_list()
    results.append(("List Active Flows", list_result))
    
    # Test 4: API Performance
    await test_api_performance()
    
    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - System is production ready!")
    else:
        print("\n⚠️ Some tests failed - Issues need to be addressed")


if __name__ == "__main__":
    asyncio.run(main())