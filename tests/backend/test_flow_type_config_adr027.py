"""
Test FlowTypeConfig Pattern (ADR-027)
Tests for Universal FlowTypeConfig Migration

Verifies:
- FlowTypeConfig registry initialization
- Phase configuration retrieval
- Phase alias normalization
- DiscoveryChildFlowService FlowTypeConfig integration
- Feature flag behavior
- API endpoint functionality
"""

import pytest
from unittest.mock import Mock

from app.core.config import settings
from app.core.context import RequestContext
from app.services.child_flow_services.discovery import DiscoveryChildFlowService
from app.services.flow_configs.phase_aliases import (
    normalize_phase_name,
    get_phase_flow_type,
)
from app.services.flow_type_registry import FlowTypeRegistry
from app.services.flow_type_registry_helpers import (
    get_flow_config,
    get_all_flow_configs,
    initialize_default_flow_configs,
    is_flow_registered,
)


class TestFlowTypeConfigRegistration:
    """Test FlowTypeConfig registry initialization and configuration"""

    def test_initialize_default_flow_configs(self):
        """Test that default flow configs can be initialized"""
        # Initialize configs
        initialize_default_flow_configs()

        # Verify all expected flows are registered
        assert is_flow_registered("discovery")
        assert is_flow_registered("collection")
        assert is_flow_registered("assessment")

    def test_get_flow_config_discovery(self):
        """Test Discovery flow configuration retrieval"""
        initialize_default_flow_configs()

        config = get_flow_config("discovery")

        assert config.name == "discovery"
        assert config.display_name == "Discovery Flow"
        assert config.version == "3.0.0"  # ADR-027 version
        assert len(config.phases) == 5  # Reduced from 9 to 5

        # Verify phase names
        phase_names = [p.name for p in config.phases]
        expected_phases = [
            "data_import",
            "data_validation",
            "field_mapping",
            "data_cleansing",
            "asset_inventory",
        ]
        assert phase_names == expected_phases

    def test_get_flow_config_assessment(self):
        """Test Assessment flow configuration retrieval"""
        initialize_default_flow_configs()

        config = get_flow_config("assessment")

        assert config.name == "assessment"
        assert config.display_name == "Assessment Flow"
        assert config.version == "3.0.0"  # ADR-027 version
        assert len(config.phases) == 6  # Expanded from 4 to 6

        # Verify phase names include migrated phases
        phase_names = [p.name for p in config.phases]
        assert "dependency_analysis" in phase_names
        assert "tech_debt_assessment" in phase_names

    def test_get_flow_config_invalid(self):
        """Test that invalid flow type raises ValueError"""
        initialize_default_flow_configs()

        with pytest.raises(ValueError, match="not registered"):
            get_flow_config("invalid_flow_type")

    def test_get_all_flow_configs(self):
        """Test retrieving all flow configs"""
        initialize_default_flow_configs()

        configs = get_all_flow_configs()

        assert len(configs) >= 3
        config_names = [c.name for c in configs]
        assert "discovery" in config_names
        assert "collection" in config_names
        assert "assessment" in config_names


class TestPhaseConfiguration:
    """Test individual phase configurations"""

    def test_discovery_phase_metadata(self):
        """Test Discovery phase metadata"""
        initialize_default_flow_configs()

        config = get_flow_config("discovery")

        # Test data_import phase
        data_import_phase = config.phases[0]
        assert data_import_phase.name == "data_import"
        assert data_import_phase.display_name == "Data Import & Validation"
        assert data_import_phase.can_pause is True
        assert data_import_phase.can_skip is False
        assert "ui_route" in data_import_phase.metadata
        assert "estimated_duration_minutes" in data_import_phase.metadata

    def test_phase_crew_config(self):
        """Test that phases have crew configurations"""
        initialize_default_flow_configs()

        config = get_flow_config("discovery")

        for phase in config.phases:
            assert phase.crew_config is not None
            assert "crew_type" in phase.crew_config
            assert "execution_config" in phase.crew_config
            # Verify memory is disabled per ADR-024
            assert phase.crew_config["execution_config"]["enable_memory"] is False

    def test_assessment_migrated_phases(self):
        """Test that migrated phases have proper metadata"""
        initialize_default_flow_configs()

        config = get_flow_config("assessment")

        # Find dependency_analysis phase
        dep_phase = next(p for p in config.phases if p.name == "dependency_analysis")
        assert "migration_note" in dep_phase.metadata
        assert "Moved from Discovery" in dep_phase.metadata["migration_note"]

        # Find tech_debt_assessment phase
        tech_debt_phase = next(
            p for p in config.phases if p.name == "tech_debt_assessment"
        )
        assert "migration_note" in tech_debt_phase.metadata


