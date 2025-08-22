"""
Manual Collection Phase Configuration

Configuration for the manual collection phase of the Collection flow.
Collects missing data through questionnaire responses and manual processes.
"""

from app.services.flow_type_registry import PhaseConfig, RetryConfig


def get_manual_collection_phase() -> PhaseConfig:
    """
    Get the Manual Collection phase configuration

    Collects missing data through questionnaire responses and manual processes.
    """

    # Define retry configuration for phases
    default_retry = RetryConfig(
        max_attempts=3,
        initial_delay_seconds=2.0,
        backoff_multiplier=2.0,
        max_delay_seconds=30.0,
    )

    return PhaseConfig(
        name="manual_collection",
        display_name="Manual Collection",
        description="Collect missing data through questionnaire responses and manual processes",
        required_inputs=["questionnaires_generated", "response_templates"],
        optional_inputs=[
            "respondent_assignments",
            "collection_deadlines",
            "response_format",
        ],
        validators=["response_validation", "completeness_validation"],
        pre_handlers=["response_preparation"],
        post_handlers=["response_processing"],
        crew_config={
            "crew_type": "manual_collection_crew",
            "crew_factory": "create_manual_collection_crew",
            "input_mapping": {
                "gaps": {
                    "data_gaps": "state.identified_gaps",
                    "gap_categories": "state.gap_categories",
                    "severity_scores": "state.gap_severity_scores",
                },
                "templates": "questionnaire_templates",
                "context": {
                    "existing_data": "state.collected_data",
                    "respondent_assignments": "respondent_assignments",
                    "collection_deadlines": "collection_deadlines",
                    "response_format": "response_format",
                    "sixr_impact": "state.sixr_impact",
                },
            },
            "output_mapping": {
                "questionnaire_responses": "crew_results.responses",
                "validation_results": "crew_results.validation",
                "confidence_scores": "crew_results.confidence",
                "remaining_gaps": "crew_results.unresolved_gaps",
                "response_quality": "crew_results.response_quality",
                "crew_confidence": "crew_results.crew_confidence",
            },
            "execution_config": {
                "timeout_seconds": 300,  # 5 minutes base
                "temperature": 0.1,  # Very conservative
                "max_iterations": 2,  # Allow follow-up questions
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
                    "responses",
                    "validation",
                    "confidence",
                    "crew_confidence",
                ],
                "success_criteria": {
                    "crew_confidence": {"min": 0.6},
                    "response_rate": {"min": 0.8},
                    "validation_pass_rate": {"min": 0.9},
                    "hallucination_risk": {"max": 0.1},
                },
            },
            "performance_config": {
                "enable_intelligent_questionnaires": True,
                "adaptive_questioning": True,
                "response_validation": True,
                "confidence_threshold": 0.6,
            },
        },
        can_pause=True,
        can_skip=True,  # Can skip if no gaps
        retry_config=default_retry,
        timeout_seconds=7200,  # 2 hours (allows for human response time)
        metadata={
            "supports_async_collection": True,
            "questionnaire_types": [
                "technical",
                "business",
                "compliance",
                "operational",
            ],
            "ai_powered_questionnaires": True,
            "intelligent_validation": True,
            "hallucination_protected": True,
            "factual_accuracy_enforced": True,
        },
    )
