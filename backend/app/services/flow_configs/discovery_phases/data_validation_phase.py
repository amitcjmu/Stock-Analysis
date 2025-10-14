"""
Data Validation Phase Configuration

Configuration for the data validation phase of the Discovery flow.
This phase validates imported data for quality and completeness.
"""

from app.services.flow_type_registry import PhaseConfig, RetryConfig


def get_data_validation_phase() -> PhaseConfig:
    """
    Get the Data Validation phase configuration

    Validates imported data for quality, completeness, and consistency.
    """

    # Define retry configuration for phases
    default_retry = RetryConfig(
        max_attempts=3,
        initial_delay_seconds=5.0,
        backoff_multiplier=2.0,
        max_delay_seconds=60.0,
    )

    return PhaseConfig(
        name="data_validation",
        display_name="Data Quality Validation",
        description="Validate imported data for quality and completeness",
        required_inputs=["imported_data"],
        optional_inputs=["validation_rules", "quality_thresholds"],
        validators=[
            "completeness_check",
            "consistency_check",
            "integrity_check",
        ],
        pre_handlers=["load_validation_rules", "prepare_validation_context"],
        post_handlers=[
            "record_validation_results",
            "update_quality_metrics",
            "prepare_next_phase",
        ],
        crew_config={
            "crew_type": "data_validation",
            "crew_factory": "create_data_validation_crew",
            "input_mapping": {
                "imported_data": "state.imported_data",
                "validation_rules": "state.validation_rules",
                "quality_thresholds": "state.quality_thresholds",
            },
            "output_mapping": {
                "validation_results": "crew_results.validation_results",
                "quality_score": "crew_results.quality_score",
                "validation_issues": "crew_results.validation_issues",
                "completeness_score": "crew_results.completeness_score",
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
            "ui_route": "/discovery/data-validation",
            "ui_short_name": "Data Validation",  # Compact name for sidebar navigation
            "estimated_duration_minutes": 15,
            "icon": "check-circle",
            "help_text": "Validate data quality and completeness",
            "success_criteria": [
                "Quality score >= 80%",
                "No critical validation issues",
                "Completeness >= 90%",
            ],
        },
    )
