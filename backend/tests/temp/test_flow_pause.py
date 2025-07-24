#!/usr/bin/env python3
"""
Test script to verify flow pause functionality
"""

import asyncio
import json
from datetime import datetime

import httpx

# Test configuration
BASE_URL = "http://localhost:8000"
HEADERS = {
    "X-Client-Account-ID": "21990f3a-abb6-4862-be06-cb6f854e167b",
    "X-Engagement-ID": "58467010-6a72-44e8-ba37-cc0238724455",
    "X-User-ID": "77b30e13-c331-40eb-a0ec-ed0717f72b22",
    "Authorization": "Bearer db-token-77b30e13-c331-40eb-a0ec-ed0717f72b22-87de7c6c",
    "Content-Type": "application/json",
}


async def test_flow_pause():
    """Test that flow properly pauses and updates status"""
    async with httpx.AsyncClient() as client:
        # Step 1: Upload test data
        print("1. Uploading test data...")
        test_data = {
            "file_data": [
                {
                    "row_index": 1,
                    "Name": "Test_App",
                    "CI Type": "Application",
                    "CI ID": "APP001",
                }
            ],
            "metadata": {"filename": "test.csv", "size": 100, "type": "text/csv"},
            "upload_context": {
                "intended_type": "app-discovery",
                "validation_upload_id": f"test-{datetime.now().isoformat()}",
                "upload_timestamp": datetime.now().isoformat(),
            },
            "client_id": "21990f3a-abb6-4862-be06-cb6f854e167b",
            "engagement_id": "58467010-6a72-44e8-ba37-cc0238724455",
        }

        resp = await client.post(
            f"{BASE_URL}/api/v1/data-import/store-import",
            headers=HEADERS,
            json=test_data,
        )

        if resp.status_code != 200:
            print(f"Error uploading: {resp.status_code} - {resp.text}")
            return

        result = resp.json()
        flow_id = result.get("flow_id")
        print(f"✅ Flow created: {flow_id}")

        # Step 2: Wait for flow to pause (up to 30 seconds)
        print("\n2. Waiting for flow to pause...")
        for i in range(30):
            await asyncio.sleep(1)

            status_resp = await client.get(
                f"{BASE_URL}/api/v1/discovery/flow/status/{flow_id}", headers=HEADERS
            )

            if status_resp.status_code == 200:
                status_data = status_resp.json()
                current_status = status_data.get("status")
                awaiting_approval = status_data.get("awaiting_user_approval", False)
                progress = status_data.get("progress_percentage", 0)

                print(
                    f"  [{i+1}s] Status: {current_status}, Progress: {progress}%, Awaiting: {awaiting_approval}"
                )

                if current_status == "waiting_for_approval" or awaiting_approval:
                    print("\n✅ Flow successfully paused for approval!")
                    print(f"   Full status: {json.dumps(status_data, indent=2)}")
                    return

        print("\n❌ Flow did not pause within 30 seconds")
        print(f"   Final status: {json.dumps(status_data, indent=2)}")


if __name__ == "__main__":
    asyncio.run(test_flow_pause())
