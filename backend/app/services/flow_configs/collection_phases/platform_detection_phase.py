"""
Platform Detection Phase Configuration

Configuration for the platform detection phase of the Collection flow.
Detects and identifies target platforms for data collection using intelligent agents.
"""

from app.services.flow_type_registry import PhaseConfig, RetryConfig


def get_platform_detection_phase() -> PhaseConfig:
    """
    Get the Platform Detection phase configuration

    Detects and identifies target platforms for data collection using intelligent agents.
    """

    # Define retry configuration for phases
    default_retry = RetryConfig(
        max_attempts=3,
        initial_delay_seconds=2.0,
        backoff_multiplier=2.0,
        max_delay_seconds=30.0,
    )

    return PhaseConfig(
        name="platform_detection",
        display_name="Platform Detection",
        description="Detect and identify target platforms for data collection using intelligent agents",
        required_inputs=["environment_config", "automation_tier"],
        optional_inputs=["credentials", "discovery_scope", "platform_hints"],
        validators=["platform_validation", "credential_validation"],
        pre_handlers=["collection_initialization"],
        post_handlers=["platform_inventory_creation"],
        crew_config={
            "crew_type": "platform_detection_crew",
            "crew_factory": "create_platform_detection_crew",
            "input_mapping": {
                "infrastructure_data": "state.environment_config",
                "context": {
                    "platform_info": "state.platform_info",
                    "credentials_available": "credentials",
                    "automation_preferences": "state.automation_preferences",
                    "automation_tier": "automation_tier",
                    "discovery_scope": "discovery_scope",
                },
            },
            "output_mapping": {
                "detected_platforms": "crew_results.platforms",
                "adapter_recommendations": "crew_results.recommended_adapters",
                "platform_metadata": "crew_results.platform_metadata",
                "tier_assignments": "crew_results.tier_assignments",
                "crew_confidence": "crew_results.crew_confidence",
            },
            "execution_config": {
                "timeout_seconds": 180,  # Conservative 3 minutes
                "temperature": 0.1,  # Very conservative for accuracy
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
                    "platforms",
                    "recommended_adapters",
                    "tier_assignments",
                    "crew_confidence",
                ],
                "success_criteria": {
                    "crew_confidence": {"min": 0.6},
                    "platforms_count": {"min": 1},
                    "adapter_coverage": {"min": 0.8},
                    "hallucination_risk": {"max": 0.1},
                },
            },
            "performance_config": {
                "enable_platform_detection": True,
                "prioritize_automation_tiers": True,
                "generate_adapter_mappings": True,
                "confidence_threshold": 0.6,
            },
        },
        can_pause=True,
        can_skip=False,
        retry_config=default_retry,
        timeout_seconds=900,  # 15 minutes
        metadata={
            "supports_auto_discovery": True,
            "platform_types": ["cloud", "on-premise", "hybrid", "saas"],
            "ai_powered_detection": True,
            "hallucination_protected": True,
            "factual_accuracy_enforced": True,
        },
    )
