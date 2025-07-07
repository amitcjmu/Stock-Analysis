#!/usr/bin/env python3
import requests
import json
import time

BASE_URL = "http://localhost:8000"
CLIENT_ID = "11111111-1111-1111-1111-111111111111"
ENGAGEMENT_ID = "22222222-2222-2222-2222-222222222222"

def test_flow_deletion():
    print("🔍 Testing Flow Deletion Fix")
    print("=" * 50)
    
    # Step 1: Login
    print("\n1. Login...")
    login_response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "email": "demo@demo-corp.com",
        "password": "Demo123!"
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return False
    
    auth_data = login_response.json()
    token = auth_data.get("access_token", auth_data.get("token"))
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Client-Account-ID": CLIENT_ID,
        "X-Engagement-ID": ENGAGEMENT_ID
    }
    
    # Step 2: List existing flows
    print("\n2. Listing existing flows...")
    flows_response = requests.get(
        f"{BASE_URL}/api/v1/flows/?flowType=discovery",
        headers=headers
    )
    
    if flows_response.status_code == 200:
        flows = flows_response.json()["flows"]
        print(f"Found {len(flows)} flows")
        for flow in flows:
            print(f"  - {flow['flow_id']}: {flow['status']}")
    
    # Step 3: Delete the existing flow
    if flows:
        flow_to_delete = flows[0]["flow_id"]
        print(f"\n3. Deleting flow {flow_to_delete}...")
        
        delete_response = requests.delete(
            f"{BASE_URL}/api/v1/master-flows/{flow_to_delete}",
            headers=headers
        )
        
        if delete_response.status_code == 200:
            print("✅ Delete request successful")
            result = delete_response.json()
            print(f"   Result: {result}")
        else:
            print(f"❌ Delete failed: {delete_response.status_code}")
            print(f"   Error: {delete_response.text}")
    
    # Step 4: List flows again to verify deletion
    print("\n4. Verifying deletion...")
    time.sleep(2)  # Give it a moment
    
    verify_response = requests.get(
        f"{BASE_URL}/api/v1/flows/?flowType=discovery",
        headers=headers
    )
    
    if verify_response.status_code == 200:
        remaining_flows = verify_response.json()["flows"]
        print(f"Remaining flows: {len(remaining_flows)}")
        
        if len(remaining_flows) == 0:
            print("✅ Flow successfully deleted and no longer appears in list!")
        else:
            print("❌ Flow still appears in list after deletion")
            for flow in remaining_flows:
                print(f"  - {flow['flow_id']}: {flow['status']}")
    
    # Step 5: Check database directly
    print("\n5. Checking database status...")
    import subprocess
    result = subprocess.run([
        'docker', 'exec', 'migration_backend', 'python', '-c',
        """
from sqlalchemy import create_engine, text
import os
db_url = os.environ.get('DATABASE_URL')
engine = create_engine(db_url)
with engine.connect() as conn:
    result = conn.execute(text('''
        SELECT flow_id, flow_status 
        FROM crewai_flow_state_extensions 
        WHERE client_account_id = '11111111-1111-1111-1111-111111111111'
        ORDER BY created_at DESC LIMIT 1
    '''))
    row = result.fetchone()
    if row:
        print(f'Latest master flow: {row[0]}, Status: {row[1]}')
"""
    ], capture_output=True, text=True)
    
    print(result.stdout.strip())
    
    print("\n" + "=" * 50)
    print("Test complete!")

if __name__ == "__main__":
    test_flow_deletion()