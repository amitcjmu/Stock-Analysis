#!/usr/bin/env python3
"""
Test script for ECHO team's flow state progression fix
Tests the core issue without requiring database
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize flows
from app.core.flow_initialization import initialize_flows_on_startup

print("[ECHO] Initializing flow configurations...")
flow_init_results = initialize_flows_on_startup()
print(f"[ECHO] Flow initialization results: {flow_init_results.get('success', False)}")

# Import CrewAI flow components
try:
    from app.core.context import RequestContext
    from app.services.crewai_flows.unified_discovery_flow import create_unified_discovery_flow
    
    print("[ECHO] Testing direct CrewAI flow execution...")
    
    # Create context
    context = RequestContext(
        client_account_id=1,
        engagement_id=1,
        user_id="test_user"
    )
    
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
        }
    ]
    
    # Create discovery flow
    flow = create_unified_discovery_flow(
        crewai_service=None,  # Will be created inside
        context=context,
        raw_data=test_data,
        flow_id="test-echo-flow-001",
        metadata={"source": "echo_test"}
    )
    
    print(f"[ECHO] Flow created: {flow}")
    print(f"[ECHO] Flow ID: {flow.flow_id}")
    print(f"[ECHO] Flow has kickoff method: {hasattr(flow, 'kickoff')}")
    
    # Test the kickoff method directly
    if hasattr(flow, 'kickoff'):
        print("\n[ECHO] Testing kickoff() method...")
        
        # The kickoff method should trigger the @start decorator
        # and begin the flow execution chain
        try:
            # Since kickoff is synchronous, we'll call it directly
            result = flow.kickoff()
            print(f"[ECHO] Kickoff result: {result}")
            print("[ECHO] ✅ Flow kickoff executed successfully!")
        except Exception as e:
            print(f"[ECHO] ❌ Kickoff failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n[ECHO] Test completed")
    
except Exception as e:
    print(f"[ECHO] ❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)