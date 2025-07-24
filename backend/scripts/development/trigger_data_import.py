#!/usr/bin/env python3
"""
Trigger Data Import Phase Execution
Script to manually trigger data import phase execution for stuck flows
"""

import json
import sys

import requests


def trigger_data_import_execution(flow_id: str):
    """Trigger data import phase execution for a specific flow"""

    # API endpoint
    base_url = "http://localhost:8000"
    execute_url = f"{base_url}/api/v1/discovery/flow/execute"

    # Headers with demo context
    headers = {
        "Content-Type": "application/json",
        "X-Client-Account-ID": "11111111-1111-1111-1111-111111111111",
        "X-Engagement-ID": "22222222-2222-2222-2222-222222222222",
        "X-User-ID": "347d1ecd-04f6-4e3a-86ca-d35703512301",
        "X-Session-ID": "22222222-2222-2222-2222-222222222222",
        "Authorization": "Bearer db-token-347d1ecd-04f6-4e3a-86ca-d35703512301-cd0e7687",
    }

    # Request payload
    payload = {
        "phase": "data_import",
        "data": {"flow_id": flow_id, "force_execution": True, "use_fallback": True},
        "execution_mode": "hybrid",
    }

    print(f"🚀 Triggering data import execution for flow: {flow_id}")
    print(f"📡 Endpoint: {execute_url}")
    print(f"📋 Payload: {json.dumps(payload, indent=2)}")

    try:
        # Make the API call
        response = requests.post(execute_url, headers=headers, json=payload)

        print(f"📊 Response Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ Success! Data import execution triggered:")
            print(f"   Status: {result.get('status')}")
            print(f"   Phase: {result.get('phase')}")
            print(f"   CrewAI Execution: {result.get('crewai_execution')}")
            print(f"   Database Execution: {result.get('database_execution')}")

            if result.get("agent_insights"):
                print(
                    f"   Agent Insights: {len(result['agent_insights'])} insights generated"
                )

            return True
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error triggering execution: {e}")
        return False


def check_flow_status(flow_id: str):
    """Check the current status of a flow"""

    base_url = "http://localhost:8000"
    status_url = f"{base_url}/api/v1/discovery/flow/status/{flow_id}"

    headers = {
        "Content-Type": "application/json",
        "X-Client-Account-ID": "11111111-1111-1111-1111-111111111111",
        "X-Engagement-ID": "22222222-2222-2222-2222-222222222222",
        "X-User-ID": "347d1ecd-04f6-4e3a-86ca-d35703512301",
        "X-Session-ID": "22222222-2222-2222-2222-222222222222",
        "Authorization": "Bearer db-token-347d1ecd-04f6-4e3a-86ca-d35703512301-cd0e7687",
    }

    print(f"🔍 Checking flow status: {flow_id}")

    try:
        response = requests.get(status_url, headers=headers)

        if response.status_code == 200:
            status = response.json()
            print("📊 Flow Status:")
            print(f"   Progress: {status.get('progress_percentage')}%")
            print(f"   Current Phase: {status.get('current_phase')}")
            print(f"   Status: {status.get('status')}")
            print(
                f"   Data Import Completed: {status.get('phases', {}).get('data_import_completed', False)}"
            )
            print(
                f"   Agent Insights: {len(status.get('agent_insights', []))} insights"
            )
            return status
        else:
            print(f"❌ Failed to get status: {response.status_code}")
            print(f"   Response: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return None


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python trigger_data_import.py <flow_id> [action]")
        print("Actions: execute (default), status")
        sys.exit(1)

    flow_id = sys.argv[1]
    action = sys.argv[2] if len(sys.argv) > 2 else "execute"

    print("🎯 Data Import Phase Trigger Tool")
    print(f"   Flow ID: {flow_id}")
    print(f"   Action: {action}")
    print("=" * 50)

    if action == "status":
        check_flow_status(flow_id)
    elif action == "execute":
        # Check status first
        print("📋 Step 1: Checking current flow status...")
        check_flow_status(flow_id)
        print("\n" + "=" * 50)

        # Trigger execution
        print("📋 Step 2: Triggering data import execution...")
        success = trigger_data_import_execution(flow_id)
        print("\n" + "=" * 50)

        if success:
            print("📋 Step 3: Checking flow status after execution...")
            check_flow_status(flow_id)
        else:
            print("❌ Execution failed - skipping status check")
    else:
        print(f"❌ Unknown action: {action}")
        sys.exit(1)


if __name__ == "__main__":
    main()
