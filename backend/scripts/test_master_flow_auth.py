#!/usr/bin/env python3
"""
Test script to verify master flow authentication is working properly
"""

import sys

import requests

# Test configuration
API_URL = "http://localhost:8000"
TEST_FLOW_ID = "test-flow-123"

def test_delete_without_auth():
    """Test DELETE request without authentication"""
    print("🧪 Testing DELETE without authentication...")
    url = f"{API_URL}/api/v1/flows/{TEST_FLOW_ID}"
    
    response = requests.delete(url)
    print(f"   Status Code: {response.status_code}")
    print("   Expected: 401 (Unauthorized)")
    
    if response.status_code == 401:
        print("   ✅ PASS: Properly rejected unauthorized request")
        return True
    else:
        print("   ❌ FAIL: Should have rejected unauthorized request")
        print(f"   Response: {response.text[:200]}")
        return False

def test_delete_with_invalid_auth():
    """Test DELETE request with invalid authentication"""
    print("\n🧪 Testing DELETE with invalid authentication...")
    url = f"{API_URL}/api/v1/flows/{TEST_FLOW_ID}"
    headers = {"Authorization": "Bearer invalid-token-12345"}
    
    response = requests.delete(url, headers=headers)
    print(f"   Status Code: {response.status_code}")
    print("   Expected: 401 (Unauthorized)")
    
    if response.status_code == 401:
        print("   ✅ PASS: Properly rejected invalid token")
        return True
    else:
        print("   ❌ FAIL: Should have rejected invalid token")
        print(f"   Response: {response.text[:200]}")
        return False

def test_delete_with_valid_auth():
    """Test DELETE request with valid authentication (requires actual token)"""
    print("\n🧪 Testing DELETE with valid authentication...")
    print("   ⚠️  SKIPPED: Requires valid authentication token")
    print("   To test with valid auth, run:")
    print("   1. Login to get a valid token")
    print("   2. Set TOKEN environment variable")
    print("   3. Run: TOKEN=your-token python test_master_flow_auth.py")
    
    import os
    token = os.environ.get('TOKEN')
    if token:
        url = f"{API_URL}/api/v1/flows/{TEST_FLOW_ID}"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.delete(url, headers=headers)
        print(f"\n   Status Code: {response.status_code}")
        print(f"   Response: {response.json() if response.status_code < 500 else response.text[:200]}")
        
        if response.status_code in [200, 404]:
            print("   ✅ PASS: Valid token accepted")
            return True
        else:
            print("   ❌ FAIL: Valid token should be accepted")
            return False
    
    return None

def main():
    """Run authentication tests"""
    print("🚀 Master Flow Authentication Test")
    print("=" * 50)
    
    results = []
    
    # Test 1: No authentication
    results.append(test_delete_without_auth())
    
    # Test 2: Invalid authentication
    results.append(test_delete_with_invalid_auth())
    
    # Test 3: Valid authentication (optional)
    result = test_delete_with_valid_auth()
    if result is not None:
        results.append(result)
    
    # Summary
    print("\n" + "=" * 50)
    passed = sum(1 for r in results if r is True)
    total = len(results)
    
    if passed == total:
        print(f"✅ All tests passed ({passed}/{total})")
        sys.exit(0)
    else:
        print(f"❌ Some tests failed ({passed}/{total} passed)")
        sys.exit(1)

if __name__ == "__main__":
    main()