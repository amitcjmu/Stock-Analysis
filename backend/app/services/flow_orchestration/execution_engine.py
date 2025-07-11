"""
Flow Execution Engine

Handles phase execution logic, CrewAI flow delegation, and execution orchestration.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.exceptions import FlowNotFoundError, InvalidFlowStateError
from app.core.context import RequestContext
from app.repositories.crewai_flow_state_extensions_repository import CrewAIFlowStateExtensionsRepository
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.services.flow_type_registry import FlowTypeRegistry
from app.services.handler_registry import HandlerRegistry
from app.services.validator_registry import ValidatorRegistry, ValidationResult

logger = get_logger(__name__)


class FlowExecutionEngine:
    """
    Handles the execution of flow phases and delegation to CrewAI flows.
    """
    
    def __init__(self, 
                 db: AsyncSession,
                 context: RequestContext,
                 master_repo: CrewAIFlowStateExtensionsRepository,
                 flow_registry: FlowTypeRegistry,
                 handler_registry: HandlerRegistry,
                 validator_registry: ValidatorRegistry):
        """
        Initialize the Flow Execution Engine
        
        Args:
            db: Database session
            context: Request context
            master_repo: Repository for master flow operations
            flow_registry: Registry for flow type configurations
            handler_registry: Registry for flow handlers
            validator_registry: Registry for flow validators
        """
        self.db = db
        self.context = context
        self.master_repo = master_repo
        self.flow_registry = flow_registry
        self.handler_registry = handler_registry
        self.validator_registry = validator_registry
        
        logger.info(f"✅ Flow Execution Engine initialized for client {context.client_account_id}")
    
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
            
            logger.info(f"✅ Executed phase '{phase_name}' for flow {flow_id}")
            
            return {
                "phase": phase_name,
                "status": "completed",
                "execution_time_ms": execution_time,
                "results": crew_result
            }
            
        except Exception as e:
            logger.error(f"❌ Phase execution failed for {flow_id}, phase {phase_name}: {e}")
            
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
            
            raise RuntimeError(f"Phase execution failed: {str(e)}")
    
    async def initialize_flow_execution(
        self,
        flow_id: str,
        flow_type: str,
        configuration: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Initialize flow execution for specific flow types
        
        Args:
            flow_id: Flow identifier
            flow_type: Type of flow to initialize
            configuration: Flow configuration
            initial_state: Initial state data
            
        Returns:
            Initialization result
        """
        try:
            logger.info(f"🚀 Initializing flow execution for {flow_type} flow: {flow_id}")
            
            # Get flow configuration
            flow_config = self.flow_registry.get_flow_config(flow_type)
            
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
                    
                    return init_result
            
            # Handle specific flow types
            if flow_type == "discovery":
                return await self._initialize_discovery_flow(flow_id, initial_state)
            elif flow_type == "assessment":
                return await self._initialize_assessment_flow(flow_id, initial_state)
            else:
                logger.warning(f"⚠️ No specific initialization for flow type: {flow_type}")
                return {"status": "initialized", "message": f"Generic initialization for {flow_type} flow"}
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize flow execution for {flow_id}: {e}")
            raise RuntimeError(f"Flow initialization failed: {str(e)}")
    
    async def _initialize_discovery_flow(
        self,
        flow_id: str,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Initialize discovery flow execution"""
        try:
            logger.info(f"🔍 Initializing discovery flow: {flow_id}")
            
            # Import discovery flow components
            from app.services.crewai_flow_service import CrewAIFlowService
            from app.services.crewai_flows.unified_discovery_flow import create_unified_discovery_flow
            
            # Create CrewAI service
            crewai_service = CrewAIFlowService(self.db)
            
            # Prepare raw data from initial state
            raw_data = initial_state.get("raw_data", []) if initial_state else []
            
            # Create discovery flow record with proper master flow linkage
            await self._create_discovery_flow_record(flow_id, initial_state)
            
            # Create the UnifiedDiscoveryFlow instance
            flow_metadata = initial_state or {}
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
                master_flow_id=flow_id
            )
            
            # Start the flow execution in background
            await self._start_discovery_flow_background(flow_id, discovery_flow)
            
            return {
                "status": "initialized",
                "flow_type": "discovery",
                "kickoff_initiated": True
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize discovery flow {flow_id}: {e}")
            raise
    
    async def _initialize_assessment_flow(
        self,
        flow_id: str,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Initialize assessment flow execution"""
        try:
            logger.info(f"📊 Initializing assessment flow: {flow_id}")
            
            # Import assessment flow components
            from app.services.unified_assessment_flow_service import AssessmentFlowService
            from app.core.database import AsyncSessionLocal
            
            # Create Assessment service
            async with AsyncSessionLocal() as db:
                assessment_service = AssessmentFlowService(db)
                
                # Get selected applications from initial state
                selected_apps = initial_state.get("selected_application_ids", []) if initial_state else []
                if not selected_apps:
                    logger.warning(f"⚠️ No selected applications provided for assessment flow {flow_id}")
                    selected_apps = []
                
                # Create the assessment flow
                assessment_result = await assessment_service.create_assessment_flow(
                    context=self.context,
                    selected_application_ids=selected_apps,
                    flow_name=f"Assessment Flow {flow_id}",
                    configuration=initial_state.get("configuration", {}) if initial_state else {}
                )
                
                logger.info(f"✅ Assessment flow created: {assessment_result}")
                
                return {
                    "status": "initialized",
                    "flow_type": "assessment",
                    "assessment_creation": assessment_result
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize assessment flow {flow_id}: {e}")
            raise
    
    async def _create_discovery_flow_record(
        self,
        flow_id: str,
        initial_state: Optional[Dict[str, Any]] = None
    ):
        """Create DiscoveryFlow record with proper master flow linkage"""
        try:
            from app.models.discovery_flow import DiscoveryFlow
            from sqlalchemy import select
            
            # Create savepoint for DiscoveryFlow operations
            discovery_savepoint = await self.db.begin_nested()
            
            try:
                # Check if DiscoveryFlow already exists for this flow_id
                existing_discovery_query = select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_id)
                existing_discovery_result = await self.db.execute(existing_discovery_query)
                existing_discovery = existing_discovery_result.scalar_one_or_none()
                
                if not existing_discovery:
                    # Create DiscoveryFlow record with master flow linkage
                    import uuid
                    discovery_flow_record = DiscoveryFlow(
                        flow_id=flow_id,
                        flow_name=f"Discovery Flow {flow_id}",
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
                await discovery_savepoint.rollback()
                raise
                
        except Exception as e:
            logger.error(f"❌ Failed to create discovery flow record: {e}")
            # Don't fail the entire flow creation, just log the error
    
    async def _start_discovery_flow_background(
        self,
        flow_id: str,
        discovery_flow
    ):
        """Start discovery flow execution in background"""
        async def run_discovery_flow():
            try:
                logger.info(f"🎯 Starting CrewAI Discovery Flow kickoff for {flow_id}")
                
                # Use a fresh database session for the background task
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
                    
                    # First update status to processing
                    await fresh_repo.update_flow_status(
                        flow_id=flow_id,
                        status="processing",
                        phase_data={"message": "CrewAI flow kickoff starting"}
                    )
                
                # CrewAI Flow kickoff() is synchronous, so run it in a thread
                logger.info(f"🚀 Calling discovery_flow.kickoff() in thread...")
                result = await asyncio.to_thread(discovery_flow.kickoff)
                logger.info(f"✅ CrewAI Discovery Flow kickoff returned: {result}")
                
                # Update flow status based on result
                await self._update_discovery_flow_status_from_result(flow_id, result)
                
            except Exception as e:
                logger.error(f"❌ CrewAI Discovery Flow execution failed: {e}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                
                # Update flow status to failed
                await self._update_discovery_flow_status_failed(flow_id, e)
        
        # Create the task but don't await it - let it run in background
        task = asyncio.create_task(run_discovery_flow())
        
        # Store task reference to prevent garbage collection
        if not hasattr(self, '_active_flow_tasks'):
            self._active_flow_tasks = {}
        self._active_flow_tasks[flow_id] = task
        
        logger.info(f"🚀 CrewAI Discovery Flow task created and running in background")
    
    async def _update_discovery_flow_status_from_result(
        self,
        flow_id: str,
        result: str
    ):
        """Update discovery flow status based on kickoff result"""
        try:
            from app.core.database import AsyncSessionLocal
            from app.repositories.crewai_flow_state_extensions_repository import CrewAIFlowStateExtensionsRepository
            
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
                    logger.info(f"✅ Flow paused for user approval, setting status: {flow_status}")
                    phase_data = {
                        "completion": result,
                        "current_phase": "attribute_mapping",
                        "progress_percentage": 60.0,
                        "paused_at": datetime.utcnow().isoformat(),
                        "awaiting_user_approval": True
                    }
                elif result in ["discovery_completed"]:
                    flow_status = "completed"
                    logger.info(f"✅ Flow completed successfully, setting status: {flow_status}")
                    phase_data = {
                        "completion": result,
                        "current_phase": "completed",
                        "progress_percentage": 100.0,
                        "completed_at": datetime.utcnow().isoformat()
                    }
                elif result in ["discovery_failed"]:
                    flow_status = "failed"
                    logger.info(f"❌ Flow failed, setting status: {flow_status}")
                    phase_data = {
                        "completion": result,
                        "current_phase": "failed",
                        "progress_percentage": 0.0,
                        "failed_at": datetime.utcnow().isoformat()
                    }
                else:
                    # Default to processing for other results
                    flow_status = "processing"
                    logger.info(f"🔄 Flow result '{result}', setting status: {flow_status}")
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
            logger.error(f"❌ Failed to update flow status from result: {e}")
    
    async def _update_discovery_flow_status_failed(
        self,
        flow_id: str,
        error: Exception
    ):
        """Update discovery flow status to failed"""
        try:
            from app.core.database import AsyncSessionLocal
            from app.repositories.crewai_flow_state_extensions_repository import CrewAIFlowStateExtensionsRepository
            
            async with AsyncSessionLocal() as fresh_db:
                fresh_repo = CrewAIFlowStateExtensionsRepository(
                    fresh_db, 
                    self.context.client_account_id,
                    self.context.engagement_id,
                    self.context.user_id
                )
                
                import traceback
                await fresh_repo.update_flow_status(
                    flow_id=flow_id,
                    status="failed",
                    phase_data={"error": str(error), "traceback": traceback.format_exc()}
                )
                
        except Exception as update_error:
            logger.error(f"❌ Failed to update flow status to failed: {update_error}")
    
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
                
                # Handle ValidationResult dataclass or dict response
                if isinstance(result, ValidationResult):
                    # ValidationResult dataclass - use attribute access
                    if not result.valid:
                        validation_results["valid"] = False
                        validation_results["errors"].extend(result.errors or [])
                    
                    validation_results["warnings"].extend(result.warnings or [])
                else:
                    # Legacy dict response - use dictionary access
                    if not result.get("valid", True):
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
        """Execute a phase through CrewAI by delegating to the actual flow implementation"""
        logger.info(f"🔄 Executing CrewAI phase: {phase_config.name} for flow type: {master_flow.flow_type}")
        
        try:
            # Delegate based on flow type
            if master_flow.flow_type == "discovery":
                return await self._execute_discovery_phase(master_flow, phase_config, phase_input)
            elif master_flow.flow_type == "assessment":
                return await self._execute_assessment_phase(master_flow, phase_config, phase_input)
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
    
    async def _execute_discovery_phase(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_config,
        phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute discovery flow phase"""
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
                # Advance to the next phase
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
    
    async def _execute_assessment_phase(
        self,
        master_flow: CrewAIFlowStateExtensions,
        phase_config,
        phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute assessment flow phase"""
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
            
            # Map phase names to assessment flow phases
            phase_mapping = {
                "readiness_assessment": "architecture_minimums",
                "complexity_analysis": "tech_debt_analysis", 
                "risk_assessment": "component_sixr_strategies",
                "recommendation_generation": "app_on_page_generation"
            }
            
            assessment_phase = phase_mapping.get(phase_config.name, phase_config.name)
            
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
                # Advance to the next phase
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