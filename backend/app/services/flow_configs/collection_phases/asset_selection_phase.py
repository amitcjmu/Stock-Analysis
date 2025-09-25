"""
Asset Selection Phase Configuration

Configuration for the asset selection phase of the Collection flow.
This phase replaces the old platform_detection and automated_collection phases,
combining platform detection and asset selection into a unified phase.
"""

from app.services.flow_type_registry import PhaseConfig, RetryConfig


def get_asset_selection_phase() -> PhaseConfig:
    """
    Get the Asset Selection phase configuration

    Combines platform detection and asset selection into a unified phase.
    Detects target platforms and allows users to select assets for collection.
    """

    # Define retry configuration for phases
    default_retry = RetryConfig(
        max_attempts=3,
        initial_delay_seconds=2.0,
        backoff_multiplier=2.0,
        max_delay_seconds=30.0,
    )

    return PhaseConfig(
        name="asset_selection",
        display_name="Asset Selection",
        description="Detect platforms and select assets for collection",
        required_inputs=["engagement_context", "client_account_id"],
        optional_inputs=[
            "discovery_data",
            "environment_config",
            "platform_hints",
            "selected_assets",
            "automation_preferences",
        ],
        validators=["platform_validation", "asset_validation"],
        pre_handlers=["asset_selection_preparation"],
        post_handlers=["asset_collection_initiation"],
        crew_config={
            "crew_type": "asset_selection_crew",
            "crew_factory": "create_asset_selection_crew",
            "input_mapping": {
                "engagement_context": "state.engagement_context",
                "discovery_data": "state.discovery_data",
                "environment_config": "environment_config",
                "platform_hints": "platform_hints",
                "selected_assets": "selected_assets",
                "context": {
                    "client_account_id": "client_account_id",
                    "automation_tier": "state.automation_tier",
                    "automation_preferences": "automation_preferences",
                },
            },
            "output_mapping": {
                "detected_platforms": "crew_results.detected_platforms",
                "platform_confidence": "crew_results.platform_confidence",
                "selected_assets": "crew_results.selected_assets",
                "asset_metadata": "crew_results.asset_metadata",
                "collection_strategy": "crew_results.collection_strategy",
                "collection_adapters": "crew_results.collection_adapters",
                "collected_data": "crew_results.collected_data",
                "collection_metrics": "crew_results.collection_metrics",
                "quality_scores": "crew_results.quality_scores",
                "crew_confidence": "crew_results.crew_confidence",
            },
            "execution_config": {
                "timeout_seconds": 240,  # 4 minutes for combined phase
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
        },
        retry_config=default_retry,
    )
