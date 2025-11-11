"""
Planning Flow Configuration
MFO-049: Wave planning, resource planning, and timeline optimization
"""

from app.services.flow_type_registry import (
    FlowCapabilities,
    FlowTypeConfig,
    PhaseConfig,
    RetryConfig,
)


def get_planning_flow_config() -> FlowTypeConfig:
    """
    MFO-049: Planning Flow Configuration

    Wave planning, resource planning, and timeline optimization
    """
    default_retry = RetryConfig(max_attempts=3, initial_delay_seconds=2.0)

    phases = [
        PhaseConfig(
            name="wave_planning",
            display_name="Wave Planning",
            description="Plan migration waves based on dependencies and constraints",
            required_inputs=["assessment_results", "business_constraints"],
            optional_inputs=[
                "dependency_graph",
                "blackout_windows",
                "priority_overrides",
            ],
            validators=["wave_validation", "dependency_validation"],
            pre_handlers=["wave_analysis"],
            post_handlers=["wave_optimization"],
            can_pause=True,
            retry_config=default_retry,
            timeout_seconds=3600,  # 60 minutes
            metadata={
                "optimization_algorithm": "constraint_satisfaction",
                "max_waves": 10,
                "parallel_execution": True,
            },
        ),
        PhaseConfig(
            name="resource_planning",
            display_name="Resource Planning",
            description="Plan resource allocation and capacity requirements",
            required_inputs=["wave_plan", "resource_constraints"],
            optional_inputs=[
                "skill_matrix",
                "vendor_availability",
                "budget_allocation",
            ],
            validators=["resource_validation", "capacity_validation"],
            pre_handlers=["resource_analysis"],
            post_handlers=["resource_optimization"],
            can_pause=True,
            retry_config=default_retry,
            timeout_seconds=2700,  # 45 minutes
            metadata={
                "resource_types": ["human", "infrastructure", "licensing", "tools"],
                "optimization_goals": ["cost", "duration", "risk"],
            },
        ),
        PhaseConfig(
            name="timeline_optimization",
            display_name="Timeline Optimization",
            description="Optimize migration timeline for efficiency",
            required_inputs=["wave_plan", "resource_plan"],
            optional_inputs=[
                "critical_path",
                "buffer_requirements",
                "acceleration_options",
            ],
            validators=["timeline_validation", "feasibility_check"],
            pre_handlers=["critical_path_analysis"],
            post_handlers=["timeline_finalization"],
            completion_handler="planning_completion",
            can_pause=True,
            can_skip=True,
            retry_config=default_retry,
            timeout_seconds=1800,  # 30 minutes
            metadata={
                "optimization_method": "critical_path_method",
                "buffer_calculation": "monte_carlo",
            },
        ),
    ]

    capabilities = FlowCapabilities(
        supports_pause_resume=True,
        supports_rollback=True,
        supports_iterations=True,
        max_iterations=5,
        supports_scheduling=True,
        supports_checkpointing=True,
        required_permissions=["planning.read", "planning.write", "planning.execute"],
    )

    return FlowTypeConfig(
        name="planning",
        display_name="Planning Flow",
        description="Migration wave and resource planning with timeline optimization",
        version="2.0.0",
        phases=phases,
        capabilities=capabilities,
        default_configuration={
            "optimization_enabled": True,
            "dependency_tracking": True,
            "resource_constraints": True,
            "scenario_planning": True,
            "monte_carlo_simulations": 1000,
        },
        initialization_handler="planning_initialization",
        finalization_handler="planning_finalization",
        error_handler="planning_error_handler",
        metadata={
            "category": "orchestration",
            "complexity": "high",
            "prerequisite_flows": ["assessment"],
        },
        tags=["planning", "optimization", "resource_management", "scheduling"],
    )
