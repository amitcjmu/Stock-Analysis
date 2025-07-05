"""
Master Flow Orchestrator

THE SINGLE ORCHESTRATOR - Replaces ALL individual flow managers
Centralized orchestration for all CrewAI flows (Discovery, Assessment, Planning, Execution, etc.)
Implements a unified flow management system with comprehensive error handling, retry logic,
performance tracking, and audit logging.
"""

import uuid
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import asyncio
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.repositories.crewai_flow_state_extensions_repository import CrewAIFlowStateExtensionsRepository
from app.services.crewai_flows.flow_state_manager import FlowStateManager
from app.core.context import RequestContext
from app.services.flow_type_registry import FlowTypeRegistry
from app.services.validator_registry import ValidatorRegistry
from app.services.handler_registry import HandlerRegistry
from app.services.flow_error_handler import FlowErrorHandler
from app.services.performance_tracker import PerformanceTracker

logger = logging.getLogger(__name__)


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
    THE SINGLE ORCHESTRATOR - Replaces ALL individual flow managers
    
    This orchestrator provides:
    - Unified flow lifecycle management
    - Centralized error handling and retry logic
    - Performance tracking and metrics
    - Comprehensive audit logging
    - Multi-tenant isolation
    - Type-safe flow operations
    """
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize the Master Flow Orchestrator
        
        Args:
            db: Database session
            context: Request context with tenant information
        """
        self.db = db
        self.context = context
        
        # Initialize repositories and managers
        self.master_repo = CrewAIFlowStateExtensionsRepository(
            db, 
            context.client_account_id,
            context.engagement_id,
            context.user_id
        )
        
        # Initialize registries and handlers
        self.flow_registry = FlowTypeRegistry()
        self.state_manager = FlowStateManager(db)
        self.validator_registry = ValidatorRegistry()
        self.handler_registry = HandlerRegistry()
        self.error_handler = FlowErrorHandler()
        self.performance_tracker = PerformanceTracker()
        
        # Operation tracking
        self._active_operations: Dict[str, datetime] = {}
        
        logger.info(f"✅ Master Flow Orchestrator initialized for client {context.client_account_id}")
    
    async def create_flow(
        self,
        flow_type: str,
        flow_name: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None
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
        start_time = datetime.utcnow()
        flow_id = None
        
        try:
            # Start performance tracking
            tracking_id = self.performance_tracker.start_operation(
                operation_type="flow_creation",
                metadata={"flow_type": flow_type}
            )
            
            # Validate flow type
            if not self.flow_registry.is_registered(flow_type):
                raise ValueError(f"Unknown flow type: {flow_type}")
            
            # Get flow configuration
            flow_config = self.flow_registry.get_flow_config(flow_type)
            
            # Generate CrewAI flow ID
            flow_id = str(uuid.uuid4())
            
            # Create master flow record
            master_flow = await self.master_repo.create_master_flow(
                flow_id=flow_id,
                flow_type=flow_type,
                user_id=self.context.user_id or "system",
                flow_name=flow_name or flow_config.display_name,
                flow_configuration=configuration or flow_config.default_configuration,
                initial_state=initial_state or {}
            )
            
            # Execute flow-specific initialization
            if flow_config.initialization_handler:
                handler = self.handler_registry.get_handler(flow_config.initialization_handler)
                if handler:
                    init_result = await handler(
                        flow_id=flow_id,
                        flow_type=flow_type,
                        configuration=configuration,
                        initial_state=initial_state,
                        context=self.context
                    )
                    
                    # Update flow with initialization results
                    await self.master_repo.update_flow_status(
                        flow_id=flow_id,
                        status="initialized",
                        phase_data={"initialization": init_result}
                    )
            
            # Log creation audit
            await self._log_audit_event(
                flow_id=flow_id,
                operation=FlowOperationType.CREATE,
                details={
                    "flow_type": flow_type,
                    "flow_name": flow_name,
                    "configuration": configuration
                }
            )
            
            # Stop performance tracking
            self.performance_tracker.end_operation(
                tracking_id,
                success=True,
                result_metadata={"flow_id": flow_id}
            )
            
            logger.info(f"✅ Created {flow_type} flow: {flow_id}")
            
            return flow_id, master_flow.to_dict()
            
        except Exception as e:
            # Handle error with retry logic
            error_result = await self.error_handler.handle_error(
                error=e,
                context={
                    "operation": "create_flow",
                    "flow_type": flow_type,
                    "flow_id": flow_id
                },
                retry_config={
                    "max_retries": 3,
                    "backoff_multiplier": 2
                }
            )
            
            if error_result.should_retry:
                # Recursive retry with backoff
                await asyncio.sleep(error_result.retry_delay)
                return await self.create_flow(flow_type, flow_name, configuration, initial_state)
            
            # Log failure audit
            await self._log_audit_event(
                flow_id=flow_id or "unknown",
                operation=FlowOperationType.CREATE,
                success=False,
                error=str(e)
            )
            
            raise RuntimeError(f"Failed to create flow: {str(e)}")
    
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
        start_time = datetime.utcnow()
        
        try:
            # Start performance tracking
            tracking_id = self.performance_tracker.start_operation(
                operation_type="phase_execution",
                metadata={
                    "flow_id": flow_id,
                    "phase_name": phase_name
                }
            )
            
            # Get flow and validate
            master_flow = await self.master_repo.get_by_flow_id(flow_id)
            if not master_flow:
                raise ValueError(f"Flow not found: {flow_id}")
            
            # Get flow configuration
            flow_config = self.flow_registry.get_flow_config(master_flow.flow_type)
            
            # Validate phase exists
            phase_config = flow_config.get_phase_config(phase_name)
            if not phase_config:
                raise ValueError(f"Phase '{phase_name}' not found in flow type '{master_flow.flow_type}'")
            
            # Check flow status
            if master_flow.flow_status not in ["initialized", "running", "resumed"]:
                raise RuntimeError(f"Cannot execute phase in status: {master_flow.flow_status}")
            
            # Run phase validators
            validation_results = await self._run_phase_validators(
                phase_config,
                phase_input,
                master_flow,
                validation_overrides
            )
            
            if not validation_results["valid"]:
                raise ValueError(f"Phase validation failed: {validation_results['errors']}")
            
            # Update flow status
            await self.master_repo.update_flow_status(
                flow_id=flow_id,
                status="running",
                collaboration_entry={
                    "timestamp": datetime.utcnow().isoformat(),
                    "phase": phase_name,
                    "action": "phase_started",
                    "details": {"input": phase_input}
                }
            )
            
            # Execute phase through CrewAI
            crew_result = await self._execute_crew_phase(
                master_flow,
                phase_config,
                phase_input
            )
            
            # Run phase completion handlers
            if phase_config.completion_handler:
                handler = self.handler_registry.get_handler(phase_config.completion_handler)
                if handler:
                    completion_result = await handler(
                        flow_id=flow_id,
                        phase_name=phase_name,
                        crew_result=crew_result,
                        context=self.context
                    )
                    crew_result.update(completion_result)
            
            # Update phase execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            master_flow.update_phase_execution_time(phase_name, execution_time)
            
            # Update flow state
            await self.master_repo.update_flow_status(
                flow_id=flow_id,
                status="running",
                phase_data={
                    f"phase_{phase_name}": crew_result,
                    "last_completed_phase": phase_name
                },
                collaboration_entry={
                    "timestamp": datetime.utcnow().isoformat(),
                    "phase": phase_name,
                    "action": "phase_completed",
                    "details": {
                        "execution_time_ms": execution_time,
                        "success": True
                    }
                }
            )
            
            # Log execution audit
            await self._log_audit_event(
                flow_id=flow_id,
                operation=FlowOperationType.EXECUTE,
                details={
                    "phase": phase_name,
                    "execution_time_ms": execution_time,
                    "success": True
                }
            )
            
            # Stop performance tracking
            self.performance_tracker.end_operation(
                tracking_id,
                success=True,
                result_metadata={
                    "phase": phase_name,
                    "execution_time_ms": execution_time
                }
            )
            
            logger.info(f"✅ Executed phase '{phase_name}' for flow {flow_id}")
            
            return {
                "phase": phase_name,
                "status": "completed",
                "execution_time_ms": execution_time,
                "results": crew_result
            }
            
        except Exception as e:
            # Handle error with retry logic
            error_result = await self.error_handler.handle_error(
                error=e,
                context={
                    "operation": "execute_phase",
                    "flow_id": flow_id,
                    "phase_name": phase_name
                },
                retry_config={
                    "max_retries": 2,
                    "backoff_multiplier": 2
                }
            )
            
            if error_result.should_retry:
                # Recursive retry with backoff
                await asyncio.sleep(error_result.retry_delay)
                return await self.execute_phase(flow_id, phase_name, phase_input, validation_overrides)
            
            # Update flow status to failed
            await self.master_repo.update_flow_status(
                flow_id=flow_id,
                status="failed",
                collaboration_entry={
                    "timestamp": datetime.utcnow().isoformat(),
                    "phase": phase_name,
                    "action": "phase_failed",
                    "error": str(e)
                }
            )
            
            # Log failure audit
            await self._log_audit_event(
                flow_id=flow_id,
                operation=FlowOperationType.EXECUTE,
                success=False,
                error=str(e),
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
            # Get flow
            master_flow = await self.master_repo.get_by_flow_id(flow_id)
            if not master_flow:
                raise ValueError(f"Flow not found: {flow_id}")
            
            # Validate flow can be paused
            if master_flow.flow_status not in ["running", "initialized"]:
                raise ValueError(f"Cannot pause flow in status: {master_flow.flow_status}")
            
            # Update flow status
            await self.master_repo.update_flow_status(
                flow_id=flow_id,
                status="paused",
                phase_data={
                    "pause_reason": reason or "user_requested",
                    "paused_at": datetime.utcnow().isoformat()
                },
                collaboration_entry={
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "flow_paused",
                    "reason": reason or "user_requested"
                }
            )
            
            # Log pause audit
            await self._log_audit_event(
                flow_id=flow_id,
                operation=FlowOperationType.PAUSE,
                details={"reason": reason}
            )
            
            logger.info(f"⏸️ Paused flow {flow_id}: {reason}")
            
            return {
                "flow_id": flow_id,
                "status": "paused",
                "reason": reason or "user_requested",
                "paused_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to pause flow {flow_id}: {e}")
            raise RuntimeError(f"Failed to pause flow: {str(e)}")
    
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
            # Get flow
            master_flow = await self.master_repo.get_by_flow_id(flow_id)
            if not master_flow:
                raise ValueError(f"Flow not found: {flow_id}")
            
            # Validate flow can be resumed
            if master_flow.flow_status != "paused":
                raise ValueError(f"Cannot resume flow in status: {master_flow.flow_status}")
            
            # Get flow configuration
            flow_config = self.flow_registry.get_flow_config(master_flow.flow_type)
            
            # Determine resume point
            last_phase = master_flow.flow_persistence_data.get("last_completed_phase")
            next_phase = flow_config.get_next_phase(last_phase) if last_phase else flow_config.phases[0].name
            
            # Update flow status
            await self.master_repo.update_flow_status(
                flow_id=flow_id,
                status="resumed",
                phase_data={
                    "resumed_at": datetime.utcnow().isoformat(),
                    "resume_phase": next_phase,
                    "resume_context": resume_context
                },
                collaboration_entry={
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "flow_resumed",
                    "resume_phase": next_phase
                }
            )
            
            # Log resume audit
            await self._log_audit_event(
                flow_id=flow_id,
                operation=FlowOperationType.RESUME,
                details={
                    "resume_phase": next_phase,
                    "context": resume_context
                }
            )
            
            logger.info(f"▶️ Resumed flow {flow_id} at phase: {next_phase}")
            
            return {
                "flow_id": flow_id,
                "status": "resumed",
                "resume_phase": next_phase,
                "resumed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to resume flow {flow_id}: {e}")
            raise RuntimeError(f"Failed to resume flow: {str(e)}")
    
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
            # Get flow
            master_flow = await self.master_repo.get_by_flow_id(flow_id)
            if not master_flow:
                raise ValueError(f"Flow not found: {flow_id}")
            
            if soft_delete:
                # Soft delete - update status
                await self.master_repo.update_flow_status(
                    flow_id=flow_id,
                    status="deleted",
                    phase_data={
                        "deleted_at": datetime.utcnow().isoformat(),
                        "deletion_reason": reason or "user_requested",
                        "soft_delete": True
                    },
                    collaboration_entry={
                        "timestamp": datetime.utcnow().isoformat(),
                        "action": "flow_deleted",
                        "soft_delete": True,
                        "reason": reason
                    }
                )
                
                logger.info(f"🗑️ Soft deleted flow {flow_id}")
                
            else:
                # Hard delete - remove from database
                success = await self.master_repo.delete_master_flow(flow_id)
                if not success:
                    raise RuntimeError("Failed to delete flow from database")
                
                logger.info(f"💀 Hard deleted flow {flow_id}")
            
            # Log deletion audit
            await self._log_audit_event(
                flow_id=flow_id,
                operation=FlowOperationType.DELETE,
                details={
                    "soft_delete": soft_delete,
                    "reason": reason
                }
            )
            
            return {
                "flow_id": flow_id,
                "deleted": True,
                "soft_delete": soft_delete,
                "deleted_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to delete flow {flow_id}: {e}")
            raise RuntimeError(f"Failed to delete flow: {str(e)}")
    
    async def get_flow_status(
        self,
        flow_id: str,
        include_details: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive flow status
        
        Args:
            flow_id: Flow identifier
            include_details: Whether to include detailed information
            
        Returns:
            Flow status information
        """
        try:
            # Start performance tracking
            tracking_id = self.performance_tracker.start_operation(
                operation_type="status_check",
                metadata={"flow_id": flow_id}
            )
            
            # Get flow
            master_flow = await self.master_repo.get_by_flow_id(flow_id)
            if not master_flow:
                raise ValueError(f"Flow not found: {flow_id}")
            
            # Get flow configuration
            flow_config = self.flow_registry.get_flow_config(master_flow.flow_type)
            
            # Build basic status
            status = {
                "flow_id": flow_id,
                "flow_type": master_flow.flow_type,
                "flow_name": master_flow.flow_name,
                "status": master_flow.flow_status,
                "created_at": master_flow.created_at.isoformat(),
                "updated_at": master_flow.updated_at.isoformat()
            }
            
            if include_details:
                # Add detailed information
                status.update({
                    "configuration": master_flow.flow_configuration,
                    "phases": {
                        "total": len(flow_config.phases),
                        "completed": len([
                            phase for phase in flow_config.phases
                            if master_flow.phase_execution_times.get(phase.name)
                        ]),
                        "execution_times": master_flow.phase_execution_times
                    },
                    "performance": master_flow.get_performance_summary(),
                    "collaboration_log": master_flow.agent_collaboration_log[-10:],  # Last 10 entries
                    "state_data": master_flow.flow_persistence_data
                })
            
            # Log status check audit
            await self._log_audit_event(
                flow_id=flow_id,
                operation=FlowOperationType.STATUS_CHECK,
                details={"include_details": include_details}
            )
            
            # Stop performance tracking
            self.performance_tracker.end_operation(
                tracking_id,
                success=True
            )
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get flow status for {flow_id}: {e}")
            raise RuntimeError(f"Failed to get flow status: {str(e)}")
    
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
            if flow_type:
                # Get flows by specific type
                flows = await self.master_repo.get_flows_by_type(flow_type, limit)
            else:
                # Get all active flows
                flows = await self.master_repo.get_active_flows(limit)
            
            # Convert to dict format
            flow_list = []
            for flow in flows:
                flow_list.append({
                    "flow_id": str(flow.flow_id),
                    "flow_type": flow.flow_type,
                    "flow_name": flow.flow_name,
                    "status": flow.flow_status,
                    "created_at": flow.created_at.isoformat(),
                    "updated_at": flow.updated_at.isoformat()
                })
            
            # Log list operation audit
            await self._log_audit_event(
                flow_id="system",
                operation=FlowOperationType.LIST,
                details={
                    "flow_type": flow_type,
                    "limit": limit,
                    "count": len(flow_list)
                }
            )
            
            return flow_list
            
        except Exception as e:
            logger.error(f"Failed to get active flows: {e}")
            raise RuntimeError(f"Failed to get active flows: {str(e)}")
    
    # Private helper methods
    
    async def _run_phase_validators(
        self,
        phase_config,
        phase_input: Dict[str, Any],
        master_flow: CrewAIFlowStateExtensions,
        validation_overrides: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Run validators for a phase"""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        for validator_name in phase_config.validators:
            validator = self.validator_registry.get_validator(validator_name)
            if validator:
                result = await validator(
                    phase_input=phase_input,
                    flow_state=master_flow.flow_persistence_data,
                    overrides=validation_overrides
                )
                
                if not result["valid"]:
                    validation_results["valid"] = False
                    validation_results["errors"].extend(result.get("errors", []))
                
                validation_results["warnings"].extend(result.get("warnings", []))
        
        return validation_results
    
    async def _execute_crew_phase(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_config,
        phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a phase through CrewAI"""
        # This is a placeholder for actual CrewAI integration
        # In real implementation, this would:
        # 1. Create/get the appropriate crew
        # 2. Execute the crew with phase input
        # 3. Collect and return results
        
        logger.info(f"Executing CrewAI phase: {phase_config.name}")
        
        # Simulate crew execution
        await asyncio.sleep(0.1)  # Simulate work
        
        return {
            "phase": phase_config.name,
            "status": "completed",
            "crew_results": {
                "agents_involved": phase_config.crew_config.get("agents", []),
                "tasks_completed": phase_config.crew_config.get("tasks", []),
                "output": phase_input  # In real implementation, this would be crew output
            }
        }
    
    async def _log_audit_event(
        self,
        flow_id: str,
        operation: FlowOperationType,
        success: bool = True,
        error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log audit event for flow operations"""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "flow_id": flow_id,
            "operation": operation.value,
            "success": success,
            "user_id": self.context.user_id,
            "client_account_id": self.context.client_account_id,
            "engagement_id": self.context.engagement_id,
            "details": details or {},
            "error": error
        }
        
        # In production, this would write to audit log storage
        logger.info(f"📝 Audit: {audit_entry}")
        
        # Also track in performance metrics
        self.performance_tracker.record_audit_event(audit_entry)