"""
Unit tests for agent tool configuration (Issue #1060).

Tests the declarative configuration pattern for agent tools.
"""

from app.services.persistent_agents.agent_tool_config import (
    AGENT_TOOL_CONFIGS,
    COMMON_TOOL_CATEGORIES,
    TOOL_FACTORIES,
    AgentToolConfig,
    ToolFactoryConfig,
    get_agent_tool_config,
    get_agents_with_category,
    get_all_agent_types,
    get_tool_factory,
    is_configuration_valid,
    validate_configuration,
)


class TestToolFactoryConfig:
    """Tests for ToolFactoryConfig dataclass."""

    def test_default_values(self):
        """Test default values are set correctly."""
        config = ToolFactoryConfig(
            module_path="app.test.module",
            factory_name="test_factory",
        )
        assert config.requires_context is True
        assert config.requires_registry is False
        assert config.is_class is False

    def test_custom_values(self):
        """Test custom values override defaults."""
        config = ToolFactoryConfig(
            module_path="app.test.module",
            factory_name="TestClass",
            requires_context=False,
            requires_registry=True,
            is_class=True,
        )
        assert config.requires_context is False
        assert config.requires_registry is True
        assert config.is_class is True


class TestAgentToolConfig:
    """Tests for AgentToolConfig dataclass."""

    def test_default_values(self):
        """Test default values are set correctly."""
        config = AgentToolConfig(agent_type="test_agent")
        assert config.specific_tools == []
        assert config.common_categories == []
        assert config.description == ""

    def test_custom_values(self):
        """Test custom values are set correctly."""
        config = AgentToolConfig(
            agent_type="custom_agent",
            specific_tools=["tool1", "tool2"],
            common_categories=["data_analysis"],
            description="Custom agent description",
        )
        assert config.agent_type == "custom_agent"
        assert config.specific_tools == ["tool1", "tool2"]
        assert config.common_categories == ["data_analysis"]
        assert config.description == "Custom agent description"


class TestConfigurationValidation:
    """Tests for configuration validation functions."""

    def test_configuration_is_valid(self):
        """All agent tool configurations should be valid."""
        assert is_configuration_valid() is True

    def test_validate_configuration_returns_empty_on_success(self):
        """validate_configuration returns empty list when valid."""
        errors = validate_configuration()
        assert errors == []

    def test_all_agent_types_have_valid_tool_references(self):
        """Every tool referenced by agents should exist in TOOL_FACTORIES."""
        for agent_type, config in AGENT_TOOL_CONFIGS.items():
            for tool_name in config.specific_tools:
                assert (
                    tool_name in TOOL_FACTORIES
                ), f"Agent '{agent_type}' references missing tool '{tool_name}'"

    def test_all_agent_types_have_valid_category_references(self):
        """Every category referenced by agents should exist."""
        for agent_type, config in AGENT_TOOL_CONFIGS.items():
            for category in config.common_categories:
                assert (
                    category in COMMON_TOOL_CATEGORIES
                ), f"Agent '{agent_type}' references missing category '{category}'"

    def test_tool_factories_have_complete_config(self):
        """All tool factories should have module_path and factory_name."""
        for tool_name, factory in TOOL_FACTORIES.items():
            assert factory.module_path, f"Tool '{tool_name}' missing module_path"
            assert factory.factory_name, f"Tool '{tool_name}' missing factory_name"


