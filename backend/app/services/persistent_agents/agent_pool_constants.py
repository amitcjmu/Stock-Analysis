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
        "memory_enabled": False,  # Per ADR-024: Use TenantMemoryManager instead
    },
    "gap_analysis_specialist": {
        "role": "Gap Analysis Specialist Agent",
        "goal": "Comprehensive analysis of data gaps in collected migration assets",
        "backstory": "Expert in identifying missing critical attributes required "
        "for successful cloud migration planning and 6R strategy development.",
        "tools": [],  # No tools - direct JSON output required for gap enhancement
        "max_retries": 3,
        "memory_enabled": False,  # Per ADR-024: Use TenantMemoryManager instead
        "llm_config": {  # Per ADR-037: Large context for comprehensive gap analysis
            "provider": "deepinfra",
            "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
            "max_tokens": 16384,  # 4x default - handles 10-15 assets with comprehensive gaps
        },
    },
    "business_impact_assessor": {
        "role": "Business Impact Assessment Agent",
        "goal": "Assessment of business impact and migration readiness",
        "backstory": "Senior business analyst specializing in migration impact assessment and readiness evaluation.",
        "tools": ["task_completion", "mapping_confidence"],
        "max_retries": 2,
        "memory_enabled": False,  # Per ADR-024: Use TenantMemoryManager instead
    },
    "quality_validator": {
        "role": "Quality Validation Agent",
        "goal": "Validation of data quality and completeness for migration planning",
        "backstory": "Quality assurance specialist focused on migration data validation and consistency checks.",
        "tools": ["data_validation"],
        "max_retries": 2,
        "memory_enabled": False,  # Per ADR-024: Use TenantMemoryManager instead
    },
    "dependency_analyst": {
        "role": "Dependency Analysis Agent",
        "goal": "Analysis of application and infrastructure dependencies",
        "backstory": "Expert in mapping complex system dependencies and integration points for migration planning.",
        "tools": ["dependency_analysis", "asset_intelligence"],
        "max_retries": 3,
        "memory_enabled": False,  # Per ADR-024: Use TenantMemoryManager instead
    },
    "questionnaire_generator": {
        "role": "Adaptive Questionnaire Generation Agent",
        "goal": "Generate intelligent, context-aware questionnaires for data collection based on gaps and asset types",
        "backstory": "Expert in adaptive form generation with deep understanding of migration requirements, "
        "specializing in creating targeted questions that resolve data gaps for all asset types including "
        "applications, infrastructure, databases, and cloud resources.",
        "tools": [],  # Per ADR-037 #1114: Remove tools - gaps provided in prompt
        "max_retries": 3,
        "memory_enabled": False,  # Per ADR-024: Use TenantMemoryManager instead
    },
    # Assessment Flow Agents
    "readiness_assessor": {
        "role": "Migration Readiness Assessment Agent",
        "goal": "Assess migration readiness of discovered assets using architecture standards and technical analysis",
        "backstory": "Expert in cloud migration readiness evaluation with deep knowledge of AWS Well-Architected "
        "Framework, Azure Cloud Adoption Framework, and enterprise architecture standards. Specializes in "
        "identifying technical, operational, and security readiness gaps.",
        "tools": ["asset_intelligence", "data_validation", "critical_attributes"],
        "max_retries": 3,
        "memory_enabled": False,  # Per ADR-024: Use TenantMemoryManager instead
        "llm_config": {
            "provider": "deepinfra",
            "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        },
    },
    "complexity_analyst": {
        "role": "Migration Complexity Analysis Agent",
        "goal": "Analyze migration complexity for each asset using comprehensive component and technical debt analysis",
        "backstory": "Senior technical analyst specializing in migration complexity assessment, technical debt "
        "quantification, and component-level analysis. Expert in identifying integration complexity, "
        "customization impact, and modernization opportunities.",
        "tools": ["dependency_analysis", "asset_intelligence", "data_validation"],
        "max_retries": 3,
        "memory_enabled": False,  # Per ADR-024: Use TenantMemoryManager instead
        "llm_config": {
            "provider": "deepinfra",
            "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        },
    },
    "risk_assessor": {
        "role": "Migration Risk Assessment Agent",
        "goal": "Assess migration risks and develop mitigation strategies using enhanced 6R analysis",
        "backstory": "Risk management specialist with expertise in cloud migration risk assessment, 6R strategy "
        "evaluation (Rehost, Replatform, Repurchase, Refactor, Retire, Retain), and mitigation planning. "
        "Deep knowledge of technical, business, and compliance risks.",
        "tools": ["dependency_analysis", "critical_attributes", "asset_intelligence"],
        "max_retries": 3,
        "memory_enabled": False,  # Per ADR-024: Use TenantMemoryManager instead
        "llm_config": {
            "provider": "deepinfra",
            "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        },
    },
    "recommendation_generator": {
        "role": "Migration Recommendation Generation Agent",
        "goal": "Generate comprehensive migration recommendations based on readiness, complexity, and risk assessments",
        "backstory": "Strategic migration advisor with extensive experience in cloud migration planning, "
        "wave planning, and migration strategy development. Expert in synthesizing technical assessments "
        "into actionable migration roadmaps.",
        "tools": ["asset_intelligence", "dependency_analysis", "critical_attributes"],
        "max_retries": 3,
        "memory_enabled": False,  # Per ADR-024: Use TenantMemoryManager instead
        "llm_config": {
            "provider": "deepinfra",
            "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        },
    },
    # Planning Flow Agents
    "wave_planning_specialist": {
        "role": "Wave Planning Specialist Agent",
        "goal": "Create optimized migration wave plans that group applications by dependencies, risk, and complexity",
        "backstory": "Expert migration strategist with 15+ years experience in enterprise cloud migrations. "
        "Specializes in dependency-aware wave planning, risk mitigation, and resource optimization. "
        "Creates wave plans that minimize downtime and maximize parallel execution.",
        "tools": [],  # Direct JSON output for wave planning
        "max_retries": 3,
        "memory_enabled": False,  # Per ADR-024: Use TenantMemoryManager instead
        "llm_config": {
            "provider": "deepinfra",
            "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
            "max_tokens": 16384,  # Large output for comprehensive wave plans
        },
    },
    # Decommission Flow Agents (7 agents per DECOMMISSION_FLOW_SOLUTION.md)
    "decommission_system_analyst": {
        "role": "System Dependency Analysis Specialist",
        "goal": "Identify all system dependencies and impact zones to prevent downstream failures during decommissioning",
        "backstory": "Expert in enterprise architecture with 15+ years analyzing system dependencies. "
        "Creates comprehensive dependency maps to ensure safe decommissioning without impacting dependent systems. "
        "Specializes in identifying hidden integrations, API dependencies, and data flows.",
        "tools": [],  # Uses tools via task context
        "max_retries": 3,
        "memory_enabled": False,  # Per ADR-024: Use TenantMemoryManager instead
        "llm_config": {
            "provider": "deepinfra",
            "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        },
    },
    "decommission_dependency_mapper": {
        "role": "System Relationship Mapping Specialist",
        "goal": "Map complex system relationships and integration points to ensure complete dependency coverage",
        "backstory": "20+ years in IT architecture, specialized in mapping complex system integrations. "
        "Expert in visualizing dependency graphs, identifying critical paths, and assessing cascade impacts. "
        "Creates dependency maps used by Fortune 500 companies for safe system retirements.",
        "tools": [],
        "max_retries": 3,
        "memory_enabled": False,  # Per ADR-024
        "llm_config": {
            "provider": "deepinfra",
            "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        },
    },
    "decommission_data_retention": {
        "role": "Data Retention and Archival Compliance Specialist",
        "goal": "Ensure data retention compliance and secure archival before system decommissioning",
        "backstory": "Compliance expert with deep knowledge of GDPR, SOX, HIPAA, and PCI-DSS. "
        "Creates retention policies that balance legal requirements with storage optimization. "
        "15+ years managing enterprise data archival for regulated industries.",
        "tools": [],
        "max_retries": 3,
        "memory_enabled": False,  # Per ADR-024
        "llm_config": {
            "provider": "deepinfra",
            "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        },
    },
    "decommission_compliance": {
        "role": "Regulatory Compliance Validation Specialist",
        "goal": "Ensure all decommission activities meet regulatory compliance requirements (GDPR, SOX, HIPAA, PCI-DSS)",
        "backstory": "Regulatory compliance officer with expertise in multi-jurisdiction compliance frameworks. "
        "Validates that decommission processes meet all regulatory requirements including data retention, "
        "audit trails, and secure data disposal. Works closely with legal teams to ensure zero compliance gaps.",
        "tools": [],
        "max_retries": 3,
        "memory_enabled": False,  # Per ADR-024
        "llm_config": {
            "provider": "deepinfra",
            "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        },
    },
    "decommission_shutdown_orchestrator": {
        "role": "Safe System Shutdown Orchestration Specialist",
        "goal": "Execute graceful system shutdowns with zero data loss and automated rollback capabilities",
        "backstory": "Infrastructure automation expert with zero-downtime deployment expertise. "
        "Implements safety checks, gradual shutdowns, and automated rollback for risk-free decommissioning. "
        "Has safely decommissioned 1000+ enterprise systems with 100% success rate.",
        "tools": [],
        "max_retries": 3,
        "memory_enabled": False,  # Per ADR-024
        "llm_config": {
            "provider": "deepinfra",
            "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        },
    },
    "decommission_validator": {
        "role": "Post-Decommission Verification and Cleanup Specialist",
        "goal": "Verify successful decommission completion and ensure complete resource cleanup",
        "backstory": "Quality assurance engineer specialized in infrastructure validation. "
        "Performs comprehensive checks to ensure complete system removal and resource cleanup. "
        "Expert in detecting residual configurations, orphaned resources, and incomplete shutdowns.",
        "tools": [],
        "max_retries": 3,
        "memory_enabled": False,  # Per ADR-024
        "llm_config": {
            "provider": "deepinfra",
            "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        },
    },
    "decommission_rollback": {
        "role": "Decommission Rollback and Recovery Specialist",
        "goal": "Handle rollback scenarios for failed decommissions and restore system state",
        "backstory": "Disaster recovery specialist with expertise in system restoration and rollback procedures. "
        "Creates comprehensive rollback plans and executes recovery operations with minimal downtime. "
        "Expert in state preservation, backup validation, and point-in-time recovery.",
        "tools": [],
        "max_retries": 3,
        "memory_enabled": False,  # Per ADR-024
        "llm_config": {
            "provider": "deepinfra",
            "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        },
    },
}

# Assessment phase-to-agent mapping (for execution engine)
ASSESSMENT_PHASE_AGENT_MAPPING = {
    "readiness_assessment": "readiness_assessor",
    "complexity_analysis": "complexity_analyst",
    "dependency_analysis": "dependency_analyst",
    "tech_debt_assessment": "complexity_analyst",  # Reuse complexity agent for tech debt
    "risk_assessment": "risk_assessor",
    "recommendation_generation": "recommendation_generator",
}

# Planning phase-to-agent mapping
PLANNING_PHASE_AGENT_MAPPING = {
    "wave_planning": "wave_planning_specialist",
}

# Decommission phase-to-agent mapping (per DECOMMISSION_FLOW_SOLUTION.md Section 4.0)
# Phase 1: decommission_planning -> system analysis + dependency mapping
# Phase 2: data_migration -> data retention + compliance
# Phase 3: system_shutdown -> shutdown orchestrator + validator + rollback
DECOMMISSION_PHASE_AGENT_MAPPING = {
    "decommission_planning": [
        "decommission_system_analyst",
        "decommission_dependency_mapper",
    ],
    "data_migration": [
        "decommission_data_retention",
        "decommission_compliance",
    ],
    "system_shutdown": [
        "decommission_shutdown_orchestrator",
        "decommission_validator",
        "decommission_rollback",
    ],
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
