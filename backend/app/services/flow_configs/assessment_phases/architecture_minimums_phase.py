"""
Architecture Minimums Phase Configuration

ADR-039 Enhancement: Compliance validation phase configuration.
Validates technology compliance against engagement architecture standards.

This phase is deterministic (no CrewAI agents) - it validates each application's
technology stack against the engagement's architecture standards.
"""

from app.services.flow_type_registry import PhaseConfig, RetryConfig


def get_architecture_minimums_phase() -> PhaseConfig:
    """
    Get the Architecture Minimums (Compliance Validation) phase configuration

    ADR-039: Validates technology versions against engagement standards.
    Unlike other phases, this does NOT use CrewAI agents - it's deterministic.
    """

    # Define retry configuration
    default_retry = RetryConfig(
        max_attempts=3,
        initial_delay_seconds=1.0,
        backoff_multiplier=2.0,
        max_delay_seconds=15.0,
    )

    return PhaseConfig(
        name="architecture_minimums",
        display_name="Architecture Standards Compliance",
        description="Validate technology stack compliance against engagement architecture standards",
        required_inputs=["asset_inventory"],
        optional_inputs=[
            "engagement_standards",
            "compliance_frameworks",
        ],
        validators=[
            "required_fields",
            "inventory_completeness",
        ],
        pre_handlers=["compliance_preparation"],
        post_handlers=["compliance_summary"],
        # Minimal crew_config since this phase doesn't use CrewAI
        crew_config={
            "crew_type": "compliance_validator",
            "crew_factory": None,  # No CrewAI factory - deterministic validation
            "input_mapping": {
                "engagement_standards": "state.engagement_standards",
                "applications": "asset_inventory.applications",
            },
            "output_mapping": {
                "compliance_validation": "phase_results.compliance_validation",
                "engagement_standards": "phase_results.engagement_standards",
            },
            "execution_config": {
                "timeout_seconds": 60,  # Fast deterministic validation
                "allow_delegation": False,
                "enable_memory": False,
                "enable_caching": True,
                "enable_parallel": False,
            },
            "validation_mapping": {
                "required_fields": [
                    "compliance_validation",
                ],
                "success_criteria": {
                    "validation_completed": {"required": True},
                },
            },
        },
        can_pause=False,  # Quick phase, no need to pause
        can_skip=True,  # Can skip if no standards defined
        retry_config=default_retry,
        timeout_seconds=120,  # 2 minutes max
        metadata={
            "ui_route": "/assessment/:flowId/compliance",
            "ui_short_name": "Compliance",
            "estimated_duration_minutes": 2,
            "icon": "shield-check",
            "help_text": "Validate technology compliance against architecture standards",
            "compliance_dimensions": [
                "language_versions",
                "database_versions",
                "cloud_providers",
                "compliance_frameworks",
            ],
            "deterministic": True,  # No AI/LLM used
            "adr_reference": "ADR-039",
        },
    )
