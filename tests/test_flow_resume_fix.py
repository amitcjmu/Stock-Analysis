#!/usr/bin/env python3
"""
Test script to verify the flow resume fixes
"""

import requests
import json

# Test configuration
BASE_URL = "http://localhost:8000"
HEADERS = {
    "Content-Type": "application/json",
    "X-Client-Account-ID": "21990f3a-abb6-4862-be06-cb6f854e167b",
    "X-Engagement-ID": "58467010-6a72-44e8-ba37-cc0238724455",
    "X-User-ID": "77b30e13-c331-40eb-a0ec-ed0717f72b22",
    "X-User-Role": "admin"
}

# Test flow ID from the logs - this flow was in field_mapping phase
TEST_FLOW_ID = "7bdc1dc3-2793-4b02-abd7-e35f1697d37a"

def test_flow_status():
    """Test if we can get flow status"""
    print(f"🔍 Testing flow status for {TEST_FLOW_ID}...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/flows/{TEST_FLOW_ID}/status",
            headers=HEADERS,
            timeout=10
        )
        
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Flow status: {data.get('status', 'unknown')}")
            print(f"✅ Flow type: {data.get('flow_type', 'unknown')}")
            print(f"✅ Current phase: {data.get('current_phase', 'unknown')}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_flow_resume():
    """Test if we can resume the flow"""
    print(f"🔄 Testing flow resume for {TEST_FLOW_ID}...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/flows/{TEST_FLOW_ID}/resume",
            headers=HEADERS,
            timeout=30
        )
        
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ Resume successful!")
            print(f"✅ Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_health_check():
    """Test basic API health"""
    print("🏥 Testing API health...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health", timeout=5)
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print("✅ API is healthy")
            return True
        else:
            print(f"❌ Health check failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Health check exception: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("🧪 Flow Resume Fix Test Suite")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_check),
        ("Flow Status", test_flow_status),
        ("Flow Resume", test_flow_resume),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
        print("-" * 30)
    
    # Summary
    print("\n📊 Test Results:")
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Flow resume fix is working.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()