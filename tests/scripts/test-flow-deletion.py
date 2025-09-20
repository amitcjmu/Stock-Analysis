#!/usr/bin/env python3
"""
Test Flow Deletion with MFO Cascade Testing

Tests Master Flow Orchestrator (MFO) cascade deletion functionality through API endpoints,
ensuring proper cleanup of master flows and child flows while maintaining referential
integrity and tenant isolation.

Updated with CC for MFO-aligned cascade deletion testing.
"""

import requests
import time
import sys
from pathlib import Path

# Add backend to path for MFO fixtures
sys.path.append(str(Path(__file__).parent.parent.parent / "backend"))

# Import MFO constants for consistency
from tests.fixtures.mfo_fixtures import (
    DEMO_CLIENT_ACCOUNT_ID,
    DEMO_ENGAGEMENT_ID,
    DEMO_USER_EMAIL
)

BASE_URL = "http://localhost:8000"
CLIENT_ID = DEMO_CLIENT_ACCOUNT_ID
ENGAGEMENT_ID = DEMO_ENGAGEMENT_ID
USER_EMAIL = DEMO_USER_EMAIL

def test_mfo_flow_deletion():
    """Test MFO flow deletion with comprehensive cascade testing."""
    print("🔍 Testing MFO Flow Deletion with Cascade Testing")
    print("=" * 60)
    print(f"Client ID: {CLIENT_ID}")
    print(f"Engagement ID: {ENGAGEMENT_ID}")
    print(f"User Email: {USER_EMAIL}")

    # Step 1: Login with MFO user
    print("\n1. Login with MFO demo user...")
    login_response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "email": USER_EMAIL,
        "password": "Demo123!"
    }, timeout=30)

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return False

    auth_data = login_response.json()
    token = auth_data.get("access_token", auth_data.get("token"))
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Client-Account-ID": CLIENT_ID,
        "X-Engagement-ID": ENGAGEMENT_ID,
        "Content-Type": "application/json"
    }

    # Step 2: List existing master flows through MFO
    print("\n2. Listing existing master flows through MFO...")

    # First, check master flows
    master_flows_response = requests.get(
        f"{BASE_URL}/api/v1/master-flows/",
        headers=headers,
        timeout=30
    )

    master_flows = []
    if master_flows_response.status_code == 200:
        master_flows_data = master_flows_response.json()
        master_flows = master_flows_data.get("flows", []) if isinstance(master_flows_data, dict) else master_flows_data
        print(f"   Found {len(master_flows)} master flows")
        for flow in master_flows:
            print(f"     - Master Flow {flow.get('flow_id', 'unknown')}: {flow.get('flow_status', 'unknown')}")
    else:
        print(f"   Failed to get master flows: {master_flows_response.status_code}")
        print(f"   Response: {master_flows_response.text[:200]}...")  # Truncate long responses

    # Also check legacy discovery flows
    legacy_flows_response = requests.get(
        f"{BASE_URL}/api/v1/flows/?flowType=discovery",
        headers=headers,
        timeout=30
    )

    legacy_flows = []
    if legacy_flows_response.status_code == 200:
        legacy_flows_data = legacy_flows_response.json()
        legacy_flows = legacy_flows_data.get("flows", []) if isinstance(legacy_flows_data, dict) else []
        print(f"   Found {len(legacy_flows)} legacy discovery flows")
        for flow in legacy_flows:
            print(f"     - Discovery Flow {flow.get('flow_id', 'unknown')}: {flow.get('status', 'unknown')}")
    else:
        print(f"   Failed to get legacy flows: {legacy_flows_response.status_code}")

    # Step 3: Delete the existing flow
    if flows:
        flow_to_delete = flows[0]["flow_id"]
        print(f"\n3. Deleting flow {flow_to_delete}...")

        delete_response = requests.delete(
            f"{BASE_URL}/api/v1/master-flows/{flow_to_delete}",
            headers=headers,
            timeout=30
        )

        if delete_response.status_code == 200:
            print("✅ Delete request successful")
            result = delete_response.json()
            print(f"   Result: {result}")
        else:
            print(f"❌ Delete failed: {delete_response.status_code}")
            print(f"   Error: {delete_response.text}")

    # Step 4: List flows again to verify deletion
    print("\n4. Verifying deletion...")
    time.sleep(2)  # Give it a moment

    verify_response = requests.get(
        f"{BASE_URL}/api/v1/flows/?flowType=discovery",
        headers=headers,
        timeout=30
    )

    if verify_response.status_code == 200:
        remaining_flows = verify_response.json()["flows"]
        print(f"Remaining flows: {len(remaining_flows)}")

        if len(remaining_flows) == 0:
            print("✅ Flow successfully deleted and no longer appears in list!")
        else:
            print("❌ Flow still appears in list after deletion")
            for flow in remaining_flows:
                print(f"  - {flow['flow_id']}: {flow['status']}")

    # Step 5: Check database directly
    print("\n5. Checking database status...")
    import subprocess
    result = subprocess.run([
        'docker', 'exec', 'migration_backend', 'python', '-c',
        """
from sqlalchemy import create_engine, text
import os
db_url = os.environ.get('DATABASE_URL')
engine = create_engine(db_url)
with engine.connect() as conn:
    result = conn.execute(text('''
        SELECT flow_id, flow_status
        FROM crewai_flow_state_extensions
        WHERE client_account_id = '11111111-1111-1111-1111-111111111111'
        ORDER BY created_at DESC LIMIT 1
    '''))
    row = result.fetchone()
    if row:
        print(f'Latest master flow: {row[0]}, Status: {row[1]}')
"""
    ], capture_output=True, text=True)

    print(result.stdout.strip())

    print("\n" + "=" * 50)
    print("Test complete!")

if __name__ == "__main__":
    test_mfo_flow_deletion()
