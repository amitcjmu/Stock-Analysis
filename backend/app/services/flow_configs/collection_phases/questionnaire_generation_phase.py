"""
Questionnaire Generation Phase Configuration

Configuration for the questionnaire generation phase of the Collection flow.
Generates adaptive questionnaires based on gap analysis using intelligent agents.
"""

from app.services.flow_type_registry import PhaseConfig, RetryConfig


def get_questionnaire_generation_phase() -> PhaseConfig:
    """
    Get the Questionnaire Generation phase configuration

    Generates adaptive questionnaires based on gap analysis using intelligent agents.
    """

    # Define retry configuration for phases
    default_retry = RetryConfig(
        max_attempts=3,
        initial_delay_seconds=2.0,
        backoff_multiplier=2.0,
        max_delay_seconds=30.0,
    )

    return PhaseConfig(
        name="questionnaire_generation",
        display_name="Questionnaire Generation",
        description="Generate adaptive questionnaires based on gap analysis using intelligent agents",
        required_inputs=["identified_gaps", "gap_categories"],
        optional_inputs=["sixr_impact", "priority_fields", "custom_requirements"],
        validators=["questionnaire_validation", "gap_coverage_validation"],
        pre_handlers=["questionnaire_preparation"],
        post_handlers=["questionnaire_delivery"],
        crew_config={
            "crew_type": "questionnaire_generation_crew",
            "crew_factory": "create_questionnaire_generation_crew",
            "input_mapping": {
                "gaps": {
                    "data_gaps": "state.identified_gaps",
                    "gap_categories": "state.gap_categories",
                    "severity_scores": "state.gap_severity_scores",
                    "sixr_impact": "state.sixr_impact",
                },
                "context": {
                    "automation_tier": "state.automation_tier",
                    "existing_data": "state.collected_data",
                    "priority_fields": "priority_fields",
                    "custom_requirements": "custom_requirements",
                },
            },
            "output_mapping": {
                "questionnaires_generated": "crew_results.questionnaires",
                "question_categories": "crew_results.categories",
                "adaptive_logic": "crew_results.adaptive_logic",
                "expected_responses": "crew_results.expected_responses",
                "delivery_plan": "crew_results.delivery_plan",
                "crew_confidence": "crew_results.crew_confidence",
            },
            "execution_config": {
                "timeout_seconds": 240,  # 4 minutes
                "temperature": 0.2,  # Slightly creative for questionnaire design
                "max_iterations": 1,
                "allow_delegation": True,
                "enable_memory": False,  # Conservative mode
                "enable_caching": True,
                "enable_parallel": False,  # Sequential for accuracy
                "conservative_mode": True,
            },
            "llm_config": {
                "temperature": 0.2,  # Slightly higher for questionnaire creativity
                "max_tokens": 4000,
                "frequency_penalty": 0.1,
                "presence_penalty": 0.1,
                "stop_sequences": ["HALLUCINATION", "SPECULATION", "ASSUMPTION"],
            },
            "validation_mapping": {
                "required_fields": [
                    "questionnaires",
                    "categories",
                    "adaptive_logic",
                    "crew_confidence",
                ],
                "success_criteria": {
                    "crew_confidence": {"min": 0.7},
                    "questionnaire_count": {"min": 1},
                    "gap_coverage": {"min": 0.8},
                    "hallucination_risk": {"max": 0.1},
                },
            },
            "performance_config": {
                "enable_adaptive_questionnaires": True,
                "gap_driven_generation": True,
                "priority_based_ordering": True,
                "confidence_threshold": 0.7,
            },
        },
        can_pause=True,
        can_skip=False,  # Required if gaps exist
        retry_config=default_retry,
        timeout_seconds=900,  # 15 minutes
        metadata={
            "ai_powered_generation": True,
            "adaptive_questionnaires": True,
            "gap_driven": True,
            "questionnaire_types": [
                "technical",
                "business",
                "compliance",
                "operational",
            ],
            "hallucination_protected": True,
            "factual_accuracy_enforced": True,
        },
    )
