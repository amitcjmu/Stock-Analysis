"""
Decommission Crew Factory

Creates phase-specific crews for decommission workflow.

Provides 3 crew creation methods:
- create_decommission_planning_crew: Phase 1 (analysis, dependencies, retention)
- create_data_migration_crew: Phase 2 (archival, compliance, integrity)
- create_system_shutdown_crew: Phase 3 (shutdown, validation, rollback)

Per ADR-024: All crews created with memory=False. Use TenantMemoryManager for learning.

ARCHITECTURAL NOTE - Direct Crew() Instantiation:
This module uses direct Crew() instantiation (not TenantScopedAgentPool) for
decommission-specific workflows. This is intentional because:

1. Decommission agents are specialized and not part of the standard discovery/assessment flows
2. DecommissionAgentPool implements its own tenant-scoped caching pattern
3. The decommission workflow has unique requirements (3 phases with specific agent combinations)
4. Direct instantiation allows for fine-grained control over task context dependencies

This pattern is approved for domain-specific agent pools. For standard discovery/assessment
agents, use TenantScopedAgentPool as documented in ADR-015.

🤖 Generated with Claude Code (CC)

Co-Authored-By: Claude <noreply@anthropic.com>
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# CrewAI imports with fallback
try:
    from crewai import Crew, Task

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False

    # Fallback classes
    class Task:  # type: ignore[no-redef]
        def __init__(self, **kwargs):
            self.description = kwargs.get("description", "")
            self.expected_output = kwargs.get("expected_output", "")

    class Crew:  # type: ignore[no-redef]
        def __init__(self, **kwargs):
            self.agents = kwargs.get("agents", [])
            self.tasks = kwargs.get("tasks", [])

        def kickoff(self, inputs=None):
            return {"status": "fallback_mode", "result": {}}


def create_decommission_planning_crew(
    agents: Dict[str, Any],
    system_ids: List[str],
    decommission_strategy: Dict[str, Any],
) -> Crew:
    """
    Create decommission planning crew (Phase 1: decommission_planning).

    This crew analyzes systems, maps dependencies, and assesses risks.

    Agents Used:
    - SystemAnalysisAgent: Analyze system dependencies
    - DependencyMapperAgent: Map system relationships
    - DataRetentionAgent: Identify data retention requirements

    Args:
        agents: Dictionary of agent instances (from get_agent)
        system_ids: List of system IDs to decommission
        decommission_strategy: Strategy configuration

    Returns:
        Crew instance ready for execution (or None in fallback mode)
    """
    if not CREWAI_AVAILABLE:
        logger.warning("CrewAI not available, returning fallback crew")
        return None  # type: ignore[return-value]

    # Get required agents
    system_analyst = agents.get("system_analysis_agent")
    dependency_mapper = agents.get("dependency_mapper_agent")
    data_retention = agents.get("data_retention_agent")

    if not all([system_analyst, dependency_mapper, data_retention]):
        missing = [
            k
            for k in [
                "system_analysis_agent",
                "dependency_mapper_agent",
                "data_retention_agent",
            ]
            if k not in agents
        ]
        raise ValueError(f"Missing required agents for planning crew: {missing}")

    # Define tasks
    system_analysis_task = Task(
        description=f"""Analyze {len(system_ids)} systems for decommissioning impact.

        Systems to analyze: {', '.join(system_ids[:5])}{"..." if len(system_ids) > 5 else ""}

        Your analysis must include:
        1. System architecture and technology stack
        2. Current usage patterns and criticality
        3. Dependencies (upstream and downstream)
        4. Integration points and API contracts
        5. Data flows and storage locations
        6. Impact assessment for each system

        Priority: {decommission_strategy.get('priority', 'cost_savings')}

        Provide comprehensive system analysis with risk categorization.""",
        expected_output="""JSON object with:
        - system_inventory: List of analyzed systems with metadata
        - dependency_summary: High-level dependency overview
        - impact_zones: Areas affected by decommissioning
        - risk_factors: Identified risks per system
        - recommendations: System-specific recommendations""",
        agent=system_analyst,
    )

    dependency_mapping_task = Task(
        description=f"""Create comprehensive dependency map for {len(system_ids)} systems.

        Using the system analysis results, map all relationships:
        1. Direct dependencies (API calls, database connections)
        2. Indirect dependencies (shared services, data flows)
        3. Integration points (message queues, event streams)
        4. Critical paths (dependencies that cannot fail)

        Identify:
        - Circular dependencies
        - Single points of failure
        - Cascade impact zones
        - Decommission order recommendations

        Output dependency graph with risk weights.""",
        expected_output="""JSON object with:
        - dependency_graph: Nodes and edges with metadata
        - critical_paths: Paths that require special handling
        - decommission_sequence: Recommended shutdown order
        - risk_matrix: Dependency risk assessment
        - mitigation_strategies: Strategies per critical dependency""",
        agent=dependency_mapper,
        context=[system_analysis_task],  # Depends on system analysis
    )

    data_retention_task = Task(
        description=f"""Identify data retention requirements for {len(system_ids)} systems.

        For each system, determine:
        1. Data types and classifications (PII, financial, medical)
        2. Applicable compliance frameworks (GDPR, SOX, HIPAA, PCI-DSS)
        3. Retention period requirements per regulation
        4. Data volume and storage locations
        5. Encryption requirements (at-rest and in-transit)

        Strategy priority: {decommission_strategy.get('priority', 'cost_savings')}

        Create retention policies that balance compliance with cost optimization.""",
        expected_output="""JSON object with:
        - retention_policies: Per-system retention requirements
        - compliance_matrix: Regulations applicable to each dataset
        - data_classification: Sensitivity levels and handling requirements
        - storage_estimates: Volume and cost projections
        - archive_timeline: Recommended archival schedule""",
        agent=data_retention,
        context=[system_analysis_task],  # Needs system inventory
    )

    # Create crew with memory=False per ADR-024
    crew = Crew(
        agents=[system_analyst, dependency_mapper, data_retention],
        tasks=[system_analysis_task, dependency_mapping_task, data_retention_task],
        verbose=False,
        memory=False,  # CRITICAL: Per ADR-024, use TenantMemoryManager instead
        process="sequential",  # Execute tasks in order
    )

    logger.info("✅ Created decommission planning crew with 3 agents and 3 tasks")
    return crew


def create_data_migration_crew(
    agents: Dict[str, Any],
    retention_policies: Dict[str, Any],
    system_ids: List[str],
) -> Crew:
    """
    Create data migration crew (Phase 2: data_migration).

    This crew executes data archival, validates compliance, and ensures data integrity.

    Agents Used:
    - DataRetentionAgent: Execute retention policies
    - ComplianceAgent: Validate regulatory compliance
    - ValidationAgent: Verify data integrity

    Args:
        agents: Dictionary of agent instances
        retention_policies: Policies from planning phase
        system_ids: List of system IDs

    Returns:
        Crew instance ready for execution (or None in fallback mode)
    """
    if not CREWAI_AVAILABLE:
        logger.warning("CrewAI not available, returning fallback crew")
        return None  # type: ignore[return-value]

    # Get required agents
    data_retention = agents.get("data_retention_agent")
    compliance = agents.get("compliance_agent")
    validator = agents.get("validation_agent")

    if not all([data_retention, compliance, validator]):
        missing = [
            k
            for k in [
                "data_retention_agent",
                "compliance_agent",
                "validation_agent",
            ]
            if k not in agents
        ]
        raise ValueError(f"Missing required agents for data migration crew: {missing}")

    # Define tasks
    archive_execution_task = Task(
        description=f"""Execute data archival for {len(system_ids)} systems.

        Retention Policies: {len(retention_policies)} policies defined

        For each system:
        1. Create archive jobs with integrity checksums
        2. Apply encryption (AES-256 at-rest minimum)
        3. Verify data completeness
        4. Test archive accessibility
        5. Update data catalog with archive locations

        Ensure zero data loss during archival.""",
        expected_output="""JSON object with:
        - archive_jobs: Per-system job status and metadata
        - integrity_checks: Checksum verification results
        - encryption_status: Encryption validation per dataset
        - storage_locations: Secure archive URLs
        - verification_results: Data completeness validation""",
        agent=data_retention,
    )

    compliance_validation_task = Task(
        description=f"""Validate compliance for {len(system_ids)} system decommissions.

        Verify:
        1. All retention policies meet regulatory requirements
        2. Data classification is complete and accurate
        3. Encryption meets industry standards (AES-256+)
        4. Audit trails are comprehensive and immutable
        5. Access controls enforce least privilege

        Regulations to check: GDPR, SOX, HIPAA, PCI-DSS

        Flag any compliance gaps for remediation.""",
        expected_output="""JSON object with:
        - compliance_status: Per-regulation validation results
        - gaps_identified: List of compliance gaps requiring action
        - remediation_plan: Steps to address each gap
        - audit_trail_status: Audit log completeness verification
        - risk_score: Overall compliance risk (0-100)""",
        agent=compliance,
        context=[archive_execution_task],  # Needs archive completion
    )

    integrity_validation_task = Task(
        description=f"""Validate data integrity for {len(system_ids)} archived systems.

        Perform:
        1. Checksum verification (SHA-256 minimum)
        2. Random sample testing (10% of datasets)
        3. Restore validation (test restore from archive)
        4. Accessibility testing (verify retrieval paths)
        5. Metadata validation (catalog accuracy)

        Ensure archived data is retrievable and complete.""",
        expected_output="""JSON object with:
        - checksum_results: Per-dataset verification status
        - sample_tests: Random sample validation results
        - restore_tests: Restore operation outcomes
        - accessibility_status: Archive access validation
        - issues_found: List of integrity issues requiring resolution""",
        agent=validator,
        context=[archive_execution_task],  # Depends on archive completion
    )

    # Create crew with memory=False per ADR-024
    crew = Crew(
        agents=[data_retention, compliance, validator],
        tasks=[
            archive_execution_task,
            compliance_validation_task,
            integrity_validation_task,
        ],
        verbose=False,
        memory=False,  # CRITICAL: Per ADR-024
        process="sequential",
    )

    logger.info("✅ Created data migration crew with 3 agents and 3 tasks")
    return crew


def create_system_shutdown_crew(
    agents: Dict[str, Any],
    decommission_plan: Dict[str, Any],
    system_ids: List[str],
) -> Crew:
    """
    Create system shutdown crew (Phase 3: system_shutdown).

    This crew executes safe shutdown, validates completion, and performs cleanup.
    Includes rollback capabilities per ADR requirements.

    Agents Used:
    - ShutdownOrchestratorAgent: Execute graceful shutdown
    - ValidationAgent: Verify shutdown completion
    - RollbackAgent: Handle rollback if needed

    Args:
        agents: Dictionary of agent instances
        decommission_plan: Plan from planning phase
        system_ids: List of system IDs

    Returns:
        Crew instance ready for execution (or None in fallback mode)
    """
    if not CREWAI_AVAILABLE:
        logger.warning("CrewAI not available, returning fallback crew")
        return None  # type: ignore[return-value]

    # Get required agents
    shutdown_orchestrator = agents.get("shutdown_orchestrator_agent")
    validator = agents.get("validation_agent")
    rollback = agents.get("rollback_agent")

    if not all([shutdown_orchestrator, validator, rollback]):
        missing = [
            k
            for k in [
                "shutdown_orchestrator_agent",
                "validation_agent",
                "rollback_agent",
            ]
            if k not in agents
        ]
        raise ValueError(f"Missing required agents for shutdown crew: {missing}")

    # Define tasks
    shutdown_execution_task = Task(
        description=f"""Execute graceful shutdown for {len(system_ids)} systems.

        Decommission Plan: {len(decommission_plan.get('systems', []))} systems planned

        Shutdown sequence (per system):
        1. Pre-shutdown validation (no active users, no pending jobs)
        2. Graceful connection termination (drain existing requests)
        3. Application layer shutdown (stop services in dependency order)
        4. Database shutdown (flush buffers, close connections)
        5. Infrastructure removal (release compute, storage, network)

        Use recommended decommission sequence to prevent cascade failures.

        Rollback enabled: {decommission_plan.get('rollback_enabled', True)}""",
        expected_output="""JSON object with:
        - shutdown_results: Per-system execution status
        - sequence_followed: Actual vs planned shutdown order
        - safety_checks: Pre-shutdown validation results
        - issues_encountered: Problems during shutdown
        - rollback_checkpoints: State snapshots for rollback""",
        agent=shutdown_orchestrator,
    )

    post_shutdown_validation_task = Task(
        description=f"""Validate successful shutdown for {len(system_ids)} systems.

        Verify:
        1. All services terminated (no running processes)
        2. Network access removed (ports closed, firewalls updated)
        3. Storage released (disks detached, backups preserved)
        4. Access revoked (service accounts disabled, API keys rotated)
        5. Monitoring alerts disabled (prevent false positives)

        Check for orphaned resources:
        - Compute instances
        - Storage volumes
        - Network interfaces
        - Load balancers
        - DNS entries

        Flag any incomplete shutdowns for manual review.""",
        expected_output="""JSON object with:
        - validation_results: Per-system validation status
        - orphaned_resources: Resources requiring manual cleanup
        - access_verification: Access revocation confirmation
        - monitoring_status: Alert disable confirmation
        - cleanup_required: List of manual cleanup tasks""",
        agent=validator,
        context=[shutdown_execution_task],  # Needs shutdown completion
    )

    rollback_readiness_task = Task(
        description=f"""Prepare rollback plan for {len(system_ids)} systems.

        For each system, document:
        1. State snapshots taken during shutdown
        2. Rollback procedures (reverse shutdown sequence)
        3. Estimated time to restore (ETA per system)
        4. Prerequisites for rollback (backups, configs)
        5. Risk assessment for rollback execution

        This rollback plan is only executed if validation fails.

        Ensure rollback capability for {decommission_plan.get('rollback_window_hours', 24)} hours post-shutdown.""",
        expected_output="""JSON object with:
        - rollback_procedures: Step-by-step recovery instructions
        - state_snapshots: Location and integrity of backups
        - restore_eta: Estimated restore time per system
        - prerequisites_met: Verification of rollback readiness
        - rollback_risk: Risk assessment for recovery operations""",
        agent=rollback,
        context=[shutdown_execution_task],  # Needs shutdown metadata
    )

    # Create crew with memory=False per ADR-024
    crew = Crew(
        agents=[shutdown_orchestrator, validator, rollback],
        tasks=[
            shutdown_execution_task,
            post_shutdown_validation_task,
            rollback_readiness_task,
        ],
        verbose=False,
        memory=False,  # CRITICAL: Per ADR-024
        process="sequential",
    )

    logger.info("✅ Created system shutdown crew with 3 agents and 3 tasks")
    return crew
