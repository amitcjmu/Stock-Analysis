"""
Crew planning and coordination functionality.

This module handles cross-crew planning coordination, data complexity analysis,
dynamic plan creation, and success criteria validation.
"""

from .coordination import CrewCoordinationMixin
from .validation import SuccessCriteriaValidationMixin
from .utils import CrewPlanningUtilsMixin


# Main mixin combining all crew planning functionality
class CrewPlanningMixin(
    CrewCoordinationMixin, SuccessCriteriaValidationMixin, CrewPlanningUtilsMixin
):
    """Mixin for crew planning and coordination functionality"""

    pass


__all__ = [
    "CrewPlanningMixin",
    "CrewCoordinationMixin",
    "SuccessCriteriaValidationMixin",
    "CrewPlanningUtilsMixin",
]
