"""
Asset Inventory Phase Configuration

Configuration for the asset inventory phase of the Discovery flow.
This phase creates asset records from cleansed data.
"""

from app.services.flow_type_registry import PhaseConfig, RetryConfig


def get_asset_inventory_phase() -> PhaseConfig:
    """
    Get the Asset Inventory Creation phase configuration

    Creates asset records from cleansed data and prepares for assessment.
    """

    # Define retry configuration for phases
    default_retry = RetryConfig(
        max_attempts=3,
        initial_delay_seconds=5.0,
        backoff_multiplier=2.0,
        max_delay_seconds=60.0,
    )

    return PhaseConfig(
        name="asset_inventory",
        display_name="Asset Inventory Creation",
        description="Create asset records from cleansed data",
        required_inputs=["cleansed_data"],
        optional_inputs=["asset_templates", "inventory_rules"],
        validators=[
            "asset_completeness_check",
            "duplicate_detection",
            "relationship_validation",
        ],
        pre_handlers=["load_asset_templates", "prepare_inventory_context"],
        post_handlers=[
            "persist_asset_inventory",
            "generate_inventory_report",
            "prepare_assessment_flow",
        ],
        crew_config={
            "crew_type": "asset_inventory",
            "crew_factory": "create_asset_inventory_crew",
            "input_mapping": {
                "cleansed_data": "state.cleansed_data",
                "asset_templates": "state.asset_templates",
                "inventory_rules": "state.inventory_rules",
            },
            "output_mapping": {
                "asset_inventory": "crew_results.asset_inventory",
                "inventory_stats": "crew_results.inventory_stats",
                "asset_relationships": "crew_results.asset_relationships",
                "inventory_completeness": "crew_results.inventory_completeness",
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
            "ui_route": "/discovery/asset-inventory",
            "estimated_duration_minutes": 20,
            "icon": "database",
            "help_text": "Create asset inventory from cleansed data",
            "success_criteria": [
                "All assets created",
                "Inventory completeness >= 90%",
                "No duplicate assets",
            ],
        },
    )
