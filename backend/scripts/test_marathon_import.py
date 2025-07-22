#!/usr/bin/env python3
import json

import requests


def test_marathon_import():
    """Test data import with Marathon context."""
    
    marathon_headers = {
        "Content-Type": "application/json",
        "X-Client-Account-ID": "73dee5f1-6a01-43e3-b1b8-dbe6c66f2990",
        "X-Engagement-ID": "baf640df-433c-4bcd-8c8f-7b01c12e9005", 
        "X-User-ID": "3ee1c326-a014-4a3c-a483-5cfcf1b419d7"
    }
    
    test_data = {
        "filename": "test_marathon_context.csv",
        "upload_type": "csv_upload",
        "headers": ["Asset_ID", "Asset_Name", "Asset_Type", "Environment"],
        "sample_data": [
            {
                "Asset_ID": "marathon-test-001", 
                "Asset_Name": "Marathon Test Server", 
                "Asset_Type": "Server", 
                "Environment": "Production"
            }
        ],
        "user_id": "3ee1c326-a014-4a3c-a483-5cfcf1b419d7"
    }
    
    print("🧪 Testing Marathon Context Data Import...")
    print(f"   Client: {marathon_headers['X-Client-Account-ID']}")
    print(f"   Engagement: {marathon_headers['X-Engagement-ID']}")
    
    try:
        # Test the import
        response = requests.post(
            "http://localhost:8000/api/v1/data-import/data-imports",
            headers=marathon_headers,
            json=test_data,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Import successful!")
            print(f"   Session ID: {result.get('session_id')}")
            print(f"   Client returned: {result.get('client_account_id')}")
            print(f"   Engagement returned: {result.get('engagement_id')}")
            
            # Now check if we can see attributes in Marathon context
            print("\n🔍 Checking Marathon context for attributes...")
            check_response = requests.get(
                "http://localhost:8000/api/v1/data-import/critical-attributes-status",
                headers=marathon_headers
            )
            
            if check_response.status_code == 200:
                check_data = check_response.json()
                total_attrs = check_data.get('statistics', {}).get('total_attributes', 0)
                print(f"   Attributes found: {total_attrs}")
                
                if total_attrs > 0:
                    print("🎉 SUCCESS: Marathon context now has data!")
                else:
                    print("❌ Still no attributes in Marathon context")
            else:
                print(f"❌ Error checking attributes: {check_response.status_code}")
                
        else:
            print(f"❌ Import failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_marathon_import() 