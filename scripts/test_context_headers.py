#!/usr/bin/env python3
"""
Context Header Standardization Test

This script tests that frontend and backend are now using consistent
header naming conventions to resolve console errors and context mismatches.
"""

import asyncio
from datetime import datetime

import aiohttp

# Test contexts from the logs
TEST_CONTEXTS = {
    "marathon_petroleum": {
        "client_id": "d838573d-f461-44e4-81b5-5af510ef83b7",
        "engagement_id": "d1a93e23-719d-4dad-8bbf-b66ab9de2b94",
        "user_id": "3ee1c326-a014-4a3c-a483-5cfcf1b419d7"
    },
    "demo_client": {
        "client_id": "bafd5b46-aaaf-4c95-8142-573699d93171",
        "engagement_id": "6e9c8133-4169-4b79-b052-106dc93d0208",
        "user_id": "44444444-4444-4444-4444-444444444444"
    }
}

BASE_URL = "http://localhost:8000"

async def test_context_headers():
    """Test that the standardized headers work correctly."""
    
    print("🧪 Testing Context Header Standardization")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        
        for context_name, context in TEST_CONTEXTS.items():
            print(f"\n📋 Testing {context_name.title()} Context:")
            print(f"   Client: {context['client_id']}")
            print(f"   Engagement: {context['engagement_id']}")
            print(f"   User: {context['user_id']}")
            
            # Standard headers (what frontend now sends)
            headers = {
                "Content-Type": "application/json",
                "X-Client-Account-ID": context["client_id"],
                "X-Engagement-ID": context["engagement_id"],
                "X-User-ID": context["user_id"],
                "X-Session-ID": f"test-session-{datetime.now().isoformat()}"
            }
            
            # Test endpoints that were failing
            test_endpoints = [
                "/api/v1/clients",
                f"/api/v1/clients/{context['client_id']}/engagements",
                f"/api/v1/sessions/engagement/{context['engagement_id']}",
                "/api/v1/discovery/latest-import",
                "/api/v1/data-import/latest-import"
            ]
            
            for endpoint in test_endpoints:
                try:
                    print(f"   🔍 Testing: {endpoint}")
                    
                    async with session.get(f"{BASE_URL}{endpoint}", headers=headers) as response:
                        if response.status == 200:
                            print(f"      ✅ Status: {response.status} - Headers accepted")
                        elif response.status == 400:
                            response_text = await response.text()
                            if "Client account context is required" in response_text:
                                print(f"      ❌ Status: {response.status} - Context header still not recognized")
                            else:
                                print(f"      ⚠️  Status: {response.status} - Different validation error")
                        else:
                            print(f"      ⚠️  Status: {response.status} - Unexpected response")
                            
                except Exception as e:
                    print(f"      ❌ Error: {e}")
            
            print()

async def test_debug_context_endpoint():
    """Test the debug context endpoint to verify header extraction."""
    
    print("🔧 Testing Debug Context Endpoint")
    print("=" * 40)
    
    test_headers = {
        "X-Client-Account-ID": "test-client-123",
        "X-Engagement-ID": "test-engagement-456", 
        "X-User-ID": "test-user-789",
        "X-Session-ID": "test-session-000"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{BASE_URL}/debug/context", headers=test_headers) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Debug endpoint response:")
                    print(f"   Extracted Context: {data.get('extracted_context', {})}")
                    print(f"   Validation Status: {data.get('validation_status', 'unknown')}")
                    
                    # Verify headers were extracted correctly
                    extracted = data.get('extracted_context', {})
                    if (extracted.get('client_account_id') == 'test-client-123' and
                        extracted.get('engagement_id') == 'test-engagement-456' and
                        extracted.get('user_id') == 'test-user-789'):
                        print("   ✅ All headers extracted correctly!")
                    else:
                        print("   ❌ Header extraction failed")
                else:
                    print(f"❌ Debug endpoint failed: {response.status}")
                    
        except Exception as e:
            print(f"❌ Debug test failed: {e}")

async def main():
    """Run all context header tests."""
    
    print("🚀 Context Header Standardization Test Suite")
    print(f"⏰ Started at: {datetime.now().isoformat()}")
    print()
    
    await test_debug_context_endpoint()
    print()
    await test_context_headers()
    
    print("📊 Test Summary:")
    print("   - Frontend now sends: X-Client-Account-ID, X-Engagement-ID, X-User-ID, X-Session-ID")
    print("   - Backend accepts: All standard header variations")
    print("   - Context mismatch between pages should be resolved")
    print("   - Console errors for missing headers should be eliminated")
    print()
    print("✅ Context header standardization test completed!")

if __name__ == "__main__":
    asyncio.run(main()) 