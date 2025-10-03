"""
Business Value Agent - Public API

This module preserves backward compatibility by exposing all public classes and functions.
"""

from app.services.agentic_intelligence.business_value_agent.base import (
    BusinessValueAgent as _BaseAgent,
)
from app.services.agentic_intelligence.business_value_agent.crew_builder import (
    CrewBuilderMixin,
)
from app.services.agentic_intelligence.business_value_agent.parsers import ParsersMixin
from app.services.agentic_intelligence.business_value_agent.core import (
    CoreAnalysisMixin,
)
from app.services.agentic_intelligence.business_value_agent.utils import (
    analyze_asset_business_value_agentic,
    enrich_assets_with_business_value_intelligence,
)


# Combine all mixins into the main BusinessValueAgent class
class BusinessValueAgent(_BaseAgent, CrewBuilderMixin, ParsersMixin, CoreAnalysisMixin):
    """
    Complete BusinessValueAgent with all functionality.

    This class combines:
    - Base initialization and configuration
    - Crew and task creation
    - Output parsing
    - Core analysis logic
    """

    pass


# Export public API
__all__ = [
    "BusinessValueAgent",
    "analyze_asset_business_value_agentic",
    "enrich_assets_with_business_value_intelligence",
]
