"""
Flow Operations Module

Contains core flow operation methods including creation, execution, and lifecycle management.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.core.exceptions import FlowError
from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.repositories.crewai_flow_state_extensions_repository import CrewAIFlowStateExtensionsRepository
from app.services.flow_error_handler import ErrorContext, RetryConfig
from app.services.flow_orchestration import FlowAuditLogger, FlowErrorHandler, FlowExecutionEngine, FlowLifecycleManager
from app.services.flow_orchestration.audit_logger import AuditCategory, AuditLevel

from .enums import FlowOperationType
from .mock_monitor import MockFlowPerformanceMonitor

logger = get_logger(__name__)


class FlowOperations:
    """Handles core flow operations"""
    
    def __init__(
        self,
        db: AsyncSession,
        context: RequestContext,
        master_repo: CrewAIFlowStateExtensionsRepository,
        flow_registry,
        handler_registry,
        validator_registry,
        lifecycle_manager: FlowLifecycleManager,
        execution_engine: FlowExecutionEngine,
        error_handler: FlowErrorHandler,
        performance_monitor: MockFlowPerformanceMonitor,
        audit_logger: FlowAuditLogger
    ):
        self.db = db
        self.context = context
        self.master_repo = master_repo
        self.flow_registry = flow_registry
        self.handler_registry = handler_registry
        self.validator_registry = validator_registry
        self.lifecycle_manager = lifecycle_manager
        self.execution_engine = execution_engine
        self.error_handler = error_handler
        self.performance_monitor = performance_monitor
        self.audit_logger = audit_logger
    
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
    
    async def get_flow_db_id(self, flow_id: str) -> Optional[uuid.UUID]:
        """Get the database ID for a given flow_id"""
        try:
            query = select(CrewAIFlowStateExtensions.id).where(
                CrewAIFlowStateExtensions.flow_id == flow_id
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.warning(f"Failed to get database ID for flow_id {flow_id}: {e}")
            return None