"""
Master Flow Orchestrator Core Module

THE SINGLE ORCHESTRATOR - Refactored with modular components
Centralized orchestration for all CrewAI flows using composition pattern.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.logging import get_logger
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from app.services.crewai_flows.flow_state_manager import FlowStateManager

# Import modular components
from app.services.flow_orchestration import (
    FlowAuditLogger,
    FlowErrorHandler,
    FlowExecutionEngine,
    FlowLifecycleManager,
    FlowStatusManager,
)
from app.services.flow_orchestration.flow_repair_service import FlowRepairService
from app.services.flow_orchestration.smart_discovery_service import (
    SmartDiscoveryService,
)

from .flow_operations import FlowOperations
from .mock_monitor import MockFlowPerformanceMonitor
from .monitoring_operations import MonitoringOperations
from .status_operations import StatusOperations

# Import operation modules
from .status_sync_operations import StatusSyncOperations

logger = get_logger(__name__)


class MasterFlowOrchestrator:
    """
    THE SINGLE ORCHESTRATOR - Refactored with modular components

    This orchestrator provides:
    - Unified flow lifecycle management (via FlowLifecycleManager)
    - Centralized error handling and retry logic (via FlowErrorHandler)
    - Performance tracking and metrics (via MockFlowPerformanceMonitor - psutil dependency disabled)
    - Comprehensive audit logging (via FlowAuditLogger)
    - Status management and retrieval (via FlowStatusManager)
    - Smart flow discovery (via SmartDiscoveryService)
    - Orphaned data repair (via FlowRepairService)
    - Multi-tenant isolation
    - Type-safe flow operations
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize the Master Flow Orchestrator with modular components

        Args:
            db: Database session
            context: Request context with tenant information
        """
        self.db = db
        self.context = context

        # Initialize repository
        self.master_repo = CrewAIFlowStateExtensionsRepository(
            db, context.client_account_id, context.engagement_id, context.user_id
        )

        # Initialize global singleton registries
        from app.services.flow_type_registry import flow_type_registry
        from app.services.handler_registry import handler_registry
        from app.services.validator_registry import validator_registry

        self.flow_registry = flow_type_registry
        self.validator_registry = validator_registry
        self.handler_registry = handler_registry

        # Initialize flow configurations if not already done
        if not self.flow_registry.list_flow_types():
            logger.info("🔄 Initializing flow configurations...")
            try:
                from app.services.flow_configs import initialize_all_flows

                result = initialize_all_flows()
                logger.info(
                    f"✅ Flow configurations initialized: {len(result.get('flows_registered', []))} flows"
                )
            except ImportError as e:
                # CC: Flow configuration module not available (likely CrewAI dependency missing)
                logger.warning(f"Flow configuration initialization skipped: {e}")
                logger.info("System will continue with minimal flow support")

        # Initialize state manager
        self.state_manager = FlowStateManager(db, context)

        # Initialize modular components using composition pattern
        self.lifecycle_manager = FlowLifecycleManager(
            db=db, context=context, master_repo=self.master_repo
        )

        self.execution_engine = FlowExecutionEngine(
            db=db,
            context=context,
            master_repo=self.master_repo,
            flow_registry=self.flow_registry,
            handler_registry=self.handler_registry,
            validator_registry=self.validator_registry,
        )

        self.error_handler = FlowErrorHandler()

        self.performance_monitor = MockFlowPerformanceMonitor()

        self.audit_logger = FlowAuditLogger()

        self.status_manager = FlowStatusManager(
            db=db,
            context=context,
            master_repo=self.master_repo,
            flow_registry=self.flow_registry,
        )

        # Initialize extracted services for discovery and repair
        self.smart_discovery_service = SmartDiscoveryService(
            db, context, self.master_repo
        )
        self.flow_repair_service = FlowRepairService(db, context, self.master_repo)

        # Initialize operation modules
        self._status_sync_ops = StatusSyncOperations(db, context)

        self._flow_ops = FlowOperations(
            db=db,
            context=context,
            master_repo=self.master_repo,
            flow_registry=self.flow_registry,
            handler_registry=self.handler_registry,
            validator_registry=self.validator_registry,
            lifecycle_manager=self.lifecycle_manager,
            execution_engine=self.execution_engine,
            error_handler=self.error_handler,
            performance_monitor=self.performance_monitor,
            audit_logger=self.audit_logger,
        )

        self._status_ops = StatusOperations(
            db=db,
            context=context,
            master_repo=self.master_repo,
            flow_registry=self.flow_registry,
            performance_monitor=self.performance_monitor,
            audit_logger=self.audit_logger,
            status_manager=self.status_manager,
            smart_discovery_service=self.smart_discovery_service,
        )

        self._monitoring_ops = MonitoringOperations(
            performance_monitor=self.performance_monitor,
            audit_logger=self.audit_logger,
            error_handler=self.error_handler,
        )

        # Operation tracking
        self._active_operations: Dict[str, datetime] = {}

        logger.info(
            f"✅ Master Flow Orchestrator initialized for client {context.client_account_id}"
        )

    # ADR-012: Status sync service methods
    async def start_flow_with_atomic_sync(
        self, flow_id: str, flow_type: str
    ) -> Dict[str, Any]:
        """Start a flow with atomic status synchronization"""
        return await self._status_sync_ops.start_flow_with_atomic_sync(
            flow_id, flow_type
        )

    async def pause_flow_with_atomic_sync(
        self, flow_id: str, flow_type: str, reason: str = "user_requested"
    ) -> Dict[str, Any]:
        """Pause a flow with atomic status synchronization"""
        return await self._status_sync_ops.pause_flow_with_atomic_sync(
            flow_id, flow_type, reason
        )

    async def resume_flow_with_atomic_sync(
        self, flow_id: str, flow_type: str
    ) -> Dict[str, Any]:
        """Resume a flow with atomic status synchronization"""
        return await self._status_sync_ops.resume_flow_with_atomic_sync(
            flow_id, flow_type
        )

    async def reconcile_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """Reconcile master flow status using MFO sync agent"""
        return await self._status_sync_ops.reconcile_flow_status(flow_id)

    async def monitor_flow_health(self) -> Dict[str, Any]:
        """Monitor flow health and fix inconsistencies"""
        return await self._status_sync_ops.monitor_flow_health()

    # Flow operation methods
    async def create_flow(
        self,
        flow_type: str,
        flow_name: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None,
        _retry_count: int = 0,
        atomic: bool = False,
    ) -> Tuple[str, Dict[str, Any]]:
        """Create a new flow of any type"""
        return await self._flow_ops.create_flow(
            flow_type, flow_name, configuration, initial_state, _retry_count, atomic
        )

    async def execute_phase(
        self,
        flow_id: str,
        phase_name: str,
        phase_input: Optional[Dict[str, Any]] = None,
        validation_overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a specific phase of a flow"""
        return await self._flow_ops.execute_phase(
            flow_id, phase_name, phase_input, validation_overrides
        )

    async def pause_flow(
        self, flow_id: str, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Pause a running flow"""
        return await self._flow_ops.pause_flow(flow_id, reason)

    async def resume_flow(
        self, flow_id: str, resume_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Resume a paused flow"""
        return await self._flow_ops.resume_flow(flow_id, resume_context)

    async def delete_flow(
        self, flow_id: str, soft_delete: bool = True, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Delete a flow (soft delete by default)"""
        return await self._flow_ops.delete_flow(flow_id, soft_delete, reason)

    async def _get_flow_db_id(self, flow_id: str) -> Optional[uuid.UUID]:
        """Get the database ID for a given flow_id"""
        return await self._flow_ops.get_flow_db_id(flow_id)

    # Status operation methods
    async def get_flow_status(
        self, flow_id: str, include_details: bool = True
    ) -> Dict[str, Any]:
        """Get comprehensive flow status with smart fallback strategies"""
        return await self._status_ops.get_flow_status(flow_id, include_details)

    async def get_active_flows(
        self, flow_type: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get list of active flows"""
        return await self._status_ops.get_active_flows(flow_type, limit)

    async def list_flows_by_engagement(
        self, engagement_id: str, flow_type: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List flows for a specific engagement"""
        return await self._status_ops.list_flows_by_engagement(
            engagement_id, flow_type, limit
        )

    # Delegated methods to extracted services
    async def smart_flow_discovery(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Delegate to SmartDiscoveryService"""
        return await self.smart_discovery_service.smart_flow_discovery(flow_id)

    async def build_status_from_discovered_data(
        self, flow_id: str, discovered_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Delegate to SmartDiscoveryService"""
        return await self.smart_discovery_service.build_status_from_discovered_data(
            flow_id, discovered_data
        )

    async def find_orphaned_data_for_flow(
        self, flow_id: str
    ) -> Optional[Dict[str, Any]]:
        """Delegate to SmartDiscoveryService"""
        return await self.smart_discovery_service.find_orphaned_data_for_flow(flow_id)

    async def generate_repair_options(
        self, flow_id: str, discovered_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Delegate to FlowRepairService"""
        return await self.flow_repair_service.generate_repair_options(
            flow_id, discovered_data
        )

    async def repair_orphaned_data(
        self,
        flow_id: str,
        repair_type: str,
        target_items: List[str],
        create_master_flow: bool = True,
    ) -> Dict[str, Any]:
        """Delegate to FlowRepairService"""
        return await self.flow_repair_service.repair_orphaned_data(
            flow_id, repair_type, target_items, create_master_flow
        )

    async def summarize_orphaned_data(
        self, discovered_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Delegate to FlowRepairService"""
        return await self.flow_repair_service.summarize_orphaned_data(discovered_data)

    # Performance and monitoring methods
    def get_performance_summary(self, flow_id: Optional[str] = None) -> Dict[str, Any]:
        """Get performance summary for a flow or system overview"""
        return self._monitoring_ops.get_performance_summary(flow_id)

    def get_audit_events(
        self,
        flow_id: str,
        category: Optional[str] = None,
        level: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get audit events for a flow"""
        return self._monitoring_ops.get_audit_events(flow_id, category, level, limit)

    def get_compliance_report(self, flow_id: Optional[str] = None) -> Dict[str, Any]:
        """Get compliance report for a flow or all flows"""
        return self._monitoring_ops.get_compliance_report(flow_id)

    def clear_flow_data(self, flow_id: str):
        """Clear all tracking data for a flow"""
        self._monitoring_ops.clear_flow_data(flow_id)
        logger.info(f"🧹 Cleared all tracking data for flow {flow_id}")
