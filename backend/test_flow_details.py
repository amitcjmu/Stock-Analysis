"""Check collection flow details"""
import asyncio
import json

import httpx


async def check_flow_details():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Login
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "demo@demo-corp.com", "password": "Demo123!"}
        )
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            token = login_data["token"]["access_token"]
            
            headers = {
                "Authorization": f"Bearer {token}",
                "X-Client-Account-Id": "11111111-1111-1111-1111-111111111111",
                "X-Engagement-Id": "22222222-2222-2222-2222-222222222222"
            }
            
            # Get flow status
            status_response = await client.get(
                "/api/v1/collection/status",
                headers=headers
            )
            
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"Flow status: {json.dumps(status, indent=2)}")
                
                if "flow_id" in status:
                    # Get detailed flow info
                    flow_id = status["flow_id"]
                    detail_response = await client.get(
                        f"/api/v1/collection/flows/{flow_id}",
                        headers=headers
                    )
                    
                    if detail_response.status_code == 200:
                        details = detail_response.json()
                        print(f"\nFlow details: {json.dumps(details, indent=2)}")
                    else:
                        print(f"Failed to get flow details: {detail_response.text}")

if __name__ == "__main__":
    asyncio.run(check_flow_details())