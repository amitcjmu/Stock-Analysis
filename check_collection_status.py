#!/usr/bin/env python3
"""
Check the current status of collection flows in the database
"""

import httpx
import json

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "demo@demo-corp.com"
TEST_PASSWORD = "Demo123!"
CLIENT_ACCOUNT_ID = "11111111-1111-1111-1111-111111111111"
ENGAGEMENT_ID = "22222222-2222-2222-2222-222222222222"

def get_auth_token():
    """Authenticate and get JWT token"""
    auth_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    with httpx.Client() as client:
        response = client.post(f"{BASE_URL}/api/v1/auth/login", json=auth_data)
        
        if response.status_code != 200:
            print(f"❌ Authentication failed: {response.status_code}")
            return None
        
        token_data = response.json()
        if "token" in token_data and "access_token" in token_data["token"]:
            return token_data["token"]["access_token"]
        return None

def check_collection_flow():
    """Check detailed collection flow status"""
    
    token = get_auth_token()
    if not token:
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Client-Account-ID": CLIENT_ACCOUNT_ID,
        "X-Engagement-ID": ENGAGEMENT_ID
    }
    
    with httpx.Client() as client:
        # Get status
        print("📊 Getting collection status...")
        response = client.get(f"{BASE_URL}/api/v1/collection/status", headers=headers)
        
        if response.status_code == 200:
            status = response.json()
            print("✅ Collection Flow Status:")
            print(f"   Flow ID: {status.get('flow_id')}")
            print(f"   Status: {status.get('status')}")
            print(f"   Current Phase: {status.get('current_phase')}")
            print(f"   Progress: {status.get('progress')}%")
            print(f"   Automation Tier: {status.get('automation_tier')}")
            print(f"   Created: {status.get('created_at')}")
            print(f"   Updated: {status.get('updated_at')}")
            
            # Get detailed flow info
            flow_id = status.get('flow_id')
            if flow_id:
                print(f"\n🔍 Getting detailed flow info for {flow_id}...")
                response = client.get(f"{BASE_URL}/api/v1/collection/flows/{flow_id}", headers=headers)
                
                if response.status_code == 200:
                    details = response.json()
                    print("✅ Collection Flow Details:")
                    print(f"   Flow ID: {details.get('id')}")
                    print(f"   Client Account: {details.get('client_account_id')}")
                    print(f"   Engagement: {details.get('engagement_id')}")
                    print(f"   Status: {details.get('status')}")
                    print(f"   Current Phase: {details.get('current_phase')}")
                    print(f"   Progress: {details.get('progress')}%")
                    print(f"   Collection Config: {json.dumps(details.get('collection_config', {}), indent=2)}")
                    print(f"   Gaps Identified: {details.get('gaps_identified', 0)}")
                    print(f"   Collection Metrics: {json.dumps(details.get('collection_metrics', {}), indent=2)}")
                    print(f"   Completed At: {details.get('completed_at')}")
                else:
                    print(f"❌ Failed to get flow details: {response.status_code} - {response.text}")
        else:
            print(f"❌ Failed to get status: {response.status_code} - {response.text}")

if __name__ == "__main__":
    print("🔍 Checking Collection Flow Status")
    print("=" * 50)
    check_collection_flow()