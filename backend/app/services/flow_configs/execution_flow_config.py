"""
Execution Flow Configuration
MFO-050: Pre-migration validation, migration execution, post-migration validation
"""

from app.services.flow_type_registry import (
    FlowCapabilities,
    FlowTypeConfig,
    PhaseConfig,
    RetryConfig,
)


def get_execution_flow_config() -> FlowTypeConfig:
    """
    MFO-050: Execution Flow Configuration

    Pre-migration validation, migration execution, post-migration validation
    """
    default_retry = RetryConfig(
        max_attempts=5, initial_delay_seconds=5.0, max_delay_seconds=300.0
    )

    phases = [
        PhaseConfig(
            name="pre_migration_validation",
            display_name="Pre-Migration Validation",
            description="Validate readiness before migration execution",
            required_inputs=["migration_plan", "target_environment"],
            optional_inputs=[
                "validation_checklist",
                "rollback_plan",
                "communication_plan",
            ],
            validators=["pre_migration_validation", "environment_validation"],
            pre_handlers=["environment_preparation"],
            post_handlers=["validation_report"],
            can_pause=True,
            retry_config=default_retry,
            timeout_seconds=1800,  # 30 minutes
            metadata={
                "validation_types": [
                    "connectivity",
                    "permissions",
                    "capacity",
                    "compatibility",
                ],
                "go_no_go_decision": True,
            },
        ),
        PhaseConfig(
            name="migration_execution",
            display_name="Migration Execution",
            description="Execute the actual migration process",
            required_inputs=["validated_plan", "execution_config"],
            optional_inputs=[
                "parallel_streams",
                "throttling_config",
                "monitoring_config",
            ],
            validators=["execution_validation", "progress_validation"],
            pre_handlers=["execution_preparation"],
            post_handlers=["execution_verification"],
            can_pause=True,
            retry_config=default_retry,
            timeout_seconds=10800,  # 180 minutes
            metadata={
                "execution_modes": ["big_bang", "phased", "parallel", "blue_green"],
                "rollback_enabled": True,
                "real_time_monitoring": True,
            },
        ),
        PhaseConfig(
            name="post_migration_validation",
            display_name="Post-Migration Validation",
            description="Validate migration success and functionality",
            required_inputs=["migration_results", "validation_criteria"],
            optional_inputs=[
                "performance_benchmarks",
                "user_acceptance_tests",
                "integration_tests",
            ],
            validators=["post_migration_validation", "success_criteria_validation"],
            pre_handlers=["validation_preparation"],
            post_handlers=["validation_summary"],
            completion_handler="migration_completion",
            can_pause=True,
            retry_config=default_retry,
            timeout_seconds=2700,  # 45 minutes
            metadata={
                "validation_levels": [
                    "infrastructure",
                    "application",
                    "data",
                    "integration",
                ],
                "automated_testing": True,
            },
        ),
    ]

    capabilities = FlowCapabilities(
        supports_pause_resume=True,
        supports_rollback=True,
        supports_branching=True,
        supports_iterations=False,
        supports_scheduling=True,
        supports_parallel_phases=True,
        supports_checkpointing=True,
        required_permissions=[
            "execution.read",
            "execution.write",
            "execution.execute",
            "execution.rollback",
        ],
    )

    return FlowTypeConfig(
        name="execution",
        display_name="Execution Flow",
        description="Migration execution with validation and rollback capabilities",
        version="2.0.0",
        phases=phases,
        capabilities=capabilities,
        default_configuration={
            "rollback_enabled": True,
            "real_time_monitoring": True,
            "automated_validation": True,
            "parallel_execution": True,
            "failure_threshold": 0.05,
        },
        initialization_handler="execution_initialization",
        finalization_handler="execution_finalization",
        error_handler="execution_error_handler",
        metadata={
            "category": "operational",
            "complexity": "critical",
            "prerequisite_flows": ["planning"],
            "requires_approval": True,
        },
        tags=["execution", "migration", "validation", "rollback", "critical"],
    )
