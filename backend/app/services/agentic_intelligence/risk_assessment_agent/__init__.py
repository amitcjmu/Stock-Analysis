"""
RiskAssessment Agent - Public API

This module preserves backward compatibility by exposing all public classes and functions.
"""

from app.services.agentic_intelligence.risk_assessment_agent.base import (
    RiskAssessmentAgent as _BaseAgent,
)
from app.services.agentic_intelligence.risk_assessment_agent.crew_builder import (
    CrewBuilderMixin,
)
from app.services.agentic_intelligence.risk_assessment_agent.parsers import ParsersMixin
from app.services.agentic_intelligence.risk_assessment_agent.core import (
    CoreAnalysisMixin,
)
from app.services.agentic_intelligence.risk_assessment_agent.utils import (
    analyze_asset_risk_agentic,
    enrich_assets_with_risk_assessment_intelligence,
)


# Combine all mixins into the main RiskAssessmentAgent class
class RiskAssessmentAgent(
    _BaseAgent, CrewBuilderMixin, ParsersMixin, CoreAnalysisMixin
):
    """
    Complete RiskAssessmentAgent with all functionality.

    This class combines:
    - Base initialization and configuration
    - Crew and task creation
    - Output parsing
    - Core analysis logic
    """

    pass


# Export public API
__all__ = [
    "RiskAssessmentAgent",
    "analyze_asset_risk_agentic",
    "enrich_assets_with_risk_assessment_intelligence",
]
