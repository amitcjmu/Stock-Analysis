"""
Discovery Child Flow Service
Service for managing discovery flow child operations
"""

import logging
from typing import Any, Dict, Optional

from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from app.services.child_flow_services.base import BaseChildFlowService

logger = logging.getLogger(__name__)


class DiscoveryChildFlowService(BaseChildFlowService):
    """Service for discovery flow child operations"""

    def __init__(self, db, context):
        super().__init__(db, context)
        # Initialize repository with proper tenant context
        self.repository = DiscoveryFlowRepository(
            db=self.db,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            user_id=context.user_id,
        )

    async def get_child_status(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get discovery flow child status

        Args:
            flow_id: Flow identifier

        Returns:
            Child flow status dictionary or None
        """
        try:
            child_flow = await self.repository.get_by_flow_id(flow_id)
            if not child_flow:
                return None

            return {
                "status": getattr(child_flow, "status", None),
                "current_phase": getattr(child_flow, "current_phase", None),
                "progress_percentage": getattr(child_flow, "progress_percentage", 0.0),
                "metadata": getattr(child_flow, "metadata", {}),
            }
        except Exception as e:
            logger.warning(f"Failed to get discovery child flow status: {e}")
            return None

    async def get_by_master_flow_id(self, flow_id: str) -> Optional[Any]:
        """
        Get discovery flow by master flow ID

        Args:
            flow_id: Master flow identifier

        Returns:
            Discovery flow entity or None
        """
        try:
            return await self.repository.get_by_master_flow_id(flow_id)
        except Exception as e:
            logger.warning(f"Failed to get discovery flow by master ID: {e}")
            return None
