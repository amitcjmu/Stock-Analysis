"""
Assessment Flow Configuration
MFO-043: Create Assessment flow configuration

Comprehensive migration assessment and recommendation flow configuration
with all 4 phases and associated validators/handlers.
"""

from typing import Dict, Any, List

from app.services.flow_type_registry import (
    FlowTypeConfig, 
    PhaseConfig, 
    FlowCapabilities,
    RetryConfig
)


def get_assessment_flow_config() -> FlowTypeConfig:
    """
    Get the Assessment flow configuration with all 4 phases
    
    Phases:
    1. Readiness Assessment - Assess migration readiness of assets
    2. Complexity Analysis - Analyze migration complexity  
    3. Risk Assessment - Assess migration risks
    4. Recommendation Generation - Generate migration recommendations
    """
    
    # Define retry configuration for phases
    default_retry = RetryConfig(
        max_attempts=3,
        initial_delay_seconds=2.0,
        backoff_multiplier=2.0,
        max_delay_seconds=30.0
    )
    
    # Phase 1: Readiness Assessment
    readiness_assessment_phase = PhaseConfig(
        name="readiness_assessment",
        display_name="Readiness Assessment",
        description="Assess migration readiness of discovered assets",
        required_inputs=["asset_inventory", "assessment_criteria"],
        optional_inputs=["business_priorities", "technical_constraints", "compliance_requirements"],
        validators=["required_fields", "assessment_validation", "inventory_completeness"],
        pre_handlers=["readiness_preparation"],
        post_handlers=["readiness_scoring"],
        can_pause=True,
        can_skip=False,
        retry_config=default_retry,
        timeout_seconds=2700,  # 45 minutes
        metadata={
            "assessment_dimensions": [
                "technical_readiness",
                "business_readiness", 
                "operational_readiness",
                "security_readiness"
            ],
            "scoring_method": "weighted_average",
            "min_score_threshold": 0.6
        }
    )
    
    # Phase 2: Complexity Analysis
    complexity_analysis_phase = PhaseConfig(
        name="complexity_analysis",
        display_name="Complexity Analysis",
        description="Analyze migration complexity for each asset",
        required_inputs=["readiness_scores", "complexity_rules"],
        optional_inputs=["dependency_map", "integration_points", "customization_level"],
        validators=["complexity_validation", "score_validation"],
        pre_handlers=["complexity_preparation"],
        post_handlers=["complexity_categorization"],
        can_pause=True,
        can_skip=False,
        retry_config=default_retry,
        timeout_seconds=2100,  # 35 minutes
        metadata={
            "complexity_factors": [
                "technical_debt",
                "dependencies",
                "data_volume",
                "integration_complexity",
                "customization_level"
            ],
            "complexity_levels": ["low", "medium", "high", "very_high"],
            "ai_analysis_enabled": True
        }
    )
    
    # Phase 3: Risk Assessment
    risk_assessment_phase = PhaseConfig(
        name="risk_assessment",
        display_name="Risk Assessment",
        description="Assess migration risks and mitigation strategies",
        required_inputs=["complexity_scores", "risk_matrix"],
        optional_inputs=["historical_data", "industry_benchmarks", "compliance_risks"],
        validators=["risk_validation", "mitigation_validation"],
        pre_handlers=["risk_identification"],
        post_handlers=["mitigation_planning"],
        can_pause=True,
        can_skip=False,
        retry_config=default_retry,
        timeout_seconds=1800,  # 30 minutes
        metadata={
            "risk_categories": [
                "technical_risk",
                "business_risk",
                "operational_risk",
                "security_risk",
                "compliance_risk"
            ],
            "risk_scoring": "probability_impact_matrix",
            "mitigation_required": True
        }
    )
    
    # Phase 4: Recommendation Generation
    recommendation_generation_phase = PhaseConfig(
        name="recommendation_generation",
        display_name="Recommendation Generation",
        description="Generate migration recommendations and roadmap",
        required_inputs=["risk_scores", "business_priorities"],
        optional_inputs=["cost_constraints", "timeline_preferences", "resource_availability"],
        validators=["recommendation_validation", "roadmap_validation"],
        pre_handlers=["recommendation_analysis"],
        post_handlers=["roadmap_generation"],
        completion_handler="assessment_completion",
        can_pause=True,
        can_skip=False,
        retry_config=default_retry,
        timeout_seconds=1500,  # 25 minutes
        metadata={
            "recommendation_types": [
                "migration_approach",
                "wave_grouping",
                "technology_stack",
                "resource_requirements",
                "timeline_optimization"
            ],
            "ai_powered_recommendations": True,
            "scenario_planning": True
        }
    )
    
    # Define flow capabilities
    capabilities = FlowCapabilities(
        supports_pause_resume=True,
        supports_rollback=True,
        supports_branching=False,
        supports_iterations=True,
        max_iterations=3,
        supports_scheduling=True,
        supports_parallel_phases=False,
        supports_checkpointing=True,
        required_permissions=["assessment.read", "assessment.write", "assessment.execute"]
    )
    
    # Create the flow configuration
    assessment_config = FlowTypeConfig(
        name="assessment",
        display_name="Assessment Flow",
        description="Comprehensive migration assessment and recommendation flow",
        version="2.0.0",
        phases=[
            readiness_assessment_phase,
            complexity_analysis_phase,
            risk_assessment_phase,
            recommendation_generation_phase
        ],
        capabilities=capabilities,
        default_configuration={
            "enable_risk_scoring": True,
            "auto_generate_reports": True,
            "assessment_depth": "comprehensive",
            "include_business_impact": True,
            "agent_collaboration": True,
            "use_historical_data": True,
            "enable_what_if_scenarios": True,
            "confidence_threshold": 0.85
        },
        initialization_handler="assessment_initialization",
        finalization_handler="assessment_finalization",
        error_handler="assessment_error_handler",
        metadata={
            "category": "analysis",
            "complexity": "high",
            "estimated_duration_minutes": 120,
            "required_agents": ["readiness_agent", "complexity_agent", "risk_agent", "recommendation_agent"],
            "output_formats": ["pdf", "excel", "json", "dashboard"],
            "prerequisite_flows": ["discovery"]
        },
        tags=["assessment", "analysis", "recommendations", "risk", "planning_prerequisite"]
    )
    
    return assessment_config