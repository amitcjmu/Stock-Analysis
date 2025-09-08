"""
Asset Utility Commands

Utility functions for asset operations.
"""

import logging
import uuid
from typing import Optional

from sqlalchemy import select

from app.models.discovery_flow import DiscoveryFlow
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

from .asset_base import AssetCommandsBase

logger = logging.getLogger(__name__)


class AssetUtilityCommands(AssetCommandsBase):
    """Handles asset utility operations"""

    async def get_master_flow_id_from_discovery(
        self, discovery_flow_id: uuid.UUID
    ) -> Optional[uuid.UUID]:
        """Get master flow ID from discovery flow"""
        try:
            # Get discovery flow
            result = await self.db.execute(
                select(DiscoveryFlow.flow_id).where(
                    DiscoveryFlow.id == discovery_flow_id
                )
            )
            flow_id = result.scalar_one_or_none()

            if not flow_id:
                logger.warning(
                    f"No flow_id found for discovery_flow_id: {discovery_flow_id}"
                )
                return None

            # Get master flow ID from extension - table name is plural
            result = await self.db.execute(
                select(CrewAIFlowStateExtensions.flow_id).where(  # PLURAL
                    CrewAIFlowStateExtensions.flow_id == flow_id
                )  # PLURAL
            )
            master_flow_id = result.scalar_one_or_none()

            return master_flow_id
        except Exception as e:
            logger.error(
                f"Failed to get master_flow_id for discovery_flow_id {discovery_flow_id}: {e}"
            )
            return None
