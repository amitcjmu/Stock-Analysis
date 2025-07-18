#!/usr/bin/env python3
"""
Test CORS configuration for the backend
This script verifies that CORS is properly configured for Vercel frontend
"""

import requests
import sys

def test_cors_preflight(backend_url="https://migrate-ui-orchestrator-production.up.railway.app", 
                        frontend_origin="https://aiforce-assess.vercel.app"):
    """Test CORS preflight request"""
    
    print(f"🧪 Testing CORS configuration")
    print(f"   Backend: {backend_url}")
    print(f"   Frontend Origin: {frontend_origin}")
    print("=" * 60)
    
    # Test 1: Basic health check
    print("\n1️⃣ Testing basic health endpoint...")
    try:
        response = requests.get(f"{backend_url}/health")
        print(f"   ✅ Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        return False
    
    # Test 2: CORS preflight request
    print("\n2️⃣ Testing CORS preflight (OPTIONS)...")
    headers = {
        "Origin": frontend_origin,
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "authorization,content-type,x-request-id"
    }
    
    try:
        response = requests.options(f"{backend_url}/api/v1/context/me", headers=headers)
        print(f"   Status: {response.status_code}")
        
        # Check CORS headers
        cors_headers = {
            "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
            "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
            "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
            "Access-Control-Allow-Credentials": response.headers.get("Access-Control-Allow-Credentials"),
        }
        
        for header, value in cors_headers.items():
            if value:
                print(f"   ✅ {header}: {value}")
            else:
                print(f"   ❌ {header}: Missing")
        
        # Verify origin is allowed
        if cors_headers["Access-Control-Allow-Origin"] == frontend_origin:
            print(f"\n   ✅ Frontend origin is allowed!")
        else:
            print(f"\n   ❌ Frontend origin NOT allowed. Got: {cors_headers['Access-Control-Allow-Origin']}")
            return False
            
    except Exception as e:
        print(f"   ❌ CORS preflight failed: {e}")
        return False
    
    # Test 3: Actual API request with CORS
    print("\n3️⃣ Testing actual API request with CORS headers...")
    headers = {
        "Origin": frontend_origin,
        "Content-Type": "application/json",
        "X-Request-ID": "test-123"
    }
    
    try:
        response = requests.get(f"{backend_url}/api/v1/context-establishment/clients", headers=headers)
        print(f"   Status: {response.status_code}")
        
        # Check CORS response headers
        if "Access-Control-Allow-Origin" in response.headers:
            print(f"   ✅ CORS headers present in response")
            print(f"   Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin')}")
        else:
            print(f"   ⚠️  No CORS headers in response (may be normal for non-CORS requests)")
            
    except Exception as e:
        print(f"   ❌ API request failed: {e}")
    
    print("\n" + "=" * 60)
    print("✅ CORS test completed. Check the results above.")
    return True


if __name__ == "__main__":
    # Allow custom backend URL and origin
    backend_url = sys.argv[1] if len(sys.argv) > 1 else "https://migrate-ui-orchestrator-production.up.railway.app"
    frontend_origin = sys.argv[2] if len(sys.argv) > 2 else "https://aiforce-assess.vercel.app"
    
    test_cors_preflight(backend_url, frontend_origin)