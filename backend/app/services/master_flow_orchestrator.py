"""
Master Flow Orchestrator - Refactored and Modularized

THE SINGLE ORCHESTRATOR - Significantly reduced by extracting methods to specialized services:
- SmartDiscoveryService for flow discovery and data correlation
- FlowRepairService for orphaned data repair and reconciliation

Centralized orchestration for all CrewAI flows using composition pattern with:
- FlowLifecycleManager for lifecycle operations
- FlowExecutionEngine for execution logic
- FlowErrorHandler for error handling
- FlowPerformanceMonitor for performance tracking
- FlowAuditLogger for audit logging
- FlowStatusManager for status management
"""

import uuid
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import asyncio
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func

from app.utils.circuit_breaker import circuit_breaker_manager

from app.core.logging import get_logger
from app.core.exceptions import (
    FlowNotFoundError,
    InvalidFlowStateError,
    CrewAIExecutionError,
    BackgroundTaskError,
    FlowError
)

from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.repositories.crewai_flow_state_extensions_repository import CrewAIFlowStateExtensionsRepository
from app.services.crewai_flows.flow_state_manager import FlowStateManager
from app.core.context import RequestContext

# Import modular components
from app.services.flow_orchestration import (
    FlowLifecycleManager,
    FlowExecutionEngine,
    FlowErrorHandler,
    FlowAuditLogger,
    FlowStatusManager
)
from app.services.flow_orchestration.smart_discovery_service import SmartDiscoveryService
from app.services.flow_orchestration.flow_repair_service import FlowRepairService
from app.services.flow_status_sync import FlowStatusSyncService
from app.services.mfo_sync_agent import MFOSyncAgent

