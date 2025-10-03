"""
Modernization Agent - Public API

This module preserves backward compatibility by exposing all public classes and functions.
"""

from app.services.agentic_intelligence.modernization_agent.base import (
    ModernizationAgent as _BaseAgent,
)
from app.services.agentic_intelligence.modernization_agent.crew_builder import (
    CrewBuilderMixin,
)
from app.services.agentic_intelligence.modernization_agent.parsers import ParsersMixin
from app.services.agentic_intelligence.modernization_agent.core import (
    CoreAnalysisMixin,
)
from app.services.agentic_intelligence.modernization_agent.utils import (
    analyze_modernization_potential_agentic,
    enrich_assets_with_modernization_intelligence,
)


# Combine all mixins into the main ModernizationAgent class
class ModernizationAgent(_BaseAgent, CrewBuilderMixin, ParsersMixin, CoreAnalysisMixin):
    """
    Complete ModernizationAgent with all functionality.

    This class combines:
    - Base initialization and configuration
    - Crew and task creation
    - Output parsing
    - Core analysis logic
    """

    pass


# Export public API
__all__ = [
    "ModernizationAgent",
    "analyze_modernization_potential_agentic",
    "enrich_assets_with_modernization_intelligence",
]
