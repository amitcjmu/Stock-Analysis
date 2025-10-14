"""
Assessment Flow Configuration
Per ADR-027: FlowTypeConfig as universal pattern

Comprehensive migration assessment and recommendation flow configuration.
Version 3.0.0 adds dependency_analysis and tech_debt_assessment phases
migrated from Discovery flow.
"""

from app.services.flow_type_registry import FlowCapabilities, FlowTypeConfig

# Import all phase configurations from assessment_phases
from .assessment_phases import (
    get_complexity_analysis_phase,
    get_dependency_analysis_phase,
    get_readiness_assessment_phase,
    get_recommendation_generation_phase,
    get_risk_assessment_phase,
    get_tech_debt_assessment_phase,
)


def get_assessment_flow_config() -> FlowTypeConfig:
    """
    Get the Assessment flow configuration

    Per ADR-027: Assessment includes analysis requiring completed Discovery data.

    Phases:
    1. Readiness Assessment - Assess migration readiness of assets
    2. Complexity Analysis - Analyze migration complexity
    3. Dependency Analysis - Analyze asset dependencies (migrated from Discovery)
    4. Technical Debt Assessment - Assess technical debt (migrated from Discovery)
    5. Risk Assessment - Assess migration risks
    6. Recommendation Generation - Generate migration recommendations
    """

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
        required_permissions=[
            "assessment.read",
            "assessment.write",
            "assessment.execute",
        ],
    )

    # Create the flow configuration
    assessment_config = FlowTypeConfig(
        name="assessment",
        display_name="Assessment Flow",
        description="Comprehensive migration assessment and recommendation flow",
        version="3.0.0",  # Major version for phase scope change
        phases=[
            get_readiness_assessment_phase(),
            get_complexity_analysis_phase(),
            get_dependency_analysis_phase(),  # Migrated from Discovery
            get_tech_debt_assessment_phase(),  # Migrated from Discovery
            get_risk_assessment_phase(),
            get_recommendation_generation_phase(),
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
            "confidence_threshold": 0.85,
        },
        initialization_handler="assessment_initialization",
        finalization_handler="assessment_finalization",
        error_handler="assessment_error_handler",
        metadata={
            "category": "analysis",
            "complexity": "high",
            "estimated_duration_minutes": 170,  # Increased for 2 additional phases
            "required_agents": [
                "readiness_agent",
                "complexity_agent",
                "dependency_agent",  # New
                "tech_debt_agent",  # New
                "risk_agent",
                "recommendation_agent",
            ],
            "output_formats": ["pdf", "excel", "json", "dashboard"],
            "prerequisite_flows": ["discovery"],
            "phase_scope_change": {
                "version": "3.0.0",
                "added_phases": ["dependency_analysis", "tech_debt_assessment"],
                "reason": "Migrated from Discovery per ADR-027",
                "prerequisite_note": "Requires completed Discovery flow with asset inventory",
            },
        },
        tags=[
            "assessment",
            "analysis",
            "recommendations",
            "risk",
            "planning_prerequisite",
        ],
    )

    return assessment_config
