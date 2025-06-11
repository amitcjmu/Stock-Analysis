#!/usr/bin/env python3
"""
Debug script to test backend fixes for admin interface issues.
Tests user deactivation and engagement creation API endpoints.
"""

import requests
import json
import uuid

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_HEADERS = {
    'Content-Type': 'application/json',
    'X-User-ID': 'admin_user',  # Demo admin user
}

def test_user_deactivation():
    """Test user deactivation endpoint with fixed datetime import."""
    print("🔍 Testing User Deactivation...")
    
    # First get list of active users
    try:
        response = requests.get(f"{BASE_URL}/api/v1/auth/active-users", headers=ADMIN_HEADERS)
        if response.status_code == 200:
            users_data = response.json()
            active_users = [u for u in users_data.get('users', []) if u.get('status') == 'active']
            
            if active_users:
                test_user_id = active_users[0]['user_id']
                print(f"   Found active user to test: {test_user_id}")
                
                # Test deactivation
                deactivate_data = {
                    "user_id": test_user_id,
                    "reason": "Test deactivation from debug script"
                }
                
                response = requests.post(
                    f"{BASE_URL}/api/v1/auth/deactivate-user",
                    headers=ADMIN_HEADERS,
                    json=deactivate_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ User deactivation SUCCESS: {result.get('message')}")
                    
                    # Test reactivation
                    reactivate_data = {"user_id": test_user_id}
                    response = requests.post(
                        f"{BASE_URL}/api/v1/auth/activate-user",
                        headers=ADMIN_HEADERS,
                        json=reactivate_data
                    )
                    
                    if response.status_code == 200:
                        print("   ✅ User reactivation SUCCESS")
                        return True
                    else:
                        print(f"   ❌ User reactivation FAILED: {response.status_code} - {response.text}")
                        return False
                else:
                    print(f"   ❌ User deactivation FAILED: {response.status_code} - {response.text}")
                    return False
            else:
                print("   ⚠️ No active users found to test")
                return True  # Not a failure, just no test data
        else:
            print(f"   ❌ Failed to get users: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception during user deactivation test: {e}")
        return False

def test_engagement_creation():
    """Test engagement creation endpoint with required enum fields."""
    print("\n🔍 Testing Engagement Creation...")
    
    try:
        # First get client accounts
        response = requests.get(f"{BASE_URL}/api/v1/admin/clients/", headers=ADMIN_HEADERS)
        
        if response.status_code == 200:
            clients_data = response.json()
            clients = clients_data.get('items', [])
            
            if clients:
                test_client_id = clients[0]['id']
                print(f"   Found client to test with: {test_client_id}")
                
                # Create test engagement with all required fields
                engagement_data = {
                    "engagement_name": "Debug Test Engagement",
                    "client_account_id": test_client_id,
                    "engagement_description": "This is a test engagement created by the debug script to validate backend functionality.",
                    "migration_scope": "full_datacenter",  # Required enum
                    "target_cloud_provider": "aws",       # Required enum
                    "engagement_manager": "Debug Test Manager",
                    "technical_lead": "Debug Test Lead",
                    "planned_start_date": "2025-02-01T00:00:00Z",
                    "planned_end_date": "2025-06-30T00:00:00Z",
                    "estimated_budget": 500000.0,
                    "team_preferences": {},
                    "agent_configuration": {},
                    "discovery_preferences": {},
                    "assessment_criteria": {}
                }
                
                response = requests.post(
                    f"{BASE_URL}/api/v1/admin/engagements/",
                    headers=ADMIN_HEADERS,
                    json=engagement_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ Engagement creation SUCCESS: {result.get('message')}")
                    
                    # Get the created engagement ID for cleanup
                    engagement_id = result.get('data', {}).get('id')
                    if engagement_id:
                        print(f"   📝 Created engagement ID: {engagement_id}")
                    
                    return True
                else:
                    print(f"   ❌ Engagement creation FAILED: {response.status_code}")
                    print(f"   Response: {response.text}")
                    return False
            else:
                print("   ⚠️ No client accounts found. Creating demo client first...")
                
                # Create a demo client account
                client_data = {
                    "account_name": "Debug Test Client",
                    "industry": "Technology",
                    "company_size": "Medium",
                    "headquarters_location": "Test City, Test Country",
                    "primary_contact_name": "Debug Test Contact",
                    "primary_contact_email": "debug@test.com"
                }
                
                response = requests.post(
                    f"{BASE_URL}/api/v1/admin/clients/",
                    headers=ADMIN_HEADERS,
                    json=client_data
                )
                
                if response.status_code == 200:
                    print("   ✅ Demo client created successfully")
                    # Retry engagement creation
                    return test_engagement_creation()
                else:
                    print(f"   ❌ Demo client creation FAILED: {response.status_code} - {response.text}")
                    return False
        else:
            print(f"   ❌ Failed to get clients: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception during engagement creation test: {e}")
        return False

def test_api_health():
    """Test basic API health."""
    print("🔍 Testing API Health...")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("   ✅ API Health check SUCCESS")
            return True
        else:
            print(f"   ❌ API Health check FAILED: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Exception during health check: {e}")
        return False

def main():
    """Run all backend tests."""
    print("🎯 Backend Fixes Validation")
    print("=" * 50)
    
    results = []
    
    # Test API health first
    results.append(test_api_health())
    
    # Test user deactivation (datetime import fix)
    results.append(test_user_deactivation())
    
    # Test engagement creation (enum field requirements)
    results.append(test_engagement_creation())
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 50)
    
    if all(results):
        print("🎉 ALL TESTS PASSED - Backend fixes working correctly!")
        print("✅ User deactivation endpoint fixed (datetime import)")
        print("✅ Engagement creation endpoint working")
        print("✅ API is healthy and responsive")
        return True
    else:
        print("❌ SOME TESTS FAILED - Backend issues still exist")
        print(f"   Test results: {results}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 