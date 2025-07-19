"""
Flow Execution Engine Initialization Module

Handles flow initialization logic for different flow types.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.context import RequestContext
from app.repositories.crewai_flow_state_extensions_repository import CrewAIFlowStateExtensionsRepository
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState
from app.services.flow_type_registry import FlowTypeRegistry
from app.services.handler_registry import HandlerRegistry
from app.services.validator_registry import ValidatorRegistry

logger = get_logger(__name__)


class FlowInitializer:
    """
    Handles initialization of different flow types.
    """
    
    def __init__(self, 
                 db: AsyncSession,
                 context: RequestContext,
                 master_repo: CrewAIFlowStateExtensionsRepository,
                 flow_registry: FlowTypeRegistry,
                 handler_registry: HandlerRegistry,
                 validator_registry: ValidatorRegistry):
        """Initialize the flow initializer"""
        self.db = db
        self.context = context
        self.master_repo = master_repo
        self.flow_registry = flow_registry
        self.handler_registry = handler_registry
        self.validator_registry = validator_registry
        
        logger.info(f"✅ Flow Initializer ready for client {context.client_account_id}")
    
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
                    # Ensure init_result is JSON serializable
                    await self.master_repo.update_flow_status(
                        flow_id=flow_id,
                        status="initialized",
                        phase_data={"initialization": self._ensure_json_serializable(init_result)}
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
                context=self.context
            )
            
            # Start the discovery flow in background
            await self._start_discovery_flow_background(discovery_flow, flow_id, crewai_service)
            
            return {
                "status": "initialized",
                "flow_type": "discovery",
                "flow_id": flow_id,
                "message": "Discovery flow initialized and started",
                "raw_data_count": len(raw_data)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize discovery flow {flow_id}: {e}")
            raise RuntimeError(f"Discovery flow initialization failed: {str(e)}")
    
    async def _initialize_assessment_flow(
        self,
        flow_id: str,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Initialize assessment flow execution"""
        try:
            logger.info(f"📊 Initializing assessment flow: {flow_id}")
            
            # Assessment flow initialization logic would go here
            # For now, return a placeholder implementation
            
            assessment_config = initial_state.get("assessment_config", {}) if initial_state else {}
            
            # Placeholder initialization
            await asyncio.sleep(0.1)  # Simulate initialization time
            
            return {
                "status": "initialized",
                "flow_type": "assessment",
                "flow_id": flow_id,
                "message": "Assessment flow initialized (placeholder)",
                "assessment_type": assessment_config.get("type", "general"),
                "scope": assessment_config.get("scope", "full")
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize assessment flow {flow_id}: {e}")
            raise RuntimeError(f"Assessment flow initialization failed: {str(e)}")
    
    async def _create_discovery_flow_record(
        self,
        flow_id: str,
        initial_state: Optional[Dict[str, Any]] = None
    ):
        """Create discovery flow record in database"""
        try:
            from app.repositories.unified_discovery_flow_state_repository import UnifiedDiscoveryFlowStateRepository
            
            # Create repository
            discovery_repo = UnifiedDiscoveryFlowStateRepository(self.db)
            
            # Check if record already exists
            existing_record = await discovery_repo.get_by_flow_id(flow_id)
            if existing_record:
                logger.info(f"🔄 Discovery flow record already exists for {flow_id}")
                return
            
            # Create new discovery flow state
            discovery_state = UnifiedDiscoveryFlowState(
                flow_id=flow_id,
                client_account_id=str(self.context.client_account_id) if self.context.client_account_id else "",
                engagement_id=str(self.context.engagement_id) if self.context.engagement_id else "",
                user_id=str(self.context.user_id) if self.context.user_id else "system",
                status="initializing",
                current_phase="initialization",
                raw_data=initial_state.get("raw_data", []) if initial_state else [],
                metadata=initial_state.get("metadata", {}) if initial_state else {},
                initialized_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Save to database
            saved_state = await discovery_repo.create(discovery_state)
            logger.info(f"✅ Created discovery flow record: {saved_state.id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to create discovery flow record: {e}")
            # Don't raise here - initialization can continue without this record
            logger.warning("⚠️ Continuing initialization without discovery flow record")
    
    async def _start_discovery_flow_background(
        self,
        discovery_flow,
        flow_id: str,
        crewai_service
    ):
        """Start discovery flow execution in background"""
        
        async def run_discovery_flow():
            try:
                logger.info(f"🚀 Starting discovery flow execution: {flow_id}")
                
                # Execute the flow (this will run the CrewAI flow)
                flow_result = await discovery_flow.kickoff()
                
                # Update master flow status based on result
                await self._update_discovery_flow_status_from_result(flow_id, flow_result)
                
                logger.info(f"✅ Discovery flow completed: {flow_id}")
                
            except Exception as e:
                logger.error(f"❌ Discovery flow execution failed for {flow_id}: {e}")
                await self._update_discovery_flow_status_failed(flow_id, str(e))
        
        # Start in background - don't await
        asyncio.create_task(run_discovery_flow())
        logger.info(f"🔄 Discovery flow {flow_id} started in background")
    
    async def _update_discovery_flow_status_from_result(
        self,
        flow_id: str,
        flow_result: Dict[str, Any]
    ):
        """Update flow status based on CrewAI flow result"""
        try:
            # Determine status from result
            if flow_result.get("status") == "completed":
                status = "completed"
            elif flow_result.get("status") == "failed":
                status = "failed"
            elif flow_result.get("status") == "paused":
                status = "paused"
            else:
                status = "completed"  # Default assumption
            
            # Extract phase data
            phase_data = {
                "final_result": flow_result,
                "completed_at": datetime.utcnow().isoformat(),
                "execution_method": "crewai_discovery_flow"
            }
            
            # Update master flow
            await self.master_repo.update_flow_status(
                flow_id=flow_id,
                status=status,
                phase_data=phase_data
            )
            
            logger.info(f"✅ Updated flow {flow_id} status to {status}")
            
        except Exception as e:
            logger.error(f"❌ Failed to update flow status for {flow_id}: {e}")
    
    async def _update_discovery_flow_status_failed(
        self,
        flow_id: str,
        error_message: str
    ):
        """Update flow status to failed"""
        try:
            phase_data = {
                "error": error_message,
                "failed_at": datetime.utcnow().isoformat(),
                "execution_method": "crewai_discovery_flow"
            }
            
            await self.master_repo.update_flow_status(
                flow_id=flow_id,
                status="failed",
                phase_data=phase_data
            )
            
            logger.info(f"❌ Updated flow {flow_id} status to failed")
            
        except Exception as e:
            logger.error(f"❌ Failed to update failed status for {flow_id}: {e}")
    
    def _ensure_json_serializable(self, obj: Any) -> Any:
        """
        Ensure object is JSON serializable for database storage
        
        Args:
            obj: Object to make serializable
            
        Returns:
            JSON-serializable version of object
        """
        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._ensure_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._ensure_json_serializable(item) for item in obj]
        else:
            # Convert unknown types to string
            return str(obj)