"""
Status Operations Module

Contains flow status retrieval and management operations.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.logging import get_logger
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from app.services.flow_contracts import (
    FlowAuditLogger,
    FlowStatusManager,
    AuditCategory,
    AuditLevel,
)
from app.services.flow_orchestration.smart_discovery_service import (
    SmartDiscoveryService,
)

from .enums import FlowOperationType
from .mock_monitor import MockFlowPerformanceMonitor

logger = get_logger(__name__)


class StatusOperations:
    """Handles flow status retrieval and management operations"""

    def __init__(
        self,
        db: AsyncSession,
        context: RequestContext,
        master_repo: CrewAIFlowStateExtensionsRepository,
        flow_registry,
        performance_monitor: MockFlowPerformanceMonitor,
        audit_logger: FlowAuditLogger,
        status_manager: FlowStatusManager,
        smart_discovery_service: SmartDiscoveryService,
    ):
        self.db = db
        self.context = context
        self.master_repo = master_repo
        self.flow_registry = flow_registry
        self.performance_monitor = performance_monitor
        self.audit_logger = audit_logger
        self.status_manager = status_manager
        self.smart_discovery_service = smart_discovery_service

    async def get_flow_status(
        self, flow_id: str, include_details: bool = True
    ) -> Dict[str, Any]:
        """Get comprehensive flow status with smart fallback strategies"""
        try:
            tracking_id = self.performance_monitor.start_operation(
                flow_id=flow_id, operation_type="status_check", metadata={}
            )

            # Try primary method first
            try:
                status = await self.status_manager.get_flow_status(
                    flow_id, include_details
                )

                # Enhance with orphaned data recovery if needed
                if include_details:
                    status = await self._enhance_status_with_smart_discovery(
                        flow_id, status
                    )

                self.performance_monitor.end_operation(tracking_id, success=True)
                return status

            except ValueError as primary_error:
                # Flow not found in primary method - try smart discovery
                logger.info(
                    f"🔍 Primary flow lookup failed for {flow_id}, attempting smart discovery..."
                )

                discovered_data = (
                    await self.smart_discovery_service.smart_flow_discovery(flow_id)
                )
                if discovered_data:
                    smart_status = await self.smart_discovery_service.build_status_from_discovered_data(
                        flow_id, discovered_data
                    )
                else:
                    smart_status = None

                if smart_status:
                    logger.info(f"✅ Smart discovery found data for flow {flow_id}")
                    self.performance_monitor.end_operation(tracking_id, success=True)
                    return smart_status
                else:
                    logger.warning(f"❌ Smart discovery failed for flow {flow_id}")
                    raise primary_error

            await self.audit_logger.log_audit_event(
                flow_id=flow_id,
                operation=FlowOperationType.STATUS_CHECK.value,
                category=AuditCategory.FLOW_LIFECYCLE,
                level=AuditLevel.DEBUG,
                context=self.context,
                success=True,
                details={"include_details": include_details},
            )

        except ValueError as e:
            logger.warning(f"Flow not found: {flow_id}")
            raise e
        except Exception as e:
            await self.audit_logger.log_audit_event(
                flow_id=flow_id,
                operation=FlowOperationType.STATUS_CHECK.value,
                category=AuditCategory.ERROR_EVENT,
                level=AuditLevel.ERROR,
                context=self.context,
                success=False,
                error_message=str(e),
            )
            raise RuntimeError(f"Failed to get flow status: {str(e)}")

    async def _enhance_status_with_smart_discovery(
        self, flow_id: str, status: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance existing status with smart discovery of related orphaned data"""
        try:
            orphaned_data = (
                await self.smart_discovery_service.find_orphaned_data_for_flow(flow_id)
            )

            if orphaned_data:
                if "metadata" not in status:
                    status["metadata"] = {}

                status["metadata"]["orphaned_data_found"] = True
                status["metadata"]["orphaned_data_summary"] = orphaned_data
                status["metadata"]["repair_available"] = True

                logger.info(
                    f"🔍 Enhanced status for flow {flow_id} with orphaned data information"
                )

            return status
        except Exception as e:
            logger.warning(f"⚠️ Failed to enhance status with smart discovery: {e}")
            return status

    async def get_active_flows(
        self, flow_type: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get list of active flows"""
        try:
            flows = await self.status_manager.get_active_flows(flow_type, limit)

            await self.audit_logger.log_audit_event(
                flow_id="system",
                operation=FlowOperationType.LIST.value,
                category=AuditCategory.FLOW_LIFECYCLE,
                level=AuditLevel.DEBUG,
                context=self.context,
                success=True,
                details={"flow_type": flow_type, "limit": limit, "count": len(flows)},
            )

            return flows
        except Exception as e:
            await self.audit_logger.log_audit_event(
                flow_id="system",
                operation=FlowOperationType.LIST.value,
                category=AuditCategory.ERROR_EVENT,
                level=AuditLevel.ERROR,
                context=self.context,
                success=False,
                error_message=str(e),
            )
            raise RuntimeError(f"Failed to get active flows: {str(e)}")

    async def list_flows_by_engagement(
        self, engagement_id: str, flow_type: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List flows for a specific engagement"""
        try:
            flows = await self.status_manager.list_flows_by_engagement(
                engagement_id, flow_type, limit
            )

            await self.audit_logger.log_audit_event(
                flow_id="system",
                operation=FlowOperationType.LIST.value,
                category=AuditCategory.FLOW_LIFECYCLE,
                level=AuditLevel.DEBUG,
                context=self.context,
                success=True,
                details={
                    "engagement_id": engagement_id,
                    "flow_type": flow_type,
                    "limit": limit,
                    "count": len(flows),
                },
            )

            return flows
        except Exception as e:
            await self.audit_logger.log_audit_event(
                flow_id="system",
                operation=FlowOperationType.LIST.value,
                category=AuditCategory.ERROR_EVENT,
                level=AuditLevel.ERROR,
                context=self.context,
                success=False,
                error_message=str(e),
            )
            return (
                []
            )  # Return empty list instead of raising to prevent user context failures
