"""
Planning Flow Repository

Repository layer for planning flow data access following seven-layer architecture.
Provides multi-tenant scoped operations for planning flows, timelines, resource pools,
and resource allocations.

Tables:
1. planning_flows - Child flow operational state (migration 112)
2. project_timelines - Master timeline for Gantt charts (migration 113)
3. timeline_phases - Migration phases within timeline (migration 113)
4. timeline_milestones - Key milestones and deliverables (migration 113)
5. resource_pools - Role-based resource capacity (migration 114)
6. resource_allocations - Resource assignments to waves (migration 114)
7. resource_skills - Skill requirements and gaps (migration 114)

Related ADRs:
- ADR-012: Two-Table Pattern (master flow + child flow)
- ADR-006: Master Flow Orchestrator integration

Related Issues:
- #698 (Wave Planning Flow - Database Schema)
- #701 (Timeline Planning Integration)
- #704 (Resource Planning Database Schema)
"""

from .base import PlanningFlowRepositoryBase
from .planning_flow_operations import PlanningFlowOperationsMixin
from .jsonb_operations import JsonbOperationsMixin
from .timeline_operations import TimelineOperationsMixin
from .resource_pool_operations import ResourcePoolOperationsMixin
from .resource_allocation_operations import ResourceAllocationOperationsMixin
from .resource_skill_operations import ResourceSkillOperationsMixin


class PlanningFlowRepository(
    PlanningFlowRepositoryBase,
    PlanningFlowOperationsMixin,
    JsonbOperationsMixin,
    TimelineOperationsMixin,
    ResourcePoolOperationsMixin,
    ResourceAllocationOperationsMixin,
    ResourceSkillOperationsMixin,
):
    """
    Repository for planning flow data access with multi-tenant scoping.

    Follows existing patterns from CollectionFlowRepository and AssessmentFlowRepository.
    All operations are automatically scoped by client_account_id and engagement_id.

    This class combines multiple mixins to provide:
    - PlanningFlow CRUD and phase management (PlanningFlowOperationsMixin)
    - JSONB data updates (JsonbOperationsMixin)
    - Timeline, phase, and milestone operations (TimelineOperationsMixin)
    - Resource pool operations (ResourcePoolOperationsMixin)
    - Resource allocation operations (ResourceAllocationOperationsMixin)
    - Resource skill operations (ResourceSkillOperationsMixin)
    """

    pass


# Export the main class for backward compatibility
__all__ = ["PlanningFlowRepository"]
