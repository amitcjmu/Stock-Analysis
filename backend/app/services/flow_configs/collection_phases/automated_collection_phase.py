"""
Automated Collection Phase Configuration

Configuration for the automated collection phase of the Collection flow.
Collects data automatically using platform-specific adapters and intelligent orchestration.
"""

from app.services.flow_type_registry import PhaseConfig, RetryConfig


def get_automated_collection_phase() -> PhaseConfig:
    """
    Get the Automated Collection phase configuration

    Collects data automatically using platform-specific adapters and intelligent orchestration.
    """

    return PhaseConfig(
        name="automated_collection",
        display_name="Automated Collection",
        description="Collect data automatically using platform-specific adapters and intelligent orchestration",
        required_inputs=["detected_platforms", "adapter_configs"],
        optional_inputs=["collection_filters", "priority_resources", "rate_limits"],
        validators=["collection_validation", "data_quality_validation"],
        pre_handlers=["adapter_preparation"],
        post_handlers=["collection_data_normalization"],
        crew_config={
            "crew_type": "automated_collection_crew",
            "crew_factory": "create_automated_collection_crew",
            "input_mapping": {
                "platforms": "state.detected_platforms",
                "adapter_configs": "adapter_configs",
                "context": {
                    "automation_tier": "state.automation_tier",
                    "tier_assignments": "state.tier_assignments",
                    "collection_filters": "collection_filters",
                    "priority_resources": "priority_resources",
                    "rate_limits": "rate_limits",
                },
            },
            "output_mapping": {
                "collected_data": "crew_results.collected_data",
                "collection_metrics": "crew_results.metrics",
                "quality_scores": "crew_results.quality_scores",
                "collection_gaps": "crew_results.identified_gaps",
                "adapter_results": "crew_results.adapter_results",
                "crew_confidence": "crew_results.crew_confidence",
            },
            "execution_config": {
                "timeout_seconds": 300,  # 5 minutes base
                "temperature": 0.1,  # Very conservative
                "max_iterations": 1,
                "allow_delegation": True,  # Enable adapter delegation
                "enable_memory": False,  # Conservative mode
                "enable_caching": True,  # Performance optimization
                "enable_parallel": True,  # Parallel adapter execution
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
                    "collected_data",
                    "quality_scores",
                    "adapter_results",
                    "crew_confidence",
                ],
                "success_criteria": {
                    "crew_confidence": {"min": 0.6},
                    "collection_success_rate": {"min": 0.7},
                    "data_quality_score": {"min": 0.6},
                    "hallucination_risk": {"max": 0.1},
                },
            },
            "performance_config": {
                "batch_size": 100,
                "parallel_adapters": 5,
                "rate_limiting": True,
                "adaptive_collection": True,
                "quality_based_routing": True,
                "confidence_threshold": 0.6,
            },
        },
        can_pause=True,
        can_skip=False,
        retry_config=RetryConfig(
            max_attempts=5,  # More retries for collection
            initial_delay_seconds=5.0,
            backoff_multiplier=2.0,
            max_delay_seconds=60.0,
        ),
        timeout_seconds=3600,  # 60 minutes
        metadata={
            "supports_incremental_collection": True,
            "adapter_based_collection": True,
            "ai_orchestrated_collection": True,
            "quality_thresholds": {
                "tier_1": 0.95,
                "tier_2": 0.85,
                "tier_3": 0.75,
                "tier_4": 0.60,
            },
            "hallucination_protected": True,
            "factual_accuracy_enforced": True,
        },
    )
