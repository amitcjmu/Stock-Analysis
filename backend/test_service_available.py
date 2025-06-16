#!/usr/bin/env python3

# Test the updated CrewAI Flow service
print("Testing CrewAI Flow Service availability...")

try:
    # Test imports first
    from app.services.crewai_flows.discovery_flow import CREWAI_FLOW_AVAILABLE
    print(f"CREWAI_FLOW_AVAILABLE from discovery_flow: {CREWAI_FLOW_AVAILABLE}")
    
    from app.services.crewai_flows.discovery_flow_redesigned import CREWAI_FLOW_AVAILABLE as REDESIGNED_AVAILABLE
    print(f"CREWAI_FLOW_AVAILABLE from discovery_flow_redesigned: {REDESIGNED_AVAILABLE}")
    
    # Test the actual service
    from app.services.crewai_flow_service import CrewAIFlowService
    from unittest.mock import Mock
    
    mock_db = Mock()
    service = CrewAIFlowService(mock_db)
    print(f"CrewAI Flow Service available: {service.service_available}")
    
    # Get service status
    status = service.get_service_status()
    print(f"Service status: {status}")
    
    # Test flow creation
    try:
        from app.services.crewai_flows.discovery_flow import create_discovery_flow
        from app.core.context import RequestContext
        
        context = RequestContext(
            client_account_id="test-client",
            engagement_id="test-engagement", 
            user_id="test-user"
        )
        
        flow = create_discovery_flow(
            session_id="test-session",
            client_account_id="test-client",
            engagement_id="test-engagement",
            user_id="test-user",
            cmdb_data={"test": "data"},
            metadata={},
            crewai_service=service,
            context=context
        )
        
        print(f"✅ Flow creation successful: {type(flow)}")
        print(f"Flow fingerprint: {getattr(flow, 'fingerprint', 'None')}")
        
    except Exception as e:
        print(f"❌ Flow creation failed: {e}")
        import traceback
        traceback.print_exc()
    
except Exception as e:
    print(f"❌ Service test failed: {e}")
    import traceback
    traceback.print_exc() 