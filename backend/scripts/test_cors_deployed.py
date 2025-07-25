#!/usr/bin/env python3
"""Test CORS configuration on deployed Railway backend"""

import requests


def test_cors():
    """Test CORS configuration"""
    base_url = "https://migrate-ui-orchestrator-production.up.railway.app"
    origin = "https://aiforce-assess.vercel.app"

    print("🔍 Testing CORS configuration on Railway deployment")
    print("=" * 60)

    # Test 1: Health endpoint
    print("\n1. Testing health endpoint:")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"   Status: {response.status_code}")
        print(
            f"   CORS headers: {response.headers.get('Access-Control-Allow-Origin', 'NONE')}"
        )
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 2: OPTIONS preflight
    print("\n2. Testing OPTIONS preflight for /api/v1/auth/login:")
    try:
        headers = {
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        }
        response = requests.options(
            f"{base_url}/api/v1/auth/login", headers=headers, timeout=10
        )
        print(f"   Status: {response.status_code}")
        print(
            f"   Allow-Origin: {response.headers.get('Access-Control-Allow-Origin', 'NONE')}"
        )
        print(
            f"   Allow-Methods: {response.headers.get('Access-Control-Allow-Methods', 'NONE')}"
        )
        print(
            f"   Allow-Headers: {response.headers.get('Access-Control-Allow-Headers', 'NONE')}"
        )
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 3: Actual POST request
    print("\n3. Testing POST to /api/v1/auth/login:")
    try:
        headers = {"Origin": origin, "Content-Type": "application/json"}
        data = {"email": "test@example.com", "password": "test"}
        response = requests.post(
            f"{base_url}/api/v1/auth/login", headers=headers, json=data, timeout=10
        )
        print(f"   Status: {response.status_code}")
        print(
            f"   Allow-Origin: {response.headers.get('Access-Control-Allow-Origin', 'NONE')}"
        )
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 4: Check if backend is detecting Railway environment
    print("\n4. Testing environment detection at /api/v1/health/debug:")
    try:
        response = requests.get(f"{base_url}/api/v1/health/debug", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Environment: {data.get('environment', 'unknown')}")
            print(f"   CORS origins: {data.get('cors_origins', [])}")
    except Exception as e:
        print(f"   ❌ Error: {e}")


if __name__ == "__main__":
    test_cors()
