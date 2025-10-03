"""
Gap Prioritization Agent - Public API
"""

from app.services.agents.gap_prioritization_agent_crewai.base import (
    GapPrioritizationAgent as _BaseAgent,
)
from app.services.agents.gap_prioritization_agent_crewai.core import (
    CorePrioritizationMixin,
)
from app.services.agents.gap_prioritization_agent_crewai.utils import UtilsMixin


# Combine base, core, and utils functionality
class GapPrioritizationAgent(_BaseAgent, CorePrioritizationMixin, UtilsMixin):
    """
    Complete GapPrioritizationAgent with all functionality.
    """

    pass


__all__ = ["GapPrioritizationAgent"]
