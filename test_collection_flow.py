#!/usr/bin/env python3
"""
Test Collection Flow to verify CrewAI agents are invoked
"""

import httpx
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "demo@demo-corp.com"
TEST_PASSWORD = "Demo123!"
CLIENT_ACCOUNT_ID = "11111111-1111-1111-1111-111111111111"
ENGAGEMENT_ID = "22222222-2222-2222-2222-222222222222"

def get_auth_token():
    """Authenticate and get JWT token"""
    print("🔑 Authenticating...")
    
    auth_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    with httpx.Client() as client:
        response = client.post(f"{BASE_URL}/api/v1/auth/login", json=auth_data)
        
        if response.status_code != 200:
            print(f"❌ Authentication failed: {response.status_code} - {response.text}")
            return None
        
        token_data = response.json()
        print(f"✅ Authentication successful")
        # Extract token from nested structure
        if "token" in token_data and "access_token" in token_data["token"]:
            return token_data["token"]["access_token"]
        else:
            print(f"Token response: {token_data}")
            return None

def test_collection_flow():
    """Test collection flow creation and execution"""
    
    # Get auth token
    token = get_auth_token()
    if not token:
        return False
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Client-Account-ID": CLIENT_ACCOUNT_ID,
        "X-Engagement-ID": ENGAGEMENT_ID
    }
    
    # Check collection status first
    print("\n📊 Checking collection status...")
    with httpx.Client() as client:
        response = client.get(f"{BASE_URL}/api/v1/collection/status", headers=headers)
        print(f"Status response: {response.status_code}")
        if response.status_code == 200:
            print(f"Current status: {response.json()}")
    
    # Create collection flow
    print("\n🚀 Creating collection flow...")
    
    collection_data = {
        "automation_tier": "tier_2",
        "collection_config": {
            "environment": "test",
            "platforms": ["aws", "azure"],
            "quality_threshold": 0.8
        }
    }
    
    with httpx.Client(timeout=60.0) as client:
        response = client.post(
            f"{BASE_URL}/api/v1/collection/flows", 
            json=collection_data, 
            headers=headers
        )
        
        print(f"Collection flow creation response: {response.status_code}")
        
        if response.status_code == 200:
            flow_data = response.json()
            flow_id = flow_data["id"]
            print(f"✅ Collection flow created successfully!")
            print(f"Flow ID: {flow_id}")
            print(f"Status: {flow_data['status']}")
            print(f"Automation Tier: {flow_data['automation_tier']}")
            
            # Monitor flow for a few seconds
            print(f"\n⏱️ Monitoring flow execution for 10 seconds...")
            for i in range(10):
                time.sleep(1)
                
                # Check flow status
                response = client.get(
                    f"{BASE_URL}/api/v1/collection/flows/{flow_id}", 
                    headers=headers
                )
                
                if response.status_code == 200:
                    current_data = response.json()
                    print(f"[{i+1}s] Status: {current_data['status']}, Progress: {current_data['progress']}%")
                else:
                    print(f"[{i+1}s] Failed to get status: {response.status_code}")
                    
            return True
            
        else:
            print(f"❌ Failed to create collection flow: {response.status_code}")
            print(f"Response: {response.text}")
            return False

if __name__ == "__main__":
    print("🧪 Testing Collection Flow with CrewAI Agents")
    print("=" * 50)
    
    success = test_collection_flow()
    
    if success:
        print("\n✅ Collection flow test completed!")
        print("📋 Check the logs in /tmp/collection_crewai.log for CrewAI agent execution details")
    else:
        print("\n❌ Collection flow test failed!")