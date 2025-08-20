"""
Flow Health Monitor - Detection and Recovery for Stuck Flows

This module provides background monitoring for collection flows that may be
stuck or experiencing issues, with automatic recovery mechanisms.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import select

from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.models.collection_flow import CollectionFlow, CollectionFlowStatus
from app.api.v1.endpoints.collection_utils import log_collection_failure

logger = logging.getLogger(__name__)


class FlowHealthMonitor:
    """Monitor and recover stuck collection flows."""

    def __init__(
        self, check_interval_minutes: int = 5, stuck_threshold_minutes: int = 10
    ):
        """Initialize the health monitor.

        Args:
            check_interval_minutes: How often to check for stuck flows (default: 5 min)
            stuck_threshold_minutes: How long without progress before considering
                stuck (default: 10 min)
        """
        self.check_interval = timedelta(minutes=check_interval_minutes)
        self.stuck_threshold = timedelta(minutes=stuck_threshold_minutes)
        self.is_running = False
        self._monitor_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the background monitoring task."""
        if self.is_running:
            logger.warning("Flow health monitor is already running")
            return

        self.is_running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Flow health monitor started")

    async def stop(self):
        """Stop the background monitoring task."""
        self.is_running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Flow health monitor stopped")

    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self.is_running:
            try:
                await self.detect_and_recover_stuck_flows()
                await asyncio.sleep(self.check_interval.total_seconds())
            except Exception as e:
                logger.error(f"Error in flow health monitor loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying

    async def detect_and_recover_stuck_flows(self) -> List[str]:
        """Detect and recover stuck collection flows.

        Returns:
            List of flow IDs that were marked as failed
        """
        failed_flow_ids = []

        async with AsyncSessionLocal() as db:
            try:
                # Find stuck flows
                cutoff_time = datetime.now(timezone.utc) - self.stuck_threshold
                stmt = select(CollectionFlow).where(
                    CollectionFlow.status.notin_(
                        [
                            CollectionFlowStatus.COMPLETED.value,
                            CollectionFlowStatus.FAILED.value,
                            CollectionFlowStatus.CANCELLED.value,
                        ]
                    ),
                    CollectionFlow.updated_at < cutoff_time,
                )
                result = await db.execute(stmt)
                stuck_flows = result.scalars().all()

                if stuck_flows:
                    logger.warning(f"Found {len(stuck_flows)} stuck collection flows")

                for flow in stuck_flows:
                    stuck_minutes = self.stuck_threshold.total_seconds() / 60
                    error_msg = (
                        f"No progress for {stuck_minutes:.0f} minutes "
                        f"in phase {flow.current_phase}"
                    )

                    # Mark as failed
                    flow.status = CollectionFlowStatus.FAILED.value
                    flow.error_message = error_msg
                    failed_flow_ids.append(str(flow.flow_id))

                    logger.error(f"Marking flow {flow.flow_id} as failed: {error_msg}")

                    # Build context from flow data
                    context = RequestContext(
                        client_account_id=flow.client_account_id,
                        engagement_id=flow.engagement_id,
                        user_id=flow.user_id or "system",
                    )

                    # Log failure with diagnostic data
                    await log_collection_failure(
                        db=db,
                        context=context,
                        source="flow_health_monitor",
                        operation="stuck_detection",
                        payload={
                            "flow_id": str(flow.flow_id),
                            "phase": flow.current_phase,
                            "last_updated": flow.updated_at.isoformat(),
                            "created_at": flow.created_at.isoformat(),
                            "time_stuck_minutes": (
                                datetime.now(timezone.utc) - flow.updated_at
                            ).total_seconds()
                            / 60,
                        },
                        error_message=error_msg,
                    )

                await db.commit()

                if failed_flow_ids:
                    logger.info(
                        f"Recovered {len(failed_flow_ids)} stuck flows by marking as failed"
                    )

            except Exception as e:
                logger.error(f"Error detecting stuck flows: {e}")
                await db.rollback()

        return failed_flow_ids

    async def check_flow_health(self, flow_id: str) -> dict:
        """Check the health of a specific flow.

        Args:
            flow_id: Flow ID to check

        Returns:
            Health status dictionary
        """
        async with AsyncSessionLocal() as db:
            stmt = select(CollectionFlow).where(CollectionFlow.flow_id == flow_id)
            result = await db.execute(stmt)
            flow = result.scalar_one_or_none()

            if not flow:
                return {"flow_id": flow_id, "status": "not_found", "healthy": False}

            # Calculate time since last update
            time_since_update = datetime.now(timezone.utc) - flow.updated_at
            is_stuck = (
                flow.status not in ["completed", "failed", "cancelled"]
                and time_since_update > self.stuck_threshold
            )

            return {
                "flow_id": flow_id,
                "status": flow.status,
                "current_phase": flow.current_phase,
                "healthy": not is_stuck,
                "is_stuck": is_stuck,
                "last_updated": flow.updated_at.isoformat(),
                "time_since_update_minutes": time_since_update.total_seconds() / 60,
                "progress_percentage": flow.progress_percentage,
                "error_message": flow.error_message,
            }

    async def recover_flow(
        self, flow_id: str, recovery_action: str = "mark_failed"
    ) -> bool:
        """Attempt to recover a stuck flow.

        Args:
            flow_id: Flow ID to recover
            recovery_action: Action to take ("mark_failed", "restart_phase", etc.)

        Returns:
            True if recovery successful, False otherwise
        """
        async with AsyncSessionLocal() as db:
            try:
                stmt = select(CollectionFlow).where(CollectionFlow.flow_id == flow_id)
                result = await db.execute(stmt)
                flow = result.scalar_one_or_none()

                if not flow:
                    logger.error(f"Flow {flow_id} not found for recovery")
                    return False

                if recovery_action == "mark_failed":
                    flow.status = CollectionFlowStatus.FAILED.value
                    flow.error_message = "Flow recovered by health monitor"

                    context = RequestContext(
                        client_account_id=flow.client_account_id,
                        engagement_id=flow.engagement_id,
                        user_id=flow.user_id or "system",
                    )

                    await log_collection_failure(
                        db=db,
                        context=context,
                        source="flow_health_monitor",
                        operation="manual_recovery",
                        payload={
                            "flow_id": str(flow.flow_id),
                            "recovery_action": recovery_action,
                            "phase": flow.current_phase,
                        },
                        error_message="Manual recovery initiated",
                    )

                    await db.commit()
                    logger.info(f"Flow {flow_id} marked as failed for recovery")
                    return True

                elif recovery_action == "restart_phase":
                    # TODO: Implement phase restart logic
                    logger.warning(
                        f"Phase restart not yet implemented for flow {flow_id}"
                    )
                    return False

                else:
                    logger.error(f"Unknown recovery action: {recovery_action}")
                    return False

            except Exception as e:
                logger.error(f"Error recovering flow {flow_id}: {e}")
                await db.rollback()
                return False


# Global instance for background monitoring
flow_health_monitor = FlowHealthMonitor()


async def start_flow_health_monitoring():
    """Start the global flow health monitor."""
    await flow_health_monitor.start()


async def stop_flow_health_monitoring():
    """Stop the global flow health monitor."""
    await flow_health_monitor.stop()


async def get_flow_health_status(flow_id: str) -> dict:
    """Get health status for a specific flow.

    Args:
        flow_id: Flow ID to check

    Returns:
        Health status dictionary
    """
    return await flow_health_monitor.check_flow_health(flow_id)
