"""
Flow Lifecycle Operations

Handles pause, resume, and delete operations with state transition management
and comprehensive cache invalidation coordination.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from app.services.flow_orchestration import FlowAuditLogger
from app.services.flow_orchestration.audit_logger import AuditCategory, AuditLevel

from .enums import FlowOperationType
from .flow_cache_manager import FlowCacheManager
from .mock_monitor import MockFlowPerformanceMonitor

logger = logging.getLogger(__name__)


class FlowLifecycleOperations:
    """Handles flow lifecycle operations (pause, resume, delete)"""

    def __init__(
        self,
        db: AsyncSession,
        context: RequestContext,
        master_repo: CrewAIFlowStateExtensionsRepository,
        flow_registry,
        performance_monitor: MockFlowPerformanceMonitor,
        audit_logger: FlowAuditLogger,
        cache_manager: FlowCacheManager,
    ):
        self.db = db
        self.context = context
        self.master_repo = master_repo
        self.flow_registry = flow_registry
        self.performance_monitor = performance_monitor
        self.audit_logger = audit_logger
        self.cache_manager = cache_manager

    async def pause_flow(self, flow_id: str) -> Dict[str, Any]:
        """
        Pause a running flow with state preservation

        Args:
            flow_id: Flow identifier

        Returns:
            Pause operation result
        """
        tracking_id = None

        try:
            tracking_id = self.performance_monitor.start_operation(
                flow_id=flow_id, operation_type="pause_flow", metadata={}
            )

            logger.info(f"⏸️ Pausing flow: {flow_id}")

            # Get flow from database
            master_flow = await self.master_repo.get_by_flow_id(flow_id)
            if not master_flow:
                raise ValueError(f"Flow not found: {flow_id}")

            # Check if flow can be paused
            if master_flow.flow_status in ["completed", "cancelled", "paused"]:
                return {
                    "status": "already_paused",
                    "flow_id": flow_id,
                    "message": f"Flow is already in '{master_flow.flow_status}' state",
                }

            # Preserve current state
            await self._preserve_flow_state(master_flow)

            # Capture current status before modification for accurate audit trail
            previous_status = master_flow.flow_status

            # Update flow status to paused
            master_flow.flow_status = "paused"
            master_flow.updated_at = datetime.now(timezone.utc)

            # Store pause metadata
            if "lifecycle_events" not in master_flow.flow_persistence_data:
                master_flow.flow_persistence_data["lifecycle_events"] = []

            master_flow.flow_persistence_data["lifecycle_events"].append(
                {
                    "event": "paused",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "previous_status": previous_status,
                    "user_id": self.context.user_id,
                }
            )

            await self.db.commit()

            # Update Redis cache
            await self._update_redis_flow_status(flow_id, "paused")

            # Log pause event
            await self.audit_logger.log_audit_event(
                flow_id=flow_id,
                operation=FlowOperationType.PAUSE.value,
                category=AuditCategory.FLOW_LIFECYCLE,
                level=AuditLevel.INFO,
                context=self.context,
                success=True,
                details={"previous_status": previous_status},
            )

            self.performance_monitor.end_operation(tracking_id, success=True)
            logger.info(f"✅ Flow paused successfully: {flow_id}")

            return {
                "status": "paused",
                "flow_id": flow_id,
                "paused_at": datetime.now(timezone.utc).isoformat(),
                "message": "Flow paused successfully",
            }

        except Exception as e:
            logger.error(f"❌ Failed to pause flow {flow_id}: {e}")

            await self.audit_logger.log_audit_event(
                flow_id=flow_id,
                operation=FlowOperationType.PAUSE.value,
                category=AuditCategory.ERROR_EVENT,
                level=AuditLevel.ERROR,
                context=self.context,
                success=False,
                error_message=str(e),
            )

            if tracking_id:
                self.performance_monitor.end_operation(tracking_id, success=False)

            raise RuntimeError(f"Failed to pause flow: {str(e)}")

    async def resume_flow(
        self, flow_id: str, resume_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Resume a paused flow from its last saved state

        Args:
            flow_id: Flow identifier
            resume_context: Additional context for resume operation

        Returns:
            Resume operation result
        """
        tracking_id = None

        try:
            tracking_id = self.performance_monitor.start_operation(
                flow_id=flow_id, operation_type="resume_flow", metadata={}
            )

            logger.info(f"▶️ Resuming flow: {flow_id}")

            # Get flow from database
            master_flow = await self.master_repo.get_by_flow_id(flow_id)
            if not master_flow:
                raise ValueError(f"Flow not found: {flow_id}")

            # Check if flow can be resumed
            if master_flow.flow_status not in [
                "paused",
                "waiting_for_approval",
                "initialized",
                "initializing",
                "running",
                "processing",  # Allow resuming flows in processing state (may have been interrupted)
                "completed",  # Allow resuming completed flows for reprocessing
                "in_progress",  # Allow resuming flows that are in progress
            ]:
                return {
                    "status": "resume_failed",
                    "flow_id": flow_id,
                    "error": f"Cannot resume flow in '{master_flow.flow_status}' state",
                }

            # Restore flow state and resume execution
            resume_result = await self._restore_and_resume_flow(
                master_flow, resume_context
            )

            # Update flow status
            master_flow.flow_status = "running"
            master_flow.updated_at = datetime.now(timezone.utc)

            # Record resume event
            if "lifecycle_events" not in master_flow.flow_persistence_data:
                master_flow.flow_persistence_data["lifecycle_events"] = []

            master_flow.flow_persistence_data["lifecycle_events"].append(
                {
                    "event": "resumed",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "previous_status": "paused",
                    "user_id": self.context.user_id,
                    "resume_context": resume_context or {},
                }
            )

            await self.db.commit()

            # Update Redis cache
            await self._update_redis_flow_status(flow_id, "running")

            # Log resume event
            await self.audit_logger.log_audit_event(
                flow_id=flow_id,
                operation=FlowOperationType.RESUME.value,
                category=AuditCategory.FLOW_LIFECYCLE,
                level=AuditLevel.INFO,
                context=self.context,
                success=True,
                details={"resume_result": resume_result},
            )

            self.performance_monitor.end_operation(tracking_id, success=True)
            logger.info(f"✅ Flow resumed successfully: {flow_id}")

            return {
                "status": "resumed",
                "flow_id": flow_id,
                "resumed_at": datetime.now(timezone.utc).isoformat(),
                "resume_result": resume_result,
                "message": "Flow resumed successfully",
            }

        except Exception as e:
            logger.error(f"❌ Failed to resume flow {flow_id}: {e}")

            await self.audit_logger.log_audit_event(
                flow_id=flow_id,
                operation=FlowOperationType.RESUME.value,
                category=AuditCategory.ERROR_EVENT,
                level=AuditLevel.ERROR,
                context=self.context,
                success=False,
                error_message=str(e),
            )

            if tracking_id:
                self.performance_monitor.end_operation(tracking_id, success=False)

            return {
                "status": "resume_failed",
                "flow_id": flow_id,
                "error": str(e),
            }

    async def delete_flow(self, flow_id: str) -> Dict[str, Any]:
        """
        Soft delete a flow with comprehensive cleanup

        Args:
            flow_id: Flow identifier

        Returns:
            Delete operation result
        """
        tracking_id = None

        try:
            tracking_id = self.performance_monitor.start_operation(
                flow_id=flow_id, operation_type="delete_flow", metadata={}
            )

            logger.info(f"🗑️ Deleting flow: {flow_id}")

            # Get flow from database
            master_flow = await self.master_repo.get_by_flow_id(flow_id)
            if not master_flow:
                raise ValueError(f"Flow not found: {flow_id}")

            # Perform soft delete
            master_flow.flow_status = "deleted"
            master_flow.updated_at = datetime.now(timezone.utc)

            # Record deletion metadata
            if "lifecycle_events" not in master_flow.flow_persistence_data:
                master_flow.flow_persistence_data["lifecycle_events"] = []

            master_flow.flow_persistence_data["lifecycle_events"].append(
                {
                    "event": "deleted",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "user_id": self.context.user_id,
                    "deletion_type": "soft_delete",
                }
            )

            await self.db.commit()

            # Comprehensive cache invalidation
            cache_result = await self.cache_manager.invalidate_comprehensive_cache(
                flow_id, operation_type="delete"
            )

            # Log deletion
            await self.audit_logger.log_audit_event(
                flow_id=flow_id,
                operation=FlowOperationType.DELETE.value,
                category=AuditCategory.FLOW_LIFECYCLE,
                level=AuditLevel.INFO,
                context=self.context,
                success=True,
                details={
                    "deletion_type": "soft_delete",
                    "cache_invalidation": cache_result,
                },
            )

            self.performance_monitor.end_operation(tracking_id, success=True)
            logger.info(f"✅ Flow deleted successfully: {flow_id}")

            return {
                "deleted": True,
                "flow_id": flow_id,
                "deleted_at": datetime.now(timezone.utc).isoformat(),
                "deletion_type": "soft_delete",
                "cache_invalidation": cache_result,
                "message": "Flow deleted successfully",
            }

        except Exception as e:
            logger.error(f"❌ Failed to delete flow {flow_id}: {e}")

            await self.audit_logger.log_audit_event(
                flow_id=flow_id,
                operation=FlowOperationType.DELETE.value,
                category=AuditCategory.ERROR_EVENT,
                level=AuditLevel.ERROR,
                context=self.context,
                success=False,
                error_message=str(e),
            )

            if tracking_id:
                self.performance_monitor.end_operation(tracking_id, success=False)

            raise RuntimeError(f"Failed to delete flow: {str(e)}")

    async def _preserve_flow_state(self, master_flow) -> None:
        """Preserve current flow state before pausing"""
        if "pause_state" not in master_flow.flow_persistence_data:
            master_flow.flow_persistence_data["pause_state"] = {}

        master_flow.flow_persistence_data["pause_state"] = {
            "preserved_at": datetime.now(timezone.utc).isoformat(),
            "current_phase": master_flow.current_phase,
            "progress_percentage": master_flow.progress_percentage,
            "flow_status": master_flow.flow_status,
        }

    async def _restore_and_resume_flow(
        self, master_flow, resume_context
    ) -> Dict[str, Any]:
        """Restore flow state and initiate resume using registered crew_class"""
        try:
            # Restore preserved state if available
            pause_state = master_flow.flow_persistence_data.get("pause_state")
            if pause_state:
                logger.info(f"Restoring flow state from pause: {master_flow.flow_id}")

            # Get the flow configuration from registry (MFO design pattern)
            flow_config = self.flow_registry.get_flow_config(master_flow.flow_type)

            # Create flow instance using crew_class if available (per MFO design)
            if flow_config.crew_class:
                flow_instance = flow_config.crew_class(
                    flow_id=master_flow.flow_id,
                    initial_state=master_flow.flow_persistence_data,
                    configuration=master_flow.flow_configuration,
                    context=self.context,
                )

                # Call resume method on the instance if it exists
                if hasattr(flow_instance, "resume_from_state"):
                    resume_result = await flow_instance.resume_from_state(
                        resume_context or {}
                    )
                elif hasattr(flow_instance, "resume_flow"):
                    resume_result = await flow_instance.resume_flow(
                        resume_context or {}
                    )
                else:
                    # Fallback: mark as resumed but let next execute_phase handle actual work
                    logger.info(
                        f"Flow instance has no resume method, marking as running for {master_flow.flow_id}"
                    )
                    resume_result = {
                        "status": "resumed",
                        "message": "Flow marked as running, ready for phase execution",
                        "current_phase": master_flow.get_current_phase()
                        or "initialization",
                    }
            else:
                # No crew_class registered - this is the actual problem we need to fix
                logger.warning(
                    f"No crew_class registered for flow type '{master_flow.flow_type}'"
                )
                resume_result = {
                    "status": "resumed",
                    "message": f"Flow type '{master_flow.flow_type}' resumed (no crew_class registered)",
                    "current_phase": master_flow.get_current_phase()
                    or "initialization",
                }

            return resume_result

        except Exception as e:
            logger.error(
                f"Failed to restore and resume flow {master_flow.flow_id}: {e}"
            )
            raise

    async def _update_redis_flow_status(self, flow_id: str, status: str) -> None:
        """Update flow status in Redis cache"""
        try:
            from app.services.caching.redis_cache import redis_cache

            await redis_cache.update_flow_status(
                flow_id,
                status,
                self.context.client_account_id,
                self.context.engagement_id,
            )
        except Exception as e:
            logger.warning(f"Failed to update Redis status for {flow_id}: {e}")
