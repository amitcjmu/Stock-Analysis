"""
Complexity Analysis Phase Configuration

Configuration for the complexity analysis phase of the Assessment flow.
Analyzes migration complexity using comprehensive component analysis.
"""

from app.services.flow_type_registry import PhaseConfig, RetryConfig


def get_complexity_analysis_phase() -> PhaseConfig:
    """
    Get the Complexity Analysis phase configuration

    Analyzes migration complexity for each asset using comprehensive
    component analysis.
    """

    # Define retry configuration for phases
    default_retry = RetryConfig(
        max_attempts=3,
        initial_delay_seconds=2.0,
        backoff_multiplier=2.0,
        max_delay_seconds=30.0,
    )

    return PhaseConfig(
        name="complexity_analysis",
        display_name="Complexity Analysis",
        description="Analyze migration complexity for each asset using comprehensive component analysis",
        required_inputs=["readiness_scores", "complexity_rules"],
        optional_inputs=["dependency_map", "integration_points", "customization_level"],
        validators=["complexity_validation", "score_validation"],
        pre_handlers=["complexity_preparation"],
        post_handlers=["complexity_categorization"],
        crew_config={
            "crew_type": "component_analysis_crew",
            "crew_factory": "create_component_analysis_crew",
            "input_mapping": {
                "application_metadata": "state.application_metadata",
                "discovery_data": "readiness_scores.discovery_data",
                "architecture_standards": "state.architecture_standards",
                "complexity_rules": "complexity_rules",
                "dependency_map": "dependency_map",
                "integration_points": "integration_points",
                "customization_level": "customization_level",
                "technology_lifecycle": "state.technology_lifecycle",
                "security_requirements": "state.security_requirements",
                "architecture_patterns": "state.architecture_patterns",
                "network_topology": "state.network_topology",
            },
            "output_mapping": {
                "complexity_scores": "crew_results.component_scores",
                "technical_debt_analysis": "crew_results.tech_debt_analysis",
                "component_inventory": "crew_results.components",
                "dependency_analysis": "crew_results.dependency_map",
                "migration_groups": "crew_results.migration_groups",
                "complexity_insights": "crew_results.analysis_insights",
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
                    "component_scores",
                    "tech_debt_analysis",
                    "component_inventory",
                    "crew_confidence",
                ],
                "success_criteria": {
                    "crew_confidence": {"min": 0.6},
                    "components_count": {"min": 1},
                    "debt_analysis_coverage": {"min": 0.8},
                    "hallucination_risk": {"max": 0.1},
                },
            },
            "performance_config": {
                "enable_complexity_focus": True,
                "prioritize_technical_debt": True,
                "generate_complexity_scores": True,
                "confidence_threshold": 0.6,
            },
        },
        can_pause=True,
        can_skip=False,
        retry_config=default_retry,
        timeout_seconds=2100,  # 35 minutes
        metadata={
            "ui_route": "/assessment/:flowId/complexity",  # Correct route for complexity phase
            "ui_short_name": "Complexity",  # Compact name for sidebar navigation
            "estimated_duration_minutes": 35,
            "icon": "activity",
            "help_text": "Analyze architectural migration complexity (not code metrics)",
            "complexity_factors": [
                "technical_debt",
                "dependencies",
                "data_volume",
                "integration_complexity",
                "customization_level",
            ],
            "complexity_levels": ["low", "medium", "high", "very_high"],
            "ai_analysis_enabled": True,
            "component_analysis_enabled": True,
            "technical_debt_specialization": True,
            "hallucination_protected": True,
            "factual_accuracy_enforced": True,
        },
    )
