"""
Gap Analysis Phase Configuration

Configuration for the gap analysis phase of the Collection flow.
Analyzes collected data for gaps and quality issues using intelligent gap detection.
"""

from app.services.flow_type_registry import PhaseConfig, RetryConfig


def get_gap_analysis_phase() -> PhaseConfig:
    """
    Get the Gap Analysis phase configuration

    Analyzes collected data for gaps and quality issues using intelligent gap detection.
    """

    # Define retry configuration for phases
    default_retry = RetryConfig(
        max_attempts=3,
        initial_delay_seconds=2.0,
        backoff_multiplier=2.0,
        max_delay_seconds=30.0,
    )

    return PhaseConfig(
        name="gap_analysis",
        display_name="Gap Analysis",
        description="Analyze collected data for gaps and quality issues using intelligent gap detection",
        required_inputs=["collected_data", "sixr_requirements"],
        optional_inputs=[
            "custom_requirements",
            "priority_fields",
            "quality_thresholds",
        ],
        validators=["gap_validation", "sixr_impact_validation"],
        pre_handlers=["gap_analysis_preparation"],
        post_handlers=["gap_prioritization"],
        crew_config={
            "crew_type": "gap_analysis_crew",
            "crew_factory": "create_gap_analysis_crew",
            "input_mapping": {
                "collected_data": "state.collected_data",
                "requirements": {
                    "sixr_requirements": "sixr_requirements",
                    "custom_requirements": "custom_requirements",
                    "priority_fields": "priority_fields",
                    "quality_thresholds": "quality_thresholds",
                },
                "context": {
                    "automation_tier": "state.automation_tier",
                    "quality_scores": "state.quality_scores",
                    "collection_metrics": "state.collection_metrics",
                },
            },
            "output_mapping": {
                "identified_gaps": "crew_results.data_gaps",
                "gap_categories": "crew_results.gap_categories",
                "sixr_impact": "crew_results.sixr_impact_analysis",
                "resolution_recommendations": "crew_results.recommendations",
                "gap_severity_scores": "crew_results.severity_scores",
                "crew_confidence": "crew_results.crew_confidence",
            },
            "execution_config": {
                "timeout_seconds": 180,  # Conservative 3 minutes
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
                    "data_gaps",
                    "sixr_impact_analysis",
                    "gap_categories",
                    "crew_confidence",
                ],
                "success_criteria": {
                    "crew_confidence": {"min": 0.6},
                    "gap_analysis_complete": True,
                    "sixr_coverage": {"min": 0.8},
                    "hallucination_risk": {"max": 0.1},
                },
            },
            "performance_config": {
                "enable_gap_detection": True,
                "sixr_alignment_mode": "strict",
                "prioritize_critical_gaps": True,
                "confidence_threshold": 0.6,
            },
        },
        can_pause=True,
        can_skip=False,
        retry_config=default_retry,
        timeout_seconds=1200,  # 20 minutes
        metadata={
            "ai_powered_gap_detection": True,
            "sixr_aligned": True,
            "gap_categories": [
                "missing_data",
                "incomplete_data",
                "quality_issues",
                "validation_errors",
            ],
            "hallucination_protected": True,
            "factual_accuracy_enforced": True,
        },
    )
