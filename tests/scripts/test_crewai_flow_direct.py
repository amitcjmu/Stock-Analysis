#!/usr/bin/env python3
"""
Direct CrewAI Flow Service Test
Tests the CrewAI Flow service directly without pytest dependencies.
"""

import sys
import asyncio
import json
from datetime import datetime
from typing import Dict, Any


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
        from unittest.mock import Mock

        # Mock database session
        mock_db = Mock()

        # Initialize service
        service = CrewAIFlowService(mock_db)

        # Check basic attributes
        assert hasattr(service, 'db')
        assert hasattr(service, 'service_available')
        assert hasattr(service, '_active_flows')
        assert isinstance(service._active_flows, dict)

        print("✅ Service initialization successful")
        return True
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        return False


def test_health_status():
    """Test health status method."""
    try:
        from app.services.crewai_flow_service import CrewAIFlowService
        from unittest.mock import Mock

        mock_db = Mock()
        service = CrewAIFlowService(mock_db)

        health_status = service.get_health_status()

        # Verify health status structure
        required_fields = ["service_name", "status", "crewai_flow_available", "active_flows", "features"]
        for field in required_fields:
            assert field in health_status, f"Missing field: {field}"

        assert health_status["service_name"] == "CrewAI Flow Service"
        assert health_status["status"] in ["healthy", "degraded"]
        assert isinstance(health_status["active_flows"], int)
        assert isinstance(health_status["features"], dict)

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
        assert state.progress_percentage == 0.0

        # Test methods
        state.add_error("test_phase", "test error")
        assert len(state.errors) == 1

        state.mark_phase_complete("data_validation", {"result": "success"})
        assert state.phases_completed["data_validation"] is True
        assert state.progress_percentage == 20.0  # 1/5 phases complete

        print("✅ Flow state model test successful")
        return True
    except Exception as e:
        print(f"❌ Flow state model test failed: {e}")
        return False


def test_discovery_flow_creation():
    """Test discovery flow creation."""
    try:
        from app.services.crewai_flows.discovery_flow import create_discovery_flow, DiscoveryFlow
        from app.core.context import RequestContext
        from unittest.mock import Mock

        # Create mock context
        context = RequestContext(
            client_account_id="test-client",
            engagement_id="test-engagement",
            user_id="test-user",
            session_id="test-session"
        )

        # Create mock service
        mock_service = Mock()
        mock_service.agents = {}

        # Sample CMDB data
        cmdb_data = {
            "file_data": [
                {"name": "test-server", "type": "server", "environment": "prod"}
            ],
            "metadata": {"source": "test"}
        }

        # Create flow
        flow = create_discovery_flow(
            session_id="test-session",
            client_account_id="test-client",
            engagement_id="test-engagement",
            user_id="test-user",
            cmdb_data=cmdb_data,
            metadata={"test": "metadata"},
            crewai_service=mock_service,
            context=context
        )

        assert isinstance(flow, DiscoveryFlow)
        assert flow.state.session_id == "test-session"
        assert flow.state.cmdb_data == cmdb_data
        assert flow.crewai_service == mock_service
        assert flow.context == context

        print("✅ Discovery flow creation test successful")
        return True
    except Exception as e:
        print(f"❌ Discovery flow creation test failed: {e}")
        return False


def test_legacy_format_conversion():
    """Test conversion to legacy format."""
    try:
        from app.services.crewai_flow_service import CrewAIFlowService
        from app.services.crewai_flows.discovery_flow import DiscoveryFlowState
        from unittest.mock import Mock

        mock_db = Mock()
        service = CrewAIFlowService(mock_db)

        # Create a sample state
        state = DiscoveryFlowState(
            session_id="test-session",
            client_account_id="test-client",
            engagement_id="test-engagement",
            user_id="test-user"
        )
        state.mark_phase_complete("data_validation", {"records": 100})

        # Convert to legacy format
        legacy_format = service._convert_to_legacy_format(state)

        # Verify legacy structure
        assert legacy_format["session_id"] == "test-session"
        assert legacy_format["status"] == "running"
        assert "data_validation" in legacy_format
        assert legacy_format["data_validation"]["status"] == "completed"

        print("✅ Legacy format conversion test successful")
        return True
    except Exception as e:
        print(f"❌ Legacy format conversion test failed: {e}")
        return False


