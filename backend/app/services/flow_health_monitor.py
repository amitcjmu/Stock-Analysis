"""
Flow Health Monitor Service

Monitors flow health and handles stuck flows automatically.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.discovery_flow import DiscoveryFlow
from app.services.caching.redis_cache import get_redis_cache

logger = logging.getLogger(__name__)


class FlowHealthMonitor:
    """Monitors and maintains flow health"""

    def __init__(self):
        self.running = False
        self.monitor_task = None
        self.redis = get_redis_cache()

    async def start(self):
        """Start the health monitor"""
        if self.running:
            logger.warning("Flow health monitor already running")
            return

        self.running = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("✅ Flow health monitor started")

    async def stop(self):
        """Stop the health monitor"""
        self.running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 Flow health monitor stopped")

    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # DISABLED: Auto-failing flows based on timeouts is problematic
                # We should handle stuck flows manually through admin UI
                # await self.check_stuck_flows()
                # await self.check_timeout_flows()

                # Only update metrics, don't auto-fail flows
                await self.update_flow_metrics()

                # Sleep for 5 minutes
                await asyncio.sleep(300)

            except Exception as e:
                logger.error(f"❌ Error in flow health monitor: {e}")
                await asyncio.sleep(60)  # Sleep for 1 minute on error

    async def check_stuck_flows(self):
        """Check for flows stuck at 0% progress

        DISABLED: This method is no longer called. Auto-failing flows is problematic.
        Flows should be managed manually through admin UI.
        """
        try:
            async with AsyncSessionLocal() as db:
                # Find flows stuck at initialization/active with 0% progress for > 1 hour
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)

                # SKIP_TENANT_CHECK - Service-level/monitoring query
                stmt = select(DiscoveryFlow).where(
                    and_(
                        DiscoveryFlow.status.in_(["active", "initialized", "running"]),
                        DiscoveryFlow.progress_percentage == 0.0,
                        DiscoveryFlow.created_at < cutoff_time,
                    )
                )

                result = await db.execute(stmt)
                stuck_flows = result.scalars().all()

                if stuck_flows:
                    logger.warning(f"⚠️ Found {len(stuck_flows)} stuck flows")

                    for flow in stuck_flows:
                        await self._handle_stuck_flow(db, flow)

                    await db.commit()

        except Exception as e:
            logger.error(f"❌ Error checking stuck flows: {e}")

    async def check_timeout_flows(self):
        """Check for flows that have exceeded their timeout

        DISABLED: This method is no longer called. Auto-failing flows is problematic.
        Flows should be managed manually through admin UI.
        """
        try:
            async with AsyncSessionLocal() as db:
                # SKIP_TENANT_CHECK - Service-level/monitoring query
                # Get all active flows
                # SKIP_TENANT_CHECK - Service-level/monitoring query
                stmt = select(DiscoveryFlow).where(
                    DiscoveryFlow.status.in_(
                        ["active", "initialized", "running", "waiting_for_approval"]
                    )
                )

                result = await db.execute(stmt)
                active_flows = result.scalars().all()

                now = datetime.now(timezone.utc)

                for flow in active_flows:
                    # Check timeout in metadata
                    if flow.crewai_state_data and "metadata" in flow.crewai_state_data:
                        timeout_str = flow.crewai_state_data["metadata"].get(
                            "timeout_at"
                        )
                        if timeout_str:
                            timeout_at = datetime.fromisoformat(
                                timeout_str.replace("Z", "+00:00")
                            )
                            if now > timeout_at:
                                logger.warning(
                                    f"⏰ Flow {flow.flow_id} has exceeded timeout"
                                )
                                await self._handle_timeout_flow(db, flow)

                await db.commit()

        except Exception as e:
            logger.error(f"❌ Error checking timeout flows: {e}")

    async def _handle_stuck_flow(self, db: AsyncSession, flow: DiscoveryFlow):
        """Handle a stuck flow"""
        try:
            logger.info(f"🔧 Handling stuck flow {flow.flow_id}")

            # Update flow status
            flow.status = "failed"
            flow.error_message = (
                "Flow stuck at initialization with no progress after 1 hour"
            )
            flow.error_phase = "initialization"
            # Ensure created_at is timezone-aware
            created_at = flow.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)

            flow.error_details = {
                "reason": "stuck_at_zero_progress",
                "stuck_duration_hours": (
                    datetime.now(timezone.utc) - created_at
                ).total_seconds()
                / 3600,
            }
            flow.updated_at = datetime.now(timezone.utc)

            # Update state data
            if not flow.crewai_state_data:
                flow.crewai_state_data = {}
            flow.crewai_state_data["status"] = "failed"
            flow.crewai_state_data["error"] = flow.error_message

            logger.info(f"✅ Marked stuck flow {flow.flow_id} as failed")

        except Exception as e:
            logger.error(f"❌ Error handling stuck flow {flow.flow_id}: {e}")

    async def _handle_timeout_flow(self, db: AsyncSession, flow: DiscoveryFlow):
        """Handle a flow that has timed out"""
        try:
            logger.info(f"⏰ Handling timeout for flow {flow.flow_id}")

            # Update flow status
            flow.status = "failed"
            flow.error_message = "Flow exceeded 24-hour timeout limit"
            flow.error_phase = flow.current_phase or "unknown"
            flow.error_details = {
                "reason": "timeout_exceeded",
                "timeout_hours": 24,
                "last_progress": flow.progress_percentage,
            }
            flow.updated_at = datetime.now(timezone.utc)

            # Update state data
            if not flow.crewai_state_data:
                flow.crewai_state_data = {}
            flow.crewai_state_data["status"] = "failed"
            flow.crewai_state_data["error"] = flow.error_message

            logger.info(f"✅ Marked timeout flow {flow.flow_id} as failed")

        except Exception as e:
            logger.error(f"❌ Error handling timeout flow {flow.flow_id}: {e}")

    async def _get_discovery_flow_by_master_id(
        self, db: AsyncSession, master_flow_id: str
    ) -> Optional[DiscoveryFlow]:
        """Get discovery flow by master ID with caching"""
        cache_key = f"v1:flow:discovery:by_master:{master_flow_id}"

        # Try to get from cache first
        if self.redis and self.redis.enabled:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                # Reconstruct the DiscoveryFlow object from cached data
                # SKIP_TENANT_CHECK - Service-level/monitoring query
                disc_stmt = select(DiscoveryFlow).where(
                    DiscoveryFlow.id == cached_data["id"]
                )
                disc_result = await db.execute(disc_stmt)
                return disc_result.scalar_one_or_none()

        # SKIP_TENANT_CHECK - Service-level/monitoring query
        # Not in cache, query database
        disc_stmt = (
            # SKIP_TENANT_CHECK - Service-level/monitoring query
            select(DiscoveryFlow)
            .where(DiscoveryFlow.master_flow_id == master_flow_id)
            .order_by(DiscoveryFlow.created_at.desc())
            .limit(1)
        )
        disc_result = await db.execute(disc_stmt)
        discovery_flow = disc_result.scalar_one_or_none()

        # Cache the result if found
        if discovery_flow and self.redis and self.redis.enabled:
            # Cache essential fields only - no PII/sensitive data
            # Only caching flow metadata: IDs, status, and progress metrics
            cache_data = {
                "id": str(discovery_flow.id),
                "flow_id": str(discovery_flow.flow_id),
                "status": discovery_flow.status,
                "progress_percentage": discovery_flow.progress_percentage,
                "current_phase": discovery_flow.current_phase,
            }
            # CACHE_SECURITY: Non-sensitive flow metadata only
            await self.redis.set(cache_key, cache_data, ttl=300)  # 5 minute TTL

        return discovery_flow

    async def update_flow_metrics(self):
        """Update flow metrics in master flow records"""
        try:
            async with AsyncSessionLocal() as db:
                # Get all master flows with discovery children
                # SKIP_TENANT_CHECK - Service-level/monitoring query
                stmt = select(CrewAIFlowStateExtensions).where(
                    CrewAIFlowStateExtensions.flow_type == "discovery"
                )

                result = await db.execute(stmt)
                master_flows = result.scalars().all()

                for master in master_flows:
                    # Get associated discovery flow with caching
                    discovery_flow = await self._get_discovery_flow_by_master_id(
                        db, str(master.flow_id)
                    )

                    if discovery_flow:
                        # Update metrics
                        if not master.flow_metadata:
                            master.flow_metadata = {}

                        master.flow_metadata["discovery_progress"] = (
                            discovery_flow.progress_percentage
                        )
                        master.flow_metadata["discovery_status"] = discovery_flow.status
                        master.flow_metadata["discovery_phase"] = (
                            discovery_flow.current_phase
                        )
                        master.updated_at = datetime.now(timezone.utc)

                await db.commit()

        except Exception as e:
            logger.error(f"❌ Error updating flow metrics: {e}")

    async def get_flow_health_report(self) -> Dict[str, Any]:
        """Get a health report for all flows"""
        try:
            async with AsyncSessionLocal() as db:
                # Count flows by status
                status_counts = {}
                for status in [
                    "active",
                    "initialized",
                    "running",
                    "complete",
                    "failed",
                    "waiting_for_approval",
                ]:
                    # SKIP_TENANT_CHECK - Service-level/monitoring query
                    stmt = select(func.count()).where(DiscoveryFlow.status == status)
                    result = await db.execute(stmt)
                    status_counts[status] = result.scalar() or 0

                # Find stuck flows
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=1)
                # SKIP_TENANT_CHECK - Service-level/monitoring query
                stuck_stmt = select(func.count()).where(
                    and_(
                        DiscoveryFlow.status.in_(["active", "initialized", "running"]),
                        DiscoveryFlow.progress_percentage == 0.0,
                        DiscoveryFlow.created_at < cutoff_time,
                    )
                )
                stuck_result = await db.execute(stuck_stmt)
                stuck_count = stuck_result.scalar() or 0

                # Average progress by status
                progress_by_status = {}
                for status in ["active", "running"]:
                    # SKIP_TENANT_CHECK - Service-level/monitoring query
                    stmt = select(func.avg(DiscoveryFlow.progress_percentage)).where(
                        DiscoveryFlow.status == status
                    )
                    result = await db.execute(stmt)
                    avg_progress = result.scalar()
                    if avg_progress is not None:
                        progress_by_status[status] = round(avg_progress, 1)

                return {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status_counts": status_counts,
                    "stuck_flows": stuck_count,
                    "average_progress": progress_by_status,
                    "health_status": "healthy" if stuck_count == 0 else "unhealthy",
                }

        except Exception as e:
            logger.error(f"❌ Error generating health report: {e}")
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
                "health_status": "error",
            }


# Global instance
flow_health_monitor = FlowHealthMonitor()
