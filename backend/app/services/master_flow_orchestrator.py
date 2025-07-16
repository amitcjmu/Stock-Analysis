"""
Master Flow Orchestrator - Refactored

THE SINGLE ORCHESTRATOR - Refactored to use modular components
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
        
        # Operation tracking
        self._active_operations: Dict[str, datetime] = {}
        
        logger.info(f"✅ Master Flow Orchestrator initialized for client {context.client_account_id}")
    
    async def _get_flow_db_id(self, flow_id: str) -> Optional[uuid.UUID]:
        """
        Get the database ID for a given flow_id.
        
        The foreign key constraint on data_imports.master_flow_id references 
        crewai_flow_state_extensions.id, not flow_id. This helper method 
        translates between the two.
        
        Args:
            flow_id: The CrewAI flow UUID
            
        Returns:
            The database record ID if found, None otherwise
        """
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
        """
        Create a new flow of any type
        
        Args:
            flow_type: Type of flow (discovery, assessment, planning, execution, etc.)
            flow_name: Optional human-readable name
            configuration: Flow-specific configuration
            initial_state: Initial state data
            
        Returns:
            Tuple of (flow_id, flow_details)
            
        Raises:
            ValueError: If flow type is invalid
            RuntimeError: If flow creation fails
        """
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
            # Handle error using error handler
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
                # Recursive retry with backoff (max 3 retries)
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
        """
        Execute a specific phase of a flow
        
        Args:
            flow_id: Flow identifier
            phase_name: Name of the phase to execute
            phase_input: Input data for the phase
            validation_overrides: Optional validation overrides
            
        Returns:
            Phase execution results
            
        Raises:
            ValueError: If flow or phase not found
            RuntimeError: If phase execution fails
        """
        try:
            # Start performance tracking
            tracking_id = self.performance_monitor.start_operation(
                flow_id=flow_id,
                operation_type="phase_execution",
                metadata={
                    "phase_name": phase_name
                }
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
                # Recursive retry with backoff
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
    
    async def pause_flow(
        self,
        flow_id: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Pause a running flow
        
        Args:
            flow_id: Flow identifier
            reason: Optional reason for pausing
            
        Returns:
            Pause operation result
        """
        try:
            # Use lifecycle manager to pause flow
            result = await self.lifecycle_manager.pause_flow(flow_id, reason)
            
            # Log pause audit
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
            # Log failure audit
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
    
    async def resume_flow(
        self,
        flow_id: str,
        resume_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Resume a paused flow
        
        Args:
            flow_id: Flow identifier
            resume_context: Optional context for resuming
            
        Returns:
            Resume operation result
        """
        try:
            # Use lifecycle manager to resume flow
            result = await self.lifecycle_manager.resume_flow(flow_id, resume_context)
            
            # Delegate to actual flow implementation for continuation
            master_flow = await self.master_repo.get_by_flow_id(flow_id)
            if master_flow and master_flow.flow_type == "discovery":
                try:
                    from app.services.crewai_flow_service import CrewAIFlowService
                    from app.core.database import AsyncSessionLocal
                    
                    # Create CrewAI service instance with database session
                    crewai_service = CrewAIFlowService(self.db)
                    
                    # Resume the actual CrewAI flow
                    async with AsyncSessionLocal() as db:
                        # If no resume_context provided, create one from master flow
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
            
            # Log resume audit
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
            # Log failure audit
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
    
    async def delete_flow(
        self,
        flow_id: str,
        soft_delete: bool = True,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete a flow (soft delete by default)
        
        Args:
            flow_id: Flow identifier
            soft_delete: Whether to soft delete (default) or hard delete
            reason: Optional reason for deletion
            
        Returns:
            Delete operation result
        """
        try:
            # Use lifecycle manager to delete flow
            result = await self.lifecycle_manager.delete_flow(flow_id, soft_delete, reason)
            
            # Log deletion audit
            await self.audit_logger.log_audit_event(
                flow_id=flow_id,
                operation=FlowOperationType.DELETE.value,
                category=AuditCategory.FLOW_LIFECYCLE,
                level=AuditLevel.INFO,
                context=self.context,
                success=True,
                details={
                    "soft_delete": soft_delete,
                    "reason": reason
                }
            )
            
            return result
            
        except Exception as e:
            # Log failure audit
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
    
    async def get_flow_status(
        self,
        flow_id: str,
        include_details: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive flow status with smart fallback strategies
        
        Args:
            flow_id: Flow identifier
            include_details: Whether to include detailed information
            
        Returns:
            Flow status information
        """
        try:
            # Start performance tracking
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
                
                # Stop performance tracking
                self.performance_monitor.end_operation(tracking_id, success=True)
                return status
                
            except ValueError as primary_error:
                # Flow not found in primary method - try smart discovery
                logger.info(f"🔍 Primary flow lookup failed for {flow_id}, attempting smart discovery...")
                
                smart_status = await self._smart_flow_discovery(flow_id, include_details)
                if smart_status:
                    logger.info(f"✅ Smart discovery found data for flow {flow_id}")
                    
                    # Stop performance tracking
                    self.performance_monitor.end_operation(tracking_id, success=True)
                    return smart_status
                else:
                    logger.warning(f"❌ Smart discovery failed for flow {flow_id}")
                    raise primary_error
            
            # Log status check audit
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
            # Flow not found - this is a legitimate 404 case
            logger.warning(f"Flow not found: {flow_id}")
            raise e
        except Exception as e:
            # Log failure audit
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
    
    async def _smart_flow_discovery(
        self,
        flow_id: str,
        include_details: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Smart flow discovery for orphaned data using multiple fallback strategies
        
        Args:
            flow_id: Flow identifier to search for
            include_details: Whether to include detailed information
            
        Returns:
            Flow status if found via smart discovery, None otherwise
        """
        try:
            logger.info(f"🔍 Starting smart flow discovery for flow_id: {flow_id}")
            
            # Strategy 1: Look for related data_import records by timestamp correlation
            related_data = await self._find_related_data_by_timestamp(flow_id)
            if related_data:
                logger.info(f"📅 Found related data by timestamp correlation for flow {flow_id}")
                return await self._build_status_from_discovered_data(flow_id, related_data, include_details)
            
            # Strategy 2: Look for related records by client context and data patterns
            context_data = await self._find_related_data_by_context(flow_id)
            if context_data:
                logger.info(f"🎯 Found related data by context correlation for flow {flow_id}")
                return await self._build_status_from_discovered_data(flow_id, context_data, include_details)
            
            # Strategy 3: Search in flow_persistence_data for references
            persistence_data = await self._find_in_flow_persistence(flow_id)
            if persistence_data:
                logger.info(f"💾 Found related data in flow persistence for flow {flow_id}")
                return await self._build_status_from_discovered_data(flow_id, persistence_data, include_details)
            
            logger.warning(f"🤷 Smart discovery found no data for flow {flow_id}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Smart flow discovery failed for {flow_id}: {e}")
            return None
    
    async def _find_related_data_by_timestamp(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Find related data using timestamp correlation"""
        try:
            from app.models.data_import import DataImport, RawImportRecord, ImportFieldMapping
            from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
            from sqlalchemy import select, and_, or_, text
            from datetime import datetime, timedelta
            
            # Get the database ID for this flow_id
            flow_db_id = await self._get_flow_db_id(flow_id)
            
            # Try to extract timestamp from flow_id if it's UUID-based
            # Look for data imports created around the same time
            
            # Search for data imports with NULL master_flow_id in the right time window
            # Use a broader time window for discovery
            time_window = timedelta(hours=24)  # Look within 24 hours
            
            if flow_db_id:
                # If we found the database ID, include it in the search
                query = select(DataImport).where(
                    and_(
                        DataImport.client_account_id == self.context.client_account_id,
                        or_(
                            DataImport.master_flow_id.is_(None),
                            DataImport.master_flow_id == flow_db_id  # Use database ID here
                        ),
                        DataImport.created_at >= datetime.utcnow() - time_window
                    )
                ).order_by(DataImport.created_at.desc()).limit(5)
            else:
                # No database ID found, just look for orphaned imports
                query = select(DataImport).where(
                    and_(
                        DataImport.client_account_id == self.context.client_account_id,
                        DataImport.master_flow_id.is_(None),
                        DataImport.created_at >= datetime.utcnow() - time_window
                    )
                ).order_by(DataImport.created_at.desc()).limit(5)
            
            result = await self.db.execute(query)
            imports = result.scalars().all()
            
            if imports:
                # Get the most recent one that matches our criteria
                for data_import in imports:
                    # Check if this could be related to our flow
                    raw_records_query = select(RawImportRecord).where(
                        RawImportRecord.data_import_id == data_import.id
                    ).limit(1)
                    raw_result = await self.db.execute(raw_records_query)
                    has_records = raw_result.scalar() is not None
                    
                    if has_records:
                        return {
                            "discovery_method": "timestamp_correlation",
                            "data_import": data_import,
                            "confidence": "medium"
                        }
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Timestamp correlation search failed: {e}")
            return None
    
    async def _find_related_data_by_context(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Find related data using client context"""
        try:
            from app.models.data_import import DataImport, RawImportRecord
            from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
            from sqlalchemy import select, and_, or_, join
            
            # Get the database ID for this flow_id
            flow_db_id = await self._get_flow_db_id(flow_id)
            
            # Look for data imports with NULL master_flow_id or matching master_flow_id
            # Note: master_flow_id FK references crewai_flow_state_extensions.id, not flow_id
            if flow_db_id:
                # If we found the database ID, include it in the search
                query = select(DataImport).where(
                    and_(
                        DataImport.client_account_id == self.context.client_account_id,
                        DataImport.engagement_id == self.context.engagement_id,
                        or_(
                            DataImport.master_flow_id.is_(None),
                            DataImport.master_flow_id == flow_db_id  # Use database ID here
                        )
                    )
                ).order_by(DataImport.created_at.desc()).limit(3)
            else:
                # No database ID found, just look for orphaned imports
                query = select(DataImport).where(
                    and_(
                        DataImport.client_account_id == self.context.client_account_id,
                        DataImport.engagement_id == self.context.engagement_id,
                        DataImport.master_flow_id.is_(None)
                    )
                ).order_by(DataImport.created_at.desc()).limit(3)
            
            result = await self.db.execute(query)
            imports = result.scalars().all()
            
            if imports:
                # Take the most recent one
                data_import = imports[0]
                
                # Verify it has raw records
                raw_records_query = select(RawImportRecord).where(
                    RawImportRecord.data_import_id == data_import.id
                ).limit(1)
                raw_result = await self.db.execute(raw_records_query)
                has_records = raw_result.scalar() is not None
                
                if has_records:
                    return {
                        "discovery_method": "context_correlation",
                        "data_import": data_import,
                        "confidence": "high"
                    }
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Context correlation search failed: {e}")
            return None
    
    async def _find_in_flow_persistence(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Search for flow references in persistence data"""
        try:
            from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
            from sqlalchemy import select, and_, text
            
            # Search for any flows that might reference this flow_id in their persistence data
            query = select(CrewAIFlowStateExtensions).where(
                and_(
                    CrewAIFlowStateExtensions.client_account_id == self.context.client_account_id,
                    text("flow_persistence_data::text LIKE :flow_id")
                )
            ).params(flow_id=f"%{flow_id}%")
            
            result = await self.db.execute(query)
            flows = result.scalars().all()
            
            for flow in flows:
                if flow.flow_persistence_data:
                    # Check if this persistence data contains our flow_id
                    persistence_str = str(flow.flow_persistence_data)
                    if flow_id in persistence_str:
                        return {
                            "discovery_method": "persistence_reference",
                            "related_flow": flow,
                            "confidence": "low"
                        }
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Persistence search failed: {e}")
            return None
    
    async def _build_status_from_discovered_data(
        self,
        flow_id: str,
        discovered_data: Dict[str, Any],
        include_details: bool
    ) -> Dict[str, Any]:
        """Build flow status from discovered data"""
        try:
            discovery_method = discovered_data.get("discovery_method", "unknown")
            confidence = discovered_data.get("confidence", "low")
            
            # Get field mappings to determine the correct flow state
            field_mappings = await self._retrieve_field_mappings_from_discovered_data(discovered_data)
            
            # Determine the actual flow state based on field mappings
            flow_status = "running"
            current_phase = "data_import"
            progress_percentage = 30.0
            awaiting_user_approval = False
            
            if field_mappings:
                # We have field mappings, check their status
                approved_count = sum(1 for mapping in field_mappings if mapping.get("status") == "approved")
                total_count = len(field_mappings)
                
                if approved_count == total_count and total_count > 0:
                    # All mappings are approved - flow should be ready to continue
                    flow_status = "running"
                    current_phase = "field_mapping"
                    progress_percentage = 80.0
                    awaiting_user_approval = False
                else:
                    # Some mappings are not approved - waiting for user approval
                    flow_status = "waiting_for_approval"
                    current_phase = "field_mapping"
                    progress_percentage = 60.0
                    awaiting_user_approval = True
            
            # Base status structure with proper frontend-compatible values
            status = {
                "flow_id": flow_id,
                "flow_type": "discovery",
                "flow_name": f"Discovery Flow",
                "status": flow_status,
                "discovery_method": discovery_method,
                "confidence": confidence,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "created_by": self.context.user_id,
                "current_phase": current_phase,
                "progress_percentage": progress_percentage,
                "configuration": {},
                "metadata": {
                    "is_discovered": True,
                    "original_data_orphaned": True,
                    "discovery_method": discovery_method
                },
                "awaiting_user_approval": awaiting_user_approval,
                "awaitingUserApproval": awaiting_user_approval,  # Frontend expects camelCase
                "currentPhase": current_phase,  # Frontend expects camelCase
                "progress": progress_percentage  # Frontend expects this alias
            }
            
            if include_details:
                # Add discovered data details
                details = {
                    "discovery_details": discovered_data,
                    "repair_options": await self._generate_repair_options(flow_id, discovered_data),
                    "orphaned_data_summary": await self._summarize_orphaned_data(discovered_data)
                }
                
                # Add field mappings
                details["field_mappings"] = field_mappings
                
                status.update(details)
            
            logger.info(f"🔧 Built status from discovered data for flow {flow_id} using {discovery_method}: {flow_status}/{current_phase} ({progress_percentage}%)")
            return status
            
        except Exception as e:
            logger.error(f"❌ Failed to build status from discovered data: {e}")
            return None
    
    async def _retrieve_field_mappings_from_discovered_data(
        self, 
        discovered_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Retrieve field mappings from discovered data"""
        try:
            from app.models.data_import import ImportFieldMapping
            from sqlalchemy import select, or_
            
            field_mappings = []
            
            # If we have a data_import in the discovered data, get its field mappings
            if "data_import" in discovered_data:
                data_import = discovered_data["data_import"]
                data_import_id = data_import.id
                
                logger.info(f"🔍 Loading field mappings for discovered data_import_id: {data_import_id}")
                
                # Query field mappings for this data import
                query = select(ImportFieldMapping).where(
                    or_(
                        ImportFieldMapping.data_import_id == data_import_id,
                        ImportFieldMapping.master_flow_id == str(data_import_id)  # Try with string conversion
                    )
                )
                result = await self.db.execute(query)
                mappings = result.scalars().all()
                
                # Convert to frontend format
                for mapping in mappings:
                    field_mappings.append({
                        "id": str(mapping.id),
                        "source_field": mapping.source_field,
                        "target_field": mapping.target_field,
                        "status": mapping.status,
                        "confidence_score": mapping.confidence_score,
                        "match_type": mapping.match_type,
                        "suggested_by": mapping.suggested_by,
                        "approved_by": mapping.approved_by,
                        "approved_at": mapping.approved_at.isoformat() if mapping.approved_at else None,
                        "transformation_rules": mapping.transformation_rules,
                        "created_at": mapping.created_at.isoformat() if mapping.created_at else None,
                        "updated_at": mapping.updated_at.isoformat() if mapping.updated_at else None,
                        "master_flow_id": mapping.master_flow_id,
                        "data_import_id": str(mapping.data_import_id) if mapping.data_import_id else None,
                        "is_discovered": True,
                        "discovery_method": discovered_data.get("discovery_method", "unknown")
                    })
                
                logger.info(f"✅ Retrieved {len(field_mappings)} field mappings from discovered data")
            
            return field_mappings
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve field mappings from discovered data: {e}")
            return []
    
    async def _enhance_status_with_smart_discovery(
        self,
        flow_id: str,
        status: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance existing status with smart discovery of related orphaned data"""
        try:
            # Look for orphaned data that might belong to this flow
            orphaned_data = await self._find_orphaned_data_for_flow(flow_id)
            
            if orphaned_data:
                # Add orphaned data information to status
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
    
    async def _find_orphaned_data_for_flow(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Find orphaned data that might belong to this flow"""
        try:
            from app.models.data_import import DataImport, RawImportRecord, ImportFieldMapping
            from sqlalchemy import select, and_
            
            # Look for data imports with NULL master_flow_id
            orphaned_imports_query = select(DataImport).where(
                and_(
                    DataImport.client_account_id == self.context.client_account_id,
                    DataImport.engagement_id == self.context.engagement_id,
                    DataImport.master_flow_id.is_(None)
                )
            ).order_by(DataImport.created_at.desc()).limit(5)
            
            result = await self.db.execute(orphaned_imports_query)
            orphaned_imports = result.scalars().all()
            
            if orphaned_imports:
                orphan_summary = []
                for import_record in orphaned_imports:
                    # Count related records
                    raw_count_query = select(func.count(RawImportRecord.id)).where(
                        RawImportRecord.data_import_id == import_record.id
                    )
                    raw_count_result = await self.db.execute(raw_count_query)
                    raw_count = raw_count_result.scalar() or 0
                    
                    mapping_count_query = select(func.count(ImportFieldMapping.id)).where(
                        ImportFieldMapping.data_import_id == import_record.id
                    )
                    mapping_count_result = await self.db.execute(mapping_count_query)
                    mapping_count = mapping_count_result.scalar() or 0
                    
                    orphan_summary.append({
                        "data_import_id": str(import_record.id),
                        "filename": import_record.filename,
                        "created_at": import_record.created_at.isoformat() if import_record.created_at else None,
                        "raw_records_count": raw_count,
                        "field_mappings_count": mapping_count,
                        "status": import_record.status
                    })
                
                return {
                    "orphaned_imports_count": len(orphaned_imports),
                    "orphaned_imports": orphan_summary
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to find orphaned data: {e}")
            return None
    
    async def get_active_flows(
        self,
        flow_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get list of active flows
        
        Args:
            flow_type: Optional filter by flow type
            limit: Maximum number of flows to return
            
        Returns:
            List of active flows
        """
        try:
            # Use status manager to get active flows
            flows = await self.status_manager.get_active_flows(flow_type, limit)
            
            # Log list operation audit
            await self.audit_logger.log_audit_event(
                flow_id="system",
                operation=FlowOperationType.LIST.value,
                category=AuditCategory.FLOW_LIFECYCLE,
                level=AuditLevel.DEBUG,
                context=self.context,
                success=True,
                details={
                    "flow_type": flow_type,
                    "limit": limit,
                    "count": len(flows)
                }
            )
            
            return flows
            
        except Exception as e:
            # Log failure audit
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
    
    async def list_flows_by_engagement(
        self,
        engagement_id: str,
        flow_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List flows for a specific engagement
        
        Args:
            engagement_id: The engagement ID to filter by
            flow_type: Optional filter by flow type
            limit: Maximum number of flows to return
            
        Returns:
            List of flows for the engagement
        """
        try:
            # Use status manager to list flows by engagement
            flows = await self.status_manager.list_flows_by_engagement(
                engagement_id, flow_type, limit
            )
            
            # Log list operation audit
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
                    "count": len(flows)
                }
            )
            
            return flows
            
        except Exception as e:
            # Log failure audit
            await self.audit_logger.log_audit_event(
                flow_id="system",
                operation=FlowOperationType.LIST.value,
                category=AuditCategory.ERROR_EVENT,
                level=AuditLevel.ERROR,
                context=self.context,
                success=False,
                error_message=str(e)
            )
            
            # Return empty list instead of raising to prevent user context failures
            return []
    
    # Performance and monitoring methods
    
    def get_performance_summary(self, flow_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance summary for a flow or system overview
        
        Args:
            flow_id: Optional flow identifier
            
        Returns:
            Performance summary
        """
        if flow_id:
            return self.performance_monitor.get_flow_performance_summary(flow_id)
        else:
            return self.performance_monitor.get_system_performance_overview()
    
    def get_audit_events(
        self,
        flow_id: str,
        category: Optional[str] = None,
        level: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get audit events for a flow
        
        Args:
            flow_id: Flow identifier
            category: Optional category filter
            level: Optional level filter
            limit: Maximum number of events to return
            
        Returns:
            List of audit events
        """
        # Convert string enums to proper enum types
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
        """
        Get compliance report for a flow or all flows
        
        Args:
            flow_id: Optional flow identifier
            
        Returns:
            Compliance report
        """
        return self.audit_logger.get_compliance_report(flow_id)
    
    def clear_flow_data(self, flow_id: str):
        """
        Clear all tracking data for a flow
        
        Args:
            flow_id: Flow identifier
        """
        self.performance_monitor.clear_flow_metrics(flow_id)
        self.audit_logger.clear_audit_events(flow_id)
        self.error_handler.clear_error_history(flow_id)
        
        logger.info(f"🧹 Cleared all tracking data for flow {flow_id}")
    
    async def _generate_repair_options(
        self,
        flow_id: str,
        discovered_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate repair options for orphaned data"""
        try:
            repair_options = []
            discovery_method = discovered_data.get("discovery_method", "unknown")
            confidence = discovered_data.get("confidence", "low")
            
            if "data_import" in discovered_data:
                data_import = discovered_data["data_import"]
                
                # Option 1: Link orphaned data to existing flow
                repair_options.append({
                    "option_id": "link_orphaned_data",
                    "title": "Link Orphaned Data to Flow",
                    "description": f"Link data import {data_import.id} to flow {flow_id}",
                    "confidence": confidence,
                    "actions": [
                        f"UPDATE data_imports SET master_flow_id = '{flow_id}' WHERE id = '{data_import.id}'",
                        f"UPDATE raw_import_records SET master_flow_id = '{flow_id}' WHERE data_import_id = '{data_import.id}'",
                        f"UPDATE import_field_mappings SET master_flow_id = '{flow_id}' WHERE data_import_id = '{data_import.id}'"
                    ],
                    "risk": "low" if confidence == "high" else "medium",
                    "reversible": True
                })
                
                # Option 2: Create new flow for orphaned data
                repair_options.append({
                    "option_id": "create_new_flow",
                    "title": "Create New Flow for Orphaned Data",
                    "description": "Create a new discovery flow for the orphaned data",
                    "confidence": "high",
                    "actions": [
                        "Create new CrewAI flow",
                        "Link all orphaned data to new flow",
                        "Initialize flow with existing data"
                    ],
                    "risk": "low",
                    "reversible": True
                })
            
            return repair_options
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to generate repair options: {e}")
            return []
    
    async def _summarize_orphaned_data(self, discovered_data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize orphaned data for display"""
        try:
            summary = {
                "discovery_method": discovered_data.get("discovery_method", "unknown"),
                "confidence": discovered_data.get("confidence", "low"),
                "data_found": False,
                "details": {}
            }
            
            if "data_import" in discovered_data:
                data_import = discovered_data["data_import"]
                summary["data_found"] = True
                summary["details"] = {
                    "data_import_id": str(data_import.id),
                    "filename": data_import.filename,
                    "created_at": data_import.created_at.isoformat() if data_import.created_at else None,
                    "status": data_import.status,
                    "import_type": data_import.import_type
                }
            
            return summary
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to summarize orphaned data: {e}")
            return {"error": str(e)}
    
    async def repair_orphaned_data(
        self,
        flow_id: str,
        repair_option_id: str,
        data_import_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Repair orphaned data by linking it to a flow
        
        Args:
            flow_id: Target flow ID to link data to
            repair_option_id: ID of repair option to execute
            data_import_id: Optional specific data import to repair
            
        Returns:
            Repair operation result
        """
        try:
            logger.info(f"🔧 Starting orphaned data repair for flow {flow_id} with option {repair_option_id}")
            
            if repair_option_id == "link_orphaned_data":
                # Find the data import to link
                target_import = None
                
                if data_import_id:
                    # Use specific data import
                    from app.models.data_import import DataImport
                    from sqlalchemy import select
                    
                    query = select(DataImport).where(DataImport.id == data_import_id)
                    result = await self.db.execute(query)
                    target_import = result.scalar_one_or_none()
                else:
                    # Find orphaned data using smart discovery
                    discovered_data = await self._find_related_data_by_context(flow_id)
                    if discovered_data:
                        target_import = discovered_data.get("data_import")
                
                if target_import:
                    # Use storage manager to link all records
                    from app.services.data_import.storage_manager import ImportStorageManager
                    
                    storage_manager = ImportStorageManager(self.db, self.context.client_account_id)
                    linkage_results = await storage_manager.update_all_records_with_flow(
                        data_import_id=target_import.id,
                        master_flow_id=flow_id
                    )
                    
                    if linkage_results["success"]:
                        logger.info(f"✅ Successfully repaired orphaned data for flow {flow_id}")
                        return {
                            "success": True,
                            "message": f"Successfully linked orphaned data to flow {flow_id}",
                            "details": linkage_results,
                            "data_import_id": str(target_import.id)
                        }
                    else:
                        logger.error(f"❌ Failed to repair orphaned data: {linkage_results['error']}")
                        return {
                            "success": False,
                            "message": f"Failed to link orphaned data: {linkage_results['error']}",
                            "details": linkage_results
                        }
                else:
                    return {
                        "success": False,
                        "message": "No orphaned data found to repair",
                        "details": {}
                    }
            
            elif repair_option_id == "create_new_flow":
                # Create a new flow for the orphaned data
                new_flow_id, flow_details = await self.create_flow(
                    flow_type="discovery",
                    flow_name=f"Recovered Flow from {flow_id}",
                    configuration={"recovery_mode": True, "original_flow_id": flow_id}
                )
                
                # Link orphaned data to new flow
                if data_import_id:
                    from app.services.data_import.storage_manager import ImportStorageManager
                    
                    storage_manager = ImportStorageManager(self.db, self.context.client_account_id)
                    linkage_results = await storage_manager.update_all_records_with_flow(
                        data_import_id=data_import_id,
                        master_flow_id=new_flow_id
                    )
                    
                    return {
                        "success": True,
                        "message": f"Created new flow {new_flow_id} for orphaned data",
                        "details": {
                            "new_flow_id": new_flow_id,
                            "linkage_results": linkage_results
                        }
                    }
                else:
                    return {
                        "success": True,
                        "message": f"Created new flow {new_flow_id} - manual data linking required",
                        "details": {"new_flow_id": new_flow_id}
                    }
            
            else:
                return {
                    "success": False,
                    "message": f"Unknown repair option: {repair_option_id}",
                    "details": {}
                }
                
        except Exception as e:
            logger.error(f"❌ Orphaned data repair failed: {e}")
            return {
                "success": False,
                "message": f"Repair operation failed: {str(e)}",
                "details": {"error": str(e)}
            }