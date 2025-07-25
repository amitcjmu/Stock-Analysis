"""
Test script to verify asset inventory multitenancy filtering
"""
import asyncio
import httpx
import json

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_TOKEN = "your-test-token-here"  # Replace with actual token

# Test scenarios
test_cases = [
    {
        "name": "Test with valid context headers",
        "headers": {
            "Authorization": f"Bearer {TEST_TOKEN}",
            "X-Client-Account-ID": "11111111-1111-1111-1111-111111111111",
            "X-Engagement-ID": "22222222-2222-2222-2222-222222222222",
            "X-User-ID": "test-user-id"
        },
        "expected": "Should return only assets for this client/engagement"
    },
    {
        "name": "Test with different client context",
        "headers": {
            "Authorization": f"Bearer {TEST_TOKEN}",
            "X-Client-Account-ID": "99999999-9999-9999-9999-999999999999",
            "X-Engagement-ID": "88888888-8888-8888-8888-888888888888",
            "X-User-ID": "test-user-id"
        },
        "expected": "Should return no assets (different client)"
    },
    {
        "name": "Test without context headers",
        "headers": {
            "Authorization": f"Bearer {TEST_TOKEN}"
        },
        "expected": "Should return empty result for security"
    }
]

async def test_asset_list_endpoint():
    """Test the paginated asset list endpoint with different contexts"""
    async with httpx.AsyncClient() as client:
        for test_case in test_cases:
            print(f"\n{'='*60}")
            print(f"Running: {test_case['name']}")
            print(f"Headers: {json.dumps(test_case['headers'], indent=2)}")
            print(f"Expected: {test_case['expected']}")

            try:
                response = await client.get(
                    f"{BASE_URL}/assets/list/paginated?page=1&page_size=10",
                    headers=test_case['headers']
                )

                print(f"Status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    asset_count = len(data.get('assets', []))
                    total_items = data.get('pagination', {}).get('total_items', 0)

                    print(f"Assets returned: {asset_count}")
                    print(f"Total items: {total_items}")

                    # Show first asset if any
                    if asset_count > 0:
                        first_asset = data['assets'][0]
                        print(f"First asset: {first_asset.get('name')} (ID: {first_asset.get('id')})")
                else:
                    print(f"Error response: {response.text}")

            except Exception as e:
                print(f"Request failed: {e}")

async def test_asset_analysis_endpoint():
    """Test the asset analysis endpoint with different contexts"""
    async with httpx.AsyncClient() as client:
        print(f"\n{'='*60}")
        print("Testing Asset Analysis Endpoint")

        # Test with valid context
        headers = {
            "Authorization": f"Bearer {TEST_TOKEN}",
            "X-Client-Account-ID": "11111111-1111-1111-1111-111111111111",
            "X-Engagement-ID": "22222222-2222-2222-2222-222222222222",
            "X-User-ID": "test-user-id"
        }

        payload = {
            "operation": "general_analysis",
            "include_patterns": True,
            "include_quality_assessment": True
        }

        try:
            response = await client.post(
                f"{BASE_URL}/assets/analyze",
                headers=headers,
                json=payload
            )

            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"Analysis status: {data.get('status')}")
                print(f"Assets analyzed: {data.get('assets_analyzed', 0)}")
            else:
                print(f"Error response: {response.text}")

        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    print("Asset Inventory Multitenancy Test")
    print("=================================")
    print("\nNote: Make sure to update TEST_TOKEN with a valid auth token")
    print("You can get a token by logging in through the UI and checking localStorage")

    # Run tests
    asyncio.run(test_asset_list_endpoint())
    asyncio.run(test_asset_analysis_endpoint())
