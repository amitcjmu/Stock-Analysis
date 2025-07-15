#!/usr/bin/env python3
"""
Test script to verify the foreign key constraint fix for data imports.
"""

import requests
import json
import time
import os

# Get platform admin credentials
ADMIN_EMAIL = "chocka@gmail.com"
ADMIN_PASSWORD = "Password123!"
BASE_URL = "http://localhost:8000"

def login():
    """Login and get access token"""
    login_data = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def get_client_context(token):
    """Get client context for API calls"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/api/v1/clients/available", headers=headers)
    if response.status_code == 200:
        clients = response.json()
        if clients:
            client = clients[0]
            return {
                "client_account_id": client["id"],
                "engagement_id": client["engagements"][0]["id"] if client.get("engagements") else None
            }
    return None

def test_data_import(token, context):
    """Test data import with the CSV file"""
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Client-Account-ID": context["client_account_id"],
        "X-Engagement-ID": context["engagement_id"]
    }
    
    # Prepare the file upload
    csv_file_path = "/Users/chocka/CursorProjects/migrate-ui-orchestrator/temp/sample_cmdb_data.csv"
    
    with open(csv_file_path, 'rb') as file:
        files = {
            'file': ('sample_cmdb_data.csv', file, 'text/csv')
        }
        
        data = {
            'import_name': 'Test Import - Foreign Key Fix',
            'import_type': 'cmdb',
            'description': 'Testing the foreign key constraint fix'
        }
        
        print("🚀 Starting data import test...")
        response = requests.post(
            f"{BASE_URL}/api/v1/data-import/store-import",
            headers=headers,
            files=files,
            data=data
        )
        
        print(f"📊 Import response: {response.status_code}")
        print(f"📝 Response body: {response.text}")
        
        if response.status_code == 200:
            import_data = response.json()
            import_id = import_data.get("data_import_id")
            print(f"✅ Import started successfully! Import ID: {import_id}")
            return import_id
        else:
            print(f"❌ Import failed: {response.status_code} - {response.text}")
            return None

def check_import_status(token, context, import_id):
    """Check the status of the import"""
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Client-Account-ID": context["client_account_id"],
        "X-Engagement-ID": context["engagement_id"]
    }
    
    print(f"🔍 Checking import status for ID: {import_id}")
    response = requests.get(f"{BASE_URL}/api/v1/data-import/{import_id}/status", headers=headers)
    
    if response.status_code == 200:
        status_data = response.json()
        print(f"📊 Import Status: {json.dumps(status_data, indent=2)}")
        return status_data
    else:
        print(f"❌ Status check failed: {response.status_code} - {response.text}")
        return None

def main():
    print("🧪 Testing data import foreign key constraint fix...")
    
    # Login
    token = login()
    if not token:
        print("❌ Failed to login")
        return
    
    print("✅ Login successful")
    
    # Get client context
    context = get_client_context(token)
    if not context:
        print("❌ Failed to get client context")
        return
    
    print(f"✅ Client context: {context}")
    
    # Test data import
    import_id = test_data_import(token, context)
    if not import_id:
        print("❌ Data import test failed")
        return
    
    # Wait a moment and check status
    time.sleep(3)
    status = check_import_status(token, context, import_id)
    
    if status:
        print("✅ Foreign key constraint fix test completed!")
        print(f"📊 Final status: {status.get('status', 'unknown')}")
    else:
        print("❌ Status check failed")

if __name__ == "__main__":
    main()