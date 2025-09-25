"""
Query operations for Collection Flow State Management
"""

import logging
import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.collection_flow import CollectionFlow, CollectionFlowStatus

logger = logging.getLogger(__name__)


class CollectionFlowQueryService:
    """Query service for Collection Flow operations"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize the Collection Flow Query Service.

        Args:
            db: Database session
            context: Request context with tenant information
        """
        self.db = db
        self.context = context
        self.client_account_id = str(context.client_account_id)
        self.engagement_id = str(context.engagement_id)

    async def get_flow_by_id(self, flow_id: uuid.UUID) -> Optional[CollectionFlow]:
        """
        Get Collection Flow by ID.

        Args:
            flow_id: Flow ID

        Returns:
            CollectionFlow instance or None
        """
        try:
            result = await self.db.execute(
                select(CollectionFlow).where(
                    CollectionFlow.flow_id == flow_id,
                    CollectionFlow.client_account_id
                    == uuid.UUID(self.client_account_id),
                )
            )
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Failed to get Collection Flow {flow_id}: {str(e)}")
            raise

    async def get_flows_by_status(
        self, status: CollectionFlowStatus, limit: int = 100
    ) -> List[CollectionFlow]:
        """
        Get Collection Flows by status.

        Args:
            status: Flow status
            limit: Maximum number of flows to return

        Returns:
            List of CollectionFlow instances
        """
        try:
            result = await self.db.execute(
                select(CollectionFlow)
                .where(
                    CollectionFlow.status == status,
                    CollectionFlow.client_account_id
                    == uuid.UUID(self.client_account_id),
                )
                .limit(limit)
            )
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Failed to get Collection Flows by status {status}: {str(e)}")
            raise
