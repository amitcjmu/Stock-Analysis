"""
Timeline Operations.

Provides CRUD operations for project timelines, timeline phases, and timeline milestones.
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, select, update
from sqlalchemy.exc import SQLAlchemyError

from app.models.planning import ProjectTimeline, TimelinePhase, TimelineMilestone

logger = logging.getLogger(__name__)


class TimelineOperationsMixin:
    """Mixin for timeline, phase, and milestone operations."""

    # ===========================
    # Timeline CRUD Operations
    # ===========================

    async def create_timeline(
        self,
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
        planning_flow_id: uuid.UUID,
        timeline_name: str,
        overall_start_date: datetime,
        overall_end_date: datetime,
        **kwargs,
    ) -> ProjectTimeline:
        """
        Create project timeline.

        Args:
            client_account_id: Client account UUID (per migration 115)
            engagement_id: Engagement UUID (per migration 115)
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
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
    ) -> Optional[ProjectTimeline]:
        """
        Get timeline for planning flow.

        Args:
            planning_flow_id: Planning flow UUID
            client_account_id: Client account UUID (per migration 115)
            engagement_id: Engagement UUID (per migration 115)

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
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
        **updates,
    ) -> Optional[ProjectTimeline]:
        """
        Update timeline.

        Args:
            timeline_id: Timeline UUID
            client_account_id: Client account UUID (per migration 115)
            engagement_id: Engagement UUID (per migration 115)
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
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
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
            client_account_id: Client account UUID (per migration 115)
            engagement_id: Engagement UUID (per migration 115)
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
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
    ) -> List[TimelinePhase]:
        """
        Get all phases for a timeline.

        Args:
            timeline_id: Timeline UUID
            client_account_id: Client account UUID (per migration 115)
            engagement_id: Engagement UUID (per migration 115)

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
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
        timeline_id: uuid.UUID,
        milestone_number: int,
        milestone_name: str,
        planned_date: datetime,
        **kwargs,
    ) -> TimelineMilestone:
        """
        Create timeline milestone.

        Args:
            client_account_id: Client account UUID (per migration 115)
            engagement_id: Engagement UUID (per migration 115)
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
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
    ) -> List[TimelineMilestone]:
        """
        Get all milestones for a timeline.

        Args:
            timeline_id: Timeline UUID
            client_account_id: Client account UUID (per migration 115)
            engagement_id: Engagement UUID (per migration 115)

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
