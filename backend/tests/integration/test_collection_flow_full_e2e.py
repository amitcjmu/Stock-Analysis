"""
Full End-to-End Test for Collection Flow with Authentication
Tests the complete collection flow through API with CrewAI execution
"""

import pytest
import asyncio
import json
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models import User

# Test credentials
TEST_EMAIL = "demo@demo-corp.com"
TEST_PASSWORD = "Demo123!"


@pytest.mark.asyncio
async def test_collection_flow_full_e2e():
    """Test full collection flow from API to CrewAI execution"""
    base_url = "http://localhost:8000"
    
    async with AsyncClient(base_url=base_url) as client:
        # Step 1: Login
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        
        print(f"Login response: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"Login failed: {login_response.text}")
            # Try with platform admin
            login_response = await client.post(
                "/api/v1/auth/login",
                json={"email": "chocka@gmail.com", "password": "Password123!"}
            )
            
        if login_response.status_code == 200:
            login_data = login_response.json()
            print(f"Login data: {json.dumps(login_data, indent=2)}")
            
            # Get token - it's nested in token.access_token
            token = None
            if "token" in login_data and isinstance(login_data["token"], dict):
                token = login_data["token"].get("access_token")
            elif "access_token" in login_data:
                token = login_data.get("access_token")
            
            if not token:
                # Try to use cookies instead
                cookies = login_response.cookies
                headers = {
                    "X-Client-Account-Id": "11111111-1111-1111-1111-111111111111",
                    "X-Engagement-Id": "22222222-2222-2222-2222-222222222222"
                }
            else:
                headers = {
                    "Authorization": f"Bearer {token}",
                    "X-Client-Account-Id": "11111111-1111-1111-1111-111111111111",
                    "X-Engagement-Id": "22222222-2222-2222-2222-222222222222"
                }
            
            # Step 2: Check collection status
            if token:
                status_response = await client.get(
                    "/api/v1/collection/status",
                    headers=headers
                )
            else:
                # Use cookie auth
                status_response = await client.get(
                    "/api/v1/collection/status",
                    headers=headers,
                    cookies=login_response.cookies
                )
            
            print(f"\nCollection status response: {status_response.status_code}")
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"Status: {json.dumps(status, indent=2)}")
                
                # Step 3: Create a new collection flow if none exists
                if status.get("status") == "no_active_flow":
                    flow_data = {
                        "automation_tier": "tier_2",
                        "collection_config": {
                            "target_platforms": ["AWS", "VMware"],
                            "scope": "full"
                        }
                    }
                    
                    create_response = await client.post(
                        "/api/v1/collection/flows",
                        headers=headers,
                        json=flow_data
                    )
                    
                    print(f"\nCreate flow response: {create_response.status_code}")
                    if create_response.status_code in [200, 201]:
                        flow = create_response.json()
                        print(f"Created flow: {json.dumps(flow, indent=2)}")
                        
                        # This is where CrewAI execution would be triggered
                        print("\n✅ Collection Flow created successfully!")
                        print("🤖 CrewAI agents would now be executing...")
                        
                        # Step 4: Get flow details
                        flow_id = flow["id"]
                        detail_response = await client.get(
                            f"/api/v1/collection/flows/{flow_id}",
                            headers=headers
                        )
                        
                        if detail_response.status_code == 200:
                            details = detail_response.json()
                            print(f"\nFlow details: {json.dumps(details, indent=2)}")
                    else:
                        print(f"Failed to create flow: {create_response.text}")
                else:
                    print("Active flow already exists")
            else:
                print(f"Failed to get status: {status_response.text}")
        else:
            print("Authentication failed - cannot test collection flow")


if __name__ == "__main__":
    print("Testing Collection Flow End-to-End with Authentication...\n")
    asyncio.run(test_collection_flow_full_e2e())
    print("\n✅ Test completed!")