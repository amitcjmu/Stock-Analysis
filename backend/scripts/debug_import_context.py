import requests


def test_import_context():
    """Test what context is captured during import API calls."""

    # Test Marathon context headers (what user is sending)
    marathon_headers = {
        "X-Client-Account-ID": "73dee5f1-6a01-43e3-b1b8-dbe6c66f2990",
        "X-Engagement-ID": "baf640df-433c-4bcd-8c8f-7b01c12e9005",
        "X-User-ID": "3ee1c326-a014-4a3c-a483-5cfcf1b419d7",
        "Content-Type": "application/json",
    }

    # Test demo context headers (working case)
    demo_headers = {
        "X-Client-Account-ID": "bafd5b46-aaaf-4c95-8142-573699d93171",
        "X-Engagement-ID": "6e9c8133-4169-4b79-b052-106dc93d0208",
        "X-User-ID": "44444444-4444-4444-4444-444444444444",
        "Content-Type": "application/json",
    }

    # Simple test payload for data import
    test_payload = {
        "filename": "test_context.csv",
        "upload_type": "csv_upload",
        "headers": ["Asset_ID", "Asset_Name", "Asset_Type"],
        "sample_data": [
            {
                "Asset_ID": "test-001",
                "Asset_Name": "Test Server",
                "Asset_Type": "Server",
            }
        ],
    }

    print("🔍 Testing Marathon Petroleum Context:")
    print(f"   Client: {marathon_headers['X-Client-Account-ID']}")
    print(f"   Engagement: {marathon_headers['X-Engagement-ID']}")

    try:
        # Test Marathon context - this should store data under Marathon client
        response = requests.post(
            "http://localhost:8000/api/v1/data-import/data-imports",
            headers=marathon_headers,
            json=test_payload,
            timeout=10,
        )

        print(f"Marathon Response Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Session ID: {data.get('session_id')}")
            print(f"Client ID returned: {data.get('client_account_id')}")
            print(f"Engagement ID returned: {data.get('engagement_id')}")

            # Now check if we can see this import in Marathon context
            check_response = requests.get(
                "http://localhost:8000/api/v1/data-import/critical-attributes-status",
                headers=marathon_headers,
                timeout=30,
            )
            check_data = check_response.json()
            print(
                f"Attributes visible in Marathon context: {check_data.get('statistics', {}).get('total_attributes', 0)}"
            )
        else:
            print(f"Error: {response.text}")

    except Exception as e:
        print(f"Error testing Marathon context: {e}")

    print("\n" + "=" * 60 + "\n")

    print("🔍 Testing Demo Context (for comparison):")
    print(f"   Client: {demo_headers['X-Client-Account-ID']}")
    print(f"   Engagement: {demo_headers['X-Engagement-ID']}")

    try:
        # Check demo context
        demo_check_response = requests.get(
            "http://localhost:8000/api/v1/data-import/critical-attributes-status",
            headers=demo_headers,
            timeout=30,
        )
        demo_check_data = demo_check_response.json()
        print(
            f"Attributes visible in Demo context: {demo_check_data.get('statistics', {}).get('total_attributes', 0)}"
        )

    except Exception as e:
        print(f"Error testing Demo context: {e}")


if __name__ == "__main__":
    test_import_context()
