#!/usr/bin/env python3
"""
Test script for admin operations with cascade deletion handling.
Tests client and engagement CRUD operations to ensure foreign key constraints are handled properly.
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_HEADERS = {
    "Content-Type": "application/json",
    "X-Client-Account-Id": "d838573d-f461-44e4-81b5-5af510ef83b7",
    "X-Engagement-Id": "d1a93e23-719d-4dad-8bbf-b66ab9de2b94",
    "X-User-Id": "3ee1c326-a014-4a3c-a483-5cfcf1b419d7",
    "X-Session-Id": "d1a93e23-719d-4dad-8bbf-b66ab9de2b94",
    "Authorization": "Bearer db-token-3ee1c326-a014-4a3c-a483-5cfcf1b419d7-461ee317"
}

class AdminOperationsTester:
    def __init__(self):
        self.session = None
        self.results = {
            "client_operations": {},
            "engagement_operations": {},
            "user_operations": {},
            "errors": []
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_client_creation(self) -> Dict[str, Any]:
        """Test client creation with full data payload."""
        print("🧪 Testing client creation...")
        
        client_data = {
            "account_name": "Test Admin Client",
            "industry": "Technology",
            "company_size": "Large (1001-5000)",
            "headquarters_location": "Seattle, WA",
            "primary_contact_name": "Admin Test User",
            "primary_contact_email": "admin.test@company.com",
            "primary_contact_phone": "+1 (555) 123-4567",
            "billing_contact_email": "billing@company.com",
            "description": "Test client created by admin operations test script",
            "subscription_tier": "enterprise",
            "business_objectives": ["Cloud Migration", "Cost Optimization"],
            "target_cloud_providers": ["aws", "azure"],
            "compliance_requirements": ["SOC2", "HIPAA"]
        }
        
        try:
            async with self.session.post(
                f"{BASE_URL}/admin/clients/",
                headers=TEST_HEADERS,
                json=client_data
            ) as response:
                result = await response.json()
                
                if response.status == 201:
                    print(f"✅ Client creation successful: {result.get('data', {}).get('account_name', 'Unknown')}")
                    return {"status": "success", "data": result, "client_id": result.get('data', {}).get('id')}
                else:
                    print(f"❌ Client creation failed: {response.status} - {result}")
                    return {"status": "error", "error": result, "status_code": response.status}
                    
        except Exception as e:
            print(f"❌ Client creation exception: {e}")
            return {"status": "exception", "error": str(e)}

    async def test_engagement_creation(self, client_id: str) -> Dict[str, Any]:
        """Test engagement creation."""
        print("🧪 Testing engagement creation...")
        
        engagement_data = {
            "engagement_name": "Test Admin Engagement",
            "client_account_id": client_id,
            "engagement_description": "Test engagement for admin operations testing",
            "migration_scope": "Full Cloud Migration",
            "target_cloud_provider": "aws",
            "planned_start_date": "2025-07-01",
            "planned_end_date": "2025-12-31",
            "engagement_manager": "Test Manager",
            "technical_lead": "Test Lead",
            "estimated_budget": 500000,
            "estimated_asset_count": 100
        }
        
        try:
            async with self.session.post(
                f"{BASE_URL}/admin/engagements/",
                headers=TEST_HEADERS,
                json=engagement_data
            ) as response:
                result = await response.json()
                
                if response.status == 201:
                    print(f"✅ Engagement creation successful: {result.get('engagement_name', 'Unknown')}")
                    return {"status": "success", "data": result, "engagement_id": result.get('id')}
                else:
                    print(f"❌ Engagement creation failed: {response.status} - {result}")
                    return {"status": "error", "error": result, "status_code": response.status}
                    
        except Exception as e:
            print(f"❌ Engagement creation exception: {e}")
            return {"status": "exception", "error": str(e)}

    async def test_user_creation(self) -> Dict[str, Any]:
        """Test user creation."""
        print("🧪 Testing user creation...")
        
        user_data = {
            "email": "admin.test.user@company.com",
            "password": "TestPassword123!",
            "full_name": "Admin Test User",
            "username": "admin.test.user",
            "organization": "Test Organization",
            "role_description": "Test Admin User",
            "phone_number": "+1-555-0199",
            "manager_email": "manager@company.com",
            "access_level": "read_write",
            "role_name": "Test Analyst",
            "notes": "Created by admin operations test script",
            "is_active": True
        }
        
        try:
            async with self.session.post(
                f"{BASE_URL}/auth/admin/create-user",
                headers=TEST_HEADERS,
                json=user_data
            ) as response:
                result = await response.json()
                
                if response.status == 200:
                    print(f"✅ User creation successful: {user_data['email']}")
                    return {"status": "success", "data": result, "user_id": result.get('user_profile_id')}
                else:
                    print(f"❌ User creation failed: {response.status} - {result}")
                    return {"status": "error", "error": result, "status_code": response.status}
                    
        except Exception as e:
            print(f"❌ User creation exception: {e}")
            return {"status": "exception", "error": str(e)}

    async def test_engagement_deletion(self, engagement_id: str) -> Dict[str, Any]:
        """Test engagement deletion with cascade handling."""
        print("🧪 Testing engagement deletion...")
        
        try:
            async with self.session.delete(
                f"{BASE_URL}/admin/engagements/{engagement_id}",
                headers=TEST_HEADERS
            ) as response:
                result = await response.json()
                
                if response.status == 200:
                    print(f"✅ Engagement deletion successful: {result.get('message', 'Unknown')}")
                    return {"status": "success", "data": result}
                else:
                    print(f"❌ Engagement deletion failed: {response.status} - {result}")
                    return {"status": "error", "error": result, "status_code": response.status}
                    
        except Exception as e:
            print(f"❌ Engagement deletion exception: {e}")
            return {"status": "exception", "error": str(e)}

    async def test_client_deletion(self, client_id: str) -> Dict[str, Any]:
        """Test client deletion with cascade handling."""
        print("🧪 Testing client deletion...")
        
        try:
            async with self.session.delete(
                f"{BASE_URL}/admin/clients/{client_id}",
                headers=TEST_HEADERS
            ) as response:
                result = await response.json()
                
                if response.status == 200:
                    print(f"✅ Client deletion successful: {result.get('message', 'Unknown')}")
                    return {"status": "success", "data": result}
                else:
                    print(f"❌ Client deletion failed: {response.status} - {result}")
                    return {"status": "error", "error": result, "status_code": response.status}
                    
        except Exception as e:
            print(f"❌ Client deletion exception: {e}")
            return {"status": "exception", "error": str(e)}

    async def run_full_test_suite(self):
        """Run the complete admin operations test suite."""
        print("🚀 Starting Admin Operations Test Suite...")
        print("=" * 60)
        
        # Test 1: Client Creation
        client_result = await self.test_client_creation()
        self.results["client_operations"]["creation"] = client_result
        
        if client_result["status"] != "success":
            print("❌ Client creation failed, skipping dependent tests")
            return self.results
        
        client_id = client_result.get("client_id")
        if not client_id:
            print("❌ No client ID returned, skipping dependent tests")
            return self.results
        
        # Test 2: Engagement Creation
        engagement_result = await self.test_engagement_creation(client_id)
        self.results["engagement_operations"]["creation"] = engagement_result
        
        # Test 3: User Creation (independent of client/engagement)
        user_result = await self.test_user_creation()
        self.results["user_operations"]["creation"] = user_result
        
        # Test 4: Engagement Deletion (test cascade handling)
        if engagement_result["status"] == "success":
            engagement_id = engagement_result.get("engagement_id")
            if engagement_id:
                engagement_deletion_result = await self.test_engagement_deletion(engagement_id)
                self.results["engagement_operations"]["deletion"] = engagement_deletion_result
        
        # Test 5: Client Deletion (test cascade handling)
        client_deletion_result = await self.test_client_deletion(client_id)
        self.results["client_operations"]["deletion"] = client_deletion_result
        
        return self.results

    def print_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 60)
        print("📊 ADMIN OPERATIONS TEST SUMMARY")
        print("=" * 60)
        
        total_tests = 0
        passed_tests = 0
        
        for category, operations in self.results.items():
            if category == "errors":
                continue
                
            print(f"\n🔧 {category.replace('_', ' ').title()}:")
            for operation, result in operations.items():
                total_tests += 1
                status = result.get("status", "unknown")
                if status == "success":
                    passed_tests += 1
                    print(f"  ✅ {operation.title()}: SUCCESS")
                else:
                    print(f"  ❌ {operation.title()}: FAILED ({status})")
                    if "error" in result:
                        print(f"     Error: {result['error']}")
        
        print(f"\n📈 Overall Results: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All admin operations are working correctly!")
        else:
            print("⚠️  Some admin operations need attention.")
        
        return passed_tests == total_tests

async def main():
    """Main test execution function."""
    print("🧪 AI Force Migration Platform - Admin Operations Test")
    print("Testing cascade deletion and CRUD operations...")
    
    async with AdminOperationsTester() as tester:
        results = await tester.run_full_test_suite()
        success = tester.print_summary()
        
        # Save detailed results
        with open("admin_operations_test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: admin_operations_test_results.json")
        
        return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 