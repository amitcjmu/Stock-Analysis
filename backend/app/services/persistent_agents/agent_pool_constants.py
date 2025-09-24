"""
Agent Pool Constants and Configurations

This module contains constants, configurations, and utility functions
for the TenantScopedAgentPool. Extracted to maintain file length limits.
"""

from typing import Dict, List, Any, Tuple

# Default configurations for agent types
AGENT_TYPE_CONFIGS = {
    "discovery_specialist": {
        "role": "Discovery Specialist Agent",
        "goal": "Intelligent asset discovery and mapping for migration planning",
        "backstory": "Expert in cloud and on-premises infrastructure discovery, "
        "with deep knowledge of asset identification and dependency mapping.",
        "tools": ["asset_creation", "data_validation", "critical_attributes"],
        "max_retries": 3,
        "memory_enabled": True,
    },
    "gap_analysis_specialist": {
        "role": "Gap Analysis Specialist Agent",
        "goal": "Comprehensive analysis of data gaps in collected migration assets",
        "backstory": "Expert in identifying missing critical attributes required "
        "for successful cloud migration planning and 6R strategy development.",
        "tools": ["data_validation", "critical_attributes"],
        "max_retries": 3,
        "memory_enabled": True,
    },
    "business_impact_assessor": {
        "role": "Business Impact Assessment Agent",
        "goal": "Assessment of business impact and migration readiness",
        "backstory": "Senior business analyst specializing in migration impact assessment and readiness evaluation.",
        "tools": ["task_completion", "mapping_confidence"],
        "max_retries": 2,
        "memory_enabled": True,
    },
    "quality_validator": {
        "role": "Quality Validation Agent",
        "goal": "Validation of data quality and completeness for migration planning",
        "backstory": "Quality assurance specialist focused on migration data validation and consistency checks.",
        "tools": ["data_validation"],
        "max_retries": 2,
        "memory_enabled": True,
    },
    "dependency_analyst": {
        "role": "Dependency Analysis Agent",
        "goal": "Analysis of application and infrastructure dependencies",
        "backstory": "Expert in mapping complex system dependencies and integration points for migration planning.",
        "tools": ["dependency_analysis", "asset_intelligence"],
        "max_retries": 3,
        "memory_enabled": True,
    },
    "questionnaire_generator": {
        "role": "Adaptive Questionnaire Generation Agent",
        "goal": "Generate intelligent, context-aware questionnaires for data collection based on gaps and asset types",
        "backstory": "Expert in adaptive form generation with deep understanding of migration requirements, "
        "specializing in creating targeted questions that resolve data gaps for all asset types including "
        "applications, infrastructure, databases, and cloud resources.",
        "tools": ["questionnaire_generation", "gap_analysis", "asset_intelligence"],
        "max_retries": 3,
        "memory_enabled": True,
    },
}

# Memory monitoring settings
MEMORY_MONITORING_CONFIG = {
    "check_interval": 300,  # 5 minutes
    "warning_threshold": 0.8,  # 80%
    "critical_threshold": 0.9,  # 90%
    "cleanup_threshold": 0.95,  # 95%
    "max_agents_per_tenant": 10,
}

# Pool management settings
POOL_MANAGEMENT_CONFIG = {
    "max_idle_time": 3600,  # 1 hour
    "cleanup_interval": 600,  # 10 minutes
    "health_check_interval": 300,  # 5 minutes
    "max_pool_size": 100,
    "min_pool_size": 1,
}

# Tool mappings for different agent types
TOOL_MAPPINGS = {
    "asset_creation": "create_asset_creation_tools",
    "task_completion": "create_task_completion_tools",
    "data_validation": "create_data_validation_tools",
    "critical_attributes": "create_critical_attributes_tools",
    "dependency_analysis": "create_dependency_analysis_tools",
    "mapping_confidence": "MappingConfidenceTool",
    "asset_intelligence": "get_asset_intelligence_tools",
    "questionnaire_generation": "create_questionnaire_generation_tools",
    "gap_analysis": "create_gap_analysis_tools",
}


def get_agent_config(agent_type: str) -> Dict[str, Any]:
    """Get configuration for a specific agent type.

    Args:
        agent_type: Type of agent

    Returns:
        Agent configuration dictionary
    """
    return AGENT_TYPE_CONFIGS.get(agent_type, {})


def get_default_agent_tools(agent_type: str) -> List[str]:
    """Get default tools for an agent type.

    Args:
        agent_type: Type of agent

    Returns:
        List of tool names
    """
    config = get_agent_config(agent_type)
    return config.get("tools", [])


def is_memory_enabled_for_agent(agent_type: str) -> bool:
    """Check if memory is enabled for an agent type.

    Args:
        agent_type: Type of agent

    Returns:
        True if memory enabled, False otherwise
    """
    config = get_agent_config(agent_type)
    return config.get("memory_enabled", False)


def get_agent_max_retries(agent_type: str) -> int:
    """Get maximum retries for an agent type.

    Args:
        agent_type: Type of agent

    Returns:
        Maximum number of retries
    """
    config = get_agent_config(agent_type)
    return config.get("max_retries", 3)


def validate_agent_type(agent_type: str) -> bool:
    """Validate if agent type is supported.

    Args:
        agent_type: Type of agent to validate

    Returns:
        True if valid, False otherwise
    """
    return agent_type in AGENT_TYPE_CONFIGS


def get_memory_threshold(threshold_type: str) -> float:
    """Get memory threshold value.

    Args:
        threshold_type: Type of threshold (warning, critical, cleanup)

    Returns:
        Threshold value as float
    """
    key = f"{threshold_type}_threshold"
    return MEMORY_MONITORING_CONFIG.get(key, 0.8)


def get_pool_config(config_key: str) -> Any:
    """Get pool management configuration value.

    Args:
        config_key: Configuration key

    Returns:
        Configuration value
    """
    return POOL_MANAGEMENT_CONFIG.get(config_key)


def build_agent_key(client_id: str, engagement_id: str, agent_type: str) -> str:
    """Build unique key for agent identification.

    Args:
        client_id: Client account ID
        engagement_id: Engagement ID
        agent_type: Type of agent

    Returns:
        Unique agent key
    """
    return f"{client_id}:{engagement_id}:{agent_type}"


def parse_agent_key(agent_key: str) -> Tuple[str, str, str]:
    """Parse agent key into components.

    Args:
        agent_key: Agent key to parse

    Returns:
        Tuple of (client_id, engagement_id, agent_type)
    """
    parts = agent_key.split(":")
    if len(parts) != 3:
        raise ValueError(f"Invalid agent key format: {agent_key}")
    return parts[0], parts[1], parts[2]
