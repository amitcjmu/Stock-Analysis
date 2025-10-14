"""
Readiness Assessment Phase Configuration

Configuration for the readiness assessment phase of the Assessment flow.
Assesses migration readiness of discovered assets using architecture standards.
"""

from app.services.flow_type_registry import PhaseConfig, RetryConfig


def get_readiness_assessment_phase() -> PhaseConfig:
    """
    Get the Readiness Assessment phase configuration

    Assesses migration readiness of discovered assets using
    architecture standards analysis.
    """

    # Define retry configuration for phases
    default_retry = RetryConfig(
        max_attempts=3,
        initial_delay_seconds=2.0,
        backoff_multiplier=2.0,
        max_delay_seconds=30.0,
    )

    return PhaseConfig(
        name="readiness_assessment",
        display_name="Readiness Assessment",
        description="Assess migration readiness of discovered assets using architecture standards analysis",
        required_inputs=["asset_inventory", "assessment_criteria"],
        optional_inputs=[
            "business_priorities",
            "technical_constraints",
            "compliance_requirements",
        ],
        validators=[
            "required_fields",
            "assessment_validation",
            "inventory_completeness",
        ],
        pre_handlers=["readiness_preparation"],
        post_handlers=["readiness_scoring"],
        crew_config={
            "crew_type": "architecture_standards_crew",
            "crew_factory": "create_architecture_standards_crew",
            "input_mapping": {
                "engagement_context": "state.engagement_context",
                "selected_applications": "asset_inventory.applications",
                "application_metadata": "asset_inventory.metadata",
                "existing_standards": "assessment_criteria.architecture_standards",
                "business_constraints": "business_priorities",
                "risk_tolerance": "assessment_criteria.risk_tolerance",
            },
            "output_mapping": {
                "readiness_scores": "crew_results.application_compliance",
                "technical_readiness": "crew_results.technical_debt_scores",
                "architecture_standards": "crew_results.engagement_standards",
                "upgrade_requirements": "crew_results.upgrade_recommendations",
                "business_readiness": "crew_results.exceptions",
                "crew_confidence": "crew_results.crew_confidence",
            },
            "execution_config": {
                "timeout_seconds": 180,  # Conservative 3 minutes
                "temperature": 0.1,  # Very conservative for accuracy
                "max_iterations": 1,
                "allow_delegation": True,  # Enable agent collaboration
                "enable_memory": False,  # Conservative mode
                "enable_caching": True,  # Performance optimization
                "enable_parallel": False,  # Sequential for accuracy
                "conservative_mode": True,
            },
            "llm_config": {
                "temperature": 0.1,  # Conservative settings
                "max_tokens": 4000,
                "frequency_penalty": 0.1,
                "presence_penalty": 0.1,
                "stop_sequences": ["HALLUCINATION", "SPECULATION", "ASSUMPTION"],
            },
            "validation_mapping": {
                "required_fields": [
                    "engagement_standards",
                    "application_compliance",
                    "technical_debt_scores",
                    "crew_confidence",
                ],
                "success_criteria": {
                    "crew_confidence": {"min": 0.6},
                    "standards_count": {"min": 1},
                    "compliance_coverage": {"min": 0.8},
                    "hallucination_risk": {"max": 0.1},
                },
            },
            "performance_config": {
                "enable_readiness_focus": True,
                "prioritize_technical_readiness": True,
                "generate_readiness_scores": True,
                "confidence_threshold": 0.6,
            },
        },
        can_pause=True,
        can_skip=False,
        retry_config=default_retry,
        timeout_seconds=2700,  # 45 minutes
        metadata={
            "ui_route": "/assessment/readiness",
            "ui_short_name": "Readiness",  # Compact name for sidebar navigation
            "estimated_duration_minutes": 45,
            "icon": "clipboard-check",
            "help_text": "Assess migration readiness of discovered assets",
            "assessment_dimensions": [
                "technical_readiness",
                "business_readiness",
                "operational_readiness",
                "security_readiness",
            ],
            "scoring_method": "weighted_average",
            "min_score_threshold": 0.6,
            "architecture_standards_enabled": True,
            "ai_powered_assessment": True,
            "hallucination_protected": True,
            "factual_accuracy_enforced": True,
        },
    )
