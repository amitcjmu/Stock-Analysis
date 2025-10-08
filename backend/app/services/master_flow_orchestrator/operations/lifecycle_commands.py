"""Flow Lifecycle Commands - Write operations for flow lifecycle"""

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
from app.services.crewai_flows.flow_state_manager import FlowStateManager

from .enums import FlowOperationType
from .flow_cache_manager import FlowCacheManager
from .mock_monitor import MockFlowPerformanceMonitor

logger = logging.getLogger(__name__)


class FlowLifecycleCommands:
    """Handles flow lifecycle write operations (pause, resume, delete)"""

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
        self.state_manager = FlowStateManager(db, context)

    async def pause_flow(self, flow_id: str) -> Dict[str, Any]:
        """Pause a running flow with state preservation"""
        tracking_id = None
        try:
            tracking_id = self.performance_monitor.start_operation(
                flow_id=flow_id, operation_type="pause_flow", metadata={}
            )

            master_flow = await self.master_repo.get_by_flow_id(flow_id)
            if not master_flow:
                logger.error(f"Flow not found: {flow_id}")
                orphaned_info = await self._check_for_orphaned_collection_flow(
                    flow_id, "pause"
                )
                if orphaned_info:
                    logger.warning(f"Found orphaned collection flow {flow_id}")
                    raise ValueError(
                        f"Flow {flow_id} is orphaned. Use continue endpoint to repair."
                    )
                raise ValueError(f"Flow not found: {flow_id}")

            if master_flow.flow_status in ["completed", "cancelled", "paused"]:
                return {
                    "status": "already_paused",
                    "flow_id": flow_id,
                    "message": f"Flow is already in '{master_flow.flow_status}' state",
                }

            await self._preserve_flow_state(master_flow)
            previous_status = master_flow.flow_status

            await self.state_manager.update_master_flow_status(
                flow_id=flow_id,
                new_status="paused",
                metadata={
                    "event": "paused",
                    "previous_status": previous_status,
                    "user_id": self.context.user_id,
                },
            )

            await self._update_redis_flow_status(flow_id, "paused")

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

            return {
                "status": "paused",
                "flow_id": flow_id,
                "paused_at": datetime.now(timezone.utc).isoformat(),
                "message": "Flow paused successfully",
            }

        except Exception as e:
            logger.error(f"Failed to pause flow {flow_id}: {e}")
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
        """Resume a paused flow from its last saved state"""
        tracking_id = None
        try:
            tracking_id = self.performance_monitor.start_operation(
                flow_id=flow_id, operation_type="resume_flow", metadata={}
            )

            master_flow = await self.master_repo.get_by_flow_id(flow_id)
            if not master_flow:
                logger.error(f"Flow not found for resume: {flow_id}")
                orphaned_info = await self._check_for_orphaned_collection_flow(
                    flow_id, "resume"
                )
                if orphaned_info:
                    logger.warning(f"Found orphaned collection flow {flow_id}")
                    return {
                        "status": "resume_failed",
                        "flow_id": flow_id,
                        "error": "orphaned_collection_flow",
                        "message": f"Cannot resume flow {flow_id}. Use collection continue endpoint to repair.",
                        "suggested_action": "use_collection_continue_endpoint",
                        "collection_flow_status": (
                            orphaned_info["status"].value
                            if hasattr(orphaned_info["status"], "value")
                            else orphaned_info["status"]
                        ),
                        "collection_flow_phase": orphaned_info["current_phase"],
                    }
                raise ValueError(f"Flow not found: {flow_id}")

            resumable_states = [
                "paused",
                "waiting_for_approval",
                "initialized",
                "initializing",
                "running",
                "processing",
            ]
            if master_flow.flow_status not in resumable_states:
                return {
                    "status": "resume_failed",
                    "flow_id": flow_id,
                    "error": f"Cannot resume flow in '{master_flow.flow_status}' state",
                }

            resume_result = await self._restore_and_resume_flow(
                master_flow, resume_context
            )

            await self.state_manager.update_master_flow_status(
                flow_id=flow_id,
                new_status="running",
                metadata={
                    "event": "resumed",
                    "previous_status": "paused",
                    "user_id": self.context.user_id,
                    "resume_context": resume_context or {},
                },
            )

            await self._update_redis_flow_status(flow_id, "running")

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

            return {
                "status": "resumed",
                "flow_id": flow_id,
                "resumed_at": datetime.now(timezone.utc).isoformat(),
                "resume_result": resume_result,
                "message": "Flow resumed successfully",
            }

        except Exception as e:
            logger.error(f"Failed to resume flow {flow_id}: {e}")
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
            return {"status": "resume_failed", "flow_id": flow_id, "error": str(e)}

    async def delete_flow(self, flow_id: str) -> Dict[str, Any]:
        """Soft delete a flow with comprehensive cleanup"""
        tracking_id = None
        try:
            tracking_id = self.performance_monitor.start_operation(
                flow_id=flow_id, operation_type="delete_flow", metadata={}
            )

            master_flow = await self.master_repo.get_by_flow_id(flow_id)
            if not master_flow:
                logger.error(f"Flow not found for deletion: {flow_id}")
                raise ValueError(f"Flow not found: {flow_id}")

            await self.state_manager.update_master_flow_status(
                flow_id=flow_id,
                new_status="deleted",
                metadata={
                    "event": "deleted",
                    "user_id": self.context.user_id,
                    "deletion_type": "soft_delete",
                },
            )

            cache_result = await self.cache_manager.invalidate_comprehensive_cache(
                flow_id, operation_type="delete"
            )

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

            return {
                "deleted": True,
                "flow_id": flow_id,
                "deleted_at": datetime.now(timezone.utc).isoformat(),
                "deletion_type": "soft_delete",
                "cache_invalidation": cache_result,
                "message": "Flow deleted successfully",
            }

        except Exception as e:
            logger.error(f"Failed to delete flow {flow_id}: {e}")
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
        master_flow.flow_persistence_data["pause_state"] = {
            "preserved_at": datetime.now(timezone.utc).isoformat(),
            "current_phase": master_flow.current_phase,
            "progress_percentage": master_flow.progress_percentage,
            "flow_status": master_flow.flow_status,
        }

    async def _restore_and_resume_flow(
        self, master_flow, resume_context
    ) -> Dict[str, Any]:
        """Restore flow state and initiate resume using registered child_flow_service"""
        try:
            pause_state = master_flow.flow_persistence_data.get("pause_state")
            if pause_state:
                logger.info(f"Restoring flow state from pause: {master_flow.flow_id}")

            flow_config = self.flow_registry.get_flow_config(master_flow.flow_type)

            # Single path - check child_flow_service ONLY (Per ADR-025)
            if flow_config.child_flow_service:
                logger.info(f"Executing {master_flow.flow_type} via child_flow_service")

                child_service = flow_config.child_flow_service(self.db, self.context)
                current_phase = master_flow.get_current_phase() or "initialization"

                result = await child_service.execute_phase(
                    flow_id=str(master_flow.flow_id),
                    phase_name=current_phase,
                    phase_input=resume_context or {},
                )

                return {
                    "status": "resumed",
                    "message": "Flow resumed via child_flow_service",
                    "current_phase": current_phase,
                    "execution_result": result,
                }
            else:
                logger.error(
                    f"No child_flow_service for flow type '{master_flow.flow_type}'"
                )
                raise ValueError(
                    f"Flow type '{master_flow.flow_type}' has no execution handler"
                )

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

    async def _check_for_orphaned_collection_flow(
        self, flow_id: str, operation: str
    ) -> Optional[Dict[str, Any]]:
        """Check for orphaned collection flow and return info if found"""
        try:
            from sqlalchemy import select
            from app.models.collection_flow import CollectionFlow

            result = await self.db.execute(
                select(CollectionFlow).where(
                    CollectionFlow.flow_id == flow_id,
                    CollectionFlow.client_account_id == self.context.client_account_id,
                    CollectionFlow.engagement_id == self.context.engagement_id,
                    CollectionFlow.master_flow_id.is_(None),
                )
            )
            orphaned_collection = result.scalar_one_or_none()

            if orphaned_collection:
                return {
                    "flow_id": flow_id,
                    "status": orphaned_collection.status,
                    "current_phase": orphaned_collection.current_phase,
                }
            return None
        except Exception as e:
            logger.warning(
                f"Failed to check for orphaned collection flow during {operation}: {e}"
            )
            return None
