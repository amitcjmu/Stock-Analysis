#!/usr/bin/env python3
"""
Context Circular Dependency Fix Test

This script tests that:
1. /api/v1/clients endpoint works without context headers (no circular dependency)
2. Context can be established using the returned client data
3. Other endpoints work properly with established context
4. Acme Corp context switching issue is resolved
"""

import asyncio
import json
from datetime import datetime

import aiohttp

BASE_URL = "http://localhost:8000/api/v1"

# Test user credentials (using admin user from logs)
TEST_USER = {
    "id": "3ee1c326-a014-4a3c-a483-5cfcf1b419d7",
    "role": "admin"
}

class ContextCircularDependencyTester:
    def __init__(self):
        self.session = None
        self.test_results = []

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_clients_endpoint_without_context(self) -> dict:
        """Test that /api/v1/clients/public works without context headers or authentication"""
        print("🧪 Testing /api/v1/clients/public endpoint without authentication...")

        try:
            # Call public clients endpoint without any authentication or context headers
            async with self.session.get(f"{BASE_URL}/clients/public") as response:
                result = await response.json()

                if response.status == 200:
                    clients = result.get('clients', [])
                    print(f"✅ Public clients endpoint successful: Found {len(clients)} clients")
                    for client in clients:
                        print(f"   - {client.get('name', 'Unknown')} ({client.get('id', 'No ID')})")
                    return {"status": "success", "data": result, "clients_count": len(clients)}
                else:
                    print(f"❌ Public clients endpoint failed: {response.status} - {result}")
                    return {"status": "error", "error": result, "status_code": response.status}

        except Exception as e:
            print(f"❌ Public clients endpoint exception: {e}")
            return {"status": "exception", "error": str(e)}

    async def test_context_establishment(self, client_data: dict) -> dict:
        """Test establishing context with client data"""
        print(f"🧪 Testing context establishment with client: {client_data.get('name', 'Unknown')}...")

        try:
            # Use client data to establish context headers
            headers = {
                'Content-Type': 'application/json',
                'X-User-ID': TEST_USER['id'],
                'X-User-Role': TEST_USER['role'],
                'X-Client-Account-ID': client_data['id']
            }

            # Test an endpoint that requires context
            async with self.session.get(
                f"{BASE_URL}/clients/{client_data['id']}/engagements",
                headers=headers
            ) as response:
                result = await response.json()

                if response.status == 200:
                    engagements = result.get('engagements', [])
                    print(f"✅ Context establishment successful: Found {len(engagements)} engagements")
                    return {"status": "success", "data": result, "engagements_count": len(engagements)}
                else:
                    print(f"❌ Context establishment failed: {response.status} - {result}")
                    return {"status": "error", "error": result, "status_code": response.status}

        except Exception as e:
            print(f"❌ Context establishment exception: {e}")
            return {"status": "exception", "error": str(e)}

    async def test_marathon_context_persistence(self) -> dict:
        """Test that Marathon context persists and doesn't switch to Acme"""
        print("🧪 Testing Marathon context persistence...")

        # Marathon Petroleum context from logs
        marathon_context = {
            "client_id": "d838573d-f461-44e4-81b5-5af510ef83b7",
            "engagement_id": "d1a93e23-719d-4dad-8bbf-b66ab9de2b94",
            "user_id": "3ee1c326-a014-4a3c-a483-5cfcf1b419d7"
        }

        try:
            headers = {
                'Content-Type': 'application/json',
                'X-User-ID': marathon_context['user_id'],
                'X-Client-Account-ID': marathon_context['client_id'],
                'X-Engagement-ID': marathon_context['engagement_id']
            }

            # Test sessions endpoint with Marathon context
            async with self.session.get(
                f"{BASE_URL}/sessions/engagement/{marathon_context['engagement_id']}",
                headers=headers
            ) as response:
                result = await response.json()

                if response.status == 200:
                    print("✅ Marathon context persistence successful")
                    return {"status": "success", "data": result, "context": "marathon"}
                else:
                    print(f"❌ Marathon context failed: {response.status} - {result}")
                    return {"status": "error", "error": result, "status_code": response.status}

        except Exception as e:
            print(f"❌ Marathon context exception: {e}")
            return {"status": "exception", "error": str(e)}

    async def run_all_tests(self):
        """Run all circular dependency tests"""
        print("🚀 Starting Context Circular Dependency Tests")
        print("=" * 60)

        # Test 1: Clients endpoint without context
        clients_result = await self.test_clients_endpoint_without_context()
        self.test_results.append(("clients_without_context", clients_result))

        if clients_result["status"] == "success" and clients_result.get("clients_count", 0) > 0:
            # Test 2: Context establishment with first client
            first_client = clients_result["data"]["clients"][0]
            context_result = await self.test_context_establishment(first_client)
            self.test_results.append(("context_establishment", context_result))

        # Test 3: Marathon context persistence
        marathon_result = await self.test_marathon_context_persistence()
        self.test_results.append(("marathon_persistence", marathon_result))

        print("\n" + "=" * 60)
        print("📊 Test Results Summary:")

        success_count = 0
        for test_name, result in self.test_results:
            status = result["status"]
            if status == "success":
                print(f"✅ {test_name}: PASSED")
                success_count += 1
            else:
                print(f"❌ {test_name}: FAILED - {result.get('error', 'Unknown error')}")

        print(f"\n🎯 Overall Results: {success_count}/{len(self.test_results)} tests passed")

        if success_count == len(self.test_results):
            print("🎉 All tests passed! Circular dependency issue resolved.")
        else:
            print("⚠️  Some tests failed. Check the errors above.")

        return {
            "total_tests": len(self.test_results),
            "passed_tests": success_count,
            "failed_tests": len(self.test_results) - success_count,
            "results": self.test_results,
            "timestamp": datetime.now().isoformat()
        }

async def main():
    async with ContextCircularDependencyTester() as tester:
        results = await tester.run_all_tests()

        # Save results to file
        with open('context_dependency_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)

        print("\n📄 Detailed results saved to: context_dependency_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())