class TestConfigurationLookups:
    """Tests for configuration lookup functions."""

    def test_get_agent_tool_config_returns_config(self):
        """get_agent_tool_config returns config for known agents."""
        config = get_agent_tool_config("discovery")
        assert config is not None
        assert config.agent_type == "discovery"

    def test_get_agent_tool_config_returns_none_for_unknown(self):
        """get_agent_tool_config returns None for unknown agents."""
        config = get_agent_tool_config("unknown_agent_type")
        assert config is None

    def test_get_tool_factory_returns_factory(self):
        """get_tool_factory returns factory for known tools."""
        factory = get_tool_factory("asset_creation")
        assert factory is not None
        assert (
            "asset_creation" in factory.module_path
            or "creation" in factory.factory_name
        )

    def test_get_tool_factory_returns_none_for_unknown(self):
        """get_tool_factory returns None for unknown tools."""
        factory = get_tool_factory("unknown_tool")
        assert factory is None

    def test_get_all_agent_types(self):
        """get_all_agent_types returns all configured agents."""
        agent_types = get_all_agent_types()
        assert "discovery" in agent_types
        assert "field_mapper" in agent_types
        assert "questionnaire_generator" in agent_types
        assert "six_r_analyzer" in agent_types
        assert "asset_inventory" in agent_types

    def test_get_agents_with_category(self):
        """get_agents_with_category returns correct agents."""
        data_analysis_agents = get_agents_with_category("data_analysis")
        assert "discovery" in data_analysis_agents
        assert "field_mapper" in data_analysis_agents
        assert "asset_inventory" in data_analysis_agents

        business_analysis_agents = get_agents_with_category("business_analysis")
        assert "questionnaire_generator" in business_analysis_agents
        assert "six_r_analyzer" in business_analysis_agents


class TestKnownAgentConfigurations:
    """Tests for specific agent configurations."""

    def test_discovery_agent_config(self):
        """Discovery agent should have correct tools."""
        config = get_agent_tool_config("discovery")
        assert config is not None
        assert "asset_creation" in config.specific_tools
        assert "data_validation" in config.specific_tools
        assert "data_analysis" in config.common_categories

    def test_field_mapper_agent_config(self):
        """Field mapper agent should have correct tools."""
        config = get_agent_tool_config("field_mapper")
        assert config is not None
        assert "mapping_confidence" in config.specific_tools
        assert "critical_attributes" in config.specific_tools
        assert "data_analysis" in config.common_categories

    def test_questionnaire_generator_agent_config(self):
        """Questionnaire generator agent should have correct tools."""
        config = get_agent_tool_config("questionnaire_generator")
        assert config is not None
        assert "questionnaire_generation" in config.specific_tools
        assert "gap_analysis" in config.specific_tools
        assert "asset_intelligence" in config.specific_tools
        assert "business_analysis" in config.common_categories

    def test_six_r_analyzer_agent_config(self):
        """6R analyzer agent should have correct tools."""
        config = get_agent_tool_config("six_r_analyzer")
        assert config is not None
        assert "dependency_analysis" in config.specific_tools
        assert "asset_intelligence" in config.specific_tools
        assert "business_analysis" in config.common_categories

    def test_asset_inventory_agent_config(self):
        """Asset inventory agent should have correct tools."""
        config = get_agent_tool_config("asset_inventory")
        assert config is not None
        assert "asset_creation" in config.specific_tools
        assert "data_validation" in config.specific_tools
        assert "data_analysis" in config.common_categories


class TestToolFactoryPaths:
    """Tests for tool factory module paths."""

    def test_asset_creation_factory_path(self):
        """Asset creation tool has correct factory path."""
        factory = get_tool_factory("asset_creation")
        assert factory is not None
        assert "asset_creation_tool" in factory.module_path
        assert factory.factory_name == "create_asset_creation_tools"

    def test_data_validation_factory_path(self):
        """Data validation tool has correct factory path."""
        factory = get_tool_factory("data_validation")
        assert factory is not None
        assert "data_validation_tool" in factory.module_path
        assert factory.factory_name == "create_data_validation_tools"

    def test_mapping_confidence_is_class(self):
        """Mapping confidence tool is marked as class."""
        factory = get_tool_factory("mapping_confidence")
        assert factory is not None
        assert factory.is_class is True
        assert factory.factory_name == "MappingConfidenceTool"

    def test_asset_intelligence_requires_no_context(self):
        """Asset intelligence tool doesn't require context."""
        factory = get_tool_factory("asset_intelligence")
        assert factory is not None
        assert factory.requires_context is False
