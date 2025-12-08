"""
Assessment Flow Phase Configurations

This module contains individual phase configurations for the Assessment flow.
Per ADR-027, some phases were migrated from Discovery flow (v3.0.0).
Per ADR-039, architecture_minimums added for compliance validation.

Phases:
- readiness_assessment: Assess migration readiness
- architecture_minimums: Validate technology compliance (ADR-039)
- complexity_analysis: Analyze migration complexity
- dependency_analysis: Analyze asset dependencies (migrated from Discovery)
- tech_debt_assessment: Assess technical debt (migrated from Discovery)
- risk_assessment: Assess migration risks
- recommendation_generation: Generate migration recommendations
"""

from .architecture_minimums_phase import get_architecture_minimums_phase  # ADR-039
from .complexity_analysis_phase import get_complexity_analysis_phase
from .dependency_analysis_phase import get_dependency_analysis_phase
from .readiness_assessment_phase import get_readiness_assessment_phase
from .recommendation_generation_phase import get_recommendation_generation_phase
from .risk_assessment_phase import get_risk_assessment_phase
from .tech_debt_assessment_phase import get_tech_debt_assessment_phase

__all__ = [
    "get_readiness_assessment_phase",
    "get_architecture_minimums_phase",  # ADR-039
    "get_complexity_analysis_phase",
    "get_dependency_analysis_phase",
    "get_tech_debt_assessment_phase",
    "get_risk_assessment_phase",
    "get_recommendation_generation_phase",
]
