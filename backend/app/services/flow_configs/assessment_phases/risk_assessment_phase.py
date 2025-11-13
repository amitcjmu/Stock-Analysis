"""
Risk Assessment Phase Configuration

Configuration for the risk assessment phase of the Assessment flow.
Assesses migration risks and mitigation strategies using enhanced 6R analysis.
"""

from app.services.flow_type_registry import PhaseConfig, RetryConfig


def get_risk_assessment_phase() -> PhaseConfig:
    """
    Get the Risk Assessment phase configuration

    Assesses migration risks and mitigation strategies using enhanced
    6R strategy analysis.
    """

    # Define retry configuration for phases
    default_retry = RetryConfig(
        max_attempts=3,
        initial_delay_seconds=2.0,
        backoff_multiplier=2.0,
        max_delay_seconds=30.0,
    )

    return PhaseConfig(
        name="risk_assessment",
        display_name="Risk Assessment",
        description="Assess migration risks and mitigation strategies using enhanced 6R strategy analysis",
        required_inputs=["complexity_scores", "risk_matrix"],
        optional_inputs=["historical_data", "industry_benchmarks", "compliance_risks"],
        validators=["risk_validation", "mitigation_validation"],
        pre_handlers=["risk_identification"],
        post_handlers=["mitigation_planning"],
        crew_config={
            "crew_type": "assessment_strategy_crew",  # Phase 6: Migrated from sixr_strategy_crew
            "crew_factory": "create_enhanced_assessment_strategy_crew",  # Phase 6: Renamed
            "input_mapping": {
                "components": "state.application_components",
                "tech_debt_analysis": "complexity_scores.tech_debt_items",
                "architecture_standards": "state.architecture_standards",
                "business_context": "state.business_context",
                "resource_constraints": "state.resource_constraints",
                "risk_matrix": "risk_matrix",
                "historical_data": "historical_data",
                "industry_benchmarks": "industry_benchmarks",
                "compliance_risks": "compliance_risks",
            },
            "output_mapping": {
                "risk_assessments": "crew_results.risk_assessments",
                "component_treatments": "crew_results.component_treatments",
                "overall_risk_score": "crew_results.overall_risk_score",
                "mitigation_strategies": "crew_results.mitigation_strategies",
                "sixr_recommendations": "crew_results.component_treatments",
                "crew_confidence": "crew_results.crew_confidence",
            },
            "execution_config": {
                "timeout_seconds": 180,  # Conservative 3 minutes
                "temperature": 0.1,  # Very conservative for risk accuracy
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
                    "risk_assessments",
                    "component_treatments",
                    "overall_risk_score",
                    "mitigation_strategies",
                    "crew_confidence",
                ],
                "success_criteria": {
                    "crew_confidence": {"min": 0.6},
                    "risk_coverage": {"min": 0.8},
                    "mitigation_completeness": {"min": 0.7},
                    "hallucination_risk": {"max": 0.1},
                },
            },
            "performance_config": {
                "enable_risk_assessment": True,
                "risk_matrix_scoring": True,
                "security_compliance_focus": True,
                "sixr_integration": True,
                "confidence_threshold": 0.6,
            },
        },
        can_pause=True,
        can_skip=False,
        retry_config=default_retry,
        timeout_seconds=1800,  # 30 minutes
        metadata={
            "ui_route": "/assessment/:flowId/sixr-review",  # Fix #632: Use React Router syntax
            "ui_short_name": "Risk",  # Compact name for sidebar navigation
            "estimated_duration_minutes": 30,
            "icon": "alert-circle",
            "help_text": "Assess migration risks and mitigation strategies",
            "risk_categories": [
                "technical_risk",
                "business_risk",
                "operational_risk",
                "security_risk",
                "compliance_risk",
            ],
            "risk_scoring": "probability_impact_matrix",
            "mitigation_required": True,
            "sixr_integration": True,
            "enhanced_risk_assessment": True,
            "hallucination_protected": True,
            "factual_accuracy_enforced": True,
        },
    )
