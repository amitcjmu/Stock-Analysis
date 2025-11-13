"""
Planning Flow CRUD and Phase Management Operations.

Provides create, read, update, delete operations for planning flows
and phase status management.
"""

import logging
import uuid
from typing import Optional

from sqlalchemy import and_, select, update, delete
from sqlalchemy.exc import SQLAlchemyError

from app.models.planning import PlanningFlow

logger = logging.getLogger(__name__)


class PlanningFlowOperationsMixin:
    """Mixin for planning flow CRUD and phase management operations."""

    # ===========================
    # PlanningFlow CRUD Operations
    # ===========================

    async def create_planning_flow(
        self,
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
        master_flow_id: uuid.UUID,
        planning_flow_id: uuid.UUID,
        current_phase: str = "initialization",
        phase_status: str = "not_started",
        **kwargs,
    ) -> PlanningFlow:
        """
        Create new planning flow (multi-tenant scoped).

        Args:
            client_account_id: Client account UUID for tenant isolation (per migration 115)
            engagement_id: Engagement UUID for project isolation (per migration 115)
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
            # Convert UUID objects to strings for JSONB serialization
            if "selected_applications" in kwargs and kwargs["selected_applications"]:
                kwargs["selected_applications"] = [
                    str(app_id) if isinstance(app_id, uuid.UUID) else app_id
                    for app_id in kwargs["selected_applications"]
                ]

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
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
    ) -> Optional[PlanningFlow]:
        """
        Get planning flow by ID (multi-tenant scoped).

        Args:
            planning_flow_id: Planning flow UUID
            client_account_id: Client account UUID for verification (per migration 115)
            engagement_id: Engagement UUID for verification (per migration 115)

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
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
    ) -> Optional[PlanningFlow]:
        """
        Get planning flow by master flow ID (multi-tenant scoped).

        Args:
            master_flow_id: Master flow UUID from crewai_flow_state_extensions
            client_account_id: Client account UUID for verification (per migration 115)
            engagement_id: Engagement UUID for verification (per migration 115)

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
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
        **updates,
    ) -> Optional[PlanningFlow]:
        """
        Update planning flow (multi-tenant scoped).

        Args:
            planning_flow_id: Planning flow UUID
            client_account_id: Client account UUID for verification (per migration 115)
            engagement_id: Engagement UUID for verification (per migration 115)
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
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
    ) -> bool:
        """
        Delete planning flow (multi-tenant scoped).

        Args:
            planning_flow_id: Planning flow UUID
            client_account_id: Client account UUID for verification (per migration 115)
            engagement_id: Engagement UUID for verification (per migration 115)

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
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
        current_phase: str,
        phase_status: str,
    ) -> Optional[PlanningFlow]:
        """
        Update current phase and status.

        Args:
            planning_flow_id: Planning flow UUID
            client_account_id: Client account UUID (per migration 115)
            engagement_id: Engagement UUID (per migration 115)
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
