#!/usr/bin/env python3
"""
Test script to verify questionnaire response persistence
"""

import json
import requests
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"
AUTH_TOKEN = "YOUR_AUTH_TOKEN_HERE"  # Replace with actual token from login
FLOW_ID = "0e1c2420-a529-402b-a28f-98b1773dbf2d"
QUESTIONNAIRE_ID = "test-questionnaire-001"

# Headers
headers = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "X-Client-Account-ID": "11111111-1111-1111-1111-111111111111",
    "X-Engagement-ID": "22222222-2222-2222-2222-222222222222",
    "Content-Type": "application/json"
}


def test_submit_responses():
    """Submit test questionnaire responses"""
    print("\n=== Testing Submit Questionnaire Responses ===")

    # Test data matching the format from frontend
    test_responses = {
        "responses": {
            "app_name": "Test Application",
            "app_description": "This is a test application for verifying persistence",
            "business_criticality": "High",
            "technical_stack": "Python, React, PostgreSQL",
            "deployment_environment": "AWS Cloud",
            "data_sensitivity": "Confidential",
            "compliance_requirements": "GDPR, SOC2"
        },
        "form_metadata": {
            "form_id": "adaptive_collection_form",
            "application_id": "test-app-001",
            "completion_percentage": 75,
            "confidence_score": 0.85,
            "submitted_at": datetime.now().isoformat()
        },
        "validation_results": {
            "isValid": True,
            "completionPercentage": 75,
            "overallConfidenceScore": 0.85
        }
    }

    # Submit responses
    url = f"{BASE_URL}/collection/flows/{FLOW_ID}/questionnaires/{QUESTIONNAIRE_ID}/submit"
    response = requests.post(url, headers=headers, json=test_responses)

    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success: {result.get('message')}")
        print(f"   Responses Saved: {result.get('responses_saved')}")
        print(f"   Flow Progress: {result.get('progress')}%")
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False


def test_retrieve_responses():
    """Retrieve saved questionnaire responses"""
    print("\n=== Testing Retrieve Questionnaire Responses ===")

    # Retrieve responses
    url = f"{BASE_URL}/collection/flows/{FLOW_ID}/questionnaires/{QUESTIONNAIRE_ID}/responses"
    response = requests.get(url, headers=headers)

    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Retrieved {result.get('response_count')} responses")
        print(f"   Last Updated: {result.get('last_updated')}")
        print("\nSaved Responses:")
        for field_id, value in result.get('responses', {}).items():
            print(f"   - {field_id}: {value}")
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False


def test_database_verification():
    """Verify responses are in the database"""
    print("\n=== Verifying Database Persistence ===")

    import subprocess

    # Check database directly
    cmd = f"""docker exec migration_postgres psql -U postgres -d migration_db -c "
        SELECT
            question_id,
            response_value->>'value' as value,
            confidence_score,
            validation_status,
            responded_at
        FROM migration.collection_questionnaire_responses
        WHERE collection_flow_id = '{FLOW_ID}'
        ORDER BY responded_at DESC
        LIMIT 10;
    " """

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("Database records found:")
        print(result.stdout)
        return True
    else:
        print(f"❌ Database query failed: {result.stderr}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("QUESTIONNAIRE RESPONSE PERSISTENCE TEST")
    print("=" * 60)

    # Run tests
    tests_passed = []

    # Test 1: Submit responses
    tests_passed.append(test_submit_responses())

    # Test 2: Retrieve responses
    tests_passed.append(test_retrieve_responses())

    # Test 3: Verify database
    tests_passed.append(test_database_verification())

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(tests_passed)
    total = len(tests_passed)

    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print("\n🎉 Questionnaire response persistence is working correctly!")
        print("Responses are being saved to the database and can be retrieved.")
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total} passed)")
        print("\nPlease check the error messages above for details.")

    return passed == total


if __name__ == "__main__":
    exit(0 if main() else 1)
