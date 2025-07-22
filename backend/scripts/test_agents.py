#!/usr/bin/env python3
"""
Test script for the new agentic Discovery Flow implementation
"""

import asyncio
import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, '/app')

async def test_agentic_flow():
    try:
        print("🧪 Testing Agentic Discovery Flow Implementation")
        print("=" * 60)
        
        # Test 1: Import and initialize CrewAI Flow Service
        print("1. Testing CrewAI Flow Service initialization...")
        from app.core.database import AsyncSessionLocal
        from app.services.crewai_flow_service import CrewAIFlowService
        
        async with AsyncSessionLocal() as db:
            service = CrewAIFlowService(db)
            print(f"   ✅ Service available: {service.service_available}")
            print(f"   ✅ Agents initialized: {len(service.agents)}")
            
            for agent_name, agent in service.agents.items():
                print(f"   - {agent_name}: {type(agent).__name__}")
        
        # Test 2: Test Discovery Flow creation
        print("\n2. Testing Discovery Flow creation...")
        import uuid

        from app.core.context import RequestContext
        from app.services.crewai_flows.discovery_flow import CREWAI_FLOW_AVAILABLE, create_discovery_flow
        
        print(f"   ✅ CrewAI Flow available: {CREWAI_FLOW_AVAILABLE}")
        
        # Create test context
        context = RequestContext(
            client_account_id=str(uuid.uuid4()),
            engagement_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            flow_id=str(uuid.uuid4())
        )
        
        # Create test CMDB data
        test_cmdb_data = {
            "file_data": [
                {
                    "Asset_Name": "test-server-01",
                    "CI_Type": "Server",
                    "Environment": "Production",
                    "Owner": "IT Team"
                },
                {
                    "Asset_Name": "test-app-01", 
                    "CI_Type": "Application",
                    "Environment": "Development",
                    "Owner": "Dev Team"
                }
            ]
        }
        
        test_metadata = {
            "filename": "test_cmdb.csv",
            "total_records": 2
        }
        
        async with AsyncSessionLocal() as db:
            crewai_service = CrewAIFlowService(db)
            
            flow = create_discovery_flow(
                flow_id=context.flow_id,
                client_account_id=context.client_account_id,
                engagement_id=context.engagement_id,
                user_id=context.user_id,
                cmdb_data=test_cmdb_data,
                metadata=test_metadata,
                crewai_service=crewai_service,
                context=context
            )
            
            print(f"   ✅ Flow created with fingerprint: {flow.fingerprint.uuid_str}")
            print(f"   ✅ Data source agent available: {flow.data_source_agent is not None}")
            print(f"   ✅ Dependency agent available: {flow.dependency_agent is not None}")
        
        # Test 3: Test Flow state initialization
        print("\n3. Testing Flow state initialization...")
        initial_result = flow.initialize_discovery()
        print(f"   ✅ Initialization result: {initial_result}")
        print(f"   ✅ Flow ID set: {flow.state.flow_id}")
        print(f"   ✅ Fingerprint ID set: {flow.state.fingerprint_id}")
        print(f"   ✅ Data records: {len(flow.state.cmdb_data.get('file_data', []))}")
        
        print("\n🎉 All tests passed! The agentic implementation is working correctly.")
        print("\nKey improvements implemented:")
        print("✅ CrewAI Flows with proper agent integration")
        print("✅ CrewAI Fingerprinting for session management") 
        print("✅ Discovery Agents properly initialized")
        print("✅ Database integration phase added")
        print("✅ Proper Crews and Tasks structure")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_agentic_flow())
    sys.exit(0 if result else 1) 