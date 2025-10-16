"""
Recommendation Generation Phase Configuration

Configuration for the recommendation generation phase of the Assessment flow.
Generates migration recommendations and roadmap.
"""

from app.services.flow_type_registry import PhaseConfig, RetryConfig


def get_recommendation_generation_phase() -> PhaseConfig:
    """
    Get the Recommendation Generation phase configuration

    Generates migration recommendations and roadmap based on assessment results.
    """

    # Define retry configuration for phases
    default_retry = RetryConfig(
        max_attempts=3,
        initial_delay_seconds=2.0,
        backoff_multiplier=2.0,
        max_delay_seconds=30.0,
    )

    return PhaseConfig(
        name="recommendation_generation",
        display_name="Recommendation Generation",
        description="Generate migration recommendations and roadmap",
        required_inputs=["risk_scores", "business_priorities"],
        optional_inputs=[
            "cost_constraints",
            "timeline_preferences",
            "resource_availability",
        ],
        validators=["recommendation_validation", "roadmap_validation"],
        pre_handlers=["recommendation_analysis"],
        post_handlers=["roadmap_generation"],
        completion_handler="assessment_completion",
        can_pause=True,
        can_skip=False,
        retry_config=default_retry,
        timeout_seconds=1500,  # 25 minutes
        metadata={
            "ui_route": "/assessment/[flowId]/app-on-page",  # Issue #4 fix: recommendations shown in app-on-page
            "ui_short_name": "Recommendations",  # Compact name for sidebar navigation
            "estimated_duration_minutes": 25,
            "icon": "lightbulb",
            "help_text": "Generate migration recommendations and roadmap",
            "recommendation_types": [
                "migration_approach",
                "wave_grouping",
                "technology_stack",
                "resource_requirements",
                "timeline_optimization",
            ],
            "ai_powered_recommendations": True,
            "scenario_planning": True,
        },
    )
