#!/usr/bin/env python3
"""
Trigger Data Import Phase Execution
Script to manually trigger data import phase execution for stuck flows
"""

import json
import re
import sys
import uuid
from typing import Optional

import requests


def validate_flow_id(flow_id: str) -> tuple[bool, str]:
    """Validate flow_id parameter.

    Args:
        flow_id: Flow ID to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not flow_id or not isinstance(flow_id, str):
        return False, "Flow ID must be a non-empty string"

    # Remove whitespace
    flow_id = flow_id.strip()

    if not flow_id:
        return False, "Flow ID cannot be empty or whitespace only"

    # Check if it's a valid UUID format
    uuid_pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        re.IGNORECASE,
    )

    if not uuid_pattern.match(flow_id):
        # Try to parse as UUID for additional validation
        try:
            uuid.UUID(flow_id)
        except ValueError:
            return False, f"Flow ID '{flow_id}' is not a valid UUID format"

    return True, ""


def trigger_data_import_execution(flow_id: str):
    """Trigger data import phase execution for a specific flow.

    Args:
        flow_id: Valid UUID string for the flow

    Returns:
        bool: True if successful, False otherwise
    """
    # Validate flow_id first
    is_valid, error_msg = validate_flow_id(flow_id)
    if not is_valid:
        print(f"❌ Invalid flow_id: {error_msg}")
        return False

    # Clean the flow_id
    flow_id = flow_id.strip()

    # API endpoint
    base_url = "http://localhost:8000"
    execute_url = f"{base_url}/api/v1/flows/{flow_id}/execute"

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
        # Make the API call with timeout
        response = requests.post(execute_url, headers=headers, json=payload, timeout=30)

        print(f"📊 Response Status: {response.status_code}")

        if response.status_code == 200:
            try:
                result = response.json()
                print("✅ Success! Data import execution triggered:")
                print(f"   Status: {result.get('status', 'Unknown')}")
                print(f"   Phase: {result.get('phase', 'Unknown')}")
                print(
                    f"   CrewAI Execution: {result.get('crewai_execution', 'Unknown')}"
                )
                print(
                    f"   Database Execution: {result.get('database_execution', 'Unknown')}"
                )

                agent_insights = result.get("agent_insights", [])
                if isinstance(agent_insights, list) and agent_insights:
                    print(
                        f"   Agent Insights: {len(agent_insights)} insights generated"
                    )
                elif agent_insights:
                    print("   Agent Insights: Available (format unknown)")
                else:
                    print("   Agent Insights: None")

                return True
            except (ValueError, TypeError) as json_error:
                print(f"❌ Error parsing response JSON: {json_error}")
                print(f"   Raw response: {response.text[:200]}...")  # First 200 chars
                return False
        else:
            print(f"❌ Failed with status {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Error: {error_detail.get('detail', 'Unknown error')}")
            except (ValueError, TypeError):
                print(f"   Response: {response.text[:200]}...")  # First 200 chars
            return False

    except requests.exceptions.Timeout:
        print("❌ Request timed out after 30 seconds")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - is the server running?")
        return False
    except requests.exceptions.RequestException as req_error:
        print(f"❌ Request error: {req_error}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error triggering execution: {e}")
        return False


def _print_status_details(status: dict) -> None:
    """Print formatted status details.

    Args:
        status: Parsed status response
    """
    print("📊 Flow Status:")

    # Safely extract values with defaults
    progress = status.get("progress_percentage", "Unknown")
    if isinstance(progress, (int, float)):
        print(f"   Progress: {progress}%")
    else:
        print(f"   Progress: {progress}")

    print(f"   Current Phase: {status.get('current_phase', 'Unknown')}")
    print(f"   Status: {status.get('status', 'Unknown')}")

    # Safely access nested phase data
    phases = status.get("phases", {})
    if isinstance(phases, dict):
        data_import_completed = phases.get("data_import_completed", False)
    else:
        data_import_completed = "Unknown"
    print(f"   Data Import Completed: {data_import_completed}")

    # Safely count agent insights
    agent_insights = status.get("agent_insights", [])
    if isinstance(agent_insights, list):
        print(f"   Agent Insights: {len(agent_insights)} insights")
    elif agent_insights:
        print("   Agent Insights: Available (format unknown)")
    else:
        print("   Agent Insights: 0 insights")


def _handle_error_response(response) -> None:
    """Handle and print error response details.

    Args:
        response: HTTP response object
    """
    print(f"❌ Failed to get status: {response.status_code}")
    try:
        error_detail = response.json()
        print(f"   Error: {error_detail.get('detail', 'Unknown error')}")
    except (ValueError, TypeError):
        print(f"   Response: {response.text[:200]}...")  # First 200 chars


def check_flow_status(flow_id: str) -> Optional[dict]:
    """Check the current status of a flow.

    Args:
        flow_id: Valid UUID string for the flow

    Returns:
        dict: Flow status information if successful, None otherwise
    """
    # Validate flow_id first
    is_valid, error_msg = validate_flow_id(flow_id)
    if not is_valid:
        print(f"❌ Invalid flow_id: {error_msg}")
        return None

    # Clean the flow_id
    flow_id = flow_id.strip()

    base_url = "http://localhost:8000"
    status_url = f"{base_url}/api/v1/flows/{flow_id}/status"

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
        response = requests.get(status_url, headers=headers, timeout=30)

        if response.status_code == 200:
            try:
                status = response.json()
                _print_status_details(status)
                return status
            except (ValueError, TypeError) as json_error:
                print(f"❌ Error parsing status response JSON: {json_error}")
                print(f"   Raw response: {response.text[:200]}...")  # First 200 chars
                return None
        else:
            _handle_error_response(response)
            return None

    except requests.exceptions.Timeout:
        print("❌ Status request timed out after 30 seconds")
        return None
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - is the server running?")
        return None
    except requests.exceptions.RequestException as req_error:
        print(f"❌ Request error: {req_error}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error checking status: {e}")
        return None


def main():
    """Main function with comprehensive input validation."""
    if len(sys.argv) < 2:
        print("Usage: python trigger_data_import.py <flow_id> [action]")
        print("Actions: execute (default), status")
        print("")
        print("Example:")
        print(
            "  python trigger_data_import.py 12345678-1234-5678-9012-123456789012 execute"
        )
        print("")
        print("Note: flow_id must be a valid UUID format")
        sys.exit(1)

    flow_id = sys.argv[1]
    action = sys.argv[2] if len(sys.argv) > 2 else "execute"

    # Validate flow_id before proceeding
    is_valid, error_msg = validate_flow_id(flow_id)
    if not is_valid:
        print(f"❌ Validation Error: {error_msg}")
        print("")
        print("Expected format: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX (UUID)")
        print("Example: 12345678-1234-5678-9012-123456789012")
        sys.exit(1)

    # Clean the flow_id
    flow_id = flow_id.strip()

    # Validate action
    valid_actions = ["execute", "status"]
    if action not in valid_actions:
        print(f"❌ Invalid action: {action}")
        print(f"Valid actions: {', '.join(valid_actions)}")
        sys.exit(1)

    print("🎯 Data Import Phase Trigger Tool")
    print(f"   Flow ID: {flow_id}")
    print(f"   Action: {action}")
    print("   Flow ID Validation: ✅ Valid UUID format")
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
