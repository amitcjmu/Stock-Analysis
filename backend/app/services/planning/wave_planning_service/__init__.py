"""
Wave Planning Service - Public API

This module preserves backward compatibility by re-exporting all public APIs
from the modularized wave_planning_service package.

Original file: wave_planning_service.py (541 lines)
Modularized into:
- base.py: WavePlanningService class and initialization (200 lines)
- agent_integration.py: CrewAI agent integration with TenantScopedAgentPool (263 lines)
- wave_logic.py: Fallback logic and data fetching (154 lines)

ADR Compliance:
- ADR-015: TenantScopedAgentPool pattern (NO direct crew instance creation)
- ADR-024: TenantMemoryManager (CrewAI memory disabled)
- ADR-029: LLM JSON sanitization
- ADR-031: CallbackHandlerIntegration for observability

Usage:
    # Old import still works:
    from app.services.planning.wave_planning_service import WavePlanningService

    # New modular imports also available:
    from app.services.planning.wave_planning_service.base import WavePlanningService
    from app.services.planning.wave_planning_service.agent_integration import (
        generate_wave_plan_with_agent
    )
"""

from typing import Any, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext

# Import public API from base module
from .base import WavePlanningService

# Import utility functions for direct use if needed
from .wave_logic import (
    fetch_application_details,
    fetch_application_dependencies,
    generate_fallback_wave_plan,
)

# Import agent integration function
from .agent_integration import generate_wave_plan_with_agent

# Define public exports
__all__ = [
    "WavePlanningService",
    "execute_wave_planning_for_flow",
    "generate_wave_plan_with_agent",
    "generate_fallback_wave_plan",
    "fetch_application_details",
    "fetch_application_dependencies",
]


# Preserve top-level convenience function
async def execute_wave_planning_for_flow(
    db: AsyncSession,
    context: RequestContext,
    planning_flow_id: UUID,
    planning_config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Execute wave planning for a planning flow.

    This convenience function maintains backward compatibility with existing code.

    Args:
        db: Database session
        context: Request context
        planning_flow_id: UUID of the planning flow
        planning_config: Configuration for wave planning

    Returns:
        Dict containing wave plan execution result
    """
    service = WavePlanningService(db, context)
    return await service.execute_wave_planning(planning_flow_id, planning_config)
