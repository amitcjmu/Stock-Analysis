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
from app.services.flow_type_registry import FlowTypeRegistry
from app.services.validator_registry import ValidatorRegistry
from app.services.handler_registry import HandlerRegistry
from app.services.flow_error_handler import FlowErrorHandler
from app.services.performance_tracker import PerformanceTracker

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
        
        # [ECHO] Use global singleton registries
        from app.services.flow_type_registry import flow_type_registry
        from app.services.validator_registry import validator_registry
        from app.services.handler_registry import handler_registry
        
        # Initialize registries and handlers
        self.flow_registry = flow_type_registry  # Use global singleton
        self.state_manager = FlowStateManager(db, context)
        self.validator_registry = validator_registry  # Use global singleton
        self.handler_registry = handler_registry  # Use global singleton
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
            
            # Create master flow record (without auto-commit for atomic operations)
            master_flow = await self.master_repo.create_master_flow(
                flow_id=flow_id,
                flow_type=flow_type,
                user_id=self.context.user_id or "system",
                flow_name=flow_name or flow_config.display_name,
                flow_configuration=configuration or flow_config.default_configuration,
                initial_state=initial_state or {},
                auto_commit=False  # FIX: Don't commit here - let the calling transaction manage commits
            )
            
            # CRITICAL: Ensure the master flow record is flushed and visible for foreign key references
            await self.db.flush()
            logger.info(f"✅ Master flow record flushed for foreign key visibility: {flow_id}")
            
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
            
            # CRITICAL FIX: For discovery and assessment flows, kick off the CrewAI flow immediately
            if flow_type == "discovery":
                logger.info(f"🚀 [FIX] Kicking off CrewAI Discovery Flow for {flow_id}")
                
                # Delegate to CrewAI flow service to start execution
                try:
                    from app.services.crewai_flow_service import CrewAIFlowService
                    from app.services.crewai_flows.unified_discovery_flow import create_unified_discovery_flow
                    
                    # Create CrewAI service
                    crewai_service = CrewAIFlowService(self.db)
                    
                    # Prepare raw data from initial state
                    raw_data = initial_state.get("raw_data", []) if initial_state else []
                    
                    # PHASE 2 FIX: Create DiscoveryFlow record with proper master flow linkage
                    # Transaction safety for DiscoveryFlow creation
                    discovery_savepoint = None
                    try:
                        from app.models.discovery_flow import DiscoveryFlow
                        from sqlalchemy import select
                        
                        # Create savepoint for DiscoveryFlow operations
                        discovery_savepoint = await self.db.begin_nested()
                        
                        # Check if DiscoveryFlow already exists for this flow_id
                        existing_discovery_query = select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_id)
                        existing_discovery_result = await self.db.execute(existing_discovery_query)
                        existing_discovery = existing_discovery_result.scalar_one_or_none()
                        
                        if not existing_discovery:
                            # Create DiscoveryFlow record with master flow linkage
                            discovery_flow_record = DiscoveryFlow(
                                flow_id=flow_id,
                                flow_name=flow_name or f"Discovery Flow {flow_id}",
                                client_account_id=uuid.UUID(str(self.context.client_account_id)),
                                engagement_id=uuid.UUID(str(self.context.engagement_id)),
                                status="initialized",
                                current_phase="initialization",
                                progress_percentage=0.0,
                                user_id=self.context.user_id or "system",
                                master_flow_id=flow_id,  # Link to master flow
                                data_import_id=initial_state.get("data_import_id") if initial_state else None
                            )
                            
                            self.db.add(discovery_flow_record)
                            await self.db.flush()  # Ensure the record is created
                            logger.info(f"✅ Created DiscoveryFlow record with master_flow_id: {flow_id}")
                        else:
                            logger.info(f"✅ DiscoveryFlow record already exists for flow_id: {flow_id}")
                            # Update master_flow_id if not set
                            if not existing_discovery.master_flow_id:
                                existing_discovery.master_flow_id = flow_id
                                logger.info(f"✅ Updated existing DiscoveryFlow with master_flow_id: {flow_id}")
                        
                        # Commit the DiscoveryFlow transaction
                        await discovery_savepoint.commit()
                        logger.info(f"✅ DiscoveryFlow transaction committed successfully")
                        
                    except Exception as discovery_record_error:
                        logger.error(f"❌ Failed to create DiscoveryFlow record: {discovery_record_error}")
                        if discovery_savepoint:
                            try:
                                await discovery_savepoint.rollback()
                                logger.info(f"🔄 Rolled back DiscoveryFlow transaction")
                            except Exception as rollback_error:
                                logger.error(f"❌ Failed to rollback DiscoveryFlow transaction: {rollback_error}")
                        # Don't fail the entire flow creation, just log the error
                    
                    # Create the UnifiedDiscoveryFlow instance
                    # Add master flow ID to metadata so discovery flow can link back
                    flow_metadata = configuration or {}
                    flow_metadata['master_flow_id'] = flow_id
                    
                    discovery_flow = create_unified_discovery_flow(
                        flow_id=flow_id,
                        client_account_id=self.context.client_account_id,
                        engagement_id=self.context.engagement_id,
                        user_id=self.context.user_id or "system",
                        raw_data=raw_data,
                        metadata=flow_metadata,
                        crewai_service=crewai_service,
                        context=self.context,
                        master_flow_id=flow_id  # Pass master_flow_id explicitly
                    )
                    
                    logger.info(f"✅ [FIX] CrewAI Discovery Flow created, starting kickoff in background")
                    
                    # Start the flow execution in background
                    import asyncio
                    
                    async def run_discovery_flow():
                        try:
                            logger.info(f"🎯 [ECHO] Starting CrewAI Discovery Flow kickoff for {flow_id}")
                            
                            # [ECHO] Use a fresh database session for the background task
                            from app.core.database import AsyncSessionLocal
                            from app.repositories.crewai_flow_state_extensions_repository import CrewAIFlowStateExtensionsRepository
                            
                            async with AsyncSessionLocal() as fresh_db:
                                # Create a fresh repository for the background task
                                fresh_repo = CrewAIFlowStateExtensionsRepository(
                                    fresh_db, 
                                    self.context.client_account_id,
                                    self.context.engagement_id,
                                    self.context.user_id
                                )
                                
                                # [ECHO] First update status to processing (DB constraint)
                                await fresh_repo.update_flow_status(
                                    flow_id=flow_id,
                                    status="processing",  # Changed from "running" to match DB constraint
                                    phase_data={"message": "CrewAI flow kickoff starting"}
                                )
                            
                            # [ECHO] Log the discovery_flow object details
                            logger.info(f"🔍 [ECHO] Discovery flow object: {discovery_flow}")
                            logger.info(f"🔍 [ECHO] Discovery flow class: {type(discovery_flow)}")
                            logger.info(f"🔍 [ECHO] Has kickoff method: {hasattr(discovery_flow, 'kickoff')}")
                            
                            # CrewAI Flow kickoff() is synchronous, so run it in a thread
                            logger.info(f"🚀 [ECHO] Calling discovery_flow.kickoff() in thread...")
                            result = await asyncio.to_thread(discovery_flow.kickoff)
                            logger.info(f"✅ [ECHO] CrewAI Discovery Flow kickoff returned: {result}")
                            
                            # Update flow status based on result
                            async with AsyncSessionLocal() as fresh_db:
                                fresh_repo = CrewAIFlowStateExtensionsRepository(
                                    fresh_db, 
                                    self.context.client_account_id,
                                    self.context.engagement_id,
                                    self.context.user_id
                                )
                                
                                # Determine appropriate status based on flow result
                                if result in ["paused_for_field_mapping_approval", "awaiting_user_approval_in_attribute_mapping"]:
                                    flow_status = "waiting_for_approval"
                                    logger.info(f"✅ [ECHO] Flow paused for user approval, setting status: {flow_status}")
                                    # Set phase and progress for frontend recognition
                                    phase_data = {
                                        "completion": result,
                                        "current_phase": "attribute_mapping",
                                        "progress_percentage": 60.0,  # Data import done, awaiting user approval
                                        "paused_at": datetime.utcnow().isoformat(),
                                        "awaiting_user_approval": True
                                    }
                                elif result in ["discovery_completed"]:
                                    flow_status = "completed"
                                    logger.info(f"✅ [ECHO] Flow completed successfully, setting status: {flow_status}")
                                    phase_data = {
                                        "completion": result,
                                        "current_phase": "completed",
                                        "progress_percentage": 100.0,
                                        "completed_at": datetime.utcnow().isoformat()
                                    }
                                elif result in ["discovery_failed"]:
                                    flow_status = "failed"
                                    logger.info(f"❌ [ECHO] Flow failed, setting status: {flow_status}")
                                    phase_data = {
                                        "completion": result,
                                        "current_phase": "failed",
                                        "progress_percentage": 0.0,
                                        "failed_at": datetime.utcnow().isoformat()
                                    }
                                else:
                                    # Default to processing for other results
                                    flow_status = "processing"
                                    logger.info(f"🔄 [ECHO] Flow result '{result}', setting status: {flow_status}")
                                    phase_data = {
                                        "completion": result,
                                        "current_phase": "processing",
                                        "progress_percentage": 30.0
                                    }
                                
                                await fresh_repo.update_flow_status(
                                    flow_id=flow_id,
                                    status=flow_status,
                                    phase_data=phase_data
                                )
                        except Exception as e:
                            logger.error(f"❌ [ECHO] CrewAI Discovery Flow execution failed: {e}")
                            import traceback
                            logger.error(f"[ECHO] Full traceback: {traceback.format_exc()}")
                            
                            # Update flow status to failed
                            try:
                                async with AsyncSessionLocal() as fresh_db:
                                    fresh_repo = CrewAIFlowStateExtensionsRepository(
                                        fresh_db, 
                                        self.context.client_account_id,
                                        self.context.engagement_id,
                                        self.context.user_id
                                    )
                                    await fresh_repo.update_flow_status(
                                        flow_id=flow_id,
                                        status="failed",
                                        phase_data={"error": str(e), "traceback": traceback.format_exc()}
                                    )
                            except Exception as update_error:
                                logger.error(f"❌ [ECHO] Failed to update flow status to failed: {update_error}")
                    
                    # Create the task but don't await it - let it run in background
                    task = asyncio.create_task(run_discovery_flow())
                    
                    # [ECHO] Store task reference to prevent garbage collection
                    if not hasattr(self, '_active_flow_tasks'):
                        self._active_flow_tasks = {}
                    self._active_flow_tasks[flow_id] = task
                    
                    logger.info(f"🚀 [ECHO] CrewAI Discovery Flow task created and running in background")
                    logger.info(f"🔍 [ECHO] Task reference stored to prevent GC: {task}")
                    
                    # [ECHO] Update flow status to running after a short delay to ensure kickoff started
                    async def update_status_after_kickoff():
                        await asyncio.sleep(0.5)  # Short delay to let kickoff start
                        try:
                            await self.master_repo.update_flow_status(
                                flow_id=flow_id,
                                status="processing",  # Changed from "running" to match DB constraint
                                phase_data={"message": "Discovery flow kickoff initiated"}
                            )
                            logger.info(f"✅ [ECHO] Updated flow status to 'running' after kickoff start")
                        except Exception as e:
                            logger.warning(f"⚠️ [ECHO] Failed to update flow status after kickoff: {e}")
                    
                    asyncio.create_task(update_status_after_kickoff())
                    
                except Exception as e:
                    logger.error(f"❌ [FIX] Failed to start CrewAI Discovery Flow: {e}")
                    # Don't fail the flow creation, just log the error
                    # The flow can still be executed later via execute_phase
                    
            elif flow_type == "assessment":
                logger.info(f"🚀 [FIX] Kicking off CrewAI Assessment Flow for {flow_id}")
                
                # Delegate to Assessment flow service to start execution
                try:
                    from app.services.unified_assessment_flow_service import AssessmentFlowService
                    from app.core.context import RequestContext
                    from app.core.database import AsyncSessionLocal
                    
                    # Create Assessment service
                    async with AsyncSessionLocal() as db:
                        assessment_service = AssessmentFlowService(db)
                        
                        # Create context for assessment
                        context = RequestContext(
                            client_account_id=self.context.client_account_id,
                            engagement_id=self.context.engagement_id,
                            user_id=self.context.user_id
                        )
                        
                        # Get selected applications from initial state
                        selected_apps = initial_state.get("selected_application_ids", []) if initial_state else []
                        if not selected_apps:
                            logger.warning(f"⚠️ [FIX] No selected applications provided for assessment flow {flow_id}")
                            # Don't fail, flow can be configured later
                            selected_apps = []
                        
                        # Create the assessment flow
                        assessment_result = await assessment_service.create_assessment_flow(
                            context=context,
                            selected_application_ids=selected_apps,
                            flow_name=flow_name or f"Assessment Flow {flow_id}",
                            configuration=configuration or {}
                        )
                        
                        logger.info(f"✅ [FIX] CrewAI Assessment Flow created: {assessment_result}")
                        
                        # Update master flow status with assessment result
                        await self.master_repo.update_flow_status(
                            flow_id=flow_id,
                            status="processing",  # Changed from "running" to match DB constraint
                            phase_data={"assessment_creation": assessment_result}
                        )
                        
                except Exception as e:
                    logger.error(f"❌ [FIX] Failed to start CrewAI Assessment Flow: {e}")
                    # Don't fail the flow creation, just log the error
            
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
            
            logger.info(
                f"✅ Created {flow_type} flow: {flow_id}",
                extra={
                    "flow_id": flow_id,
                    "flow_type": flow_type,
                    "flow_name": flow_name
                }
            )
            
            # NOTE: Transaction commit is now managed by the calling code for atomicity
            logger.info(f"✅ Master flow created - transaction will be committed by caller for atomicity")
            
            return flow_id, master_flow.to_dict()
            
        except Exception as e:
            # Handle error with retry logic
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
            
            if error_result.should_retry:
                # Recursive retry with backoff
                await asyncio.sleep(error_result.retry_delay)
                return await self.create_flow(flow_type, flow_name, configuration, initial_state)
            
            # Log failure audit
            await self._log_audit_event(
                flow_id=flow_id or "unknown",
                operation=FlowOperationType.CREATE,
                success=False,
                error=str(e),
                details=error_result.metadata
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
                raise FlowNotFoundError(flow_id)
            
            # Get flow configuration
            flow_config = self.flow_registry.get_flow_config(master_flow.flow_type)
            
            # Validate phase exists
            phase_config = flow_config.get_phase_config(phase_name)
            if not phase_config:
                raise ValueError(f"Phase '{phase_name}' not found in flow type '{master_flow.flow_type}'")
            
            # Check flow status - use valid statuses from DB constraint
            if master_flow.flow_status not in ["initialized", "active", "processing", "waiting_for_approval"]:
                raise InvalidFlowStateError(
                    current_state=master_flow.flow_status,
                    target_state="processing",
                    flow_id=flow_id
                )
            
            # Run phase validators
            validation_results = await self._run_phase_validators(
                phase_config,
                phase_input,
                master_flow,
                validation_overrides
            )
            
            if not validation_results["valid"]:
                raise ValueError(f"Phase validation failed: {validation_results['errors']}")
            
            # Update flow status - use 'processing' instead of 'running' for DB constraint
            await self.master_repo.update_flow_status(
                flow_id=flow_id,
                status="processing",  # Changed from "running" to match DB constraint
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
            
            # Update flow state - use 'processing' instead of 'running' for DB constraint
            await self.master_repo.update_flow_status(
                flow_id=flow_id,
                status="processing",  # Changed from "running" to match DB constraint
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
            
            # Validate flow can be paused - use valid statuses from DB constraint
            if master_flow.flow_status not in ["active", "processing", "initialized"]:
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
                raise FlowNotFoundError(flow_id)
            
            # Validate flow can be resumed
            if master_flow.flow_status not in ["paused", "waiting_for_approval"]:
                raise InvalidFlowStateError(
                    current_state=master_flow.flow_status,
                    target_state="active",
                    flow_id=flow_id
                )
            
            # Get flow configuration
            flow_config = self.flow_registry.get_flow_config(master_flow.flow_type)
            
            # Determine resume point
            last_phase = master_flow.flow_persistence_data.get("last_completed_phase")
            next_phase = flow_config.get_next_phase(last_phase) if last_phase else flow_config.phases[0].name
            
            # Update flow status - use 'active' instead of 'resumed' for DB constraint
            await self.master_repo.update_flow_status(
                flow_id=flow_id,
                status="active",  # Changed from "resumed" to match DB constraint
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
            
            # Delegate to actual flow implementation based on flow type
            # TODO: Implement proper delegation based on flow type
            # For now, discovery flows can use CrewAIFlowService
            if master_flow.flow_type == "discovery":
                try:
                    from app.services.crewai_flow_service import CrewAIFlowService
                    from app.core.database import AsyncSessionLocal
                    
                    # Create CrewAI service instance
                    crewai_service = CrewAIFlowService()
                    
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
                            logger.info(f"🔍 Created resume_context from master flow: {resume_context}")
                        
                        crew_result = await crewai_service.resume_flow(
                            flow_id=str(flow_id),
                            resume_context=resume_context
                        )
                        
                        logger.info(
                            f"✅ Delegated to CrewAI Flow Service: {crew_result}",
                            extra={
                                "flow_id": flow_id,
                                "flow_type": "discovery",
                                "action": "resume"
                            }
                        )
                        
                except Exception as e:
                    logger.warning(
                        f"⚠️ Failed to delegate to CrewAI Flow Service: {e}",
                        extra={
                            "flow_id": flow_id,
                            "error_type": type(e).__name__,
                            "action": "resume_delegation"
                        }
                    )
                    # Continue with master flow tracking even if delegation fails
            
            # Log resume audit
            await self._log_audit_event(
                flow_id=flow_id,
                operation=FlowOperationType.RESUME,
                details={
                    "resume_phase": next_phase,
                    "context": resume_context
                }
            )
            
            logger.info(
                f"▶️ Resumed flow {flow_id} at phase: {next_phase}",
                extra={
                    "flow_id": flow_id,
                    "flow_type": master_flow.flow_type,
                    "resume_phase": next_phase
                }
            )
            
            return {
                "flow_id": flow_id,
                "status": "active",  # Changed from "resumed" to match what's stored in DB
                "resume_phase": next_phase,
                "resumed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(
                f"Failed to resume flow {flow_id}: {e}",
                extra={
                    "flow_id": flow_id,
                    "error_type": type(e).__name__,
                    "operation": "resume_flow"
                },
                exc_info=True
            )
            
            # Re-raise as FlowError with context
            if not isinstance(e, (FlowNotFoundError, InvalidFlowStateError)):
                raise FlowError(
                    message=f"Failed to resume flow: {str(e)}",
                    flow_id=flow_id,
                    details={
                        "operation": "resume",
                        "original_error": type(e).__name__
                    }
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
            # Get flow
            master_flow = await self.master_repo.get_by_flow_id(flow_id)
            if not master_flow:
                raise ValueError(f"Flow not found: {flow_id}")
            
            if soft_delete:
                # Soft delete - use 'cancelled' instead of 'deleted' for DB constraint
                await self.master_repo.update_flow_status(
                    flow_id=flow_id,
                    status="cancelled",  # Changed from "deleted" to match DB constraint
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
                "updated_at": master_flow.updated_at.isoformat(),
                "created_by": getattr(master_flow, 'created_by', self.context.user_id),
                "current_phase": getattr(master_flow, 'current_phase', None),
                "progress_percentage": getattr(master_flow, 'progress_percentage', 0.0),
                "configuration": master_flow.flow_configuration if hasattr(master_flow, 'flow_configuration') and master_flow.flow_configuration else {},
                "metadata": {}
            }
            
            if include_details:
                # Get agent insights for this flow
                logger.info(f"🔍 Getting agent insights for flow {flow_id} (type: {master_flow.flow_type})")
                agent_insights = await self._get_flow_agent_insights(flow_id, master_flow.flow_type)
                logger.info(f"🔍 Retrieved {len(agent_insights)} agent insights for flow {flow_id}")
                
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
                    "state_data": master_flow.flow_persistence_data,
                    "agent_insights": agent_insights
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
    
    async def _get_flow_agent_insights(self, flow_id: str, flow_type: str) -> List[Dict[str, Any]]:
        """
        Get agent insights for a specific flow from multiple sources.
        
        Args:
            flow_id: Flow identifier
            flow_type: Type of flow (discovery, assessment, etc.)
            
        Returns:
            List of agent insights
        """
        try:
            insights = []
            logger.info(f"🔍 _get_flow_agent_insights called for flow_id={flow_id}, flow_type={flow_type}")
            
            # Try to get insights from agent_ui_bridge service
            try:
                from app.services.agent_ui_bridge import AgentUIBridge
                bridge = AgentUIBridge(data_dir="backend/data")
                
                # Get insights by page context based on flow type
                page_context = "discovery" if flow_type == "discovery" else "assessment" if flow_type == "assessment" else "general"
                logger.info(f"🔍 Searching for insights with page_context: {page_context}")
                bridge_insights = bridge.get_insights_for_page(page_context)
                
                # Also get flow-specific insights
                flow_page_context = f"flow_{flow_id}"
                logger.info(f"🔍 Searching for flow-specific insights with page_context: {flow_page_context}")
                flow_insights = bridge.get_insights_for_page(flow_page_context)
                
                if bridge_insights:
                    logger.info(f"🔗 Found {len(bridge_insights)} insights from agent_ui_bridge for {flow_type} flow")
                    # Filter insights by flow_id if available, or include those with null flow_id for the flow type
                    flow_specific_insights = [
                        insight for insight in bridge_insights 
                        if insight.get("flow_id") == flow_id or 
                           (insight.get("flow_id") is None and insight.get("page") == page_context)
                    ]
                    insights.extend(flow_specific_insights)
                    logger.info(f"🔍 Filtered {len(flow_specific_insights)} flow-specific insights for flow {flow_id} from {len(bridge_insights)} total insights")
                    if len(flow_specific_insights) > 0:
                        logger.info(f"🔍 Sample insight: {flow_specific_insights[0]}")
                else:
                    logger.info(f"🔍 No bridge insights found for page_context: {page_context}")
                
                if flow_insights:
                    logger.info(f"🔗 Found {len(flow_insights)} flow-specific insights for flow {flow_id}")
                    insights.extend(flow_insights)
                    if len(flow_insights) > 0:
                        logger.info(f"🔍 Sample flow insight: {flow_insights[0]}")
                else:
                    logger.info(f"🔍 No flow-specific insights found for page_context: {flow_page_context}")
                    
            except Exception as e:
                logger.warning(f"⚠️ Could not get insights from agent_ui_bridge: {e}")
            
            # Get insights from flow persistence data if available
            try:
                master_flow = await self.master_repo.get_by_flow_id(flow_id)
                if master_flow and master_flow.flow_persistence_data:
                    flow_data = master_flow.flow_persistence_data
                    
                    # Check if there are agent insights stored in the flow data
                    flow_insights_found = []
                    
                    # Look for agent insights in multiple possible locations
                    if "agent_insights" in flow_data:
                        flow_insights = flow_data["agent_insights"]
                        if isinstance(flow_insights, list):
                            flow_insights_found.extend(flow_insights)
                            logger.info(f"📊 Found {len(flow_insights)} insights from flow_data.agent_insights")
                    
                    # Check for insights in nested structures (like crewai_state_data)
                    if "crewai_state_data" in flow_data and isinstance(flow_data["crewai_state_data"], dict):
                        crewai_data = flow_data["crewai_state_data"]
                        if "agent_insights" in crewai_data and isinstance(crewai_data["agent_insights"], list):
                            nested_insights = crewai_data["agent_insights"]
                            # Transform nested insights to standard format
                            for insight in nested_insights:
                                if isinstance(insight, dict):
                                    # Convert from nested format to standard format
                                    standardized_insight = {
                                        "id": f"nested-{flow_id}-{len(flow_insights_found)}",
                                        "agent_id": insight.get("agent", "unknown").lower().replace(" ", "_"),
                                        "agent_name": insight.get("agent", "Unknown Agent"),
                                        "insight_type": "agent_analysis",
                                        "title": insight.get("insight", "")[:50] + "..." if len(insight.get("insight", "")) > 50 else insight.get("insight", ""),
                                        "description": insight.get("insight", "No description available"),
                                        "confidence": insight.get("confidence", 0.5),
                                        "supporting_data": {
                                            "flow_id": flow_id,
                                            "timestamp": insight.get("timestamp"),
                                            "original_data": insight
                                        },
                                        "actionable": True,
                                        "page": f"flow_{flow_id}",
                                        "created_at": insight.get("timestamp"),
                                        "flow_id": flow_id
                                    }
                                    flow_insights_found.append(standardized_insight)
                            logger.info(f"📊 Found {len(nested_insights)} insights from crewai_state_data.agent_insights")
                    
                    # Add all found insights
                    if flow_insights_found:
                        insights.extend(flow_insights_found)
                        logger.info(f"📊 Total {len(flow_insights_found)} insights extracted from flow persistence data")
                    
                    # Generate insights from flow state
                    # Check multiple locations for current phase and progress
                    current_phase = flow_data.get("current_phase")
                    progress_percentage = flow_data.get("progress_percentage", 0.0)
                    
                    # Also check nested crewai_state_data
                    if not current_phase and "crewai_state_data" in flow_data:
                        crewai_data = flow_data["crewai_state_data"]
                        if isinstance(crewai_data, dict):
                            current_phase = crewai_data.get("current_phase")
                            if not progress_percentage:
                                progress_percentage = crewai_data.get("progress_percentage", 0.0)
                    
                    # Check phase_execution_times for phase information
                    if not current_phase and master_flow.phase_execution_times:
                        try:
                            phase_times = master_flow.phase_execution_times
                            if isinstance(phase_times, dict):
                                current_phase = phase_times.get("current_phase")
                                if not progress_percentage:
                                    progress_percentage = phase_times.get("progress_percentage", 0.0)
                        except Exception as e:
                            logger.debug(f"Could not extract phase from phase_execution_times: {e}")
                    
                    # Default if still not found
                    current_phase = current_phase or "unknown"
                    
                    logger.info(f"🔍 Flow status insight: phase={current_phase}, progress={progress_percentage}, status={master_flow.flow_status}")
                    
                    if master_flow.flow_status:
                        insights.append({
                            "id": f"flow-status-{flow_id}",
                            "agent_id": "flow-orchestrator",
                            "agent_name": "Flow Orchestrator",
                            "insight_type": "flow_status",
                            "title": f"Flow Status: {master_flow.flow_status.title()}",
                            "description": f"Flow is currently in {current_phase} phase with {master_flow.flow_status} status",
                            "confidence": "high",
                            "supporting_data": {
                                "flow_id": flow_id,
                                "flow_type": flow_type,
                                "status": master_flow.flow_status,
                                "phase": current_phase,
                                "progress": progress_percentage
                            },
                            "actionable": master_flow.flow_status in ["paused", "error"],
                            "page": "discovery" if flow_type == "discovery" else "assessment",
                            "created_at": master_flow.updated_at.isoformat() if master_flow.updated_at else None
                        })
                        
            except Exception as e:
                logger.warning(f"⚠️ Could not get insights from flow persistence data: {e}")
            
            # If no insights found, provide a default message
            if not insights:
                insights.append({
                    "id": f"no-insights-{flow_id}",
                    "agent_id": "system-monitor",
                    "agent_name": "System Monitor",
                    "insight_type": "system_status",
                    "title": "Flow Monitoring Active",
                    "description": f"Flow {flow_id} is being monitored - agents will provide insights as they analyze your data",
                    "confidence": "medium",
                    "supporting_data": {"flow_id": flow_id, "flow_type": flow_type},
                    "actionable": False,
                    "page": "discovery" if flow_type == "discovery" else "assessment",
                    "created_at": datetime.utcnow().isoformat()
                })
            
            logger.info(f"✅ Returning {len(insights)} agent insights for flow {flow_id}")
            return insights
            
        except Exception as e:
            logger.error(f"❌ Error getting agent insights for flow {flow_id}: {e}")
            return []
    
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
                    "updated_at": flow.updated_at.isoformat(),
                    "created_by": getattr(flow, 'created_by', self.context.user_id),
                    "current_phase": getattr(flow, 'current_phase', None),
                    "progress_percentage": getattr(flow, 'progress_percentage', 0.0),
                    "configuration": flow.flow_configuration if hasattr(flow, 'flow_configuration') and flow.flow_configuration else {},
                    "metadata": {}
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
        """Execute a phase through CrewAI by delegating to the actual flow implementation
        
        This method delegates to the actual CrewAI flow implementations based on flow type:
        - "discovery" -> UnifiedDiscoveryFlow (via CrewAIFlowService)
        - "assessment" -> AssessmentFlowService (when available)
        - Other flow types -> Their respective flow service implementations
        """
        logger.info(f"🔄 Executing CrewAI phase: {phase_config.name} for flow type: {master_flow.flow_type}")
        
        try:
            # Delegate based on flow type
            if master_flow.flow_type == "discovery":
                # Use CrewAIFlowService for discovery flows
                from app.services.crewai_flow_service import CrewAIFlowService
                from app.core.database import AsyncSessionLocal
                
                async with AsyncSessionLocal() as db:
                    crewai_service = CrewAIFlowService(db)
                    
                    # Create context from master flow
                    context = {
                        'client_account_id': master_flow.client_account_id,
                        'engagement_id': master_flow.engagement_id,
                        'user_id': master_flow.user_id,
                        'approved_by': master_flow.user_id
                    }
                    
                    # Map phase names to CrewAI flow phases
                    phase_mapping = {
                        "data_import": "data_import_validation",
                        "field_mapping": "field_mapping",
                        "data_cleansing": "data_cleansing",
                        "asset_creation": "asset_inventory",
                        "asset_inventory": "asset_inventory",
                        "dependency_analysis": "dependency_analysis"
                    }
                    
                    crewai_phase = phase_mapping.get(phase_config.name, phase_config.name)
                    
                    # Check if this is a resume from pause (e.g., field mapping approval)
                    if phase_config.name == "field_mapping" and phase_input.get("user_approval"):
                        # Resume flow with approval context
                        resume_context = {
                            **context,
                            'user_approval': phase_input.get("user_approval"),
                            'approval_timestamp': phase_input.get("approval_timestamp", datetime.utcnow().isoformat()),
                            'notes': phase_input.get("notes", "")
                        }
                        
                        result = await crewai_service.resume_flow(
                            flow_id=str(master_flow.flow_id),
                            resume_context=resume_context
                        )
                        
                        logger.info(f"✅ Resumed discovery flow for field mapping approval: {result}")
                        
                        return {
                            "phase": phase_config.name,
                            "status": "completed",
                            "crew_results": result.get("execution_result", {}),
                            "method": "crewai_flow_resume"
                        }
                    else:
                        # For discovery flows created via master orchestrator, ensure CrewAI flow is running
                        logger.info(f"🔄 [FIX] Ensuring CrewAI flow is running for phase execution")
                        
                        # Check if flow exists and is running
                        flow_status = await crewai_service.get_flow_status(
                            flow_id=str(master_flow.flow_id),
                            context=context
                        )
                        
                        if flow_status.get("flow_status") == "not_found" or flow_status.get("current_phase") == "initialization":
                            logger.warning(f"⚠️ [FIX] CrewAI flow not active, need to start it first")
                            
                            # The flow should have been started during create_flow, but if not, we can't
                            # start it here without the raw data. Return error status.
                            if not phase_input or not phase_input.get("raw_data"):
                                return {
                                    "phase": phase_config.name,
                                    "status": "failed",
                                    "error": "CrewAI flow not initialized. Please provide raw_data in phase_input.",
                                    "crew_results": {},
                                    "method": "crewai_flow_not_initialized"
                                }
                            
                            # If we have raw data, create and start the flow
                            from app.services.crewai_flows.unified_discovery_flow import create_unified_discovery_flow
                            from app.core.context import RequestContext
                            
                            discovery_flow = create_unified_discovery_flow(
                                flow_id=str(master_flow.flow_id),
                                client_account_id=master_flow.client_account_id,
                                engagement_id=master_flow.engagement_id,
                                user_id=master_flow.user_id or "system",
                                raw_data=phase_input["raw_data"],
                                metadata={
                                    "source": "master_flow_orchestrator",
                                    "phase": phase_config.name
                                },
                                crewai_service=crewai_service,
                                context=RequestContext(
                                    client_account_id=master_flow.client_account_id,
                                    engagement_id=master_flow.engagement_id,
                                    user_id=master_flow.user_id
                                )
                            )
                            
                            # Start the flow
                            logger.info(f"🚀 [FIX] Starting CrewAI flow kickoff for phase execution")
                            
                            try:
                                import asyncio
                                result = await asyncio.to_thread(discovery_flow.kickoff)
                                logger.info(f"✅ [FIX] CrewAI flow kickoff completed: {result}")
                            except Exception as e:
                                logger.error(f"❌ [FIX] CrewAI flow kickoff failed: {e}")
                                return {
                                    "phase": phase_config.name,
                                    "status": "failed",
                                    "error": str(e),
                                    "crew_results": {},
                                    "method": "crewai_flow_kickoff_failed"
                                }
                        
                        # Now advance to the next phase
                        advance_result = await crewai_service.advance_flow_phase(
                            flow_id=str(master_flow.flow_id),
                            next_phase=crewai_phase,
                            context=context
                        )
                        
                        logger.info(f"✅ Advanced discovery flow to phase {crewai_phase}: {advance_result}")
                        
                        return {
                            "phase": phase_config.name,
                            "status": advance_result.get("status", "completed"),
                            "crew_results": advance_result.get("result", {}),
                            "method": "crewai_flow_advance"
                        }
                        
            elif master_flow.flow_type == "assessment":
                # Use AssessmentFlowService for assessment flows
                logger.info("🎯 Delegating to Assessment Flow Service")
                
                try:
                    from app.services.unified_assessment_flow_service import AssessmentFlowService
                    from app.core.database import AsyncSessionLocal
                    
                    async with AsyncSessionLocal() as db:
                        assessment_service = AssessmentFlowService(db)
                        
                        # Create context from master flow
                        context = RequestContext(
                            client_account_id=master_flow.client_account_id,
                            engagement_id=master_flow.engagement_id,
                            user_id=master_flow.user_id
                        )
                        
                        # Check if this is a resume from pause (user input)
                        if phase_input and phase_input.get("user_input"):
                            logger.info("🔄 Resuming assessment flow with user input")
                            
                            # Resume flow with user input
                            resume_context = {
                                **phase_input,
                                'user_input': phase_input.get("user_input"),
                                'approval_timestamp': phase_input.get("approval_timestamp", datetime.utcnow().isoformat()),
                                'notes': phase_input.get("notes", "")
                            }
                            
                            result = await assessment_service.resume_flow(
                                flow_id=str(master_flow.flow_id),
                                resume_context=resume_context,
                                context=context
                            )
                            
                            logger.info(f"✅ Resumed assessment flow: {result}")
                            
                            return {
                                "phase": phase_config.name,
                                "status": "completed",
                                "crew_results": result,
                                "method": "assessment_flow_resume"
                            }
                        else:
                            # Check if assessment flow exists and is running
                            flow_status = await assessment_service.get_flow_status(
                                flow_id=str(master_flow.flow_id),
                                context=context
                            )
                            
                            if flow_status.get("flow_status") == "not_found":
                                logger.info("🚀 Creating new assessment flow")
                                
                                # Create new assessment flow
                                selected_apps = phase_input.get("selected_application_ids", []) if phase_input else []
                                if not selected_apps:
                                    return {
                                        "phase": phase_config.name,
                                        "status": "failed",
                                        "error": "No selected applications provided for assessment flow",
                                        "crew_results": {},
                                        "method": "assessment_flow_creation_failed"
                                    }
                                
                                creation_result = await assessment_service.create_assessment_flow(
                                    context=context,
                                    selected_application_ids=selected_apps,
                                    flow_name=f"Assessment for Master Flow {master_flow.flow_id}",
                                    configuration=phase_input.get("configuration", {})
                                )
                                
                                logger.info(f"✅ Created assessment flow: {creation_result}")
                                
                                return {
                                    "phase": phase_config.name,
                                    "status": "initialized",
                                    "crew_results": creation_result,
                                    "method": "assessment_flow_created"
                                }
                            else:
                                # Advance to the next phase
                                phase_mapping = {
                                    "readiness_assessment": "architecture_minimums",
                                    "complexity_analysis": "tech_debt_analysis", 
                                    "risk_assessment": "component_sixr_strategies",
                                    "recommendation_generation": "app_on_page_generation"
                                }
                                
                                assessment_phase = phase_mapping.get(phase_config.name, phase_config.name)
                                
                                advance_result = await assessment_service.advance_flow_phase(
                                    flow_id=str(master_flow.flow_id),
                                    next_phase=assessment_phase,
                                    context=context,
                                    phase_input=phase_input
                                )
                                
                                logger.info(f"✅ Advanced assessment flow to phase {assessment_phase}: {advance_result}")
                                
                                return {
                                    "phase": phase_config.name,
                                    "status": advance_result.get("status", "completed"),
                                    "crew_results": advance_result.get("result", {}),
                                    "method": "assessment_flow_advance"
                                }
                                
                except Exception as e:
                    logger.error(f"❌ Assessment flow delegation failed: {e}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    
                    return {
                        "phase": phase_config.name,
                        "status": "failed",
                        "error": str(e),
                        "crew_results": {},
                        "method": "assessment_flow_error"
                    }
                
            else:
                # For other flow types, use placeholder until services are implemented
                logger.warning(f"⚠️ Flow type '{master_flow.flow_type}' delegation not yet implemented")
                
                return {
                    "phase": phase_config.name,
                    "status": "completed",
                    "crew_results": {
                        "message": f"{master_flow.flow_type} flow delegation pending implementation",
                        "flow_type": master_flow.flow_type,
                        "phase": phase_config.name,
                        "phase_input": phase_input
                    },
                    "warning": f"{master_flow.flow_type} flow service not yet implemented"
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to execute crew phase: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Return error result but don't raise - let the orchestrator handle it
            return {
                "phase": phase_config.name,
                "status": "failed",
                "error": str(e),
                "crew_results": {},
                "method": "error_during_delegation"
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