#!/usr/bin/env python3
"""
Test script to verify field mapping approval resume functionality.
This script simulates the frontend's "Continue to Data Cleansing" action.
"""

import asyncio
import httpx
import json
import sys
from datetime import datetime
from uuid import uuid4

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_FLOW_ID = None  # Will be populated from active flows

# Test headers simulating authenticated user
TEST_HEADERS = {
    "Content-Type": "application/json",
    "X-Client-Account-ID": "fc1cf7f8-6e81-42c8-95f9-03419e6e4df8",  # TechGlobal demo client
    "X-Engagement-ID": "a5e3c9f1-4b5d-4f3e-9c7a-8d3f2e1a9b8c",     # Cloud Migration engagement
    "X-User-ID": "550e8400-def0-def0-def0-446655440001",           # Demo user
    "Authorization": "Bearer test-token"  # In real scenario, use actual auth token
}


async def get_active_flows():
    """Get active discovery flows to find one in waiting_for_approval state."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/discovery/flows/active",
            headers=TEST_HEADERS
        )
        
        if response.status_code == 200:
            flows = response.json()
            print(f"Found {len(flows)} active flows")
            
            # Find a flow waiting for approval
            for flow in flows:
                if flow.get("status") in ["waiting_for_approval", "waiting_for_user_approval", "paused"]:
                    return flow
            
            # Return any active flow
            if flows:
                return flows[0]
        else:
            print(f"Failed to get active flows: {response.status_code}")
            print(response.text)
    
    return None


async def get_flow_status(flow_id: str):
    """Get detailed status of a specific flow."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/discovery/flows/{flow_id}/status",
            headers=TEST_HEADERS
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get flow status: {response.status_code}")
            print(response.text)
            return None


async def resume_flow_with_approval(flow_id: str, field_mappings: dict = None):
    """Resume a paused flow with field mapping approval."""
    
    # Default field mappings if none provided
    if field_mappings is None:
        field_mappings = {
            "hostname": "server_name",
            "ip_address": "ip_address", 
            "os": "operating_system",
            "environment": "environment_type",
            "application": "application_name",
            "cpu_cores": "cpu_count",
            "memory_gb": "memory_size",
            "storage_gb": "storage_size"
        }
    
    resume_data = {
        "field_mappings": field_mappings,
        "notes": "Field mappings approved via test script",
        "approval_timestamp": datetime.utcnow().isoformat(),
        "user_approval": True
    }
    
    print(f"\nResuming flow {flow_id} with approval data:")
    print(json.dumps(resume_data, indent=2))
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{API_BASE_URL}/discovery/flow/{flow_id}/resume",
            headers=TEST_HEADERS,
            json=resume_data
        )
        
        print(f"\nResume response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("Resume successful!")
            print(json.dumps(result, indent=2))
            return result
        else:
            print(f"Resume failed: {response.status_code}")
            print(response.text)
            return None


async def monitor_flow_progress(flow_id: str, max_checks: int = 10):
    """Monitor flow progress after resume."""
    print(f"\nMonitoring flow progress for {flow_id}...")
    
    for i in range(max_checks):
        await asyncio.sleep(2)  # Wait 2 seconds between checks
        
        status = await get_flow_status(flow_id)
        if status:
            current_phase = status.get("current_phase", "unknown")
            progress = status.get("progress_percentage", 0)
            flow_status = status.get("status", "unknown")
            awaiting_approval = status.get("awaiting_user_approval", False)
            
            print(f"\nCheck {i+1}: Status={flow_status}, Phase={current_phase}, Progress={progress}%, Awaiting Approval={awaiting_approval}")
            
            # Check if flow has moved past field mapping
            if current_phase == "data_cleansing" or progress > 33:
                print("\n✅ SUCCESS! Flow has progressed to data cleansing phase!")
                return True
            
            # Check if flow is stuck
            if flow_status in ["failed", "error"]:
                print(f"\n❌ Flow failed with status: {flow_status}")
                return False
    
    print("\n⚠️ Flow did not progress after maximum checks")
    return False


async def main():
    """Main test function."""
    print("Field Mapping Resume Test Script")
    print("================================\n")
    
    # Step 1: Find an active flow
    print("Step 1: Finding active discovery flow...")
    flow = await get_active_flows()
    
    if not flow:
        print("❌ No active flows found. Please start a discovery flow first.")
        return
    
    flow_id = flow.get("flow_id")
    print(f"✅ Found flow: {flow_id}")
    print(f"   Status: {flow.get('status')}")
    print(f"   Phase: {flow.get('current_phase')}")
    
    # Step 2: Get detailed flow status
    print("\nStep 2: Getting detailed flow status...")
    status = await get_flow_status(flow_id)
    
    if status:
        print(f"✅ Current status: {status.get('status')}")
        print(f"   Awaiting approval: {status.get('awaiting_user_approval', False)}")
        print(f"   Field mappings: {len(status.get('field_mappings', {}))}")
    
    # Step 3: Resume flow with approval
    print("\nStep 3: Resuming flow with field mapping approval...")
    resume_result = await resume_flow_with_approval(flow_id)
    
    if not resume_result:
        print("❌ Failed to resume flow")
        return
    
    # Step 4: Monitor progress
    print("\nStep 4: Monitoring flow progress...")
    success = await monitor_flow_progress(flow_id)
    
    if success:
        print("\n🎉 Test PASSED! Field mapping approval and flow continuation working correctly.")
    else:
        print("\n❌ Test FAILED! Flow did not progress after approval.")


if __name__ == "__main__":
    asyncio.run(main())