"""
Test Flow Configurations
MFO-057: Test all flow types

Tests to ensure all flow configurations are properly set up and working.
"""

import pytest

from app.services.flow_configs import (
    get_flow_summary,
    initialize_all_flows,
    verify_flow_configurations,
)
from app.services.flow_type_registry import FlowTypeRegistry
from app.services.handler_registry import HandlerRegistry
from app.services.validator_registry import ValidatorRegistry


class TestFlowConfigurations:
    """Test suite for flow configurations"""

    def test_initialize_all_flows(self):
        """MFO-057: Test flow initialization"""
        # Initialize all flows
        results = initialize_all_flows()

        # Check results structure
        assert "flows_registered" in results
        assert "validators_registered" in results
        assert "handlers_registered" in results
        assert "errors" in results

        # Verify all 9 flows are registered
        expected_flows = [
            "discovery",
            "assessment",
            "collection",
            "planning",
            "execution",
            "modernize",
            "finops",
            "observability",
            "decommission",
        ]

        if results.get("status") != "already_initialized":
            assert len(results["flows_registered"]) == 9
            for flow in expected_flows:
                assert flow in results["flows_registered"]

            # Check validators were registered
            assert len(results["validators_registered"]) > 0

            # Check handlers were registered
            assert len(results["handlers_registered"]) > 0

            # Check no errors occurred
            assert len(results["errors"]) == 0

    def test_verify_flow_configurations(self):
        """MFO-058: Test configuration consistency"""
        # First ensure flows are initialized
        initialize_all_flows()

        # Verify configurations
        verification = verify_flow_configurations()

        # Check verification structure
        assert "total_flows" in verification
        assert "flow_details" in verification
        assert "consistency_check" in verification
        assert "issues" in verification

        # Verify all flows present
        assert verification["total_flows"] == 9
        assert verification["consistency_check"] is True
        assert len(verification["issues"]) == 0

        # Check each flow has proper configuration
        for flow_name, details in verification["flow_details"].items():
            assert details["phases"] > 0
            assert details["has_validators"] is True
            assert details["has_handlers"] is True
            assert details["capabilities"]["pause_resume"] is True
            assert details["capabilities"]["checkpointing"] is True

    def test_get_flow_summary(self):
        """Test flow summary retrieval"""
        # Ensure flows are initialized
        initialize_all_flows()

        # Get summary
        summary = get_flow_summary()

        # Check summary
        assert len(summary) == 9

        for flow_summary in summary:
            assert "name" in flow_summary
            assert "display_name" in flow_summary
            assert "description" in flow_summary
            assert "version" in flow_summary
            assert "phase_count" in flow_summary
            assert "tags" in flow_summary

            # Verify phase count is reasonable
            assert flow_summary["phase_count"] >= 3
            assert flow_summary["phase_count"] <= 6

    def test_discovery_flow_configuration(self):
        """Test Discovery flow specific configuration"""
        # Ensure flows are initialized
        initialize_all_flows()

        # Get flow registry
        flow_registry = FlowTypeRegistry()

        # Get Discovery flow config
        discovery_config = flow_registry.get_flow_config("discovery")

        # Check Discovery flow specifics
        assert discovery_config.name == "discovery"
        assert discovery_config.display_name == "Discovery Flow"
        assert len(discovery_config.phases) == 6

        # Check phase names
        phase_names = [phase.name for phase in discovery_config.phases]
        expected_phases = [
            "data_import",
            "field_mapping",
            "data_cleansing",
            "asset_creation",
            "asset_inventory",
            "dependency_analysis",
        ]
        assert phase_names == expected_phases

        # Check handlers
        assert discovery_config.initialization_handler == "discovery_initialization"
        assert discovery_config.finalization_handler == "discovery_finalization"
        assert discovery_config.error_handler == "discovery_error_handler"

    def test_assessment_flow_configuration(self):
        """Test Assessment flow specific configuration"""
        # Ensure flows are initialized
        initialize_all_flows()

        # Get flow registry
        flow_registry = FlowTypeRegistry()

        # Get Assessment flow config
        assessment_config = flow_registry.get_flow_config("assessment")

        # Check Assessment flow specifics
        assert assessment_config.name == "assessment"
        assert assessment_config.display_name == "Assessment Flow"
        assert len(assessment_config.phases) == 4

        # Check phase names
        phase_names = [phase.name for phase in assessment_config.phases]
        expected_phases = [
            "readiness_assessment",
            "complexity_analysis",
            "risk_assessment",
            "recommendation_generation",
        ]
        assert phase_names == expected_phases

    def test_planning_flow_configuration(self):
        """Test Planning flow configuration"""
        # Ensure flows are initialized
        initialize_all_flows()

        flow_registry = FlowTypeRegistry()
        planning_config = flow_registry.get_flow_config("planning")

        assert planning_config.name == "planning"
        assert len(planning_config.phases) == 3
        assert planning_config.capabilities.supports_iterations is True
        assert planning_config.capabilities.max_iterations == 5

    def test_execution_flow_configuration(self):
        """Test Execution flow configuration"""
        # Ensure flows are initialized
        initialize_all_flows()

        flow_registry = FlowTypeRegistry()
        execution_config = flow_registry.get_flow_config("execution")

        assert execution_config.name == "execution"
        assert len(execution_config.phases) == 3
        assert execution_config.capabilities.supports_rollback is True
        assert execution_config.capabilities.supports_parallel_phases is True

    def test_validator_registration(self):
        """Test that validators are properly registered"""
        # Ensure flows are initialized
        initialize_all_flows()

        validator_registry = ValidatorRegistry()

        # Test some key validators
        assert validator_registry.is_registered("field_mapping_validation")
        assert validator_registry.is_registered("asset_validation")
        assert validator_registry.is_registered("assessment_validation")
        assert validator_registry.is_registered("wave_validation")
        assert validator_registry.is_registered("pre_migration_validation")

    def test_handler_registration(self):
        """Test that handlers are properly registered"""
        # Ensure flows are initialized
        initialize_all_flows()

        handler_registry = HandlerRegistry()

        # Test some key handlers
        assert handler_registry.is_registered("discovery_initialization")
        assert handler_registry.is_registered("assessment_completion")
        assert handler_registry.is_registered("planning_error_handler")
        assert handler_registry.is_registered("execution_finalization")

    @pytest.mark.asyncio
    async def test_validator_execution(self):
        """Test that validators can be executed"""
        # Ensure flows are initialized
        initialize_all_flows()

        validator_registry = ValidatorRegistry()

        # Test field mapping validation
        validator = validator_registry.get_validator("field_mapping_validation")

        # Test with valid input
        valid_input = {
            "mapping_rules": {
                "hostname": "server_name",
                "ip_address": "ip",
                "os_type": "operating_system",
                "environment": "env",
                "application_name": "app_name",
            },
            "imported_data": [
                {
                    "server_name": "server1",
                    "ip": "10.0.0.1",
                    "operating_system": "Linux",
                    "env": "production",
                    "app_name": "webapp",
                }
            ],
        }

        result = await validator(valid_input, {})
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_handler_execution(self):
        """Test that handlers can be executed"""
        # Ensure flows are initialized
        initialize_all_flows()

        handler_registry = HandlerRegistry()

        # Test discovery initialization handler
        handler = handler_registry.get_handler("discovery_initialization")

        result = await handler(
            flow_id="test_flow_123",
            flow_type="discovery",
            context={},
            configuration={"parallel_processing": True},
        )

        assert result["initialized"] is True
        assert result["flow_id"] == "test_flow_123"
        assert "discovery_config" in result

    def test_flow_phases_have_validators(self):
        """Test that all flow phases have appropriate validators"""
        # Ensure flows are initialized
        initialize_all_flows()

        flow_registry = FlowTypeRegistry()

        for flow_name in flow_registry.list_flow_types():
            config = flow_registry.get_flow_config(flow_name)

            # Check that most phases have validators
            phases_with_validators = sum(
                1 for phase in config.phases if phase.validators
            )

            # At least 50% of phases should have validators
            assert phases_with_validators >= len(config.phases) * 0.5

    def test_flow_error_handlers(self):
        """Test that all flows have error handlers"""
        # Ensure flows are initialized
        initialize_all_flows()

        flow_registry = FlowTypeRegistry()

        for flow_name in flow_registry.list_flow_types():
            config = flow_registry.get_flow_config(flow_name)

            # All flows should have error handlers
            assert config.error_handler is not None
            assert config.error_handler == f"{flow_name}_error_handler"


def test_flow_configurations_basic():
    """Basic test that can be run directly"""
    # Initialize flows
    results = initialize_all_flows()

    if results.get("status") != "already_initialized":
        print(f"Flows registered: {results['flows_registered']}")
        print(f"Validators registered: {len(results['validators_registered'])}")
        print(f"Handlers registered: {len(results['handlers_registered'])}")
        print(f"Errors: {results['errors']}")

    # Verify configurations
    verification = verify_flow_configurations()
    print("\nVerification results:")
    print(f"Total flows: {verification['total_flows']}")
    print(f"Consistency check: {verification['consistency_check']}")
    print(f"Issues: {verification['issues']}")

    # Get summary
    summary = get_flow_summary()
    print("\nFlow summary:")
    for flow in summary:
        print(f"- {flow['name']}: {flow['phase_count']} phases, v{flow['version']}")

    assert verification["total_flows"] == 9
    assert verification["consistency_check"] is True


if __name__ == "__main__":
    # Run basic test
    test_flow_configurations_basic()
    print("\n✅ All flow configurations tested successfully!")
