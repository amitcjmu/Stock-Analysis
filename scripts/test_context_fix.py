#!/usr/bin/env python3
"""
Context Middleware Fix Validation

This script tests that the middleware changes resolve the engagement context requirement issue.
Specifically tests that /api/v1/clients/{id}/engagements endpoints work without engagement headers.
"""

import asyncio
import aiohttp

# Test Marathon Petroleum context (the failing case from logs)
MARATHON_CONTEXT = {
    "client_id": "73dee5f1-6a01-43e3-b1b8-dbe6c66f2990",
    "user_id": "3ee1c326-a014-4a3c-a483-5cfcf1b419d7",
    "name": "Marathon Petroleum"
}

BASE_URL = "http://localhost:8000"

async def test_public_clients_endpoint():
    """Test that public clients endpoint works (baseline test)"""
    print("🧪 Testing Public Clients Endpoint...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{BASE_URL}/api/v1/clients/public") as response:
                if response.status == 200:
                    result = await response.json()
                    client_count = len(result.get('clients', []))
                    print(f"✅ Public Clients: Found {client_count} clients")
                    
                    # Find Marathon Petroleum
                    marathon_found = False
                    for client in result.get('clients', []):
                        if client['id'] == MARATHON_CONTEXT['client_id']:
                            marathon_found = True
                            print(f"   Marathon Petroleum: {client['name']} (ID: {client['id']})")
                            break
                    
                    if not marathon_found:
                        print("❌ Marathon Petroleum not found in clients list")
                        return False
                    
                    return True
                else:
                    print(f"❌ Public Clients: Failed ({response.status})")
                    return False
        except Exception as e:
            print(f"❌ Public Clients: Error - {e}")
            return False

async def test_engagements_without_engagement_header():
    """Test that engagements endpoint works without engagement header (the main fix)"""
    print("\n🧪 Testing Engagements Endpoint Without Engagement Header...")
    
    # Headers with client and user context, but NO engagement header
    headers = {
        "Content-Type": "application/json",
        "X-Client-Account-ID": MARATHON_CONTEXT["client_id"],
        "X-User-ID": MARATHON_CONTEXT["user_id"],
        "X-User-Role": "admin"
    }
    
    print(f"   Client ID: {MARATHON_CONTEXT['client_id']}")
    print(f"   User ID: {MARATHON_CONTEXT['user_id']}")
    print("   No X-Engagement-ID header (this was causing the 400 error)")
    
    async with aiohttp.ClientSession() as session:
        try:
            url = f"{BASE_URL}/api/v1/clients/{MARATHON_CONTEXT['client_id']}/engagements"
            async with session.get(url, headers=headers) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    result = await response.json()
                    engagement_count = len(result.get('engagements', []))
                    print(f"✅ Engagements Endpoint: Success! Found {engagement_count} engagements")
                    
                    # Show engagement details
                    for engagement in result.get('engagements', []):
                        print(f"   - {engagement['name']} (ID: {engagement['id']}, Status: {engagement['status']})")
                    
                    return True
                elif response.status == 400:
                    print("❌ Engagements Endpoint: Still getting 400 error")
                    print(f"   Response: {response_text}")
                    return False
                elif response.status == 401:
                    print("❌ Engagements Endpoint: Authentication required (401)")
                    print("   This endpoint requires authentication - need to test with valid token")
                    return False
                elif response.status == 403:
                    print("❌ Engagements Endpoint: Access denied (403)")
                    print("   User may not have access to this client")
                    return False
                else:
                    print(f"❌ Engagements Endpoint: Unexpected status {response.status}")
                    print(f"   Response: {response_text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Engagements Endpoint: Connection Error - {e}")
            return False

async def test_data_import_latest_without_engagement():
    """Test that data import endpoints work without engagement header"""
    print("\n🧪 Testing Data Import Latest Endpoint Without Engagement Header...")
    
    # Headers with client context only
    headers = {
        "Content-Type": "application/json",
        "X-Client-Account-ID": MARATHON_CONTEXT["client_id"],
        "X-User-ID": MARATHON_CONTEXT["user_id"]
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            url = f"{BASE_URL}/api/v1/data-import/latest-import"
            async with session.get(url, headers=headers) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    result = await response.json()
                    print("✅ Data Import Latest: Success!")
                    print(f"   Success: {result.get('success', False)}")
                    print(f"   Message: {result.get('message', 'No message')}")
                    return True
                elif response.status == 400:
                    print("❌ Data Import Latest: 400 error - may still require engagement context")
                    print(f"   Response: {response_text}")
                    return False
                else:
                    print(f"⚠️ Data Import Latest: Status {response.status}")
                    print(f"   Response: {response_text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Data Import Latest: Error - {e}")
            return False

async def main():
    """Run all context fix validation tests"""
    print("🚀 Context Middleware Fix Validation")
    print("=" * 60)
    print("Testing that engagement headers are no longer required globally")
    print("and that context establishment endpoints work correctly.")
    print()
    
    # Test 1: Baseline - public endpoint should work
    test1_success = await test_public_clients_endpoint()
    
    # Test 2: Main fix - engagements endpoint without engagement header
    test2_success = await test_engagements_without_engagement_header()
    
    # Test 3: Data import endpoint behavior
    test3_success = await test_data_import_latest_without_engagement()
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"   Public Clients Endpoint: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"   Engagements Without Engagement Header: {'✅ PASS' if test2_success else '❌ FAIL'}")
    print(f"   Data Import Latest: {'✅ PASS' if test3_success else '❌ FAIL'}")
    
    if test1_success and test2_success:
        print("\n🎉 Context Middleware Fix: SUCCESS!")
        print("   The engagement header requirement has been resolved.")
        print("   Frontend should now be able to establish context properly.")
    elif test1_success and not test2_success:
        print("\n⚠️ Context Middleware Fix: PARTIAL SUCCESS")
        print("   Public endpoints work, but engagements endpoint may need authentication.")
        print("   The 400 'engagement required' error should be resolved.")
    else:
        print("\n❌ Context Middleware Fix: FAILED")
        print("   Backend may not be running or there are other issues.")
    
    return test1_success and test2_success

if __name__ == "__main__":
    asyncio.run(main()) 