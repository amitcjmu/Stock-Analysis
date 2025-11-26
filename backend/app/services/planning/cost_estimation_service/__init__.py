"""
Cost Estimation Service - Public API.

This module preserves backward compatibility after modularization.
All original imports and functions remain accessible through this package.

Usage:
    from app.services.planning.cost_estimation_service import CostEstimationService
    from app.services.planning.cost_estimation_service import execute_cost_estimation_for_flow
"""

from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext

# Import base class
from .base import CostEstimationService as _BaseCostEstimationService

# Import mixin
from .agent_integration import AgentIntegrationMixin


# Create combined class with all functionality
class CostEstimationService(_BaseCostEstimationService, AgentIntegrationMixin):
    """
    Service for generating migration cost estimates using CrewAI agents.

    This class combines base initialization with agent integration methods.
    """

    pass


# Re-export helper function for backward compatibility
async def execute_cost_estimation_for_flow(
    db: AsyncSession,
    context: RequestContext,
    planning_flow_id: UUID,
    phase_input: Optional[Dict[str, Any]] = None,
    custom_rate_cards: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Execute cost estimation for a planning flow.

    Args:
        db: Database session
        context: Request context
        planning_flow_id: UUID of the planning flow
        phase_input: Optional input data for cost estimation
        custom_rate_cards: Optional custom hourly rates by role

    Returns:
        Dict containing cost estimation result
    """
    service = CostEstimationService(db, context)
    return await service.generate_cost_estimate(
        planning_flow_id, phase_input, custom_rate_cards
    )


# Public API
__all__ = [
    "CostEstimationService",
    "execute_cost_estimation_for_flow",
]
