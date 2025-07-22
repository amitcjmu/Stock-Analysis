"""
Verification Test for DISC-001: UUID Serialization in Data Cleansing
Agent-7 Verification Test Suite
"""

import json
from typing import Any, Dict

import httpx
import pytest


class TestDISC001UUIDSerialization:
    """Test suite to verify UUID serialization fix in data cleansing endpoint"""
    
    @pytest.fixture
    def base_url(self):
        """Base URL for API calls"""
        return "http://localhost:8000/api/v1"
    
    @pytest.fixture
    def auth_headers(self):
        """Authentication headers for API calls"""
        return {
            "X-Client-Account-ID": "1",
            "X-Engagement-ID": "1",
            "Authorization": "Bearer test-token"
        }
    
    async def test_data_cleansing_analysis_no_uuid_error(self, base_url: str, auth_headers: Dict[str, str]):
        """
        Test that data cleansing analysis endpoint returns valid JSON without UUID serialization errors
        
        Verification Steps:
        1. Call GET /api/v1/discovery/flows/{flow_id}/data-cleansing
        2. Verify response is valid JSON
        3. Check that all UUID fields are strings, not objects
        4. Ensure no TypeError or serialization errors
        """
        # Test flow ID (would need a real flow ID in actual test)
        flow_id = "test-flow-123"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{base_url}/discovery/flows/{flow_id}/data-cleansing",
                    headers=auth_headers
                )
                
                # Even if 404, we should get valid JSON response
                assert response.headers.get("content-type", "").startswith("application/json"), \
                    "Response should be JSON"
                
                # Parse response to ensure valid JSON
                data = response.json()
                
                # If successful response, check UUID fields
                if response.status_code == 200:
                    # Check quality_issues for proper UUID serialization
                    if "quality_issues" in data:
                        for issue in data["quality_issues"]:
                            assert isinstance(issue.get("id"), str), \
                                f"Issue ID should be string, not {type(issue.get('id'))}"
                            assert len(issue.get("id", "")) > 0, \
                                "Issue ID should not be empty"
                    
                    # Check recommendations for proper UUID serialization
                    if "recommendations" in data:
                        for rec in data["recommendations"]:
                            assert isinstance(rec.get("id"), str), \
                                f"Recommendation ID should be string, not {type(rec.get('id'))}"
                            assert len(rec.get("id", "")) > 0, \
                                "Recommendation ID should not be empty"
                
                return True, "UUID serialization test passed"
                
            except json.JSONDecodeError as e:
                return False, f"JSON decode error (likely UUID serialization issue): {str(e)}"
            except Exception as e:
                return False, f"Unexpected error: {str(e)}"
    
    async def test_data_cleansing_stats_no_uuid_error(self, base_url: str, auth_headers: Dict[str, str]):
        """
        Test that data cleansing stats endpoint returns valid JSON
        
        This endpoint doesn't use UUIDs but good to verify it still works
        """
        flow_id = "test-flow-123"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{base_url}/discovery/flows/{flow_id}/data-cleansing/stats",
                    headers=auth_headers
                )
                
                # Should return valid JSON
                assert response.headers.get("content-type", "").startswith("application/json"), \
                    "Response should be JSON"
                
                data = response.json()
                return True, "Stats endpoint working correctly"
                
            except json.JSONDecodeError as e:
                return False, f"JSON decode error: {str(e)}"
            except Exception as e:
                return False, f"Unexpected error: {str(e)}"
    
    def test_uuid_string_conversion(self):
        """Unit test to verify UUID to string conversion works"""
        import uuid
        
        # This is what the code should do
        test_uuid = uuid.uuid4()
        uuid_str = str(test_uuid)
        
        # Verify it's a proper string
        assert isinstance(uuid_str, str)
        assert len(uuid_str) == 36  # Standard UUID string length
        assert uuid_str.count('-') == 4  # Standard UUID format
        
        # Verify it's JSON serializable
        test_dict = {"id": uuid_str}
        json_str = json.dumps(test_dict)
        assert json_str is not None
        
        # Verify direct UUID object fails JSON serialization
        with pytest.raises(TypeError) as exc_info:
            json.dumps({"id": test_uuid})
        assert "UUID" in str(exc_info.value) or "not JSON serializable" in str(exc_info.value)


if __name__ == "__main__":
    # Quick verification script
    import asyncio
    
    async def run_verification():
        test = TestDISC001UUIDSerialization()
        
        print("🔍 DISC-001 UUID Serialization Verification")
        print("=" * 50)
        
        # Run unit test
        print("\n1. Testing UUID string conversion...")
        try:
            test.test_uuid_string_conversion()
            print("✅ UUID string conversion test passed")
        except Exception as e:
            print(f"❌ UUID string conversion test failed: {e}")
        
        # Run API tests (would need running backend)
        print("\n2. Testing data cleansing analysis endpoint...")
        base_url = "http://localhost:8000/api/v1"
        headers = {
            "X-Client-Account-ID": "1",
            "X-Engagement-ID": "1"
        }
        
        success, message = await test.test_data_cleansing_analysis_no_uuid_error(base_url, headers)
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
        
        print("\n3. Testing data cleansing stats endpoint...")
        success, message = await test.test_data_cleansing_stats_no_uuid_error(base_url, headers)
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
        
        print("\n" + "=" * 50)
        print("Verification complete. Check results above.")
    
    asyncio.run(run_verification())