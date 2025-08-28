"""
Flow maintenance operations.

Handles cleanup, maintenance, and critical fixes for flows.
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy import and_, update

from app.models.discovery_flow import DiscoveryFlow
from .flow_base import FlowCommandsBase

logger = logging.getLogger(__name__)


class FlowMaintenanceCommands(FlowCommandsBase):
    """Handles flow maintenance operations"""

    async def cleanup_stuck_flows(self, hours_threshold: int = 24) -> int:
        """Clean up flows that have been stuck for more than the threshold"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_threshold)

            # Find stuck flows
            stmt = (
                update(DiscoveryFlow)
                .where(
                    and_(
                        DiscoveryFlow.client_account_id == self.client_account_id,
                        DiscoveryFlow.engagement_id == self.engagement_id,
                        DiscoveryFlow.status.in_(["active", "initialized", "running"]),
                        DiscoveryFlow.progress_percentage == 0.0,
                        DiscoveryFlow.created_at < cutoff_time,
                    )
                )
                .values(
                    status="failed",
                    error_message=f"Flow timed out after {hours_threshold} hours with no progress",
                    error_phase="timeout",
                    error_details={
                        "reason": "no_progress",
                        "threshold_hours": hours_threshold,
                    },
                    updated_at=datetime.utcnow(),
                )
            )

            result = await self.db.execute(stmt)
            await self.db.commit()

            count = result.rowcount
            if count > 0:
                logger.info(
                    f"🧹 Cleaned up {count} stuck flows older than {hours_threshold} hours"
                )

            return count

        except Exception as e:
            logger.error(f"❌ Failed to cleanup stuck flows: {e}")
            await self.db.rollback()
            return 0

    async def update_master_flow_reference(
        self, flow_id: str, master_flow_id: str
    ) -> bool:
        """
        Update the master_flow_id for existing flows where it's NULL.
        Uses SQLAlchemy update statement for efficiency.
        Don't commit, just flush - let caller handle transaction.

        CRITICAL: This method fixes NULL master_flow_id issues for production data integrity.
        """
        try:
            # Ensure flow_id and master_flow_id are UUIDs
            flow_uuid = self._ensure_uuid(flow_id)
            master_uuid = self._ensure_uuid(master_flow_id)

            # Update master_flow_id where it's currently NULL
            stmt = (
                update(DiscoveryFlow)
                .where(
                    and_(
                        DiscoveryFlow.flow_id == flow_uuid,
                        DiscoveryFlow.client_account_id == self.client_account_id,
                        DiscoveryFlow.engagement_id == self.engagement_id,
                        DiscoveryFlow.master_flow_id.is_(
                            None
                        ),  # Only update NULL values
                    )
                )
                .values(
                    master_flow_id=master_uuid,
                    updated_at=datetime.utcnow(),
                )
            )

            result = await self.db.execute(stmt)
            # 🔧 CC FIX: Only flush, don't commit - let caller handle transaction
            await self.db.flush()

            if result.rowcount > 0:
                logger.info(
                    f"✅ Updated master_flow_id for flow {flow_id}: {master_flow_id}"
                )
                return True
            else:
                logger.warning(
                    f"⚠️ No flow found to update or master_flow_id already set: {flow_id}"
                )
                return False

        except Exception as e:
            logger.error(
                f"❌ Failed to update master_flow_reference for {flow_id}: {e}"
            )
            raise
