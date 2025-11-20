"""
Collection Child Flow Service - Base Class
Service for managing collection flow child operations following ADR-025
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.repositories.collection_flow_repository import CollectionFlowRepository
from app.services.child_flow_services.base import BaseChildFlowService
from app.services.collection_flow.state_management import CollectionFlowStateService

logger = logging.getLogger(__name__)


class CollectionChildFlowServiceBase(BaseChildFlowService):
    """Base service for collection flow child operations"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        super().__init__(db, context)
        # Initialize repository with explicit tenant scoping (per ADR-025)
        self.repository = CollectionFlowRepository(
            db=self.db,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
        )
        self.state_service = CollectionFlowStateService(db, context)

    async def get_child_status(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get collection flow child status

        Args:
            flow_id: Master flow identifier

        Returns:
            Child flow status dictionary or None
        """
        try:
            child_flow = await self.repository.get_by_master_flow_id(UUID(flow_id))
            if not child_flow:
                logger.warning(f"Collection flow not found for master flow {flow_id}")
                return None

            return {
                "status": child_flow.status,
                "current_phase": child_flow.current_phase,
                "progress_percentage": child_flow.progress_percentage,
                "automation_tier": child_flow.automation_tier,
                "collection_config": child_flow.collection_config,
                # Per ADR-028: phase_state field removed from collection_flow
            }
        except Exception as e:
            logger.warning(f"Failed to get collection child flow status: {e}")
            return None

    async def get_by_master_flow_id(self, flow_id: str):
        """
        Get collection flow by master flow ID

        Args:
            flow_id: Master flow identifier (UUID string)

        Returns:
            Collection flow entity or None
        """
        try:
            return await self.repository.get_by_master_flow_id(UUID(flow_id))
        except Exception as e:
            logger.warning(f"Failed to get collection flow by master ID: {e}")
            return None
