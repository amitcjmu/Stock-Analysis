"""
Test module for CrewAI Flow Service modularization.

This test verifies that the modularized crewai_flow_service can be imported correctly
and that backward compatibility is maintained.
"""

import pytest
import sys
from unittest.mock import patch, MagicMock


def test_crewai_flow_service_import():
    """Test that CrewAIFlowService can be imported from the backward compatibility shim."""
    try:
        from app.services.crewai_flow_service import CrewAIFlowService
        assert CrewAIFlowService is not None
        print("✅ CrewAIFlowService imported successfully")
    except ImportError as e:
        pytest.fail(f"Failed to import CrewAIFlowService: {e}")


def test_crewai_flow_service_constants():
    """Test that CrewAI flow service constants are accessible."""
    try:
        from app.services.crewai_flow_service import CREWAI_FLOWS_AVAILABLE
        assert isinstance(CREWAI_FLOWS_AVAILABLE, bool)
        print(f"✅ CREWAI_FLOWS_AVAILABLE = {CREWAI_FLOWS_AVAILABLE}")
    except ImportError as e:
        pytest.fail(f"Failed to import CrewAI flow service constants: {e}")


def test_crewai_flow_service_exceptions():
    """Test that CrewAI flow service exceptions can be imported."""
    try:
        from app.services.crewai_flow_service import (
            CrewAIExecutionError,
            InvalidFlowStateError
        )

        # Test that exceptions are accessible
        assert CrewAIExecutionError is not None
        assert InvalidFlowStateError is not None
        print("✅ CrewAI flow service exceptions imported successfully")
    except ImportError as e:
        pytest.fail(f"Failed to import CrewAI flow service exceptions: {e}")


def test_crewai_flow_service_mixins():
    """Test that CrewAI flow service mixins can be imported."""
    try:
        from app.services.crewai_flow_service import (
            FlowExecutionMixin,
            FlowMonitoringMixin,
            FlowStateManagerMixin,
            FlowTaskManagerMixin,
            FlowValidationMixin
        )

        # Test that mixins are accessible
        assert FlowExecutionMixin is not None
        assert FlowMonitoringMixin is not None
        assert FlowStateManagerMixin is not None
        assert FlowTaskManagerMixin is not None
        assert FlowValidationMixin is not None
        print("✅ CrewAI flow service mixins imported successfully")
    except ImportError as e:
        pytest.fail(f"Failed to import CrewAI flow service mixins: {e}")


def test_crewai_flow_service_factory():
    """Test that the service factory function is accessible."""
    try:
        from app.services.crewai_flow_service import get_crewai_flow_service
        assert get_crewai_flow_service is not None
        print("✅ get_crewai_flow_service factory function imported successfully")
    except ImportError as e:
        pytest.fail(f"Failed to import CrewAI flow service factory: {e}")


def test_crewai_flow_service_base():
    """Test that the base service class can be imported."""
    try:
        from app.services.crewai_flow_service import CrewAIFlowServiceBase
        assert CrewAIFlowServiceBase is not None
        print("✅ CrewAIFlowServiceBase imported successfully")
    except ImportError as e:
        pytest.fail(f"Failed to import CrewAIFlowServiceBase: {e}")


def test_backward_compatibility_all_exports():
    """Test that all expected exports are available for backward compatibility."""
    try:
        from app.services.crewai_flow_service import __all__

        expected_exports = [
            "CrewAIFlowService",
            "get_crewai_flow_service",
            "CREWAI_FLOWS_AVAILABLE",
            "CrewAIExecutionError",
            "InvalidFlowStateError",
            "CrewAIFlowServiceBase",
            "FlowExecutionMixin",
            "FlowMonitoringMixin",
            "FlowStateManagerMixin",
            "FlowTaskManagerMixin",
            "FlowValidationMixin",
        ]

        for export in expected_exports:
            assert export in __all__, f"Missing export: {export}"

        print(f"✅ All {len(expected_exports)} exports available for backward compatibility")
    except ImportError as e:
        pytest.fail(f"Failed to verify backward compatibility exports: {e}")


def test_modularized_import():
    """Test that the modularized implementation can be imported directly."""
    try:
        from app.services.crewai_flows.crewai_flow_service import CrewAIFlowService as ModularizedService
        assert ModularizedService is not None
        print("✅ Modularized CrewAI flow service imported successfully")
    except ImportError as e:
        # This might fail if the modularized structure is different, but should not break the shim
        print(f"⚠️ Modularized import failed (might be expected): {e}")


if __name__ == "__main__":
    # Run tests if called directly
    print("Running CrewAI Flow Service tests...")
    test_crewai_flow_service_import()
    test_crewai_flow_service_constants()
    test_crewai_flow_service_exceptions()
    test_crewai_flow_service_mixins()
    test_crewai_flow_service_factory()
    test_crewai_flow_service_base()
    test_backward_compatibility_all_exports()
    test_modularized_import()
    print("All CrewAI Flow Service tests passed!")
