"""
Resource Pool Operations.

Provides CRUD operations for resource pools.
"""

import logging
import uuid
from typing import List, Optional

from sqlalchemy import and_, select, update
from sqlalchemy.exc import SQLAlchemyError

from app.models.planning import ResourcePool

logger = logging.getLogger(__name__)


class ResourcePoolOperationsMixin:
    """Mixin for resource pool operations."""

    # ===========================
    # Resource Pool CRUD Operations
    # ===========================

    async def create_resource_pool(
        self,
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
        pool_name: str,
        role_name: str,
        total_capacity_hours: float,
        hourly_rate: Optional[float] = None,
        **kwargs,
    ) -> ResourcePool:
        """
        Create resource pool.

        Args:
            client_account_id: Client account UUID (per migration 115)
            engagement_id: Engagement UUID (per migration 115)
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
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
        is_active: bool = True,
    ) -> List[ResourcePool]:
        """
        List all resource pools (multi-tenant scoped).

        Args:
            client_account_id: Client account UUID (per migration 115)
            engagement_id: Engagement UUID (per migration 115)
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
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
    ) -> Optional[ResourcePool]:
        """
        Get resource pool by ID.

        Args:
            pool_id: Resource pool UUID
            client_account_id: Client account UUID (per migration 115)
            engagement_id: Engagement UUID (per migration 115)

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
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
        **updates,
    ) -> Optional[ResourcePool]:
        """
        Update resource pool.

        Args:
            pool_id: Resource pool UUID
            client_account_id: Client account UUID (per migration 115)
            engagement_id: Engagement UUID (per migration 115)
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
