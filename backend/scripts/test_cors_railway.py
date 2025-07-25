#!/usr/bin/env python3
"""
Test CORS configuration on Railway deployment
"""

import requests
import sys


def test_cors_on_railway():
    """Test CORS configuration on the Railway backend"""
    backend_url = "https://migrate-ui-orchestrator-production.up.railway.app"
    frontend_origin = "https://aiforce-assess.vercel.app"

    print(f"🧪 Testing CORS on Railway backend: {backend_url}")
    print(f"   Frontend origin: {frontend_origin}")

    # Test 1: Basic connectivity
    print("\n1️⃣ Testing basic connectivity...")
    try:
        response = requests.get(f"{backend_url}/health", timeout=10)
        print(f"   ✅ Health check status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        return

    # Test 2: CORS preflight request
    print("\n2️⃣ Testing CORS preflight (OPTIONS) for /api/v1/auth/login...")
    try:
        headers = {
            "Origin": frontend_origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        }

        response = requests.options(
            f"{backend_url}/api/v1/auth/login", headers=headers, timeout=10
        )

        print(f"   Status Code: {response.status_code}")
        print(f"   Headers:")

        # Check CORS headers
        cors_headers = {
            "Access-Control-Allow-Origin": response.headers.get(
                "Access-Control-Allow-Origin"
            ),
            "Access-Control-Allow-Methods": response.headers.get(
                "Access-Control-Allow-Methods"
            ),
            "Access-Control-Allow-Headers": response.headers.get(
                "Access-Control-Allow-Headers"
            ),
            "Access-Control-Allow-Credentials": response.headers.get(
                "Access-Control-Allow-Credentials"
            ),
        }

        for header, value in cors_headers.items():
            print(f"   {header}: {value}")

        # Check if origin is allowed
        if cors_headers["Access-Control-Allow-Origin"] == frontend_origin:
            print(f"\n   ✅ Frontend origin IS allowed!")
        elif cors_headers["Access-Control-Allow-Origin"] == "*":
            print(f"\n   ✅ All origins allowed (wildcard)")
        else:
            print(
                f"\n   ❌ Frontend origin NOT allowed. Got: {cors_headers['Access-Control-Allow-Origin']}"
            )

    except Exception as e:
        print(f"   ❌ CORS preflight failed: {e}")

    # Test 3: CORS test endpoint
    print("\n3️⃣ Testing CORS test endpoint...")
    try:
        headers = {
            "Origin": frontend_origin,
        }

        response = requests.get(f"{backend_url}/cors-test", headers=headers, timeout=10)

        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")

        # Check CORS response headers
        if "Access-Control-Allow-Origin" in response.headers:
            print(
                f"   Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin')}"
            )

    except Exception as e:
        print(f"   ❌ CORS test endpoint failed: {e}")

    print("\n✅ CORS test completed. Check the results above.")


if __name__ == "__main__":
    test_cors_on_railway()
