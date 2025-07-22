#!/usr/bin/env python3
"""
Test script to upload a file and monitor backend logs for errors
"""
import requests
import time
import subprocess
import threading
import uuid
from datetime import datetime

# Test CSV data
test_csv_data = [
    {
        "row_index": 1,
        "App_ID": "APP-001",
        "App_Name": "TestApp1",
        "App_Version": "1.0.0",
        "Dependency_List": "LibA,LibB",
        "Owner_Group": "Dev Team",
        "Scan_Date": "2025-01-27 10:00:00",
        "Scan_Status": "Completed",
        "Port_Usage": "8080,8443",
        "Last_Update": "2025-01-27"
    },
    {
        "row_index": 2,
        "App_ID": "APP-002", 
        "App_Name": "TestApp2",
        "App_Version": "2.0.0",
        "Dependency_List": "LibC,LibD",
        "Owner_Group": "Ops Team",
        "Scan_Date": "2025-01-27 11:00:00",
        "Scan_Status": "Completed",
        "Port_Usage": "80,443",
        "Last_Update": "2025-01-27"
    }
]

def monitor_backend_logs():
    """Monitor backend logs in real-time"""
    print("🔍 Starting backend log monitoring...")
    try:
        process = subprocess.Popen(
            ["docker-compose", "logs", "-f", "backend"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        for line in process.stdout:
            if any(keyword in line.lower() for keyword in ['error', 'failed', 'invalid', 'uuid', 'analysis', 'phase', 'completed']):
                print(f"🚨 {datetime.now().strftime('%H:%M:%S')} | {line.strip()}")
                
    except Exception as e:
        print(f"❌ Log monitoring error: {e}")

def upload_test_file():
    """Upload test file to the discovery import endpoint"""
    print("📤 Starting file upload test...")
    
    # Generate proper UUIDs
    validation_session_id = str(uuid.uuid4())
    
    upload_data = {
        "file_data": test_csv_data,
        "metadata": {
            "filename": "test_discovery.csv",
            "size": 500,
            "type": "text/csv"
        },
        "upload_context": {
            "intended_type": "app-discovery",
            "validation_session_id": validation_session_id,
            "upload_timestamp": datetime.now().isoformat()
        },
        "client_id": "dfea7406-1575-4348-a0b2-2770cbe2d9f9",
        "engagement_id": "ce27e7b1-2ac6-4b74-8dd5-b52d542a1669"
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Client-Account-ID": "dfea7406-1575-4348-a0b2-2770cbe2d9f9",
        "X-Engagement-ID": "ce27e7b1-2ac6-4b74-8dd5-b52d542a1669",
        "X-User-ID": "ebbc3a18-f9fd-471e-a1b3-2ffd575fcc02",
        "X-Session-ID": "ce27e7b1-2ac6-4b74-8dd5-b52d542a1669"
    }
    
    try:
        print(f"📡 Sending upload request with validation_session_id: {validation_session_id}")
        response = requests.post(
            "http://localhost:8000/api/v1/data-import/store-import",
            json=upload_data,
            headers=headers,
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload successful!")
            print(f"📋 Flow ID: {result.get('flow_id', 'N/A')}")
            print(f"📋 Import Session: {result.get('import_session_id', 'N/A')}")
            return result.get('flow_id')
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return None

def main():
    print("🚀 Starting Discovery Flow Upload Test with Proper UUIDs")
    print("=" * 60)
    
    # Start log monitoring in background
    log_thread = threading.Thread(target=monitor_backend_logs, daemon=True)
    log_thread.start()
    
    # Wait a moment for log monitoring to start
    time.sleep(2)
    
    # Upload test file
    flow_id = upload_test_file()
    
    if flow_id:
        print(f"\n⏳ Monitoring flow {flow_id} for 90 seconds...")
        print("👀 Watch for CrewAI discovery flow errors in the logs above...")
        time.sleep(90)
    else:
        print("\n❌ Upload failed, monitoring for 30 seconds anyway...")
        time.sleep(30)
    
    print("\n🏁 Test completed!")

if __name__ == "__main__":
    main() 