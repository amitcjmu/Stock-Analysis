"""
Resource Allocation Operations.

Provides CRUD operations for resource allocations.
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, select, update
from sqlalchemy.exc import SQLAlchemyError

from app.models.planning import ResourceAllocation

logger = logging.getLogger(__name__)


class ResourceAllocationOperationsMixin:
    """Mixin for resource allocation operations."""

    # ===========================
    # Resource Allocation CRUD Operations
    # ===========================

    async def create_resource_allocation(
        self,
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
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
            client_account_id: Client account UUID (per migration 115)
            engagement_id: Engagement UUID (per migration 115)
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
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
    ) -> List[ResourceAllocation]:
        """
        Get all resource allocations for a wave.

        Args:
            wave_id: Wave UUID
            client_account_id: Client account UUID (per migration 115)
            engagement_id: Engagement UUID (per migration 115)

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
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
    ) -> List[ResourceAllocation]:
        """
        Get all resource allocations for a planning flow.

        Args:
            planning_flow_id: Planning flow UUID
            client_account_id: Client account UUID (per migration 115)
            engagement_id: Engagement UUID (per migration 115)

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
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
        **updates,
    ) -> Optional[ResourceAllocation]:
        """
        Update resource allocation.

        Args:
            allocation_id: Allocation UUID
            client_account_id: Client account UUID (per migration 115)
            engagement_id: Engagement UUID (per migration 115)
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