class TestPhaseAliases:
    """Test phase alias normalization system"""

    def test_normalize_canonical_phase_name(self):
        """Test that canonical names pass through unchanged"""
        initialize_default_flow_configs()

        result = normalize_phase_name("discovery", "data_import")
        assert result == "data_import"

        result = normalize_phase_name("discovery", "field_mapping")
        assert result == "field_mapping"

    def test_normalize_legacy_phase_names(self):
        """Test that legacy names are normalized"""
        initialize_default_flow_configs()

        # Test legacy name mapping
        result = normalize_phase_name("discovery", "data_cleaning")
        assert result == "data_cleansing"

        result = normalize_phase_name("discovery", "assets")
        assert result == "asset_inventory"

    def test_normalize_invalid_phase(self):
        """Test that invalid phases raise ValueError"""
        initialize_default_flow_configs()

        with pytest.raises(ValueError, match="Unknown phase"):
            normalize_phase_name("discovery", "invalid_phase_name")

    def test_get_phase_flow_type(self):
        """Test determining which flow a phase belongs to"""
        initialize_default_flow_configs()

        # Discovery phase
        flow_type = get_phase_flow_type("data_import")
        assert flow_type == "discovery"

        # Assessment phase
        flow_type = get_phase_flow_type("dependency_analysis")
        assert flow_type == "assessment"

        # Invalid phase
        flow_type = get_phase_flow_type("non_existent_phase")
        assert flow_type is None


class TestDiscoveryChildFlowService:
    """Test DiscoveryChildFlowService FlowTypeConfig integration"""

    def setup_method(self):
        """Setup for each test method"""
        initialize_default_flow_configs()

        # Create mock context
        self.context = RequestContext(
            client_account_id=1, engagement_id=1, user_id="test-user"
        )

        # Create service with mock db
        self.service = DiscoveryChildFlowService(None, self.context)

    def test_get_all_phases(self):
        """Test retrieving all phases from FlowTypeConfig"""
        phases = self.service.get_all_phases()

        assert len(phases) == 5
        assert phases == [
            "data_import",
            "data_validation",
            "field_mapping",
            "data_cleansing",
            "asset_inventory",
        ]

    def test_validate_phase_valid(self):
        """Test validating valid phase names"""
        assert self.service.validate_phase("data_import") is True
        assert self.service.validate_phase("field_mapping") is True
        assert self.service.validate_phase("asset_inventory") is True

    def test_validate_phase_invalid(self):
        """Test validating invalid phase names"""
        assert self.service.validate_phase("invalid_phase") is False
        assert self.service.validate_phase("dependency_analysis") is False  # Moved to Assessment

    def test_get_phase_config(self):
        """Test retrieving phase configuration"""
        phase_config = self.service.get_phase_config("field_mapping")

        assert phase_config is not None
        assert phase_config.name == "field_mapping"
        assert phase_config.display_name == "Field Mapping & Transformation"
        assert phase_config.can_pause is True

    def test_get_phase_metadata(self):
        """Test retrieving phase metadata"""
        metadata = self.service.get_phase_metadata("field_mapping")

        assert metadata is not None
        assert metadata["name"] == "field_mapping"
        assert metadata["display_name"] == "Field Mapping & Transformation"
        assert "ui_route" in metadata
        assert "estimated_duration_minutes" in metadata
        assert metadata["can_pause"] is True

    def test_get_phase_metadata_invalid(self):
        """Test that invalid phase returns None"""
        metadata = self.service.get_phase_metadata("invalid_phase")
        assert metadata is None

    def test_get_next_phase(self):
        """Test phase progression"""
        # First phase
        next_phase = self.service.get_next_phase("data_import")
        assert next_phase == "data_validation"

        # Middle phase
        next_phase = self.service.get_next_phase("field_mapping")
        assert next_phase == "data_cleansing"

        # Last phase
        next_phase = self.service.get_next_phase("asset_inventory")
        assert next_phase is None

    def test_get_next_phase_invalid(self):
        """Test that invalid phase returns None"""
        next_phase = self.service.get_next_phase("invalid_phase")
        assert next_phase is None


