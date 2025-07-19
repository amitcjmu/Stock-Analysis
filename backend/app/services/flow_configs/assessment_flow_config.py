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
        description="Assess migration readiness of discovered assets using architecture standards analysis",
        required_inputs=["asset_inventory", "assessment_criteria"],
        optional_inputs=["business_priorities", "technical_constraints", "compliance_requirements"],
        validators=["required_fields", "assessment_validation", "inventory_completeness"],
        pre_handlers=["readiness_preparation"],
        post_handlers=["readiness_scoring"],
        crew_config={
            "crew_type": "architecture_standards_crew",
            "crew_factory": "create_architecture_standards_crew",
            "input_mapping": {
                "engagement_context": "state.engagement_context",
                "selected_applications": "asset_inventory.applications",
                "application_metadata": "asset_inventory.metadata",
                "existing_standards": "assessment_criteria.architecture_standards",
                "business_constraints": "business_priorities",
                "risk_tolerance": "assessment_criteria.risk_tolerance"
            },
            "output_mapping": {
                "readiness_scores": "crew_results.application_compliance",
                "technical_readiness": "crew_results.technical_debt_scores",
                "architecture_standards": "crew_results.engagement_standards",
                "upgrade_requirements": "crew_results.upgrade_recommendations",
                "business_readiness": "crew_results.exceptions",
                "crew_confidence": "crew_results.crew_confidence"
            },
            "execution_config": {
                "timeout_seconds": 180,           # Conservative 3 minutes
                "temperature": 0.1,               # Very conservative for accuracy
                "max_iterations": 1,
                "allow_delegation": True,         # Enable agent collaboration
                "enable_memory": False,           # Conservative mode
                "enable_caching": True,           # Performance optimization
                "enable_parallel": False,         # Sequential for accuracy
                "conservative_mode": True
            },
            "llm_config": {
                "temperature": 0.1,               # Conservative settings
                "max_tokens": 4000,
                "frequency_penalty": 0.1,
                "presence_penalty": 0.1,
                "stop_sequences": ["HALLUCINATION", "SPECULATION", "ASSUMPTION"]
            },
            "validation_mapping": {
                "required_fields": [
                    "engagement_standards", 
                    "application_compliance", 
                    "technical_debt_scores",
                    "crew_confidence"
                ],
                "success_criteria": {
                    "crew_confidence": {"min": 0.6},
                    "standards_count": {"min": 1},
                    "compliance_coverage": {"min": 0.8},
                    "hallucination_risk": {"max": 0.1}
                }
            },
            "performance_config": {
                "enable_readiness_focus": True,
                "prioritize_technical_readiness": True,
                "generate_readiness_scores": True,
                "confidence_threshold": 0.6
            }
        },
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
            "min_score_threshold": 0.6,
            "architecture_standards_enabled": True,
            "ai_powered_assessment": True,
            "hallucination_protected": True,
            "factual_accuracy_enforced": True
        }
    )
    
    # Phase 2: Complexity Analysis
    complexity_analysis_phase = PhaseConfig(
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
                "network_topology": "state.network_topology"
            },
            "output_mapping": {
                "complexity_scores": "crew_results.component_scores",
                "technical_debt_analysis": "crew_results.tech_debt_analysis",
                "component_inventory": "crew_results.components",
                "dependency_analysis": "crew_results.dependency_map",
                "migration_groups": "crew_results.migration_groups",
                "complexity_insights": "crew_results.analysis_insights",
                "crew_confidence": "crew_results.crew_confidence"
            },
            "execution_config": {
                "timeout_seconds": 180,           # Conservative 3 minutes
                "temperature": 0.1,               # Very conservative for accuracy
                "max_iterations": 1,
                "allow_delegation": True,         # Enable agent collaboration
                "enable_memory": False,           # Conservative mode
                "enable_caching": True,           # Performance optimization
                "enable_parallel": False,         # Sequential for accuracy
                "conservative_mode": True
            },
            "llm_config": {
                "temperature": 0.1,               # Conservative settings
                "max_tokens": 4000,
                "frequency_penalty": 0.1,
                "presence_penalty": 0.1,
                "stop_sequences": ["HALLUCINATION", "SPECULATION", "ASSUMPTION"]
            },
            "validation_mapping": {
                "required_fields": [
                    "component_scores",
                    "tech_debt_analysis",
                    "component_inventory",
                    "crew_confidence"
                ],
                "success_criteria": {
                    "crew_confidence": {"min": 0.6},
                    "components_count": {"min": 1},
                    "debt_analysis_coverage": {"min": 0.8},
                    "hallucination_risk": {"max": 0.1}
                }
            },
            "performance_config": {
                "enable_complexity_focus": True,
                "prioritize_technical_debt": True,
                "generate_complexity_scores": True,
                "confidence_threshold": 0.6
            }
        },
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
            "ai_analysis_enabled": True,
            "component_analysis_enabled": True,
            "technical_debt_specialization": True,
            "hallucination_protected": True,
            "factual_accuracy_enforced": True
        }
    )
    
    # Phase 3: Risk Assessment
    risk_assessment_phase = PhaseConfig(
        name="risk_assessment",
        display_name="Risk Assessment",
        description="Assess migration risks and mitigation strategies using enhanced 6R strategy analysis",
        required_inputs=["complexity_scores", "risk_matrix"],
        optional_inputs=["historical_data", "industry_benchmarks", "compliance_risks"],
        validators=["risk_validation", "mitigation_validation"],
        pre_handlers=["risk_identification"],
        post_handlers=["mitigation_planning"],
        crew_config={
            "crew_type": "sixr_strategy_crew",
            "crew_factory": "create_enhanced_sixr_strategy_crew",
            "input_mapping": {
                "components": "state.application_components",
                "tech_debt_analysis": "complexity_scores.tech_debt_items",
                "architecture_standards": "state.architecture_standards",
                "business_context": "state.business_context",
                "resource_constraints": "state.resource_constraints",
                "risk_matrix": "risk_matrix",
                "historical_data": "historical_data",
                "industry_benchmarks": "industry_benchmarks",
                "compliance_risks": "compliance_risks"
            },
            "output_mapping": {
                "risk_assessments": "crew_results.risk_assessments",
                "component_treatments": "crew_results.component_treatments",
                "overall_risk_score": "crew_results.overall_risk_score",
                "mitigation_strategies": "crew_results.mitigation_strategies",
                "sixr_recommendations": "crew_results.component_treatments",
                "crew_confidence": "crew_results.crew_confidence"
            },
            "execution_config": {
                "timeout_seconds": 180,           # Conservative 3 minutes
                "temperature": 0.1,               # Very conservative for risk accuracy
                "max_iterations": 1,
                "allow_delegation": True,         # Enable agent collaboration
                "enable_memory": False,           # Conservative mode
                "enable_caching": True,           # Performance optimization
                "enable_parallel": False,         # Sequential for accuracy
                "conservative_mode": True
            },
            "llm_config": {
                "temperature": 0.1,               # Conservative settings
                "max_tokens": 4000,
                "frequency_penalty": 0.1,
                "presence_penalty": 0.1,
                "stop_sequences": ["HALLUCINATION", "SPECULATION", "ASSUMPTION"]
            },
            "validation_mapping": {
                "required_fields": [
                    "risk_assessments",
                    "component_treatments",
                    "overall_risk_score",
                    "mitigation_strategies",
                    "crew_confidence"
                ],
                "success_criteria": {
                    "crew_confidence": {"min": 0.6},
                    "risk_coverage": {"min": 0.8},
                    "mitigation_completeness": {"min": 0.7},
                    "hallucination_risk": {"max": 0.1}
                }
            },
            "performance_config": {
                "enable_risk_assessment": True,
                "risk_matrix_scoring": True,
                "security_compliance_focus": True,
                "sixr_integration": True,
                "confidence_threshold": 0.6
            }
        },
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
            "mitigation_required": True,
            "sixr_integration": True,
            "enhanced_risk_assessment": True,
            "hallucination_protected": True,
            "factual_accuracy_enforced": True
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