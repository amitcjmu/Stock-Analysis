"""
Decommission Agent Configurations

Defines the 7 specialized decommission agents with their roles, goals, and LLM configs.

Per ADR-024: All agents created with memory=False. Use TenantMemoryManager for learning.

🤖 Generated with Claude Code (CC)

Co-Authored-By: Claude <noreply@anthropic.com>
"""

# Decommission agent configurations
# Per ADR-024: memory_enabled=False for all agents
DECOMMISSION_AGENT_CONFIGS = {
    "system_analysis_agent": {
        "role": "System Dependency Analysis Specialist",
        "goal": (
            "Identify all system dependencies and impact zones to prevent "
            "downstream failures during decommissioning"
        ),
        "backstory": """Expert in enterprise architecture with 15+ years analyzing system dependencies.
        Creates comprehensive dependency maps to ensure safe decommissioning without impacting dependent systems.
        Specializes in identifying hidden integrations, API dependencies, and data flows.""",
        "tools": ["cmdb_query", "network_discovery", "api_dependency_mapper"],
        "memory_enabled": False,  # Per ADR-024: Use TenantMemoryManager
        "llm_config": {
            "provider": "deepinfra",
            "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        },
    },
    "dependency_mapper_agent": {
        "role": "System Relationship Mapping Specialist",
        "goal": "Map complex system relationships and integration points to ensure complete dependency coverage",
        "backstory": """20+ years in IT architecture, specialized in mapping complex system integrations.
        Expert in visualizing dependency graphs, identifying critical paths, and assessing cascade impacts.
        Creates dependency maps used by Fortune 500 companies for safe system retirements.""",
        "tools": [
            "dependency_graph_builder",
            "integration_analyzer",
            "critical_path_finder",
        ],
        "memory_enabled": False,  # Per ADR-024
        "llm_config": {
            "provider": "deepinfra",
            "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        },
    },
    "data_retention_agent": {
        "role": "Data Retention and Archival Compliance Specialist",
        "goal": "Ensure data retention compliance and secure archival before system decommissioning",
        "backstory": """Compliance expert with deep knowledge of GDPR, SOX, HIPAA, and PCI-DSS.
        Creates retention policies that balance legal requirements with storage optimization.
        15+ years managing enterprise data archival for regulated industries including healthcare and finance.""",
        "tools": ["compliance_policy_lookup", "data_classifier", "archive_calculator"],
        "memory_enabled": False,  # Per ADR-024
        "llm_config": {
            "provider": "deepinfra",
            "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        },
    },
    "compliance_agent": {
        "role": "Regulatory Compliance Validation Specialist",
        "goal": (
            "Ensure all decommission activities meet regulatory compliance requirements "
            "(GDPR, SOX, HIPAA, PCI-DSS)"
        ),
        "backstory": """Regulatory compliance officer with expertise in multi-jurisdiction compliance frameworks.
        Validates that decommission processes meet all regulatory requirements including data retention,
        audit trails, and secure data disposal. Works closely with legal teams to ensure zero compliance gaps.""",
        "tools": [
            "compliance_checker",
            "regulatory_validator",
            "audit_trail_generator",
        ],
        "memory_enabled": False,  # Per ADR-024
        "llm_config": {
            "provider": "deepinfra",
            "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        },
    },
    "shutdown_orchestrator_agent": {
        "role": "Safe System Shutdown Orchestration Specialist",
        "goal": "Execute graceful system shutdowns with zero data loss and automated rollback capabilities",
        "backstory": """Infrastructure automation expert with zero-downtime deployment expertise.
        Implements safety checks, gradual shutdowns, and automated rollback for risk-free decommissioning.
        Has safely decommissioned 1000+ enterprise systems with 100% success rate.""",
        "tools": ["service_controller", "health_monitor", "rollback_orchestrator"],
        "memory_enabled": False,  # Per ADR-024
        "llm_config": {
            "provider": "deepinfra",
            "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        },
    },
    "validation_agent": {
        "role": "Post-Decommission Verification and Cleanup Specialist",
        "goal": "Verify successful decommission completion and ensure complete resource cleanup",
        "backstory": """Quality assurance engineer specialized in infrastructure validation.
        Performs comprehensive checks to ensure complete system removal and resource cleanup.
        Expert in detecting residual configurations, orphaned resources, and incomplete shutdowns.""",
        "tools": ["access_verifier", "resource_scanner", "compliance_auditor"],
        "memory_enabled": False,  # Per ADR-024
        "llm_config": {
            "provider": "deepinfra",
            "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        },
    },
    "rollback_agent": {
        "role": "Decommission Rollback and Recovery Specialist",
        "goal": "Handle rollback scenarios for failed decommissions and restore system state",
        "backstory": """Disaster recovery specialist with expertise in system restoration and rollback procedures.
        Creates comprehensive rollback plans and executes recovery operations with minimal downtime.
        Expert in state preservation, backup validation, and point-in-time recovery.""",
        "tools": ["backup_validator", "state_restorer", "recovery_orchestrator"],
        "memory_enabled": False,  # Per ADR-024
        "llm_config": {
            "provider": "deepinfra",
            "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        },
    },
}
