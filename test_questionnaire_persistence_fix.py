#!/usr/bin/env python3
"""
Test script to verify questionnaire persistence is working.
This will create a test flow, add test responses, and verify they are saved.
"""

import asyncio
import json
import os
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
import requests

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5433/migration_db"
)
API_BASE_URL = "http://localhost:8000/api/v1"

# Test user credentials
TEST_USER_EMAIL = "demo@demo-corp.com"
TEST_USER_PASSWORD = "demo-password"

def get_auth_headers():
    """Get authentication headers for API requests."""
    # Login to get token
    login_response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
        }
    )

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return None

    token_data = login_response.json()
    token = token_data.get("access_token")

    return {
        "Authorization": f"Bearer {token}",
        "X-Client-Account-ID": "11111111-1111-1111-1111-111111111111",
        "X-Engagement-ID": "22222222-2222-2222-2222-222222222222",
        "Content-Type": "application/json"
    }

async def check_database_responses():
    """Check if responses exist in the database."""
    engine = create_async_engine(DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        # Check collection_questionnaire_responses table
        result = await conn.execute(
            text("""
                SELECT
                    cqr.id,
                    cqr.collection_flow_id,
                    cqr.questionnaire_type,
                    cqr.question_id,
                    cqr.response_value,
                    cqr.confidence_score,
                    cqr.responded_at,
                    cf.flow_id as flow_uuid
                FROM migration.collection_questionnaire_responses cqr
                JOIN migration.collection_flows cf ON cqr.collection_flow_id = cf.id
                ORDER BY cqr.responded_at DESC
                LIMIT 10
            """)
        )

        rows = result.fetchall()

        if rows:
            print(f"\n✅ Found {len(rows)} saved questionnaire responses in database:")
            for row in rows:
                print(f"  - Question: {row.question_id}")
                print(f"    Response: {row.response_value}")
                print(f"    Flow UUID: {row.flow_uuid}")
                print(f"    Confidence: {row.confidence_score}")
                print(f"    Saved at: {row.responded_at}")
                print()
        else:
            print("\n⚠️ No questionnaire responses found in database")

        # Get count of all responses
        count_result = await conn.execute(
            text("SELECT COUNT(*) FROM migration.collection_questionnaire_responses")
        )
        total_count = count_result.scalar()
        print(f"📊 Total responses in database: {total_count}")

    await engine.dispose()
    return len(rows) if rows else 0

def test_save_questionnaire_response():
    """Test saving questionnaire responses via API."""

    headers = get_auth_headers()
    if not headers:
        return False

    print("\n🔄 Testing questionnaire persistence...")

    # Step 1: Get or create a collection flow
    print("\n1️⃣ Getting collection flow...")
    flow_response = requests.post(
        f"{API_BASE_URL}/collection/flows/ensure",
        headers=headers
    )

    if flow_response.status_code != 200:
        print(f"❌ Failed to get collection flow: {flow_response.text}")
        return False

    flow_data = flow_response.json()
    flow_id = flow_data.get("flow_id") or flow_data.get("id")
    print(f"✅ Using collection flow: {flow_id}")

    # Step 2: Create test questionnaire responses
    test_responses = {
        "responses": {
            "application_name": "Test Application",
            "application_description": "This is a test application for persistence testing",
            "technical_stack": "Python, React, PostgreSQL",
            "data_sensitivity": "High",
            "compliance_requirements": "GDPR, HIPAA",
            "user_count": "1000-5000",
            "deployment_model": "Cloud Native",
            "integration_points": "REST APIs, Message Queues",
        },
        "form_metadata": {
            "form_id": "adaptive_form_test",
            "application_id": "test-app-001",
            "completion_percentage": 75,
            "confidence_score": 85,
            "submitted_at": datetime.utcnow().isoformat(),
        },
        "validation_results": {
            "isValid": True,
            "fieldResults": {
                "application_name": {"valid": True, "confidence": 100},
                "application_description": {"valid": True, "confidence": 90},
                "technical_stack": {"valid": True, "confidence": 85},
            }
        }
    }

    # Step 3: Submit responses to the API
    print("\n2️⃣ Submitting test questionnaire responses...")
    print(f"   Endpoint: /collection/flows/{flow_id}/questionnaires/test-questionnaire-001/responses")

    save_response = requests.post(
        f"{API_BASE_URL}/collection/flows/{flow_id}/questionnaires/test-questionnaire-001/responses",
        headers=headers,
        json=test_responses
    )

    if save_response.status_code == 200:
        print("✅ Questionnaire responses saved successfully!")
        print(f"   Response: {json.dumps(save_response.json(), indent=2)}")
    else:
        print(f"❌ Failed to save responses: {save_response.status_code}")
        print(f"   Error: {save_response.text}")
        return False

    # Step 4: Retrieve saved responses
    print("\n3️⃣ Retrieving saved responses...")
    get_response = requests.get(
        f"{API_BASE_URL}/collection/flows/{flow_id}/questionnaires/test-questionnaire-001/responses",
        headers=headers
    )

    if get_response.status_code == 200:
        saved_data = get_response.json()
        print("✅ Successfully retrieved saved responses:")
        print(f"   Response count: {len(saved_data.get('responses', []))}")
        if saved_data.get('responses'):
            print("   Sample responses:")
            for key, value in list(saved_data['responses'].items())[:3]:
                print(f"     - {key}: {value}")
    else:
        print(f"⚠️ Could not retrieve responses: {get_response.text}")

    return True

async def main():
    """Main test function."""
    print("=" * 60)
    print("🧪 QUESTIONNAIRE PERSISTENCE TEST")
    print("=" * 60)

    # Check initial database state
    print("\n📋 Checking initial database state...")
    initial_count = await check_database_responses()

    # Run API test
    success = test_save_questionnaire_response()

    if success:
        # Wait a moment for database to update
        await asyncio.sleep(2)

        # Check final database state
        print("\n📋 Checking final database state...")
        final_count = await check_database_responses()

        if final_count > initial_count:
            print(f"\n🎉 SUCCESS: Questionnaire persistence is working!")
            print(f"   Added {final_count - initial_count} new responses to database")
        else:
            print(f"\n⚠️ WARNING: API returned success but no new database records found")
            print(f"   This might indicate a database commit issue")
    else:
        print("\n❌ FAILED: Questionnaire persistence test failed")

    print("\n" + "=" * 60)
    print("Test complete!")

if __name__ == "__main__":
    asyncio.run(main())