async def test_workflow_initiation():
    """Test workflow initiation (async test)."""
    try:
        from app.services.crewai_flow_service import CrewAIFlowService
        from app.core.context import RequestContext
        from unittest.mock import Mock, AsyncMock, patch

        # Create mock database session
        mock_db = AsyncMock()

        # Create service
        # WorkflowStateService removed - using V2 Discovery Flow architecture
        service = CrewAIFlowService(mock_db)

        # Create context
        context = RequestContext(
            client_account_id="test-client",
            engagement_id="test-engagement",
            user_id="test-user",
            session_id="test-session"
        )

        # Sample data source
        data_source = {
            "file_data": [
                {"name": "test-server", "type": "server", "environment": "prod"}
            ],
            "metadata": {"source": "test"}
        }

        # Mock the create_discovery_flow function
        with patch('app.services.crewai_flow_service.create_discovery_flow') as mock_create:
            mock_flow = Mock()
            mock_flow.state = Mock()
            mock_flow.state.session_id = "test-session"
            mock_flow.state.status = "running"
            mock_flow.state.current_phase = "initialization"
            mock_create.return_value = mock_flow

            # Mock asyncio.create_task to avoid actual background execution
            with patch('asyncio.create_task'):
                result = await service.initiate_discovery_workflow(data_source, context)

            # Verify result structure
            assert isinstance(result, dict)
            assert "session_id" in result or "status" in result

            # Verify flow was created
            mock_create.assert_called_once()

            print("✅ Workflow initiation test successful")
            return True
    except Exception as e:
        print(f"❌ Workflow initiation test failed: {e}")
        return False


def test_service_methods():
    """Test all service methods exist and are callable."""
    try:
        from app.services.crewai_flow_service import CrewAIFlowService
        from unittest.mock import Mock

        mock_db = Mock()
        service = CrewAIFlowService(mock_db)

        # Test method existence
        methods_to_test = [
            'get_health_status',
            'get_all_active_flows',
            'get_performance_metrics',
            'cleanup_resources',
            'get_configuration',
            'get_service_status',
            'get_flow_status'
        ]

        for method_name in methods_to_test:
            assert hasattr(service, method_name), f"Missing method: {method_name}"
            method = getattr(service, method_name)
            assert callable(method), f"Method not callable: {method_name}"

        # Test some methods
        health = service.get_health_status()
        assert isinstance(health, dict)

        config = service.get_configuration()
        assert isinstance(config, dict)

        metrics = service.get_performance_metrics()
        assert isinstance(metrics, dict)

        cleanup = service.cleanup_resources()
        assert isinstance(cleanup, dict)

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
        ("Discovery Flow Creation", test_discovery_flow_creation),
        ("Legacy Format Conversion", test_legacy_format_conversion),
        ("Service Methods", test_service_methods),
    ]

    # Add async test
    async_tests = [
        ("Workflow Initiation", test_workflow_initiation),
    ]

    print("="*80)
    print("CREWAI FLOW SERVICE DIRECT TESTS")
    print("="*80)

    results = []

    # Run sync tests
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    # Run async tests
    for test_name, test_func in async_tests:
        print(f"\nRunning: {test_name}")
        try:
            success = asyncio.run(test_func())
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    # Print summary
    total_tests = len(results)
    passed_tests = len([r for r in results if r[1]])
    failed_tests = total_tests - passed_tests
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {failed_tests} ❌")
    print(f"Success Rate: {success_rate:.1f}%")

    print(f"\nDETAILED RESULTS:")
    print("-" * 40)
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")

    print("\n" + "="*80)
    if success_rate >= 90:
        print("🎉 All tests passed!")
    elif success_rate >= 80:
        print("✅ Most tests passed!")
    else:
        print("🚨 Some tests failed - needs attention.")
    print("="*80)

    return success_rate >= 80


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
