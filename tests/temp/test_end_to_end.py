#!/usr/bin/env python3
"""
End-to-end test to verify the Discovery Flow works after repository fixes
"""

import requests
import time

# Test data
test_data = [
    {
        "hostname": "web-server-01",
        "type": "Server", 
        "os": "Linux",
        "application": "WebApp",
        "environment": "Production"
    },
    {
        "hostname": "db-server-01",
        "type": "Database",
        "os": "Linux", 
        "application": "MySQL",
        "environment": "Production"
    }
]

# Headers
headers = {
    "Content-Type": "application/json",
    "X-Client-Account-ID": "524e4dea-2c05-4df1-ab1f-35f67aad1415",
    "X-Engagement-ID": "72470319-c5d6-468f-ab53-cf9e302e466"
}

print("🧪 Testing end-to-end Discovery Flow...")

# Test 1: Check backend health
print("1. Testing backend health...")
try:
    response = requests.get("http://localhost:8000/health")
    if response.status_code == 200:
        print("✅ Backend is healthy")
    else:
        print(f"❌ Backend health check failed: {response.status_code}")
        exit(1)
except Exception as e:
    print(f"❌ Backend connection failed: {e}")
    exit(1)

# Test 2: Check frontend
print("2. Testing frontend...")
try:
    response = requests.get("http://localhost:8081")
    if response.status_code == 200:
        print("✅ Frontend is accessible")
    else:
        print(f"❌ Frontend check failed: {response.status_code}")
except Exception as e:
    print(f"❌ Frontend connection failed: {e}")

# Test 3: Try to trigger a Discovery Flow via unified API 
print("3. Testing Discovery Flow creation...")
try:
    payload = {
        "raw_data": test_data,
        "metadata": {
            "filename": "test_data.csv",
            "source": "end_to_end_test"
        },
        "execution_mode": "hybrid"
    }
    
    response = requests.post(
        "http://localhost:8000/api/v1/discovery/flow/initialize",
        json=payload,
        headers=headers
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response: {response.text[:500]}...")
    
    if response.status_code == 200:
        result = response.json()
        if "flow_id" in result:
            flow_id = result["flow_id"]
            print(f"✅ Discovery Flow created: {flow_id}")
            
            # Test 4: Check flow status
            print("4. Checking flow status...")
            time.sleep(2)  # Give it time to start
            
            status_response = requests.get(
                f"http://localhost:8000/api/v1/discovery/flow/status/{flow_id}",
                headers=headers
            )
            
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"✅ Flow status retrieved: {status.get('status', 'unknown')}")
                print(f"📊 Current phase: {status.get('current_phase', 'unknown')}")
            else:
                print(f"⚠️ Could not get flow status: {status_response.status_code}")
        else:
            print(f"⚠️ Flow created but no flow_id returned: {result}")
    else:
        print(f"⚠️ Discovery Flow creation returned: {response.status_code}")
        
except Exception as e:
    print(f"❌ Discovery Flow test failed: {e}")

print("✅ End-to-end test completed!")