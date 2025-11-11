"""
Modernize Flow Configuration
MFO-051: Assessment, architecture redesign, implementation planning
"""

from app.services.flow_type_registry import (
    FlowCapabilities,
    FlowTypeConfig,
    PhaseConfig,
    RetryConfig,
)


def get_modernize_flow_config() -> FlowTypeConfig:
    """
    MFO-051: Modernize Flow Configuration

    Assessment, architecture redesign, implementation planning
    """
    default_retry = RetryConfig(max_attempts=3, initial_delay_seconds=2.0)

    phases = [
        PhaseConfig(
            name="modernization_assessment",
            display_name="Modernization Assessment",
            description="Assess modernization opportunities and readiness",
            required_inputs=["current_architecture", "modernization_goals"],
            optional_inputs=[
                "technology_trends",
                "skill_assessment",
                "budget_constraints",
            ],
            validators=["modernization_validation", "goal_alignment_validation"],
            pre_handlers=["modernization_analysis"],
            post_handlers=["opportunity_identification"],
            can_pause=True,
            retry_config=default_retry,
            timeout_seconds=3600,  # 60 minutes
            metadata={
                "assessment_areas": [
                    "containerization",
                    "microservices",
                    "serverless",
                    "cloud_native",
                ],
                "maturity_model": "cloud_native_maturity_model_v2",
            },
        ),
        PhaseConfig(
            name="architecture_redesign",
            display_name="Architecture Redesign",
            description="Redesign architecture for cloud-native patterns",
            required_inputs=["modernization_opportunities", "design_principles"],
            optional_inputs=[
                "reference_architectures",
                "pattern_library",
                "constraints",
            ],
            validators=["architecture_validation", "pattern_validation"],
            pre_handlers=["design_preparation"],
            post_handlers=["design_review"],
            can_pause=True,
            retry_config=default_retry,
            timeout_seconds=5400,  # 90 minutes
            metadata={
                "design_patterns": [
                    "microservices",
                    "event_driven",
                    "api_first",
                    "twelve_factor",
                ],
                "architecture_tools": ["diagrams", "models", "prototypes"],
            },
        ),
        PhaseConfig(
            name="implementation_planning",
            display_name="Implementation Planning",
            description="Plan modernization implementation approach",
            required_inputs=["new_architecture", "implementation_constraints"],
            optional_inputs=["pilot_selection", "training_plan", "transition_approach"],
            validators=["implementation_validation", "feasibility_validation"],
            pre_handlers=["implementation_analysis"],
            post_handlers=["roadmap_creation"],
            completion_handler="modernization_completion",
            can_pause=True,
            retry_config=default_retry,
            timeout_seconds=2700,  # 45 minutes
            metadata={
                "implementation_approaches": [
                    "rehost",
                    "replatform",
                    "refactor",
                    "rebuild",
                ],
                "pilot_program": True,
            },
        ),
    ]

    capabilities = FlowCapabilities(
        supports_pause_resume=True,
        supports_rollback=False,
        supports_iterations=True,
        max_iterations=3,
        supports_scheduling=True,
        supports_checkpointing=True,
        required_permissions=["modernize.read", "modernize.write", "modernize.design"],
    )

    return FlowTypeConfig(
        name="modernize",
        display_name="Modernize Flow",
        description="Application modernization and cloud-native transformation",
        version="2.0.0",
        phases=phases,
        capabilities=capabilities,
        default_configuration={
            "cloud_native_patterns": True,
            "microservices_assessment": True,
            "containerization_analysis": True,
            "ai_recommendations": True,
        },
        initialization_handler="modernize_initialization",
        finalization_handler="modernize_finalization",
        error_handler="modernize_error_handler",
        metadata={
            "category": "transformation",
            "complexity": "high",
            "prerequisite_flows": ["assessment"],
        },
        tags=["modernization", "cloud_native", "transformation", "architecture"],
    )