# Mock FlowPerformanceMonitor to avoid psutil dependency
class MockFlowPerformanceMonitor:
    """Mock implementation to avoid psutil dependency"""
    def start_operation(self, flow_id: str, operation_type: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        return f"mock-{uuid.uuid4()}"
    
    def end_operation(self, tracking_id: str, success: bool = True, result_metadata: Optional[Dict[str, Any]] = None):
        return None
    
    def get_flow_performance_summary(self, flow_id: str) -> Dict[str, Any]:
        return {"flow_id": flow_id, "total_operations": 0, "message": "Performance monitoring disabled"}
    
    def get_system_performance_overview(self) -> Dict[str, Any]:
        return {"status": "disabled", "message": "Performance monitoring unavailable"}
    
    def record_audit_event(self, audit_entry: Dict[str, Any]):
        pass

# Import registries
from app.services.flow_type_registry import FlowTypeRegistry
from app.services.validator_registry import ValidatorRegistry
from app.services.handler_registry import HandlerRegistry

# Import audit logging enums
from app.services.flow_orchestration.audit_logger import AuditCategory, AuditLevel

logger = get_logger(__name__)


class FlowOperationType(Enum):
    """Flow operation types for audit logging"""
    CREATE = "create"
    EXECUTE = "execute"
    PAUSE = "pause"
    RESUME = "resume"
    DELETE = "delete"
    STATUS_CHECK = "status_check"
    LIST = "list"


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
            db, 
            context.client_account_id,
            context.engagement_id,
            context.user_id
        )
        
        # Initialize global singleton registries
        from app.services.flow_type_registry import flow_type_registry
        from app.services.validator_registry import validator_registry
        from app.services.handler_registry import handler_registry
        
        self.flow_registry = flow_type_registry
        self.validator_registry = validator_registry
        self.handler_registry = handler_registry
        
        # Initialize flow configurations if not already done
        if not self.flow_registry.list_flow_types():
            logger.info("🔄 Initializing flow configurations...")
            from app.services.flow_configs import initialize_all_flows
            result = initialize_all_flows()
            logger.info(f"✅ Flow configurations initialized: {len(result.get('flows_registered', []))} flows")
        
        # Initialize state manager
        self.state_manager = FlowStateManager(db, context)
        
        # Initialize modular components using composition pattern
        self.lifecycle_manager = FlowLifecycleManager(
            db=db,
            context=context,
            master_repo=self.master_repo
        )
        
        self.execution_engine = FlowExecutionEngine(
            db=db,
            context=context,
            master_repo=self.master_repo,
            flow_registry=self.flow_registry,
            handler_registry=self.handler_registry,
            validator_registry=self.validator_registry
        )
        
        self.error_handler = FlowErrorHandler()
        
        self.performance_monitor = MockFlowPerformanceMonitor()
        
        self.audit_logger = FlowAuditLogger()
        
        self.status_manager = FlowStatusManager(
            db=db,
            context=context,
            master_repo=self.master_repo,
            flow_registry=self.flow_registry
        )
        
        # Initialize ADR-012 status sync services
        self.status_sync_service = FlowStatusSyncService(db, context)
        self.mfo_sync_agent = MFOSyncAgent(db, context)
        
        # Initialize extracted services for discovery and repair
        self.smart_discovery_service = SmartDiscoveryService(db, context, self.master_repo)
        self.flow_repair_service = FlowRepairService(db, context, self.master_repo)
        
        # Operation tracking
        self._active_operations: Dict[str, datetime] = {}
        
        logger.info(f"✅ Master Flow Orchestrator initialized for client {context.client_account_id}")
    
    # ADR-012: Status sync service methods
    async def start_flow_with_atomic_sync(self, flow_id: str, flow_type: str) -> Dict[str, Any]:
        """Start a flow with atomic status synchronization"""
        return await self.status_sync_service.start_flow(flow_id, flow_type)
    
    async def pause_flow_with_atomic_sync(self, flow_id: str, flow_type: str, reason: str = "user_requested") -> Dict[str, Any]:
        """Pause a flow with atomic status synchronization"""
        return await self.status_sync_service.pause_flow(flow_id, flow_type, reason)
    
    async def resume_flow_with_atomic_sync(self, flow_id: str, flow_type: str) -> Dict[str, Any]:
        """Resume a flow with atomic status synchronization"""
        return await self.status_sync_service.resume_flow(flow_id, flow_type)
    
    async def reconcile_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """Reconcile master flow status using MFO sync agent"""
        return await self.mfo_sync_agent.reconcile_master_status(flow_id)
    
    async def monitor_flow_health(self) -> Dict[str, Any]:
        """Monitor flow health and fix inconsistencies"""
        return await self.mfo_sync_agent.monitor_flows_health()
    
    async def _get_flow_db_id(self, flow_id: str) -> Optional[uuid.UUID]:
        """Get the database ID for a given flow_id"""
        try:
            from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
            from sqlalchemy import select
            
            query = select(CrewAIFlowStateExtensions.id).where(
                CrewAIFlowStateExtensions.flow_id == flow_id
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.warning(f"Failed to get database ID for flow_id {flow_id}: {e}")
            return None
    
    async def create_flow(
        self,
        flow_type: str,
        flow_name: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None,
        _retry_count: int = 0
    ) -> Tuple[str, Dict[str, Any]]:
        """Create a new flow of any type"""
        logger.info(f"🔄 MFO: Creating flow of type '{flow_type}' with initial state: {initial_state}")
        flow_id = None
        
        try:
            # Validate flow type
            if not self.flow_registry.is_registered(flow_type):
                raise ValueError(f"Unknown flow type: {flow_type}")
            
            # Generate CrewAI flow ID
            flow_id = uuid.uuid4()
            
            # Start performance tracking
            tracking_id = self.performance_monitor.start_operation(
                flow_id=flow_id,
                operation_type="flow_creation",
                metadata={"flow_type": flow_type}
            )
            
            # Get flow configuration
            flow_config = self.flow_registry.get_flow_config(flow_type)
            flow_name = flow_name or flow_config.display_name
            
            # Create master flow record using lifecycle manager
            master_flow = await self.lifecycle_manager.create_flow_record(
                flow_id=flow_id,
                flow_type=flow_type,
                flow_name=flow_name,
                flow_configuration=configuration or flow_config.default_configuration,
                initial_state=initial_state or {}
            )
            
            # Initialize flow execution using execution engine
            await self.execution_engine.initialize_flow_execution(
                flow_id=flow_id,
                flow_type=flow_type,
                configuration=configuration,
                initial_state=initial_state
            )
            
            # Log creation audit
            await self.audit_logger.log_audit_event(
                flow_id=flow_id,
                operation=FlowOperationType.CREATE.value,
                category=AuditCategory.FLOW_LIFECYCLE,
                level=AuditLevel.INFO,
                context=self.context,
                success=True,
                details={
                    "flow_type": flow_type,
                    "flow_name": flow_name,
                    "configuration": configuration
                }
            )
            
            # Stop performance tracking
            self.performance_monitor.end_operation(
                tracking_id,
                success=True,
                result_metadata={"flow_id": flow_id}
            )
            
            logger.info(
                f"✅ Created {flow_type} flow: {flow_id}",
                extra={
                    "flow_id": flow_id,
                    "flow_type": flow_type,
                    "flow_name": flow_name
                }
            )
            
            return flow_id, master_flow.to_dict()
            
        except Exception as e:
            # Handle error using error handler with retry logic
            from app.services.flow_error_handler import ErrorContext, RetryConfig
            
            error_context = ErrorContext(
                operation="create_flow",
                flow_type=flow_type,
                flow_id=flow_id,
                user_id=self.context.user_id,
                additional_context={
                    "flow_name": flow_name,
                    "configuration": configuration
                }
            )
            
            retry_config = RetryConfig(
                max_retries=3,
                backoff_multiplier=2
            )
            
            error_result = await self.error_handler.handle_error(
                error=e,
                context=error_context,
                retry_config=retry_config
            )
            
            if error_result.get("should_retry", False) and _retry_count < 3:
                retry_delay = error_result.get("retry_delay", 1)
                logger.warning(f"Retrying flow creation ({_retry_count + 1}/3) after {retry_delay}s delay")
                await asyncio.sleep(retry_delay)
                return await self.create_flow(
                    flow_type, flow_name, configuration, initial_state, 
                    _retry_count=_retry_count + 1
                )
            elif _retry_count >= 3:
                logger.error(f"Max retries (3) reached for flow creation of type {flow_type}")
            
            # Log failure audit
            await self.audit_logger.log_audit_event(
                flow_id=flow_id or "unknown",
                operation=FlowOperationType.CREATE.value,
                category=AuditCategory.ERROR_EVENT,
                level=AuditLevel.ERROR,
                context=self.context,
                success=False,
                error_message=str(e),
                details=error_result
            )
            
            # Re-raise as FlowError with context
            raise FlowError(
                message=f"Failed to create {flow_type} flow: {str(e)}",
                flow_name=flow_name,
                flow_id=flow_id,
                details={
                    "flow_type": flow_type,
                    "original_error": type(e).__name__
                }
            )
    
    async def execute_phase(
        self,
        flow_id: str,
        phase_name: str,
        phase_input: Optional[Dict[str, Any]] = None,
        validation_overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a specific phase of a flow"""
        try:
            # Start performance tracking
            tracking_id = self.performance_monitor.start_operation(
                flow_id=flow_id,
                operation_type="phase_execution",
                metadata={"phase_name": phase_name}
            )
            
            # Execute phase using execution engine
            result = await self.execution_engine.execute_phase(
                flow_id=flow_id,
                phase_name=phase_name,
                phase_input=phase_input,
                validation_overrides=validation_overrides
            )
            
            # Log execution audit
            await self.audit_logger.log_audit_event(
                flow_id=flow_id,
                operation=FlowOperationType.EXECUTE.value,
                category=AuditCategory.FLOW_EXECUTION,
                level=AuditLevel.INFO,
                context=self.context,
                success=True,
                details={
                    "phase": phase_name,
                    "execution_time_ms": result.get("execution_time_ms"),
                    "success": True
                }
            )
            
            # Stop performance tracking
            self.performance_monitor.end_operation(
                tracking_id,
                success=True,
                result_metadata={
                    "phase": phase_name,
                    "execution_time_ms": result.get("execution_time_ms")
                }
            )
            
            return result
            
        except Exception as e:
            # Handle error using error handler
            from app.services.flow_error_handler import ErrorContext, RetryConfig
            
            error_context = ErrorContext(
                operation="execute_phase",
                flow_id=flow_id,
                phase=phase_name,
                user_id=self.context.user_id
            )
            
            retry_config = RetryConfig(
                max_retries=2,
                backoff_multiplier=2
            )
            
            error_result = await self.error_handler.handle_error(
                error=e,
                context=error_context,
                retry_config=retry_config
            )
            
            if error_result.get("should_retry", False):
                await asyncio.sleep(error_result.get("retry_delay", 1))
                return await self.execute_phase(flow_id, phase_name, phase_input, validation_overrides)
            
            # Log failure audit
            await self.audit_logger.log_audit_event(
                flow_id=flow_id,
                operation=FlowOperationType.EXECUTE.value,
                category=AuditCategory.ERROR_EVENT,
                level=AuditLevel.ERROR,
                context=self.context,
                success=False,
                error_message=str(e),
                details={"phase": phase_name}
            )
            
            raise RuntimeError(f"Phase execution failed: {str(e)}")
    
    async def pause_flow(self, flow_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """Pause a running flow"""
        try:
            result = await self.lifecycle_manager.pause_flow(flow_id, reason)
            
            await self.audit_logger.log_audit_event(
                flow_id=flow_id,
                operation=FlowOperationType.PAUSE.value,
                category=AuditCategory.FLOW_LIFECYCLE,
                level=AuditLevel.INFO,
                context=self.context,
                success=True,
                details={"reason": reason}
            )
            
            return result
        except Exception as e:
            await self.audit_logger.log_audit_event(
                flow_id=flow_id,
                operation=FlowOperationType.PAUSE.value,
                category=AuditCategory.ERROR_EVENT,
                level=AuditLevel.ERROR,
                context=self.context,
                success=False,
                error_message=str(e)
            )
            raise
    
    async def resume_flow(self, flow_id: str, resume_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Resume a paused flow"""
        try:
            result = await self.lifecycle_manager.resume_flow(flow_id, resume_context)
            
            # Delegate to actual flow implementation for continuation
            master_flow = await self.master_repo.get_by_flow_id(flow_id)
            if master_flow and master_flow.flow_type == "discovery":
                try:
                    from app.services.crewai_flow_service import CrewAIFlowService
                    from app.core.database import AsyncSessionLocal
                    
                    crewai_service = CrewAIFlowService(self.db)
                    
                    async with AsyncSessionLocal() as db:
                        if resume_context is None:
                            resume_context = {
                                'client_account_id': str(master_flow.client_account_id),
                                'engagement_id': str(master_flow.engagement_id),
                                'user_id': master_flow.user_id,
                                'approved_by': master_flow.user_id,
                                'resume_from': 'master_flow_orchestrator'
                            }
                        
                        crew_result = await crewai_service.resume_flow(
                            flow_id=str(flow_id),
                            resume_context=resume_context
                        )
                        
                        logger.info(f"✅ Delegated to CrewAI Flow Service: {crew_result}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Failed to delegate to CrewAI Flow Service: {e}")
            
            await self.audit_logger.log_audit_event(
                flow_id=flow_id,
                operation=FlowOperationType.RESUME.value,
                category=AuditCategory.FLOW_LIFECYCLE,
                level=AuditLevel.INFO,
                context=self.context,
                success=True,
                details={"context": resume_context}
            )
            
            return result
        except Exception as e:
            await self.audit_logger.log_audit_event(
                flow_id=flow_id,
                operation=FlowOperationType.RESUME.value,
                category=AuditCategory.ERROR_EVENT,
                level=AuditLevel.ERROR,
                context=self.context,
                success=False,
                error_message=str(e)
            )
            raise
    
    async def delete_flow(self, flow_id: str, soft_delete: bool = True, reason: Optional[str] = None) -> Dict[str, Any]:
        """Delete a flow (soft delete by default)"""
        try:
            result = await self.lifecycle_manager.delete_flow(flow_id, soft_delete, reason)
            
            await self.audit_logger.log_audit_event(
                flow_id=flow_id,
                operation=FlowOperationType.DELETE.value,
                category=AuditCategory.FLOW_LIFECYCLE,
                level=AuditLevel.INFO,
                context=self.context,
                success=True,
                details={"soft_delete": soft_delete, "reason": reason}
            )
            
            return result
        except Exception as e:
            await self.audit_logger.log_audit_event(
                flow_id=flow_id,
                operation=FlowOperationType.DELETE.value,
                category=AuditCategory.ERROR_EVENT,
                level=AuditLevel.ERROR,
                context=self.context,
                success=False,
                error_message=str(e)
            )
            raise
    
    async def get_flow_status(self, flow_id: str, include_details: bool = True) -> Dict[str, Any]:
        """Get comprehensive flow status with smart fallback strategies"""
        try:
            tracking_id = self.performance_monitor.start_operation(
                flow_id=flow_id,
                operation_type="status_check",
                metadata={}
            )
            
            # Try primary method first
            try:
                status = await self.status_manager.get_flow_status(flow_id, include_details)
                
                # Enhance with orphaned data recovery if needed
                if include_details:
                    status = await self._enhance_status_with_smart_discovery(flow_id, status)
                
                self.performance_monitor.end_operation(tracking_id, success=True)
                return status
                
            except ValueError as primary_error:
                # Flow not found in primary method - try smart discovery
                logger.info(f"🔍 Primary flow lookup failed for {flow_id}, attempting smart discovery...")
                
                discovered_data = await self.smart_discovery_service.smart_flow_discovery(flow_id)
                if discovered_data:
                    smart_status = await self.smart_discovery_service.build_status_from_discovered_data(flow_id, discovered_data)
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
                details={"include_details": include_details}
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
                error_message=str(e)
            )
            raise RuntimeError(f"Failed to get flow status: {str(e)}")
    
    async def _enhance_status_with_smart_discovery(self, flow_id: str, status: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance existing status with smart discovery of related orphaned data"""
        try:
            orphaned_data = await self.smart_discovery_service.find_orphaned_data_for_flow(flow_id)
            
            if orphaned_data:
                if "metadata" not in status:
                    status["metadata"] = {}
                
                status["metadata"]["orphaned_data_found"] = True
                status["metadata"]["orphaned_data_summary"] = orphaned_data
                status["metadata"]["repair_available"] = True
                
                logger.info(f"🔍 Enhanced status for flow {flow_id} with orphaned data information")
            
            return status
        except Exception as e:
            logger.warning(f"⚠️ Failed to enhance status with smart discovery: {e}")
            return status
    
    async def get_active_flows(self, flow_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
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
                details={"flow_type": flow_type, "limit": limit, "count": len(flows)}
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
                error_message=str(e)
            )
            raise RuntimeError(f"Failed to get active flows: {str(e)}")
    
    async def list_flows_by_engagement(self, engagement_id: str, flow_type: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List flows for a specific engagement"""
        try:
            flows = await self.status_manager.list_flows_by_engagement(engagement_id, flow_type, limit)
            
            await self.audit_logger.log_audit_event(
                flow_id="system",
                operation=FlowOperationType.LIST.value,
                category=AuditCategory.FLOW_LIFECYCLE,
                level=AuditLevel.DEBUG,
                context=self.context,
                success=True,
                details={"engagement_id": engagement_id, "flow_type": flow_type, "limit": limit, "count": len(flows)}
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
                error_message=str(e)
            )
            return []  # Return empty list instead of raising to prevent user context failures
    
    # Delegated methods to extracted services
    
    async def smart_flow_discovery(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Delegate to SmartDiscoveryService"""
        return await self.smart_discovery_service.smart_flow_discovery(flow_id)
    
    async def build_status_from_discovered_data(self, flow_id: str, discovered_data: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to SmartDiscoveryService"""
        return await self.smart_discovery_service.build_status_from_discovered_data(flow_id, discovered_data)
    
    async def find_orphaned_data_for_flow(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Delegate to SmartDiscoveryService"""
        return await self.smart_discovery_service.find_orphaned_data_for_flow(flow_id)
    
    async def generate_repair_options(self, flow_id: str, discovered_data: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to FlowRepairService"""
        return await self.flow_repair_service.generate_repair_options(flow_id, discovered_data)
    
    async def repair_orphaned_data(self, flow_id: str, repair_type: str, target_items: List[str], create_master_flow: bool = True) -> Dict[str, Any]:
        """Delegate to FlowRepairService"""
        return await self.flow_repair_service.repair_orphaned_data(flow_id, repair_type, target_items, create_master_flow)
    
    async def summarize_orphaned_data(self, discovered_data: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to FlowRepairService"""
        return await self.flow_repair_service.summarize_orphaned_data(discovered_data)
    
    # Performance and monitoring methods
    
    def get_performance_summary(self, flow_id: Optional[str] = None) -> Dict[str, Any]:
        """Get performance summary for a flow or system overview"""
        if flow_id:
            return self.performance_monitor.get_flow_performance_summary(flow_id)
        else:
            return self.performance_monitor.get_system_performance_overview()
    
    def get_audit_events(self, flow_id: str, category: Optional[str] = None, level: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get audit events for a flow"""
        audit_category = None
        audit_level = None
        
        if category:
            try:
                audit_category = AuditCategory(category)
            except ValueError:
                pass
        
        if level:
            try:
                audit_level = AuditLevel(level)
            except ValueError:
                pass
        
        return self.audit_logger.get_audit_events(flow_id, audit_category, audit_level, limit)
    
    def get_compliance_report(self, flow_id: Optional[str] = None) -> Dict[str, Any]:
        """Get compliance report for a flow or all flows"""
        return self.audit_logger.get_compliance_report(flow_id)
    
    def clear_flow_data(self, flow_id: str):
        """Clear all tracking data for a flow"""
        self.performance_monitor.clear_flow_metrics(flow_id)
        self.audit_logger.clear_audit_events(flow_id)
        self.error_handler.clear_error_history(flow_id)
        
        logger.info(f"🧹 Cleared all tracking data for flow {flow_id}")