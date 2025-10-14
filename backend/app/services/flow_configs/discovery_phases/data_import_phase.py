"""
Data Import Phase Configuration

Configuration for the data import phase of the Discovery flow.
This phase imports CMDB data and validates format/quality.
"""

from app.services.flow_type_registry import PhaseConfig, RetryConfig


def get_data_import_phase() -> PhaseConfig:
    """
    Get the Data Import & Validation phase configuration

    Imports CMDB data and validates format/quality before proceeding.
    """

    # Define retry configuration for phases
    default_retry = RetryConfig(
        max_attempts=3,
        initial_delay_seconds=5.0,
        backoff_multiplier=2.0,
        max_delay_seconds=60.0,
    )

    return PhaseConfig(
        name="data_import",
        display_name="Data Import & Validation",
        description="Import CMDB data and validate format/quality",
        required_inputs=["file_upload"],
        optional_inputs=["import_options"],
        validators=[
            "file_format_validation",
            "data_quality_check",
            "schema_validation",
        ],
        pre_handlers=["create_import_record", "initialize_storage"],
        post_handlers=[
            "persist_completion_flag",
            "notify_completion",
            "prepare_next_phase",
        ],
        crew_config={
            "crew_type": "data_import_validation",
            "crew_factory": "create_data_import_validation_crew",
            "input_mapping": {
                "file_data": "state.file_upload",
                "import_options": "state.import_options",
            },
            "output_mapping": {
                "import_results": "crew_results.validation_results",
                "data_quality_score": "crew_results.quality_score",
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
            "ui_route": "/discovery/cmdb-import",
            "estimated_duration_minutes": 10,
            "icon": "upload",
            "help_text": "Upload your CMDB export file",
            "success_criteria": [
                "File format valid",
                "No critical data quality issues",
                "At least 1 asset imported",
            ],
        },
    )
