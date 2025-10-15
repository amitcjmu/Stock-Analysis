"""
Data Cleansing Phase Configuration

Configuration for the data cleansing phase of the Discovery flow.
This phase cleans and normalizes data.
"""

from app.services.flow_type_registry import PhaseConfig, RetryConfig


def get_data_cleansing_phase() -> PhaseConfig:
    """
    Get the Data Cleansing & Normalization phase configuration

    Cleans and normalizes data according to target schema and business rules.
    """

    # Define retry configuration for phases
    default_retry = RetryConfig(
        max_attempts=3,
        initial_delay_seconds=5.0,
        backoff_multiplier=2.0,
        max_delay_seconds=60.0,
    )

    return PhaseConfig(
        name="data_cleansing",
        display_name="Data Cleansing & Normalization",
        description="Clean and normalize data according to target schema",
        required_inputs=["mapped_data", "field_mappings"],
        optional_inputs=["cleansing_rules", "normalization_rules"],
        validators=[
            "data_format_validation",
            "normalization_validation",
            "quality_improvement_check",
        ],
        pre_handlers=["load_cleansing_rules", "prepare_cleansing_context"],
        post_handlers=[
            "persist_cleansed_data",
            "update_quality_metrics",
            "prepare_next_phase",
        ],
        crew_config={
            "crew_type": "data_cleansing",
            "crew_factory": "create_data_cleansing_crew",
            "input_mapping": {
                "mapped_data": "state.mapped_data",
                "field_mappings": "state.field_mappings",
                "cleansing_rules": "state.cleansing_rules",
            },
            "output_mapping": {
                "cleansed_data": "crew_results.cleansed_data",
                "cleansing_results": "crew_results.cleansing_results",
                "quality_improvement": "crew_results.quality_improvement",
                "normalization_stats": "crew_results.normalization_stats",
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
            "ui_route": "/discovery/data-cleansing",
            "ui_short_name": "Data Cleansing",  # Compact name for sidebar navigation
            "estimated_duration_minutes": 15,
            "icon": "filter",
            "help_text": "Clean and normalize data",
            "success_criteria": [
                "Data format compliance >= 95%",
                "Quality improvement visible",
                "Normalization complete",
            ],
        },
    )
