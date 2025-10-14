"""
Technical Debt Assessment Phase Configuration

Configuration for the technical debt assessment phase of the Assessment flow.
Migrated from Discovery flow per ADR-027.

This phase assesses technical debt across asset inventory,
requiring both asset inventory and dependency analysis.
"""

from app.services.flow_type_registry import PhaseConfig, RetryConfig


def get_tech_debt_assessment_phase() -> PhaseConfig:
    """
    Get the Technical Debt Assessment phase configuration

    Migrated from Discovery flow in v3.0.0 per ADR-027.
    Assesses technical debt across asset inventory.
    """

    # Define retry configuration for phases
    default_retry = RetryConfig(
        max_attempts=3,
        initial_delay_seconds=5.0,
        backoff_multiplier=2.0,
        max_delay_seconds=60.0,
    )

    return PhaseConfig(
        name="tech_debt_assessment",
        display_name="Technical Debt Assessment",
        description="Assess technical debt across asset inventory",
        required_inputs=["asset_inventory", "dependency_map"],
        optional_inputs=["tech_debt_rules", "assessment_criteria"],
        validators=[
            "asset_inventory_exists",
            "dependency_map_exists",
            "tech_debt_validation",
        ],
        pre_handlers=["load_tech_debt_rules", "prepare_assessment_context"],
        post_handlers=[
            "persist_tech_debt_assessment",
            "generate_tech_debt_report",
            "prepare_next_phase",
        ],
        crew_config={
            "crew_type": "tech_debt_assessment",
            "crew_factory": "create_tech_debt_assessment_crew",
            "input_mapping": {
                "asset_inventory": "state.asset_inventory",
                "dependency_map": "state.dependency_map",
                "tech_debt_rules": "state.tech_debt_rules",
                "assessment_criteria": "state.assessment_criteria",
            },
            "output_mapping": {
                "tech_debt_scores": "crew_results.tech_debt_scores",
                "tech_debt_items": "crew_results.tech_debt_items",
                "remediation_recommendations": "crew_results.remediation_recommendations",
                "tech_debt_priority": "crew_results.tech_debt_priority",
            },
            "execution_config": {
                "timeout_seconds": 300,
                "temperature": 0.1,
                "enable_memory": False,  # Per ADR-024
            },
        },
        can_pause=True,
        can_skip=False,
        retry_config=default_retry,
        timeout_seconds=1800,  # 30 minutes
        metadata={
            "ui_route": "/assessment/tech-debt",
            "ui_short_name": "Tech Debt",  # Compact name for sidebar navigation
            "estimated_duration_minutes": 30,
            "icon": "alert-triangle",
            "help_text": "Assess technical debt across assets",
            "migration_note": "Moved from Discovery flow in v3.0.0",
            "success_criteria": [
                "Tech debt scores calculated",
                "All tech debt items identified",
                "Remediation recommendations generated",
            ],
        },
    )
