#!/usr/bin/env python3
"""
Simple CrewAI Flow Service Test
"""

import sys
import asyncio
from unittest.mock import Mock, AsyncMock, patch

def test_service_import():
    """Test that the service can be imported."""
    try:
        from app.services.crewai_flow_service import CrewAIFlowService
        print("✅ CrewAI Flow Service import successful")
        return True
    except ImportError as e:
        print(f"❌ CrewAI Flow Service import failed: {e}")
        return False

def test_service_initialization():
    """Test service initialization."""
    try:
        from app.services.crewai_flow_service import CrewAIFlowService
        
        # Mock database session
        mock_db = Mock()
        
        # Initialize service
        service = CrewAIFlowService(mock_db)
        
        # Check basic attributes
        assert hasattr(service, "db")
        assert hasattr(service, "service_available")
        assert hasattr(service, "_active_flows")
        
        print("✅ Service initialization successful")
        return True
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        return False

def test_health_status():
    """Test health status method."""
    try:
        from app.services.crewai_flow_service import CrewAIFlowService
        
        mock_db = Mock()
        service = CrewAIFlowService(mock_db)
        
        health_status = service.get_health_status()
        
        # Verify health status structure
        required_fields = ["service_name", "status", "crewai_flow_available", "active_flows", "features"]
        for field in required_fields:
            assert field in health_status, f"Missing field: {field}"
        
        print("✅ Health status test successful")
        return True
    except Exception as e:
        print(f"❌ Health status test failed: {e}")
        return False

def test_flow_state_model():
    """Test the DiscoveryFlowState model."""
    try:
        from app.services.crewai_flows.discovery_flow import DiscoveryFlowState
        
        # Create a flow state
        state = DiscoveryFlowState(
            session_id="test-session",
            client_account_id="test-client",
            engagement_id="test-engagement",
            user_id="test-user"
        )
        
        # Test basic attributes
        assert state.session_id == "test-session"
        assert state.current_phase == "initialization"
        assert state.status == "running"
        
        print("✅ Flow state model test successful")
        return True
    except Exception as e:
        print(f"❌ Flow state model test failed: {e}")
        return False

def test_service_methods():
    """Test service methods exist and are callable."""
    try:
        from app.services.crewai_flow_service import CrewAIFlowService
        
        mock_db = Mock()
        service = CrewAIFlowService(mock_db)
        
        # Test method existence
        methods = ['get_health_status', 'get_all_active_flows', 'get_performance_metrics']
        
        for method_name in methods:
            assert hasattr(service, method_name), f"Missing method: {method_name}"
            method = getattr(service, method_name)
            assert callable(method), f"Method not callable: {method_name}"
        
        # Test some methods
        health = service.get_health_status()
        assert isinstance(health, dict)
        
        metrics = service.get_performance_metrics()
        assert isinstance(metrics, dict)
        
        print("✅ Service methods test successful")
        return True
    except Exception as e:
        print(f"❌ Service methods test failed: {e}")
        return False

def run_all_tests():
    """Run all tests and return summary."""
    tests = [
        ("Service Import", test_service_import),
        ("Service Initialization", test_service_initialization),
        ("Health Status", test_health_status),
        ("Flow State Model", test_flow_state_model),
        ("Service Methods", test_service_methods),
    ]
    
    print("="*60)
    print("CREWAI FLOW SERVICE TESTS")
    print("="*60)
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    total_tests = len(results)
    passed_tests = len([r for r in results if r[1]])
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {total_tests - passed_tests} ❌")
    print(f"Success Rate: {success_rate:.1f}%")
    
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
    
    return success_rate >= 80

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 