#!/usr/bin/env python3
"""
Test script for Issue #999 Recovery Endpoint
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

import httpx

async def test_recovery():
    """Test the manual recovery endpoint"""

    # Login first to get token
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Login
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "demo@demo-corp.com",
                "password": "Demo123!"
            }
        )

        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(login_response.text)
            return

        token_data = login_response.json()
        access_token = token_data.get("access_token")
        print(f"✅ Login successful, got token")

        # Call recovery endpoint
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        flow_id = "8bdaa388-75a7-4059-81f6-d29af2037538"

        print(f"\n🚀 Testing recovery endpoint for flow {flow_id}...")
        recovery_response = await client.post(
            f"/api/v1/assessment-flow/{flow_id}/recover",
            headers=headers
        )

        print(f"\n📊 Status Code: {recovery_response.status_code}")
        print(f"📄 Response:")
        print(recovery_response.json())

        if recovery_response.status_code == 200:
            print("\n✅ Recovery endpoint called successfully!")
            print("\n⏳ Waiting 60 seconds for background task to complete...")
            await asyncio.sleep(60)

            # Check database to verify recovery worked
            print("\n🔍 Check database with:")
            print(f'docker exec migration_postgres psql -U postgres -d migration_db -c "')
            print(f'SELECT current_phase, progress, ')
            print(f'CASE WHEN phase_results IS NULL OR phase_results::text = \\'{{}}\\' THEN \\'EMPTY\\' ELSE \\'POPULATED\\' END as results ')
            print(f'FROM migration.assessment_flows WHERE id = \\'{flow_id}\\';')
            print(f'"')
        else:
            print(f"\n❌ Recovery failed: {recovery_response.status_code}")

if __name__ == "__main__":
    asyncio.run(test_recovery())
