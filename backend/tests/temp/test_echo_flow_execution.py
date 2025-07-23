#!/usr/bin/env python3
"""
Test script for ECHO team's Discovery flow execution fix
Tests that flows progress from 'initialized' to 'running' state
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
from datetime import datetime

from sqlalchemy import select

from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.services.master_flow_orchestrator import MasterFlowOrchestrator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# [ECHO] Initialize flows before testing
from app.core.flow_initialization import initialize_flows_on_startup

print("[ECHO] Initializing flow configurations...")
flow_init_results = initialize_flows_on_startup()
print(f"[ECHO] Flow initialization results: {flow_init_results.get('success', False)}")

async def test_flow_execution():
    """Test that Discovery flows progress beyond initialized status"""
    
    async with AsyncSessionLocal() as db:
        # Create context
        context = RequestContext(
            client_account_id=1,
            engagement_id=1,
            user_id="test_user"
        )
        
        # Create Master Flow Orchestrator
        orchestrator = MasterFlowOrchestrator(db, context)
        
        # Test data
        test_data = [
            {
                "Server Name": "web-server-01",
                "IP Address": "10.0.1.10",
                "Operating System": "Ubuntu 20.04",
                "CPU": "4 cores",
                "Memory": "16GB",
                "Storage": "500GB SSD",
                "Application": "Web Frontend",
                "Environment": "Production",
                "Business Unit": "Sales",
                "Criticality": "High"
            },
            {
                "Server Name": "db-server-01",
                "IP Address": "10.0.2.20",
                "Operating System": "RHEL 8",
                "CPU": "8 cores",
                "Memory": "64GB",
                "Storage": "2TB SSD",
                "Application": "PostgreSQL Database",
                "Environment": "Production",
                "Business Unit": "IT",
                "Criticality": "Critical"
            }
        ]
        
        print(f"\n[ECHO] Creating Discovery flow at {datetime.now()}")
        
        # Create flow
        flow_id, flow_details = await orchestrator.create_flow(
            flow_type="discovery",
            flow_name="ECHO Test Discovery Flow",
            configuration={
                "source": "test_script",
                "test_mode": True
            },
            initial_state={
                "raw_data": test_data
            }
        )
        
        print(f"[ECHO] Flow created: {flow_id}")
        print(f"[ECHO] Initial status: {flow_details.get('flow_status', 'N/A')}")
        
        # Wait a bit for async task to start
        print("[ECHO] Waiting 2 seconds for flow kickoff to start...")
        await asyncio.sleep(2)
        
        # Check flow status
        status = await orchestrator.get_flow_status(flow_id)
        print("\n[ECHO] Flow status after 2 seconds:")
        print(f"  - Status: {status['status']}")
        print(f"  - Current phase: {status.get('current_phase', 'N/A')}")
        print(f"  - Progress: {status.get('progress_percentage', 0)}%")
        
        # Check database directly
        stmt = select(CrewAIFlowStateExtensions).where(
            CrewAIFlowStateExtensions.flow_id == flow_id
        )
        result = await db.execute(stmt)
        db_flow = result.scalar_one_or_none()
        
        if db_flow:
            print("\n[ECHO] Database record:")
            print(f"  - DB Status: {db_flow.flow_status}")
            print(f"  - Configuration: {db_flow.flow_configuration}")
            print(f"  - Updated at: {db_flow.updated_at}")
        
        # Wait a bit more and check again
        print("\n[ECHO] Waiting 5 more seconds for phase progression...")
        await asyncio.sleep(5)
        
        # Final status check
        final_status = await orchestrator.get_flow_status(flow_id)
        print("\n[ECHO] Final flow status after 7 seconds total:")
        print(f"  - Status: {final_status['status']}")
        print(f"  - Current phase: {final_status.get('current_phase', 'N/A')}")
        print(f"  - Progress: {final_status.get('progress_percentage', 0)}%")
        
        # Verify fix worked
        if final_status['status'] != 'initialized':
            print("\n✅ [ECHO] SUCCESS: Flow progressed beyond 'initialized' status!")
            print(f"   Flow is now in '{final_status['status']}' status")
            return True
        else:
            print("\n❌ [ECHO] FAILURE: Flow still stuck at 'initialized' status")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_flow_execution())
    sys.exit(0 if success else 1)