"""
Field Mapping Phase Configuration

Configuration for the field mapping phase of the Discovery flow.
This phase maps source fields to target schema.
"""

from app.services.flow_type_registry import PhaseConfig, RetryConfig


def get_field_mapping_phase() -> PhaseConfig:
    """
    Get the Field Mapping & Transformation phase configuration

    Maps source fields to target schema and defines transformations.
    """

    # Define retry configuration for phases
    default_retry = RetryConfig(
        max_attempts=3,
        initial_delay_seconds=5.0,
        backoff_multiplier=2.0,
        max_delay_seconds=60.0,
    )

    return PhaseConfig(
        name="field_mapping",
        display_name="Field Mapping & Transformation",
        description="Map source fields to target schema and define transformations",
        required_inputs=["validated_data", "target_schema"],
        optional_inputs=["mapping_suggestions", "transformation_rules"],
        validators=[
            "schema_compatibility_check",
            "mapping_completeness_check",
            "transformation_validation",
        ],
        pre_handlers=["load_target_schema", "generate_mapping_suggestions"],
        post_handlers=[
            "persist_field_mappings",
            "validate_mappings",
            "prepare_next_phase",
        ],
        crew_config={
            "crew_type": "field_mapping",
            "crew_factory": "create_field_mapping_crew",
            "input_mapping": {
                "validated_data": "state.validated_data",
                "target_schema": "state.target_schema",
                "mapping_suggestions": "state.mapping_suggestions",
            },
            "output_mapping": {
                "field_mappings": "crew_results.field_mappings",
                "transformation_rules": "crew_results.transformation_rules",
                "mapping_confidence": "crew_results.mapping_confidence",
                "unmapped_fields": "crew_results.unmapped_fields",
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
            "ui_route": "/discovery/field-mapping",
            "estimated_duration_minutes": 20,
            "icon": "git-branch",
            "help_text": "Map source fields to target schema",
            "success_criteria": [
                "All required fields mapped",
                "Mapping confidence >= 85%",
                "Transformations validated",
            ],
        },
    )
