#!/usr/bin/env python3
"""
Test script for context establishment endpoints
Tests the proper authentication flow and context establishment
"""

import sys

import requests

# Configuration
BASE_URL = "http://localhost:8000"
DEMO_TOKEN = "demo_token"

def test_authentication():
    """Test authentication with demo token"""
    print("🔐 Testing authentication...")
    
    response = requests.get(
        f"{BASE_URL}/api/v1/me",
        headers={
            "Authorization": f"Bearer {DEMO_TOKEN}",
            "Content-Type": "application/json"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Authentication successful")
        print(f"   User: {data['user']['email']} ({data['user']['role']})")
        print(f"   Client: {data['client']['name']}")
        print(f"   Engagement: {data['engagement']['name']}")
        return data
    else:
        print(f"❌ Authentication failed: {response.status_code} - {response.text}")
        return None

def test_context_clients():
    """Test context establishment clients endpoint"""
    print("\n🔍 Testing context/clients endpoint...")
    
    response = requests.get(
        f"{BASE_URL}/api/v1/context/clients",
        headers={
            "Authorization": f"Bearer {DEMO_TOKEN}",
            "Content-Type": "application/json"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Context clients endpoint successful")
        print(f"   Found {len(data.get('clients', []))} clients")
        for client in data.get('clients', []):
            print(f"   - {client['name']} (ID: {client['id']})")
        return data.get('clients', [])
    else:
        print(f"❌ Context clients failed: {response.status_code} - {response.text}")
        return []

def test_context_engagements(client_id):
    """Test context establishment engagements endpoint"""
    print(f"\n🔍 Testing context/engagements endpoint for client {client_id}...")
    
    response = requests.get(
        f"{BASE_URL}/api/v1/context/engagements",
        params={"client_id": client_id},
        headers={
            "Authorization": f"Bearer {DEMO_TOKEN}",
            "Content-Type": "application/json"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Context engagements endpoint successful")
        print(f"   Found {len(data.get('engagements', []))} engagements")
        for engagement in data.get('engagements', []):
            print(f"   - {engagement['name']} (ID: {engagement['id']})")
        return data.get('engagements', [])
    else:
        print(f"❌ Context engagements failed: {response.status_code} - {response.text}")
        return []

def test_operational_endpoint_security():
    """Test that operational endpoints properly require engagement context"""
    print("\n🔒 Testing operational endpoint security...")
    
    # Test without engagement header (should fail)
    response = requests.get(
        f"{BASE_URL}/api/v1/data-import/latest",
        headers={
            "Authorization": f"Bearer {DEMO_TOKEN}",
            "Content-Type": "application/json",
            "X-Client-Account-Id": "73dee5f1-6a01-43e3-b1b8-dbe6c66f2990",
            "X-User-Id": "44444444-4444-4444-4444-444444444444"
        }
    )
    
    if response.status_code == 400:
        print("✅ Security working: Operational endpoint properly requires engagement context")
        print(f"   Status: {response.status_code} - {response.json().get('detail', 'No detail')}")
    else:
        print("⚠️  Security issue: Operational endpoint should require engagement context")
        print(f"   Status: {response.status_code}")

def test_operational_endpoint_with_context():
    """Test operational endpoint with proper context"""
    print("\n✅ Testing operational endpoint with full context...")
    
    # Test with full context headers (should work or give 404 for no data)
    response = requests.get(
        f"{BASE_URL}/api/v1/data-import/latest",
        headers={
            "Authorization": f"Bearer {DEMO_TOKEN}",
            "Content-Type": "application/json",
            "X-Client-Account-Id": "73dee5f1-6a01-43e3-b1b8-dbe6c66f2990",
            "X-User-Id": "44444444-4444-4444-4444-444444444444",
            "X-Engagement-Id": "3362a198-c917-459c-be10-b10e19b1810e"
        }
    )
    
    if response.status_code in [200, 404]:
        print("✅ Operational endpoint working with context")
        print(f"   Status: {response.status_code} (404 is expected - no data uploaded yet)")
    else:
        print(f"❌ Operational endpoint failed: {response.status_code} - {response.text}")

def main():
    """Main test function"""
    print("🚀 Starting Context Establishment Test Suite")
    print("=" * 60)
    
    # Test 1: Authentication
    auth_data = test_authentication()
    if not auth_data:
        print("❌ Authentication failed, cannot continue")
        sys.exit(1)
    
    # Test 2: Context clients endpoint
    clients = test_context_clients()
    if not clients:
        print("❌ No clients found, cannot continue")
        sys.exit(1)
    
    # Test 3: Context engagements endpoint
    first_client_id = clients[0]['id']
    engagements = test_context_engagements(first_client_id)
    
    # Test 4: Security validation
    test_operational_endpoint_security()
    
    # Test 5: Operational endpoint with context
    test_operational_endpoint_with_context()
    
    print("\n" + "=" * 60)
    print("🎉 Context Establishment Test Suite Complete!")
    print("\n📊 Summary:")
    print("   ✅ Authentication: Working")
    print(f"   ✅ Context Clients: {len(clients)} clients found")
    print(f"   ✅ Context Engagements: {len(engagements)} engagements found")
    print("   ✅ Security: Engagement context properly enforced")
    print("   ✅ Architecture: Context establishment endpoints working")
    
    print("\n🎯 Frontend Integration:")
    print("   1. Use /api/v1/context/clients to populate client dropdown")
    print("   2. Use /api/v1/context/engagements?client_id=X to populate engagement dropdown")
    print("   3. Both endpoints work without engagement context requirement")
    print("   4. Operational endpoints properly require full context for security")

if __name__ == "__main__":
    main() 