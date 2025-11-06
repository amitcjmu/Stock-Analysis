"""
Decommission Flow Configuration
Per ADR-027: FlowTypeConfig as universal pattern
Per ADR-025: Uses DecommissionChildFlowService (NO crew_class)

Safe system decommissioning with data preservation and compliance.
Created for Issue #939: FlowTypeConfig Registration - COMPLETE
"""

from app.services.child_flow_services import DecommissionChildFlowService
from app.services.flow_type_registry import (
    FlowCapabilities,
    FlowTypeConfig,
    PhaseConfig,
    RetryConfig,
)


def get_decommission_flow_config() -> FlowTypeConfig:
    """
    Get Decommission flow configuration

    Per ADR-027: Decommission flow handles safe system shutdown with
    data preservation and compliance requirements.

    Per ADR-025: Uses DecommissionChildFlowService for child flow operations.
    NO crew_class specified (deprecated pattern).

    Phases:
    1. Decommission Planning - Dependency analysis, risk assessment, cost analysis
    2. Data Migration - Data retention policies, archival jobs
    3. System Shutdown - Pre-validation, shutdown, post-validation, cleanup
    """

    # Conservative retry config for critical decommission operations
    default_retry = RetryConfig(
        max_attempts=5, initial_delay_seconds=10.0, max_delay_seconds=600.0
    )

    # Define flow capabilities
    capabilities = FlowCapabilities(
        supports_pause_resume=True,
        supports_rollback=True,  # Critical for decommission safety
        supports_branching=False,
        supports_iterations=False,  # Decommission is one-way operation
        max_iterations=1,
        supports_scheduling=True,
        supports_parallel_phases=False,  # Sequential execution required
        supports_checkpointing=True,
        required_permissions=[
            "decommission.read",
            "decommission.write",
            "decommission.execute",
            "decommission.approve",  # Approval required for destructive operations
        ],
    )

    # Create flow configuration
    return FlowTypeConfig(
        name="decommission",
        display_name="Decommission Flow",
        description=(
            "Safe system decommissioning with data preservation, "
            "compliance verification, and cost savings analysis"
        ),
        version="2.0.0",
        phases=[
            PhaseConfig(
                name="decommission_planning",
                display_name="Decommission Planning",
                description="Plan safe system decommissioning approach with dependency and risk analysis",
                required_inputs=["decommission_targets", "business_requirements"],
                optional_inputs=[
                    "dependency_analysis",
                    "risk_assessment",
                    "compliance_requirements",
                ],
                validators=["decommission_validation", "dependency_validation"],
                pre_handlers=["impact_analysis"],
                post_handlers=["plan_approval"],
                can_pause=True,
                can_skip=False,  # Planning cannot be skipped
                can_rollback=True,
                retry_config=default_retry,
                timeout_seconds=2700,  # 45 minutes
                metadata={
                    "planning_aspects": [
                        "data",
                        "dependencies",
                        "compliance",
                        "communication",
                    ],
                    "approval_required": True,
                    "rollback_planning": True,
                    "cost_analysis_enabled": True,
                },
                outputs=[
                    "decommission_plan",
                    "dependency_graph",
                    "risk_assessment",
                    "estimated_savings",
                ],
                expected_duration_minutes=45,
                success_criteria={
                    "plan_approved": True,
                    "dependencies_analyzed": True,
                    "risks_identified": True,
                },
            ),
            PhaseConfig(
                name="data_migration",
                display_name="Data Migration",
                description="Migrate and archive critical data with retention policies before decommission",
                required_inputs=["decommission_plan", "data_requirements"],
                optional_inputs=[
                    "archive_policies",
                    "retention_requirements",
                    "encryption_keys",
                ],
                validators=["data_migration_validation", "integrity_validation"],
                pre_handlers=["data_inventory"],
                post_handlers=["migration_verification"],
                can_pause=True,
                can_skip=False,  # Data migration cannot be skipped
                can_rollback=True,
                retry_config=default_retry,
                timeout_seconds=7200,  # 120 minutes
                metadata={
                    "migration_methods": ["backup", "archive", "transfer", "export"],
                    "data_validation": True,
                    "encryption_required": True,
                    "retention_policy_enforcement": True,
                },
                outputs=[
                    "archived_data_location",
                    "migration_report",
                    "data_integrity_verification",
                ],
                expected_duration_minutes=120,
                dependencies=["decommission_planning"],
                success_criteria={
                    "data_archived": True,
                    "integrity_verified": True,
                    "retention_policies_applied": True,
                },
            ),
            PhaseConfig(
                name="system_shutdown",
                display_name="System Shutdown",
                description="Safely shutdown and decommission systems with verification",
                required_inputs=["migrated_data", "shutdown_procedures"],
                optional_inputs=[
                    "verification_checklist",
                    "stakeholder_signoff",
                    "audit_requirements",
                ],
                validators=["shutdown_validation", "completion_validation"],
                pre_handlers=["final_backup"],
                post_handlers=["decommission_verification"],
                completion_handler="decommission_completion",
                can_pause=True,
                can_skip=False,  # Shutdown cannot be skipped
                can_rollback=False,  # Point of no return
                retry_config=default_retry,
                timeout_seconds=3600,  # 60 minutes
                metadata={
                    "shutdown_sequence": [
                        "connections",
                        "applications",
                        "databases",
                        "infrastructure",
                    ],
                    "verification_required": True,
                    "audit_trail": True,
                    "point_of_no_return": True,
                },
                outputs=[
                    "shutdown_report",
                    "decommission_verification",
                    "audit_log",
                    "cost_savings_actual",
                ],
                expected_duration_minutes=60,
                dependencies=["data_migration"],
                success_criteria={
                    "systems_shutdown": True,
                    "verification_complete": True,
                    "audit_log_created": True,
                },
            ),
        ],
        child_flow_service=DecommissionChildFlowService,  # Per ADR-025
        capabilities=capabilities,
        default_configuration={
            "data_backup_required": True,
            "approval_workflow": True,
            "audit_trail": True,
            "compliance_checks": True,
            "point_of_no_return_warning": True,
            "cost_tracking_enabled": True,
            "agent_collaboration": True,
        },
        initialization_handler="decommission_initialization",
        finalization_handler="decommission_finalization",
        error_handler="decommission_error_handler",
        metadata={
            "category": "lifecycle",
            "complexity": "high",
            "estimated_duration_minutes": 225,  # 45 + 120 + 60
            "required_agents": [
                "decommission_planning_agent",
                "data_migration_agent",
                "system_shutdown_agent",
            ],
            "output_formats": ["json", "pdf", "audit_log"],
            "prerequisite_flows": [
                "assessment"
            ],  # Requires assessment for dependency analysis
            "irreversible": True,
            "requires_approval": True,
            "compliance_critical": True,
            "cost_savings_tracking": True,
        },
        tags=[
            "decommission",
            "lifecycle",
            "data_migration",
            "compliance",
            "critical",
            "cost_savings",
        ],
    )
