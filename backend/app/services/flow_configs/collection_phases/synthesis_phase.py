"""
Synthesis Phase Configuration

Configuration for the synthesis phase of the Collection flow.
Synthesizes and validates all collected data for completeness and quality using intelligent synthesis.
"""

from app.services.flow_type_registry import PhaseConfig, RetryConfig


def get_synthesis_phase() -> PhaseConfig:
    """
    Get the Data Synthesis phase configuration

    Synthesizes and validates all collected data for completeness and quality using intelligent synthesis.
    """

    # Define retry configuration for phases
    default_retry = RetryConfig(
        max_attempts=3,
        initial_delay_seconds=2.0,
        backoff_multiplier=2.0,
        max_delay_seconds=30.0,
    )

    return PhaseConfig(
        name="synthesis",
        display_name="Data Synthesis",
        description=(
            "Synthesize and validate all collected data for completeness and quality "
            "using intelligent synthesis"
        ),
        required_inputs=["all_collected_data", "validation_rules"],
        optional_inputs=[
            "synthesis_preferences",
            "output_format",
            "export_requirements",
        ],
        validators=["final_validation", "sixr_readiness_validation"],
        pre_handlers=["synthesis_preparation"],
        post_handlers=["collection_finalization"],
        crew_config={
            "crew_type": "data_synthesis_crew",
            "crew_factory": "create_data_synthesis_crew",
            "input_mapping": {
                "data_sources": {
                    "automated_data": "state.automated_collection_data",
                    "manual_data": "state.manual_collection_data",
                    "gap_resolutions": "state.questionnaire_responses",
                },
                "validation_rules": "validation_rules",
                "context": {
                    "automation_tier": "state.automation_tier",
                    "quality_scores": "state.quality_scores",
                    "collection_metrics": "state.collection_metrics",
                    "synthesis_preferences": "synthesis_preferences",
                    "output_format": "output_format",
                },
            },
            "output_mapping": {
                "synthesized_data": "crew_results.final_data",
                "quality_report": "crew_results.quality_report",
                "sixr_readiness": "crew_results.sixr_readiness_score",
                "collection_summary": "crew_results.summary",
                "data_lineage": "crew_results.data_lineage",
                "crew_confidence": "crew_results.crew_confidence",
            },
            "execution_config": {
                "timeout_seconds": 240,  # 4 minutes base
                "temperature": 0.1,  # Very conservative
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
                    "final_data",
                    "quality_report",
                    "sixr_readiness_score",
                    "crew_confidence",
                ],
                "success_criteria": {
                    "crew_confidence": {"min": 0.6},
                    "data_completeness": {"min": 0.85},
                    "quality_score": {"min": 0.8},
                    "sixr_readiness_score": {"min": 0.75},
                    "hallucination_risk": {"max": 0.1},
                },
            },
            "performance_config": {
                "enable_data_synthesis": True,
                "quality_assurance": True,
                "sixr_alignment_validation": True,
                "data_lineage_tracking": True,
                "confidence_threshold": 0.6,
            },
        },
        can_pause=True,
        can_skip=False,
        retry_config=default_retry,
        timeout_seconds=1500,  # 25 minutes
        metadata={
            "generates_quality_report": True,
            "sixr_alignment_check": True,
            "output_formats": ["json", "excel", "pdf"],
            "ai_powered_synthesis": True,
            "data_lineage_enabled": True,
            "hallucination_protected": True,
            "factual_accuracy_enforced": True,
        },
    )
