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

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.models.planning import (
    PlanningFlow,
    ProjectTimeline,
    TimelinePhase,
    TimelineMilestone,
    ResourcePool,
    ResourceAllocation,
    ResourceSkill,
)
from app.repositories.context_aware_repository import ContextAwareRepository

logger = logging.getLogger(__name__)


class PlanningFlowRepository(ContextAwareRepository[PlanningFlow]):
    """
    Repository for planning flow data access with multi-tenant scoping.

    Follows existing patterns from CollectionFlowRepository and AssessmentFlowRepository.
    All operations are automatically scoped by client_account_id and engagement_id.
    """

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
    ):
        """
        Initialize planning flow repository with context.

        Args:
            db: Async database session
            client_account_id: Client account UUID for tenant scoping
            engagement_id: Engagement UUID for project scoping
        """
        super().__init__(db, PlanningFlow, client_account_id, engagement_id)
        logger.debug(
            f"Initialized PlanningFlowRepository: "
            f"client_account_id={client_account_id}, engagement_id={engagement_id}"
        )

    # ===========================
    # PlanningFlow CRUD Operations
    # ===========================

    async def create_planning_flow(
        self,
        client_account_id: int,
        engagement_id: int,
        master_flow_id: uuid.UUID,
        planning_flow_id: uuid.UUID,
        current_phase: str = "initialization",
        phase_status: str = "not_started",
        **kwargs,
    ) -> PlanningFlow:
        """
        Create new planning flow (multi-tenant scoped).

        Args:
            client_account_id: Client account ID for tenant isolation
            engagement_id: Engagement ID for project isolation
            master_flow_id: Master flow ID from crewai_flow_state_extensions
            planning_flow_id: Unique planning flow ID
            current_phase: Initial phase (default: initialization)
            phase_status: Initial status (default: not_started)
            **kwargs: Additional flow fields

        Returns:
            Created PlanningFlow instance

        Raises:
            SQLAlchemyError: On database errors
        """
        try:
            flow_data = {
                "client_account_id": client_account_id,
                "engagement_id": engagement_id,
                "master_flow_id": master_flow_id,
                "planning_flow_id": planning_flow_id,
                "current_phase": current_phase,
                "phase_status": phase_status,
                **kwargs,
            }

            planning_flow = await self.create(commit=False, **flow_data)

            logger.info(
                f"Created planning flow: planning_flow_id={planning_flow_id}, "
                f"master_flow_id={master_flow_id}"
            )

            return planning_flow

        except SQLAlchemyError as e:
            logger.error(f"Failed to create planning flow: {e}")
            raise

    async def get_planning_flow_by_id(
        self,
        planning_flow_id: uuid.UUID,
        client_account_id: int,
        engagement_id: int,
    ) -> Optional[PlanningFlow]:
        """
        Get planning flow by ID (multi-tenant scoped).

        Args:
            planning_flow_id: Planning flow UUID
            client_account_id: Client account ID for verification
            engagement_id: Engagement ID for verification

        Returns:
            PlanningFlow instance or None if not found
        """
        try:
            stmt = select(PlanningFlow).where(
                and_(
                    PlanningFlow.planning_flow_id == planning_flow_id,
                    PlanningFlow.client_account_id == client_account_id,
                    PlanningFlow.engagement_id == engagement_id,
                )
            )

            result = await self.db.execute(stmt)
            flow = result.scalar_one_or_none()

            if flow:
                logger.debug(f"Retrieved planning flow: {planning_flow_id}")
            else:
                logger.debug(f"Planning flow not found: {planning_flow_id}")

            return flow

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving planning flow {planning_flow_id}: {e}")
            return None

    async def get_by_master_flow_id(
        self,
        master_flow_id: uuid.UUID,
        client_account_id: int,
        engagement_id: int,
    ) -> Optional[PlanningFlow]:
        """
        Get planning flow by master flow ID (multi-tenant scoped).

        Args:
            master_flow_id: Master flow UUID from crewai_flow_state_extensions
            client_account_id: Client account ID for verification
            engagement_id: Engagement ID for verification

        Returns:
            PlanningFlow instance or None if not found
        """
        try:
            stmt = select(PlanningFlow).where(
                and_(
                    PlanningFlow.master_flow_id == master_flow_id,
                    PlanningFlow.client_account_id == client_account_id,
                    PlanningFlow.engagement_id == engagement_id,
                )
            )

            result = await self.db.execute(stmt)
            flow = result.scalar_one_or_none()

            if flow:
                logger.debug(
                    f"Retrieved planning flow by master_flow_id: {master_flow_id}"
                )
            else:
                logger.debug(
                    f"Planning flow not found for master_flow_id: {master_flow_id}"
                )

            return flow

        except SQLAlchemyError as e:
            logger.error(
                f"Error retrieving planning flow by master_flow_id {master_flow_id}: {e}"
            )
            return None

    async def update_planning_flow(
        self,
        planning_flow_id: uuid.UUID,
        client_account_id: int,
        engagement_id: int,
        **updates,
    ) -> Optional[PlanningFlow]:
        """
        Update planning flow (multi-tenant scoped).

        Args:
            planning_flow_id: Planning flow UUID
            client_account_id: Client account ID for verification
            engagement_id: Engagement ID for verification
            **updates: Fields to update

        Returns:
            Updated PlanningFlow instance or None if not found
        """
        try:
            # Build update statement with tenant scoping
            stmt = (
                update(PlanningFlow)
                .where(
                    and_(
                        PlanningFlow.planning_flow_id == planning_flow_id,
                        PlanningFlow.client_account_id == client_account_id,
                        PlanningFlow.engagement_id == engagement_id,
                    )
                )
                .values(**updates)
                .execution_options(synchronize_session="fetch")
            )

            await self.db.execute(stmt)
            await self.db.flush()

            # Retrieve updated flow
            updated_flow = await self.get_planning_flow_by_id(
                planning_flow_id, client_account_id, engagement_id
            )

            if updated_flow:
                logger.info(f"Updated planning flow: {planning_flow_id}")
            else:
                logger.warning(
                    f"Planning flow not found for update: {planning_flow_id}"
                )

            return updated_flow

        except SQLAlchemyError as e:
            logger.error(f"Error updating planning flow {planning_flow_id}: {e}")
            return None

    async def delete_planning_flow(
        self,
        planning_flow_id: uuid.UUID,
        client_account_id: int,
        engagement_id: int,
    ) -> bool:
        """
        Delete planning flow (multi-tenant scoped).

        Args:
            planning_flow_id: Planning flow UUID
            client_account_id: Client account ID for verification
            engagement_id: Engagement ID for verification

        Returns:
            True if deleted, False if not found or error
        """
        try:
            stmt = delete(PlanningFlow).where(
                and_(
                    PlanningFlow.planning_flow_id == planning_flow_id,
                    PlanningFlow.client_account_id == client_account_id,
                    PlanningFlow.engagement_id == engagement_id,
                )
            )

            result = await self.db.execute(stmt)
            await self.db.flush()

            deleted = result.rowcount > 0

            if deleted:
                logger.info(f"Deleted planning flow: {planning_flow_id}")
            else:
                logger.warning(
                    f"Planning flow not found for deletion: {planning_flow_id}"
                )

            return deleted

        except SQLAlchemyError as e:
            logger.error(f"Error deleting planning flow {planning_flow_id}: {e}")
            return False

    # ===========================
    # Phase Management
    # ===========================

    async def update_phase_status(
        self,
        planning_flow_id: uuid.UUID,
        client_account_id: int,
        engagement_id: int,
        current_phase: str,
        phase_status: str,
    ) -> Optional[PlanningFlow]:
        """
        Update current phase and status.

        Args:
            planning_flow_id: Planning flow UUID
            client_account_id: Client account ID
            engagement_id: Engagement ID
            current_phase: New phase value
            phase_status: New status value

        Returns:
            Updated PlanningFlow or None if not found
        """
        return await self.update_planning_flow(
            planning_flow_id=planning_flow_id,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            current_phase=current_phase,
            phase_status=phase_status,
        )

    # ===========================
    # JSONB Data Updates
    # ===========================

    async def save_wave_plan_data(
        self,
        planning_flow_id: uuid.UUID,
        client_account_id: int,
        engagement_id: int,
        wave_plan_data: Dict[str, Any],
    ) -> Optional[PlanningFlow]:
        """
        Save wave planning results.

        Args:
            planning_flow_id: Planning flow UUID
            client_account_id: Client account ID
            engagement_id: Engagement ID
            wave_plan_data: Wave plan JSONB data

        Returns:
            Updated PlanningFlow or None if not found
        """
        return await self.update_planning_flow(
            planning_flow_id=planning_flow_id,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            wave_plan_data=wave_plan_data,
        )

    async def save_resource_allocation_data(
        self,
        planning_flow_id: uuid.UUID,
        client_account_id: int,
        engagement_id: int,
        resource_allocation_data: Dict[str, Any],
    ) -> Optional[PlanningFlow]:
        """
        Save resource allocation data.

        Args:
            planning_flow_id: Planning flow UUID
            client_account_id: Client account ID
            engagement_id: Engagement ID
            resource_allocation_data: Resource allocation JSONB data

        Returns:
            Updated PlanningFlow or None if not found
        """
        return await self.update_planning_flow(
            planning_flow_id=planning_flow_id,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            resource_allocation_data=resource_allocation_data,
        )

    async def save_timeline_data(
        self,
        planning_flow_id: uuid.UUID,
        client_account_id: int,
        engagement_id: int,
        timeline_data: Dict[str, Any],
    ) -> Optional[PlanningFlow]:
        """
        Save timeline data.

        Args:
            planning_flow_id: Planning flow UUID
            client_account_id: Client account ID
            engagement_id: Engagement ID
            timeline_data: Timeline JSONB data

        Returns:
            Updated PlanningFlow or None if not found
        """
        return await self.update_planning_flow(
            planning_flow_id=planning_flow_id,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            timeline_data=timeline_data,
        )

    async def save_cost_estimation_data(
        self,
        planning_flow_id: uuid.UUID,
        client_account_id: int,
        engagement_id: int,
        cost_estimation_data: Dict[str, Any],
    ) -> Optional[PlanningFlow]:
        """
        Save cost estimation data.

        Args:
            planning_flow_id: Planning flow UUID
            client_account_id: Client account ID
            engagement_id: Engagement ID
            cost_estimation_data: Cost estimation JSONB data

        Returns:
            Updated PlanningFlow or None if not found
        """
        return await self.update_planning_flow(
            planning_flow_id=planning_flow_id,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            cost_estimation_data=cost_estimation_data,
        )

    # ===========================
    # Timeline CRUD Operations
    # ===========================

    async def create_timeline(
        self,
        client_account_id: int,
        engagement_id: int,
        planning_flow_id: uuid.UUID,
        timeline_name: str,
        overall_start_date: datetime,
        overall_end_date: datetime,
        **kwargs,
    ) -> ProjectTimeline:
        """
        Create project timeline.

        Args:
            client_account_id: Client account ID
            engagement_id: Engagement ID
            planning_flow_id: Planning flow UUID
            timeline_name: Timeline name
            overall_start_date: Timeline start date
            overall_end_date: Timeline end date
            **kwargs: Additional timeline fields

        Returns:
            Created ProjectTimeline instance

        Raises:
            SQLAlchemyError: On database errors
        """
        try:
            timeline = ProjectTimeline(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                planning_flow_id=planning_flow_id,
                timeline_name=timeline_name,
                overall_start_date=overall_start_date,
                overall_end_date=overall_end_date,
                **kwargs,
            )

            self.db.add(timeline)
            await self.db.flush()

            logger.info(
                f"Created timeline: {timeline_name} for planning_flow_id={planning_flow_id}"
            )

            return timeline

        except SQLAlchemyError as e:
            logger.error(f"Failed to create timeline: {e}")
            raise

    async def get_timeline_by_planning_flow(
        self,
        planning_flow_id: uuid.UUID,
        client_account_id: int,
        engagement_id: int,
    ) -> Optional[ProjectTimeline]:
        """
        Get timeline for planning flow.

        Args:
            planning_flow_id: Planning flow UUID
            client_account_id: Client account ID
            engagement_id: Engagement ID

        Returns:
            ProjectTimeline instance or None if not found
        """
        try:
            stmt = select(ProjectTimeline).where(
                and_(
                    ProjectTimeline.planning_flow_id == planning_flow_id,
                    ProjectTimeline.client_account_id == client_account_id,
                    ProjectTimeline.engagement_id == engagement_id,
                )
            )

            result = await self.db.execute(stmt)
            timeline = result.scalar_one_or_none()

            if timeline:
                logger.debug(
                    f"Retrieved timeline for planning_flow_id: {planning_flow_id}"
                )
            else:
                logger.debug(
                    f"No timeline found for planning_flow_id: {planning_flow_id}"
                )

            return timeline

        except SQLAlchemyError as e:
            logger.error(
                f"Error retrieving timeline for planning_flow_id {planning_flow_id}: {e}"
            )
            return None

    async def update_timeline(
        self,
        timeline_id: uuid.UUID,
        client_account_id: int,
        engagement_id: int,
        **updates,
    ) -> Optional[ProjectTimeline]:
        """
        Update timeline.

        Args:
            timeline_id: Timeline UUID
            client_account_id: Client account ID
            engagement_id: Engagement ID
            **updates: Fields to update

        Returns:
            Updated ProjectTimeline or None if not found
        """
        try:
            stmt = (
                update(ProjectTimeline)
                .where(
                    and_(
                        ProjectTimeline.id == timeline_id,
                        ProjectTimeline.client_account_id == client_account_id,
                        ProjectTimeline.engagement_id == engagement_id,
                    )
                )
                .values(**updates)
                .execution_options(synchronize_session="fetch")
            )

            await self.db.execute(stmt)
            await self.db.flush()

            # Retrieve updated timeline
            select_stmt = select(ProjectTimeline).where(
                and_(
                    ProjectTimeline.id == timeline_id,
                    ProjectTimeline.client_account_id == client_account_id,
                    ProjectTimeline.engagement_id == engagement_id,
                )
            )

            result = await self.db.execute(select_stmt)
            timeline = result.scalar_one_or_none()

            if timeline:
                logger.info(f"Updated timeline: {timeline_id}")
            else:
                logger.warning(f"Timeline not found for update: {timeline_id}")

            return timeline

        except SQLAlchemyError as e:
            logger.error(f"Error updating timeline {timeline_id}: {e}")
            return None

    # ===========================
    # Timeline Phase Operations
    # ===========================

    async def create_timeline_phase(
        self,
        client_account_id: int,
        engagement_id: int,
        timeline_id: uuid.UUID,
        phase_number: int,
        phase_name: str,
        planned_start_date: datetime,
        planned_end_date: datetime,
        **kwargs,
    ) -> TimelinePhase:
        """
        Create timeline phase.

        Args:
            client_account_id: Client account ID
            engagement_id: Engagement ID
            timeline_id: Timeline UUID
            phase_number: Phase sequence number
            phase_name: Phase name
            planned_start_date: Planned start date
            planned_end_date: Planned end date
            **kwargs: Additional phase fields

        Returns:
            Created TimelinePhase instance

        Raises:
            SQLAlchemyError: On database errors
        """
        try:
            phase = TimelinePhase(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                timeline_id=timeline_id,
                phase_number=phase_number,
                phase_name=phase_name,
                planned_start_date=planned_start_date,
                planned_end_date=planned_end_date,
                **kwargs,
            )

            self.db.add(phase)
            await self.db.flush()

            logger.info(
                f"Created timeline phase: {phase_name} (#{phase_number}) for timeline_id={timeline_id}"
            )

            return phase

        except SQLAlchemyError as e:
            logger.error(f"Failed to create timeline phase: {e}")
            raise

    async def get_phases_by_timeline(
        self,
        timeline_id: uuid.UUID,
        client_account_id: int,
        engagement_id: int,
    ) -> List[TimelinePhase]:
        """
        Get all phases for a timeline.

        Args:
            timeline_id: Timeline UUID
            client_account_id: Client account ID
            engagement_id: Engagement ID

        Returns:
            List of TimelinePhase instances
        """
        try:
            stmt = (
                select(TimelinePhase)
                .where(
                    and_(
                        TimelinePhase.timeline_id == timeline_id,
                        TimelinePhase.client_account_id == client_account_id,
                        TimelinePhase.engagement_id == engagement_id,
                    )
                )
                .order_by(TimelinePhase.phase_number)
            )

            result = await self.db.execute(stmt)
            phases = result.scalars().all()

            logger.debug(
                f"Retrieved {len(phases)} phases for timeline_id: {timeline_id}"
            )

            return list(phases)

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving phases for timeline_id {timeline_id}: {e}")
            return []

    # ===========================
    # Timeline Milestone Operations
    # ===========================

    async def create_milestone(
        self,
        client_account_id: int,
        engagement_id: int,
        timeline_id: uuid.UUID,
        milestone_number: int,
        milestone_name: str,
        planned_date: datetime,
        **kwargs,
    ) -> TimelineMilestone:
        """
        Create timeline milestone.

        Args:
            client_account_id: Client account ID
            engagement_id: Engagement ID
            timeline_id: Timeline UUID
            milestone_number: Milestone sequence number
            milestone_name: Milestone name
            planned_date: Planned milestone date
            **kwargs: Additional milestone fields

        Returns:
            Created TimelineMilestone instance

        Raises:
            SQLAlchemyError: On database errors
        """
        try:
            milestone = TimelineMilestone(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                timeline_id=timeline_id,
                milestone_number=milestone_number,
                milestone_name=milestone_name,
                planned_date=planned_date,
                **kwargs,
            )

            self.db.add(milestone)
            await self.db.flush()

            logger.info(
                f"Created milestone: {milestone_name} (#{milestone_number}) for timeline_id={timeline_id}"
            )

            return milestone

        except SQLAlchemyError as e:
            logger.error(f"Failed to create milestone: {e}")
            raise

    async def get_milestones_by_timeline(
        self,
        timeline_id: uuid.UUID,
        client_account_id: int,
        engagement_id: int,
    ) -> List[TimelineMilestone]:
        """
        Get all milestones for a timeline.

        Args:
            timeline_id: Timeline UUID
            client_account_id: Client account ID
            engagement_id: Engagement ID

        Returns:
            List of TimelineMilestone instances
        """
        try:
            stmt = (
                select(TimelineMilestone)
                .where(
                    and_(
                        TimelineMilestone.timeline_id == timeline_id,
                        TimelineMilestone.client_account_id == client_account_id,
                        TimelineMilestone.engagement_id == engagement_id,
                    )
                )
                .order_by(TimelineMilestone.milestone_number)
            )

            result = await self.db.execute(stmt)
            milestones = result.scalars().all()

            logger.debug(
                f"Retrieved {len(milestones)} milestones for timeline_id: {timeline_id}"
            )

            return list(milestones)

        except SQLAlchemyError as e:
            logger.error(
                f"Error retrieving milestones for timeline_id {timeline_id}: {e}"
            )
            return []

    # ===========================
    # Resource Pool CRUD Operations
    # ===========================

    async def create_resource_pool(
        self,
        client_account_id: int,
        engagement_id: int,
        pool_name: str,
        role_name: str,
        total_capacity_hours: float,
        hourly_rate: Optional[float] = None,
        **kwargs,
    ) -> ResourcePool:
        """
        Create resource pool.

        Args:
            client_account_id: Client account ID
            engagement_id: Engagement ID
            pool_name: Pool name
            role_name: Role name
            total_capacity_hours: Total capacity in hours
            hourly_rate: Optional hourly rate
            **kwargs: Additional pool fields

        Returns:
            Created ResourcePool instance

        Raises:
            SQLAlchemyError: On database errors
        """
        try:
            # Default available capacity equals total capacity on creation
            available_capacity = kwargs.pop(
                "available_capacity_hours", total_capacity_hours
            )

            resource_pool = ResourcePool(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                pool_name=pool_name,
                role_name=role_name,
                total_capacity_hours=total_capacity_hours,
                available_capacity_hours=available_capacity,
                hourly_rate=hourly_rate,
                **kwargs,
            )

            self.db.add(resource_pool)
            await self.db.flush()

            logger.info(f"Created resource pool: {pool_name} ({role_name})")

            return resource_pool

        except SQLAlchemyError as e:
            logger.error(f"Failed to create resource pool: {e}")
            raise

    async def list_resource_pools(
        self,
        client_account_id: int,
        engagement_id: int,
        is_active: bool = True,
    ) -> List[ResourcePool]:
        """
        List all resource pools (multi-tenant scoped).

        Args:
            client_account_id: Client account ID
            engagement_id: Engagement ID
            is_active: Filter by active status (default: True)

        Returns:
            List of ResourcePool instances
        """
        try:
            stmt = select(ResourcePool).where(
                and_(
                    ResourcePool.client_account_id == client_account_id,
                    ResourcePool.engagement_id == engagement_id,
                    ResourcePool.is_active == is_active,
                )
            )

            result = await self.db.execute(stmt)
            pools = result.scalars().all()

            logger.debug(
                f"Retrieved {len(pools)} resource pools (is_active={is_active})"
            )

            return list(pools)

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving resource pools: {e}")
            return []

    async def get_resource_pool_by_id(
        self,
        pool_id: uuid.UUID,
        client_account_id: int,
        engagement_id: int,
    ) -> Optional[ResourcePool]:
        """
        Get resource pool by ID.

        Args:
            pool_id: Resource pool UUID
            client_account_id: Client account ID
            engagement_id: Engagement ID

        Returns:
            ResourcePool instance or None if not found
        """
        try:
            stmt = select(ResourcePool).where(
                and_(
                    ResourcePool.id == pool_id,
                    ResourcePool.client_account_id == client_account_id,
                    ResourcePool.engagement_id == engagement_id,
                )
            )

            result = await self.db.execute(stmt)
            pool = result.scalar_one_or_none()

            if pool:
                logger.debug(f"Retrieved resource pool: {pool_id}")
            else:
                logger.debug(f"Resource pool not found: {pool_id}")

            return pool

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving resource pool {pool_id}: {e}")
            return None

    async def update_resource_pool(
        self,
        pool_id: uuid.UUID,
        client_account_id: int,
        engagement_id: int,
        **updates,
    ) -> Optional[ResourcePool]:
        """
        Update resource pool.

        Args:
            pool_id: Resource pool UUID
            client_account_id: Client account ID
            engagement_id: Engagement ID
            **updates: Fields to update

        Returns:
            Updated ResourcePool or None if not found
        """
        try:
            stmt = (
                update(ResourcePool)
                .where(
                    and_(
                        ResourcePool.id == pool_id,
                        ResourcePool.client_account_id == client_account_id,
                        ResourcePool.engagement_id == engagement_id,
                    )
                )
                .values(**updates)
                .execution_options(synchronize_session="fetch")
            )

            await self.db.execute(stmt)
            await self.db.flush()

            # Retrieve updated pool
            pool = await self.get_resource_pool_by_id(
                pool_id, client_account_id, engagement_id
            )

            if pool:
                logger.info(f"Updated resource pool: {pool_id}")
            else:
                logger.warning(f"Resource pool not found for update: {pool_id}")

            return pool

        except SQLAlchemyError as e:
            logger.error(f"Error updating resource pool {pool_id}: {e}")
            return None

    # ===========================
    # Resource Allocation CRUD Operations
    # ===========================

    async def create_resource_allocation(
        self,
        client_account_id: int,
        engagement_id: int,
        planning_flow_id: uuid.UUID,
        wave_id: uuid.UUID,
        resource_pool_id: uuid.UUID,
        allocated_hours: float,
        allocation_start_date: datetime,
        allocation_end_date: datetime,
        **kwargs,
    ) -> ResourceAllocation:
        """
        Allocate resource to wave.

        Args:
            client_account_id: Client account ID
            engagement_id: Engagement ID
            planning_flow_id: Planning flow UUID
            wave_id: Wave UUID
            resource_pool_id: Resource pool UUID
            allocated_hours: Allocated hours
            allocation_start_date: Allocation start date
            allocation_end_date: Allocation end date
            **kwargs: Additional allocation fields

        Returns:
            Created ResourceAllocation instance

        Raises:
            SQLAlchemyError: On database errors
        """
        try:
            allocation = ResourceAllocation(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                planning_flow_id=planning_flow_id,
                wave_id=wave_id,
                resource_pool_id=resource_pool_id,
                allocated_hours=allocated_hours,
                allocation_start_date=allocation_start_date,
                allocation_end_date=allocation_end_date,
                **kwargs,
            )

            self.db.add(allocation)
            await self.db.flush()

            logger.info(
                f"Created resource allocation: {allocated_hours}h to wave_id={wave_id} "
                f"from pool_id={resource_pool_id}"
            )

            return allocation

        except SQLAlchemyError as e:
            logger.error(f"Failed to create resource allocation: {e}")
            raise

    async def list_allocations_by_wave(
        self,
        wave_id: uuid.UUID,
        client_account_id: int,
        engagement_id: int,
    ) -> List[ResourceAllocation]:
        """
        Get all resource allocations for a wave.

        Args:
            wave_id: Wave UUID
            client_account_id: Client account ID
            engagement_id: Engagement ID

        Returns:
            List of ResourceAllocation instances
        """
        try:
            stmt = select(ResourceAllocation).where(
                and_(
                    ResourceAllocation.wave_id == wave_id,
                    ResourceAllocation.client_account_id == client_account_id,
                    ResourceAllocation.engagement_id == engagement_id,
                )
            )

            result = await self.db.execute(stmt)
            allocations = result.scalars().all()

            logger.debug(
                f"Retrieved {len(allocations)} allocations for wave_id: {wave_id}"
            )

            return list(allocations)

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving allocations for wave_id {wave_id}: {e}")
            return []

    async def list_allocations_by_planning_flow(
        self,
        planning_flow_id: uuid.UUID,
        client_account_id: int,
        engagement_id: int,
    ) -> List[ResourceAllocation]:
        """
        Get all resource allocations for a planning flow.

        Args:
            planning_flow_id: Planning flow UUID
            client_account_id: Client account ID
            engagement_id: Engagement ID

        Returns:
            List of ResourceAllocation instances
        """
        try:
            stmt = select(ResourceAllocation).where(
                and_(
                    ResourceAllocation.planning_flow_id == planning_flow_id,
                    ResourceAllocation.client_account_id == client_account_id,
                    ResourceAllocation.engagement_id == engagement_id,
                )
            )

            result = await self.db.execute(stmt)
            allocations = result.scalars().all()

            logger.debug(
                f"Retrieved {len(allocations)} allocations for planning_flow_id: {planning_flow_id}"
            )

            return list(allocations)

        except SQLAlchemyError as e:
            logger.error(
                f"Error retrieving allocations for planning_flow_id {planning_flow_id}: {e}"
            )
            return []

    async def update_allocation(
        self,
        allocation_id: uuid.UUID,
        client_account_id: int,
        engagement_id: int,
        **updates,
    ) -> Optional[ResourceAllocation]:
        """
        Update resource allocation.

        Args:
            allocation_id: Allocation UUID
            client_account_id: Client account ID
            engagement_id: Engagement ID
            **updates: Fields to update

        Returns:
            Updated ResourceAllocation or None if not found
        """
        try:
            stmt = (
                update(ResourceAllocation)
                .where(
                    and_(
                        ResourceAllocation.id == allocation_id,
                        ResourceAllocation.client_account_id == client_account_id,
                        ResourceAllocation.engagement_id == engagement_id,
                    )
                )
                .values(**updates)
                .execution_options(synchronize_session="fetch")
            )

            await self.db.execute(stmt)
            await self.db.flush()

            # Retrieve updated allocation
            select_stmt = select(ResourceAllocation).where(
                and_(
                    ResourceAllocation.id == allocation_id,
                    ResourceAllocation.client_account_id == client_account_id,
                    ResourceAllocation.engagement_id == engagement_id,
                )
            )

            result = await self.db.execute(select_stmt)
            allocation = result.scalar_one_or_none()

            if allocation:
                logger.info(f"Updated resource allocation: {allocation_id}")
            else:
                logger.warning(
                    f"Resource allocation not found for update: {allocation_id}"
                )

            return allocation

        except SQLAlchemyError as e:
            logger.error(f"Error updating allocation {allocation_id}: {e}")
            return None

    # ===========================
    # Resource Skills Operations
    # ===========================

    async def create_resource_skill(
        self,
        client_account_id: int,
        engagement_id: int,
        wave_id: uuid.UUID,
        skill_name: str,
        required_hours: float,
        **kwargs,
    ) -> ResourceSkill:
        """
        Create resource skill requirement.

        Args:
            client_account_id: Client account ID
            engagement_id: Engagement ID
            wave_id: Wave UUID
            skill_name: Skill name
            required_hours: Required hours for this skill
            **kwargs: Additional skill fields

        Returns:
            Created ResourceSkill instance

        Raises:
            SQLAlchemyError: On database errors
        """
        try:
            skill = ResourceSkill(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                wave_id=wave_id,
                skill_name=skill_name,
                required_hours=required_hours,
                **kwargs,
            )

            self.db.add(skill)
            await self.db.flush()

            logger.info(f"Created resource skill: {skill_name} for wave_id={wave_id}")

            return skill

        except SQLAlchemyError as e:
            logger.error(f"Failed to create resource skill: {e}")
            raise

    async def list_skills_by_wave(
        self,
        wave_id: uuid.UUID,
        client_account_id: int,
        engagement_id: int,
    ) -> List[ResourceSkill]:
        """
        Get all skill requirements for a wave.

        Args:
            wave_id: Wave UUID
            client_account_id: Client account ID
            engagement_id: Engagement ID

        Returns:
            List of ResourceSkill instances
        """
        try:
            stmt = select(ResourceSkill).where(
                and_(
                    ResourceSkill.wave_id == wave_id,
                    ResourceSkill.client_account_id == client_account_id,
                    ResourceSkill.engagement_id == engagement_id,
                )
            )

            result = await self.db.execute(stmt)
            skills = result.scalars().all()

            logger.debug(f"Retrieved {len(skills)} skills for wave_id: {wave_id}")

            return list(skills)

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving skills for wave_id {wave_id}: {e}")
            return []

    async def list_skill_gaps_by_wave(
        self,
        wave_id: uuid.UUID,
        client_account_id: int,
        engagement_id: int,
    ) -> List[ResourceSkill]:
        """
        Get all skill gaps for a wave.

        Args:
            wave_id: Wave UUID
            client_account_id: Client account ID
            engagement_id: Engagement ID

        Returns:
            List of ResourceSkill instances with has_gap=True
        """
        try:
            stmt = select(ResourceSkill).where(
                and_(
                    ResourceSkill.wave_id == wave_id,
                    ResourceSkill.client_account_id == client_account_id,
                    ResourceSkill.engagement_id == engagement_id,
                    ResourceSkill.has_gap
                    == True,  # noqa: E712 - Per coding-agent-guide.md
                )
            )

            result = await self.db.execute(stmt)
            gaps = result.scalars().all()

            logger.debug(f"Retrieved {len(gaps)} skill gaps for wave_id: {wave_id}")

            return list(gaps)

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving skill gaps for wave_id {wave_id}: {e}")
            return []
