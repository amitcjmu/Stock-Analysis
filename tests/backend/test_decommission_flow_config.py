"""
Test Decommission Flow Configuration
Issue #939: FlowTypeConfig Registration - COMPLETE

Tests for decommission flow configuration per ADR-027 (FlowTypeConfig pattern)
and ADR-025 (child flow service usage).
"""

import pytest

from app.services.child_flow_services import DecommissionChildFlowService
from app.services.flow_configs import get_decommission_flow_config
from app.services.flow_type_registry import FlowTypeRegistry


class TestDecommissionFlowConfig:
    """Test suite for decommission flow configuration"""

    def test_get_decommission_flow_config(self):
        """Test get_decommission_flow_config returns valid FlowTypeConfig"""
        config = get_decommission_flow_config()

        # Basic structure
        assert config.name == "decommission"
        assert config.display_name == "Decommission Flow"
        assert config.version == "2.0.0"
        assert config.description is not None
        assert len(config.description) > 0

        # Per ADR-025: Uses DecommissionChildFlowService
        assert config.child_flow_service == DecommissionChildFlowService

        # Per ADR-025: NO crew_class (deprecated)
        assert config.crew_class is None

    def test_decommission_phases(self):
        """Test decommission flow has correct 3 phases"""
        config = get_decommission_flow_config()

        # Verify 3 phases per ADR-027
        assert len(config.phases) == 3

        # Extract phase names
        phase_names = [phase.name for phase in config.phases]
        expected_phases = [
            "decommission_planning",
            "data_migration",
            "system_shutdown",
        ]
        assert phase_names == expected_phases

    def test_decommission_planning_phase(self):
        """Test decommission_planning phase configuration"""
        config = get_decommission_flow_config()
        phase = config.get_phase_config("decommission_planning")

        assert phase is not None
        assert phase.display_name == "Decommission Planning"
        assert phase.timeout_seconds == 2700  # 45 minutes
        assert phase.can_pause is True
        assert phase.can_skip is False  # Critical phase
        assert phase.can_rollback is True

        # Verify validators
        assert "decommission_validation" in phase.validators
        assert "dependency_validation" in phase.validators

        # Verify handlers
        assert "impact_analysis" in phase.pre_handlers
        assert "plan_approval" in phase.post_handlers

        # Verify retry config
        assert phase.retry_config is not None
        assert phase.retry_config.max_attempts == 5
        assert phase.retry_config.initial_delay_seconds == 10.0

        # Verify outputs
        assert "decommission_plan" in phase.outputs
        assert "dependency_graph" in phase.outputs
        assert "estimated_savings" in phase.outputs

    def test_data_migration_phase(self):
        """Test data_migration phase configuration"""
        config = get_decommission_flow_config()
        phase = config.get_phase_config("data_migration")

        assert phase is not None
        assert phase.display_name == "Data Migration"
        assert phase.timeout_seconds == 7200  # 120 minutes
        assert phase.can_pause is True
        assert phase.can_skip is False  # Cannot skip data migration
        assert phase.can_rollback is True

        # Verify validators
        assert "data_migration_validation" in phase.validators
        assert "integrity_validation" in phase.validators

        # Verify handlers
        assert "data_inventory" in phase.pre_handlers
        assert "migration_verification" in phase.post_handlers

        # Verify dependencies
        assert "decommission_planning" in phase.dependencies

        # Verify outputs
        assert "archived_data_location" in phase.outputs
        assert "migration_report" in phase.outputs
        assert "data_integrity_verification" in phase.outputs

    def test_system_shutdown_phase(self):
        """Test system_shutdown phase configuration"""
        config = get_decommission_flow_config()
        phase = config.get_phase_config("system_shutdown")

        assert phase is not None
        assert phase.display_name == "System Shutdown"
        assert phase.timeout_seconds == 3600  # 60 minutes
        assert phase.can_pause is True
        assert phase.can_skip is False  # Cannot skip shutdown
        assert phase.can_rollback is False  # Point of no return

        # Verify validators
        assert "shutdown_validation" in phase.validators
        assert "completion_validation" in phase.validators

        # Verify handlers
        assert "final_backup" in phase.pre_handlers
        assert "decommission_verification" in phase.post_handlers
        assert phase.completion_handler == "decommission_completion"

        # Verify dependencies
        assert "data_migration" in phase.dependencies

        # Verify outputs
        assert "shutdown_report" in phase.outputs
        assert "audit_log" in phase.outputs
        assert "cost_savings_actual" in phase.outputs

        # Verify point of no return metadata
        assert phase.metadata.get("point_of_no_return") is True

    def test_decommission_capabilities(self):
        """Test decommission flow capabilities"""
        config = get_decommission_flow_config()
        capabilities = config.capabilities

        # Critical capabilities for decommission
        assert capabilities.supports_pause_resume is True
        assert capabilities.supports_rollback is True  # Safety requirement
        assert capabilities.supports_checkpointing is True

        # Decommission-specific constraints
        assert capabilities.supports_branching is False
        assert capabilities.supports_iterations is False  # One-way operation
        assert capabilities.max_iterations == 1
        assert capabilities.supports_parallel_phases is False  # Sequential only

        # Permissions
        assert "decommission.read" in capabilities.required_permissions
        assert "decommission.write" in capabilities.required_permissions
        assert "decommission.execute" in capabilities.required_permissions
        assert "decommission.approve" in capabilities.required_permissions

    def test_decommission_handlers(self):
        """Test decommission flow handlers are configured"""
        config = get_decommission_flow_config()

        assert config.initialization_handler == "decommission_initialization"
        assert config.finalization_handler == "decommission_finalization"
        assert config.error_handler == "decommission_error_handler"

    def test_decommission_metadata(self):
        """Test decommission flow metadata"""
        config = get_decommission_flow_config()
        metadata = config.metadata

        # Critical metadata flags
        assert metadata["category"] == "lifecycle"
        assert metadata["complexity"] == "high"
        assert metadata["irreversible"] is True
        assert metadata["requires_approval"] is True
        assert metadata["compliance_critical"] is True
        assert metadata["cost_savings_tracking"] is True

        # Prerequisites
        assert "assessment" in metadata["prerequisite_flows"]

        # Required agents
        required_agents = metadata["required_agents"]
        assert "decommission_planning_agent" in required_agents
        assert "data_migration_agent" in required_agents
        assert "system_shutdown_agent" in required_agents

        # Estimated duration (45 + 120 + 60 = 225 minutes)
        assert metadata["estimated_duration_minutes"] == 225

    def test_decommission_default_configuration(self):
        """Test decommission flow default configuration"""
        config = get_decommission_flow_config()
        default_config = config.default_configuration

        # Safety configurations
        assert default_config["data_backup_required"] is True
        assert default_config["approval_workflow"] is True
        assert default_config["audit_trail"] is True
        assert default_config["compliance_checks"] is True
        assert default_config["point_of_no_return_warning"] is True
        assert default_config["cost_tracking_enabled"] is True
        assert default_config["agent_collaboration"] is True

    def test_decommission_tags(self):
        """Test decommission flow tags"""
        config = get_decommission_flow_config()

        expected_tags = [
            "decommission",
            "lifecycle",
            "data_migration",
            "compliance",
            "critical",
            "cost_savings",
        ]

        for tag in expected_tags:
            assert tag in config.tags

    def test_decommission_phase_progression(self):
        """Test phase progression logic"""
        config = get_decommission_flow_config()

        # First phase
        first_phase = config.get_next_phase(None)
        assert first_phase == "decommission_planning"

        # Second phase
        second_phase = config.get_next_phase("decommission_planning")
        assert second_phase == "data_migration"

        # Third phase
        third_phase = config.get_next_phase("data_migration")
        assert third_phase == "system_shutdown"

        # No more phases
        no_more = config.get_next_phase("system_shutdown")
        assert no_more is None

    def test_decommission_phase_validation(self):
        """Test phase name validation"""
        config = get_decommission_flow_config()

        # Valid phases
        assert config.is_phase_valid("decommission_planning") is True
        assert config.is_phase_valid("data_migration") is True
        assert config.is_phase_valid("system_shutdown") is True

        # Invalid phases
        assert config.is_phase_valid("invalid_phase") is False
        assert config.is_phase_valid("") is False

    def test_decommission_phase_indices(self):
        """Test phase index retrieval"""
        config = get_decommission_flow_config()

        assert config.get_phase_index("decommission_planning") == 0
        assert config.get_phase_index("data_migration") == 1
        assert config.get_phase_index("system_shutdown") == 2
        assert config.get_phase_index("invalid_phase") == -1

    def test_decommission_config_validation(self):
        """Test flow configuration validation"""
        config = get_decommission_flow_config()

        # Should have no validation errors
        errors = config.validate()
        assert len(errors) == 0

    def test_decommission_registry_integration(self):
        """Test decommission flow can be registered in FlowTypeRegistry"""
        from app.services.flow_configs import initialize_all_flows

        # Initialize all flows (includes decommission)
        results = initialize_all_flows()

        # Check decommission was registered
        if results.get("status") != "already_initialized":
            assert "decommission" in results["flows_registered"]
            assert len(results["errors"]) == 0

        # Verify can retrieve from registry
        flow_registry = FlowTypeRegistry()
        assert flow_registry.is_registered("decommission")

        # Get config from registry
        registered_config = flow_registry.get_flow_config("decommission")
        assert registered_config.name == "decommission"
        assert registered_config.child_flow_service == DecommissionChildFlowService

    def test_decommission_child_flow_service_reference(self):
        """Test child_flow_service is correctly set per ADR-025"""
        config = get_decommission_flow_config()

        # Per ADR-025: child_flow_service must be DecommissionChildFlowService
        assert config.child_flow_service is not None
        assert config.child_flow_service == DecommissionChildFlowService

        # Verify it's a class reference, not an instance
        assert isinstance(config.child_flow_service, type)

        # Per ADR-025: NO crew_class (deprecated pattern)
        assert config.crew_class is None

    def test_decommission_phase_timeouts(self):
        """Test all phases have appropriate timeouts"""
        config = get_decommission_flow_config()

        for phase in config.phases:
            # All phases should have timeout configured
            assert phase.timeout_seconds > 0

            # Verify timeout matches expected duration
            if phase.expected_duration_minutes:
                expected_timeout = phase.expected_duration_minutes * 60
                assert phase.timeout_seconds == expected_timeout

    def test_decommission_phase_retry_configs(self):
        """Test all phases have retry configurations"""
        config = get_decommission_flow_config()

        for phase in config.phases:
            # All phases should have retry config
            assert phase.retry_config is not None

            # Conservative retry for critical operations
            assert phase.retry_config.max_attempts == 5
            assert phase.retry_config.initial_delay_seconds == 10.0
            assert phase.retry_config.max_delay_seconds == 600.0

    def test_decommission_success_criteria(self):
        """Test all phases have success criteria defined"""
        config = get_decommission_flow_config()

        for phase in config.phases:
            # All phases should have success criteria
            assert phase.success_criteria is not None
            assert len(phase.success_criteria) > 0

            # Verify meaningful criteria
            assert any(
                value is True or value is not None
                for value in phase.success_criteria.values()
            )


def test_decommission_flow_basic():
    """Basic test that can be run directly"""
    config = get_decommission_flow_config()

    print(f"\nDecommission Flow: {config.display_name} v{config.version}")
    print(f"Description: {config.description}")
    print(f"Phases: {len(config.phases)}")

    for i, phase in enumerate(config.phases, 1):
        print(
            f"  {i}. {phase.display_name} ({phase.name}) - {phase.expected_duration_minutes}min"
        )
        print(f"     Validators: {', '.join(phase.validators)}")
        print(f"     Can rollback: {phase.can_rollback}")

    print(f"\nChild Flow Service: {config.child_flow_service.__name__}")
    print(f"Crew Class: {config.crew_class} (should be None per ADR-025)")

    # Verify critical aspects
    assert config.name == "decommission"
    assert len(config.phases) == 3
    assert config.child_flow_service == DecommissionChildFlowService
    assert config.crew_class is None

    print("\n✅ Decommission flow configuration is valid!")


if __name__ == "__main__":
    # Run basic test
    test_decommission_flow_basic()
