"""
Dependency Analysis Phase Configuration

Configuration for the dependency analysis phase of the Assessment flow.
Migrated from Discovery flow per ADR-027.

This phase analyzes dependencies and relationships between assets,
which requires completed asset inventory from Discovery flow.
"""

from app.services.flow_type_registry import PhaseConfig, RetryConfig


def get_dependency_analysis_phase() -> PhaseConfig:
    """
    Get the Dependency Analysis phase configuration

    Migrated from Discovery flow in v3.0.0 per ADR-027.
    Analyzes dependencies and relationships between assets.
    """

    # Define retry configuration for phases
    default_retry = RetryConfig(
        max_attempts=3,
        initial_delay_seconds=5.0,
        backoff_multiplier=2.0,
        max_delay_seconds=60.0,
    )

    return PhaseConfig(
        name="dependency_analysis",
        display_name="Dependency Analysis",
        description="Analyze dependencies and relationships between assets",
        required_inputs=["asset_inventory"],
        optional_inputs=["dependency_rules", "relationship_types"],
        validators=[
            "asset_inventory_exists",
            "dependency_validation",
            "relationship_validation",
        ],
        pre_handlers=["load_asset_relationships", "prepare_dependency_context"],
        post_handlers=[
            "persist_dependency_map",
            "generate_dependency_report",
            "prepare_next_phase",
        ],
        crew_config={
            "crew_type": "dependency_analysis",
            "crew_factory": "create_dependency_analysis_crew",
            "input_mapping": {
                "asset_inventory": "state.asset_inventory",
                "dependency_rules": "state.dependency_rules",
                "relationship_types": "state.relationship_types",
            },
            "output_mapping": {
                "dependency_map": "crew_results.dependency_map",
                "relationship_graph": "crew_results.relationship_graph",
                "dependency_complexity": "crew_results.dependency_complexity",
                "critical_dependencies": "crew_results.critical_dependencies",
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
            "ui_route": "/assessment/dependency-analysis",
            "estimated_duration_minutes": 20,
            "icon": "share-2",
            "help_text": "Analyze asset dependencies and relationships",
            "migration_note": "Moved from Discovery flow in v3.0.0",
            "success_criteria": [
                "Dependency map created",
                "All relationships identified",
                "Critical dependencies flagged",
            ],
        },
    )