class TestFeatureFlags:
    """Test feature flag behavior"""

    def test_use_flow_type_config_default(self):
        """Test that USE_FLOW_TYPE_CONFIG defaults to True"""
        assert settings.USE_FLOW_TYPE_CONFIG is True

    def test_legacy_phase_sequences_default(self):
        """Test that LEGACY_PHASE_SEQUENCES_ENABLED defaults to False"""
        assert settings.LEGACY_PHASE_SEQUENCES_ENABLED is False

    def test_feature_flags_exist(self):
        """Test that feature flags are accessible"""
        # Should not raise AttributeError
        use_config = settings.USE_FLOW_TYPE_CONFIG
        legacy_enabled = settings.LEGACY_PHASE_SEQUENCES_ENABLED

        assert isinstance(use_config, bool)
        assert isinstance(legacy_enabled, bool)


class TestFlowTypeConfigBackwardCompatibility:
    """Test backward compatibility features"""

    def test_discovery_phases_removed(self):
        """Test that dependency_analysis and tech_debt_assessment are removed from Discovery"""
        initialize_default_flow_configs()

        config = get_flow_config("discovery")
        phase_names = [p.name for p in config.phases]

        assert "dependency_analysis" not in phase_names
        assert "tech_debt_assessment" not in phase_names

    def test_assessment_phases_added(self):
        """Test that dependency_analysis and tech_debt_assessment are in Assessment"""
        initialize_default_flow_configs()

        config = get_flow_config("assessment")
        phase_names = [p.name for p in config.phases]

        assert "dependency_analysis" in phase_names
        assert "tech_debt_assessment" in phase_names

    def test_phase_metadata_includes_version(self):
        """Test that flow configs include version 3.0.0"""
        initialize_default_flow_configs()

        discovery = get_flow_config("discovery")
        assessment = get_flow_config("assessment")

        assert discovery.version == "3.0.0"
        assert assessment.version == "3.0.0"


class TestFlowTypeRegistry:
    """Test FlowTypeRegistry singleton behavior"""

    def test_registry_singleton(self):
        """Test that registry is a singleton"""
        registry1 = FlowTypeRegistry()
        registry2 = FlowTypeRegistry()

        assert registry1 is registry2

    def test_registry_list_flow_types(self):
        """Test listing registered flow types"""
        initialize_default_flow_configs()

        registry = FlowTypeRegistry()
        flow_types = registry.list_flow_types()

        assert "discovery" in flow_types
        assert "collection" in flow_types
        assert "assessment" in flow_types


# Integration test
@pytest.mark.integration
class TestFlowTypeConfigIntegration:
    """Integration tests for FlowTypeConfig pattern"""

    def test_full_discovery_flow_config(self):
        """Test complete Discovery flow configuration"""
        initialize_default_flow_configs()

        config = get_flow_config("discovery")

        # Verify all phases have required attributes
        for phase in config.phases:
            assert phase.name
            assert phase.display_name
            assert phase.description
            assert phase.crew_config
            assert "ui_route" in phase.metadata

        # Verify capabilities
        assert config.capabilities.supports_pause_resume is True
        assert config.capabilities.supports_checkpointing is True

        # Verify handlers
        assert config.initialization_handler
        assert config.finalization_handler
        assert config.error_handler

    def test_phase_order_consistency(self):
        """Test that phase order is preserved"""
        initialize_default_flow_configs()

        config = get_flow_config("discovery")
        phases = [p.name for p in config.phases]

        # Verify order
        assert phases.index("data_import") < phases.index("data_validation")
        assert phases.index("data_validation") < phases.index("field_mapping")
        assert phases.index("field_mapping") < phases.index("data_cleansing")
        assert phases.index("data_cleansing") < phases.index("asset_inventory")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
