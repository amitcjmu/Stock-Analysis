#!/usr/bin/env python3
"""
Test script for CMDB analysis endpoint.
"""

import time

import requests


def test_cmdb_analysis():
    """Test the CMDB analysis endpoint."""
    print("🧪 Testing CMDB Analysis Endpoint")
    print("=" * 50)

    # Wait for backend to be ready
    print("⏳ Waiting for backend to be ready...")
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ Backend is ready!")
                break
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
        print(f"   Waiting... ({i+1}/30)")
    else:
        print("❌ Backend not ready after 30 seconds")
        return False

    # Test data
    test_csv_content = """Name,CI_Type,Environment,CPU_Cores,Memory_GB,IP_Address
WebServer01,Server,Production,4,8,192.168.1.10
AppServer02,Server,Production,8,16,192.168.1.11
PaymentApp,Application,Production,,,
DatabaseSrv,Server,Production,16,32,192.168.1.12"""

    # Test request
    test_request = {
        "filename": "test_cmdb_export.csv",
        "content": test_csv_content,
        "fileType": "text/csv",
    }

    print("\n📊 Testing CMDB Analysis...")
    print(f"   File: {test_request['filename']}")
    rows_count = len(test_csv_content.split("\n")) - 1
    print(f"   Rows: {rows_count}")

    try:
        # Make the API call
        response = requests.post(
            "http://localhost:8000/api/v1/unified-discovery/analyze-cmdb",
            json=test_request,
            timeout=60,  # 60 second timeout
        )

        print(f"   Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ Analysis completed successfully!")
            print(f"   Status: {result.get('status', 'unknown')}")
            print(
                f"   Data Quality Score: {result.get('dataQuality', {}).get('score', 'N/A')}"
            )
            print(f"   Coverage: {result.get('coverage', {})}")
            print(f"   Missing Fields: {len(result.get('missingFields', []))}")
            print(f"   Ready for Import: {result.get('readyForImport', False)}")

            # Show some details
            if result.get("dataQuality", {}).get("issues"):
                print(f"   Issues Found: {len(result['dataQuality']['issues'])}")
                for issue in result["dataQuality"]["issues"][:3]:  # Show first 3
                    print(f"     - {issue}")

            return True
        else:
            print(f"❌ Analysis failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("❌ Request timed out after 60 seconds")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = test_cmdb_analysis()
    if success:
        print("\n🎉 CMDB Analysis endpoint is working!")
    else:
        print("\n💥 CMDB Analysis endpoint has issues")

    exit(0 if success else 1)
