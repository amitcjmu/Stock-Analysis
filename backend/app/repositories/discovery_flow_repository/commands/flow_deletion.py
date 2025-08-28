"""
Flow deletion operations.

Handles flow deletion and cleanup.
"""

import logging
from sqlalchemy import and_, delete

from app.models.discovery_flow import DiscoveryFlow
from .flow_base import FlowCommandsBase

logger = logging.getLogger(__name__)


class FlowDeletionCommands(FlowCommandsBase):
    """Handles flow deletion operations"""

    async def delete_flow(self, flow_id: str) -> bool:
        """Delete discovery flow"""
        try:
            # Ensure flow_id is UUID
            flow_uuid = self._ensure_uuid(flow_id)

            # Delete the flow
            stmt = delete(DiscoveryFlow).where(
                and_(
                    DiscoveryFlow.flow_id == flow_uuid,
                    DiscoveryFlow.client_account_id == self.client_account_id,
                    DiscoveryFlow.engagement_id == self.engagement_id,
                )
            )

            result = await self.db.execute(stmt)
            await self.db.commit()

            if result.rowcount > 0:
                logger.info(f"✅ Deleted discovery flow: {flow_id}")
                return True
            else:
                logger.warning(f"⚠️ No flow found to delete: {flow_id}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to delete flow {flow_id}: {e}")
            await self.db.rollback()
            return False
