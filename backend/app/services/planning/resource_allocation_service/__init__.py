"""
Resource Allocation Service for Planning Flow

Generates AI-driven resource allocations for migration waves using the
resource_allocation_specialist CrewAI agent, with support for manual overrides
and learning from human adjustments.

This service integrates with:
- TenantScopedAgentPool (ADR-015) for persistent agent instances
- TenantMemoryManager (ADR-024) for learning from overrides
- CallbackHandlerIntegration (ADR-031) for observability
- JSON sanitization (ADR-029) for safe LLM output parsing

JSONB Storage Pattern:
    All resource allocation data is stored in planning_flows.resource_allocation_data JSONB column:
    {
        "allocations": [
            {
                "wave_id": "wave-1",
                "resources": [
                    {
                        "role": "cloud_architect",
                        "count": 2,
                        "effort_hours": 120,
                        "confidence_score": 85,
                        "rationale": "Complex architecture requires dedicated architects"
                    },
                    ...
                ],
                "total_cost": 50000.00,
                "overrides": [
                    {
                        "timestamp": "2025-11-26T10:00:00Z",
                        "user_id": "user-uuid",
                        "field": "resources.cloud_architect.count",
                        "old_value": 2,
                        "new_value": 3,
                        "reason": "Additional capacity needed for parallel workstreams"
                    }
                ]
            }
        ],
        "metadata": {
            "generated_at": "2025-11-26T10:00:00Z",
            "agent_version": "resource_allocation_specialist_v1",
            "total_estimated_cost": 150000.00
        }
    }
"""

# typing imports moved to submodules
# uuid import moved to submodules
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext

from .agent_integration import AgentIntegration
from .allocation_logic import AllocationLogic
from .base import BaseResourceAllocationService, Task, CREWAI_AVAILABLE


class ResourceAllocationService(AgentIntegration, AllocationLogic):
    """
    Service for AI-driven resource allocation for migration waves.

    This service generates optimal resource allocations using CrewAI agents
    and supports manual overrides with learning capabilities.

    This class combines functionality from:
    - BaseResourceAllocationService: Initialization and tenant scoping
    - AgentIntegration: CrewAI agent task creation and execution
    - AllocationLogic: Allocation parsing, persistence, and overrides
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize resource allocation service.

        Args:
            db: Async database session
            context: Request context with tenant scoping
        """
        # Initialize base class (handles repository setup)
        BaseResourceAllocationService.__init__(self, db, context)


# Preserve backward compatibility - export main class and Task for testing
__all__ = ["ResourceAllocationService", "Task", "CREWAI_AVAILABLE"]
