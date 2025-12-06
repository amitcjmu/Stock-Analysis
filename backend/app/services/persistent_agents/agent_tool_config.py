"""
Declarative Agent Tool Configuration - Issue #1060

Single source of truth for agent-tool mappings. This module centralizes all
agent tool configurations, eliminating scattered if/elif blocks and improving
maintainability.

Benefits:
- All agent-tool mappings in one place
- Easy to add new agent types (just add dictionary entry)
- Configuration validation at startup
- Better testability
- No string literal typos (validated references)
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# Type alias for tool factory functions
ToolFactoryFunc = Callable[[Dict[str, Any]], List[Any]]


@dataclass
class ToolFactoryConfig:
    """Configuration for a tool factory function."""

    module_path: str
    factory_name: str
    requires_context: bool = True
    requires_registry: bool = False
    is_class: bool = False  # True if factory is a class to instantiate


@dataclass
class AgentToolConfig:
    """Complete tool configuration for an agent type."""

    agent_type: str
    specific_tools: List[str] = field(default_factory=list)
    common_categories: List[str] = field(default_factory=list)
    description: str = ""


# Tool factory registry - maps tool name to import path and factory function
TOOL_FACTORIES: Dict[str, ToolFactoryConfig] = {
    # Asset and data tools
    "asset_creation": ToolFactoryConfig(
        module_path="app.services.crewai_flows.tools.asset_creation_tool",
        factory_name="create_asset_creation_tools",
    ),
    "data_validation": ToolFactoryConfig(
        module_path="app.services.crewai_flows.tools.data_validation_tool",
        factory_name="create_data_validation_tools",
    ),
    # Field mapping tools
    "mapping_confidence": ToolFactoryConfig(
        module_path="app.services.crewai_flows.tools.mapping_confidence_tool",
        factory_name="MappingConfidenceTool",
        is_class=True,
    ),
    "critical_attributes": ToolFactoryConfig(
        module_path="app.services.crewai_flows.tools.critical_attributes_tool",
        factory_name="create_critical_attributes_tools",
    ),
    # Questionnaire and gap analysis tools
    "questionnaire_generation": ToolFactoryConfig(
        module_path="app.services.ai_analysis.questionnaire_generator.tools",
        factory_name="create_questionnaire_generation_tools",
    ),
    "gap_analysis": ToolFactoryConfig(
        module_path="app.services.ai_analysis.questionnaire_generator.tools",
        factory_name="create_gap_analysis_tools",
    ),
    # Intelligence and analysis tools
    "asset_intelligence": ToolFactoryConfig(
        module_path="app.services.tools.asset_intelligence_tools",
        factory_name="get_asset_intelligence_tools",
        requires_context=False,
    ),
    "dependency_analysis": ToolFactoryConfig(
        module_path="app.services.crewai_flows.tools.dependency_analysis_tool",
        factory_name="create_dependency_analysis_tools",
    ),
    # Issue #1243: Three-level compliance validation tools
    "eol_catalog_lookup": ToolFactoryConfig(
        module_path="app.services.persistent_agents.tools.eol_catalog_lookup_tool",
        factory_name="create_eol_catalog_lookup_tools",
        requires_registry=True,
    ),
    "rag_eol_enrichment": ToolFactoryConfig(
        module_path="app.services.persistent_agents.tools.rag_eol_enrichment_tool",
        factory_name="create_rag_eol_enrichment_tools",
        requires_registry=True,
    ),
    "asset_product_linker": ToolFactoryConfig(
        module_path="app.services.persistent_agents.tools.asset_product_linker_tool",
        factory_name="create_asset_product_linker_tools",
        requires_registry=True,
    ),
}


# Agent-specific tool configurations
AGENT_TOOL_CONFIGS: Dict[str, AgentToolConfig] = {
    "discovery": AgentToolConfig(
        agent_type="discovery",
        specific_tools=["asset_creation", "data_validation"],
        common_categories=["data_analysis"],
        description="Discovery agent for data analysis and asset creation",
    ),
    "field_mapper": AgentToolConfig(
        agent_type="field_mapper",
        specific_tools=["mapping_confidence", "critical_attributes"],
        common_categories=["data_analysis"],
        description="Field mapping agent for data transformation",
    ),
    "questionnaire_generator": AgentToolConfig(
        agent_type="questionnaire_generator",
        specific_tools=[
            "questionnaire_generation",
            "gap_analysis",
            "asset_intelligence",
        ],
        common_categories=["business_analysis"],
        description="Questionnaire generation agent for gap analysis",
    ),
    "business_value_analyst": AgentToolConfig(
        agent_type="business_value_analyst",
        specific_tools=[
            "gap_analysis",
            "questionnaire_generation",
            "asset_intelligence",
        ],
        common_categories=[],
        description="Business value analysis agent",
    ),
    "six_r_analyzer": AgentToolConfig(
        agent_type="six_r_analyzer",
        specific_tools=["dependency_analysis", "asset_intelligence"],
        common_categories=["business_analysis"],
        description="6R strategy analysis agent",
    ),
    "asset_inventory": AgentToolConfig(
        agent_type="asset_inventory",
        specific_tools=["asset_creation", "data_validation"],
        common_categories=["data_analysis"],
        description="Asset inventory management agent",
    ),
    "data_cleansing": AgentToolConfig(
        agent_type="data_cleansing",
        specific_tools=[],
        common_categories=["data_analysis"],
        description="Data cleansing agent",
    ),
    # Issue #1243: Three-level compliance validation agent
    "compliance_validator": AgentToolConfig(
        agent_type="compliance_validator",
        specific_tools=[
            "eol_catalog_lookup",
            "rag_eol_enrichment",
            "asset_product_linker",
        ],
        common_categories=[],  # No common categories - dedicated compliance tools only
        description="Multi-level technology compliance validation agent for EOL and architecture standards",
    ),
}


# Common tool category configurations
# Maps category name to list of tool adder method names
COMMON_TOOL_CATEGORIES: Dict[str, str] = {
    "data_analysis": "add_data_analysis_tools",
    "business_analysis": "add_business_analysis_tools",
}


def get_agent_tool_config(agent_type: str) -> Optional[AgentToolConfig]:
    """Get tool configuration for an agent type."""
    return AGENT_TOOL_CONFIGS.get(agent_type)


def get_tool_factory(tool_name: str) -> Optional[ToolFactoryConfig]:
    """Get factory configuration for a tool."""
    return TOOL_FACTORIES.get(tool_name)


def get_all_agent_types() -> Set[str]:
    """Get all configured agent types."""
    return set(AGENT_TOOL_CONFIGS.keys())


def get_agents_with_category(category: str) -> List[str]:
    """Get all agent types that use a specific tool category."""
    return [
        config.agent_type
        for config in AGENT_TOOL_CONFIGS.values()
        if category in config.common_categories
    ]


def validate_configuration() -> List[str]:
    """
    Validate that all agent tool configurations are valid.

    Returns:
        List of validation error messages (empty if valid)
    """
    errors: List[str] = []

    # Check all agent types have valid tool references
    for agent_type, config in AGENT_TOOL_CONFIGS.items():
        for tool_name in config.specific_tools:
            if tool_name not in TOOL_FACTORIES:
                errors.append(
                    f"Agent '{agent_type}' references unknown tool '{tool_name}'"
                )

        for category in config.common_categories:
            if category not in COMMON_TOOL_CATEGORIES:
                errors.append(
                    f"Agent '{agent_type}' references unknown category '{category}'"
                )

    # Check tool factory module paths are valid format
    for tool_name, factory in TOOL_FACTORIES.items():
        if not factory.module_path or not factory.factory_name:
            errors.append(f"Tool '{tool_name}' has incomplete factory configuration")

    if errors:
        for error in errors:
            logger.error(f"Configuration validation error: {error}")
    else:
        logger.info(
            f"Agent tool configuration validated: "
            f"{len(AGENT_TOOL_CONFIGS)} agents, {len(TOOL_FACTORIES)} tool factories"
        )

    return errors


def is_configuration_valid() -> bool:
    """Check if configuration is valid (no errors)."""
    return len(validate_configuration()) == 0
