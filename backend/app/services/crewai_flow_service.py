"""
CrewAI Flow Service - Modular Implementation
Uses existing handlers to support the CrewAI Flow while maintaining proper separation of concerns
Following CrewAI best practices and platform modular handler patterns
"""

import logging
import asyncio
import uuid
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal

# Import handlers with graceful fallback
try:
    from .crewai_flows.handlers.session_handler import SessionHandler
    from .crewai_flows.handlers.status_handler import StatusHandler
    from .crewai_flows.handlers.error_handler import ErrorHandler
    from .crewai_flows.handlers.callback_handler import CallbackHandler
    from .crewai_flows.handlers.planning_coordination_handler import PlanningCoordinationHandler
    from .crewai_flows.handlers.learning_management_handler import LearningManagementHandler
    from .crewai_flows.handlers.collaboration_tracking_handler import CollaborationTrackingHandler
    from .crewai_flows.handlers.initialization_handler import InitializationHandler
    HANDLERS_AVAILABLE = True
except ImportError:
    HANDLERS_AVAILABLE = False

# Import CrewAI Flow with graceful fallback
try:
    from .crewai_flows.unified_discovery_flow import UnifiedDiscoveryFlow, create_unified_discovery_flow
    CREWAI_FLOW_AVAILABLE = True
except ImportError:
    CREWAI_FLOW_AVAILABLE = False

# OpenLIT observability for CrewAI agents
try:
    import openlit
    openlit.init(
        otlp_endpoint="http://127.0.0.1:4318",
        disable_metrics=True
    )
    OPENLIT_AVAILABLE = True
    logging.info("✅ OpenLIT observability initialized for CrewAI agents")
except ImportError:
    OPENLIT_AVAILABLE = False
    logging.warning("⚠️ OpenLIT not available - agent observability limited")

logger = logging.getLogger(__name__)

class CrewAIFlowService:
    """
    Modular CrewAI Flow Service for Discovery Workflows
    
    Provides a unified interface for CrewAI-powered discovery workflows with:
    - Modular handler architecture for maintainability
    - Graceful fallback when CrewAI Flow is not available
    - V2 Discovery Flow architecture support
    """
    
    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        
        # V2 Discovery Flow architecture - no workflow state service needed
        logger.info("✅ Using V2 Discovery Flow state management")
        
        self.service_available = CREWAI_FLOW_AVAILABLE
        
        # Active flows tracking
        self._active_flows: Dict[str, UnifiedDiscoveryFlow] = {}
        self._flow_creation_lock = asyncio.Lock()
        self._flow_registry: Dict[str, Dict[str, Any]] = {}
        
        # Initialize modular handlers
        self._initialize_handlers()
        
        # Initialize agents using existing logic
        self.agents = self._initialize_agents()
        
        logger.info("✅ Modular CrewAI Flow Service initialized with V2 architecture")
        if not self.service_available:
            logger.warning("⚠️ CrewAI Flow not available - using fallback mode")
    
    def _initialize_handlers(self):
        """Initialize all modular handlers"""
        if not HANDLERS_AVAILABLE:
            logger.warning("⚠️ Handlers not available - using minimal functionality")
            return
            
        # Core handlers
        self.session_handler = SessionHandler()
        self.status_handler = StatusHandler()
        self.error_handler = ErrorHandler()
        self.callback_handler = CallbackHandler()
        
        # Advanced handlers
        self.planning_handler = PlanningCoordinationHandler(self)
        self.learning_handler = LearningManagementHandler(self)
        self.collaboration_handler = CollaborationTrackingHandler(self)
        
        # Setup handler components
        self.session_handler.setup_database_sessions()
        self.callback_handler.setup_callbacks()
        self.planning_handler.setup_planning_components()
        
        logger.info("✅ All modular handlers initialized")
    
    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize CrewAI crews for enhanced discovery workflows"""
        agents = {}
        
        try:
            # Import CrewAI crew factory functions (but don't initialize yet)
            # Crews will be created on-demand during flow execution with proper parameters
            from app.services.crewai_flows.crews.inventory_building_crew import create_inventory_building_crew
            from app.services.crewai_flows.crews.field_mapping_crew import create_field_mapping_crew
            from app.services.crewai_flows.crews.app_server_dependency_crew import create_app_server_dependency_crew
            from app.services.crewai_flows.crews.data_cleansing_crew import create_data_cleansing_crew
            
            # Store crew factory functions for on-demand creation
            agents['inventory_building_factory'] = create_inventory_building_crew
            agents['field_mapping_factory'] = create_field_mapping_crew
            agents['dependency_analysis_factory'] = create_app_server_dependency_crew
            agents['data_cleansing_factory'] = create_data_cleansing_crew
            
            logger.info(f"✅ Initialized {len(agents)} CrewAI Crew factories for discovery workflows")
            
        except ImportError as e:
            logger.warning(f"CrewAI crew factories not available: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize CrewAI crew factories: {e}")
        
        return agents
    
    async def initiate_discovery_workflow(
        self,
        data_source: Dict[str, Any],
        context: RequestContext
    ) -> Dict[str, Any]:
        """
        Initiate a discovery workflow using modular handlers and CrewAI Flow
        """
        logger.info(f"🚀 Initiating discovery workflow with session: {context.session_id}")
        
        # Validate database availability
        if not self.db:
            return {
                "status": "error",
                "message": "Database not available for workflow state management"
            }
        
        try:
            # Parse and validate input data
            parsed_data = self._parse_input_data(data_source)
            metadata = data_source.get("metadata", {})
            cmdb_data = {"file_data": parsed_data, "metadata": metadata}
            
            # Validate context
            session_id, validated_context = self._validate_context(context)
            
            # Ensure data import session exists
            await self._ensure_data_import_session_exists(
                session_id, validated_context, metadata
            )
            
            # Use initialization handler to setup flow
            if HANDLERS_AVAILABLE:
                initialization_handler = InitializationHandler(self, validated_context)
                flow_id = initialization_handler.setup_flow_id(
                    session_id, 
                    validated_context.client_account_id,
                    validated_context.engagement_id,
                    parsed_data
                )
            else:
                flow_id = str(uuid.uuid4())
            
            # Create and execute the CrewAI Flow
            flow = await self._create_and_execute_flow(
                session_id, validated_context, cmdb_data, metadata, flow_id
            )
            
            # Track active flow
            self._active_flows[flow_id] = flow
            
            # Return status using status handler
            return {
                "status": "success",
                "message": "Discovery workflow initiated successfully",
                "session_id": session_id,
                "flow_id": flow_id,
                "workflow_status": "running",
                "current_phase": "initialization"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to initiate discovery workflow: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _parse_input_data(self, data_source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse and validate input data"""
        file_data = data_source.get("file_data")
        if not file_data:
            raise ValueError("file_data is required for analysis")
        
        if isinstance(file_data, str):
            try:
                if file_data.strip().startswith('['):
                    return json.loads(file_data)
                else:
                    # Handle base64 encoded CSV
                    import base64
                    import csv
                    import io
                    decoded = base64.b64decode(file_data).decode('utf-8')
                    string_io = io.StringIO(decoded)
                    return list(csv.DictReader(string_io))
            except Exception as e:
                raise ValueError(f"Invalid file_data format: {str(e)}")
        elif isinstance(file_data, list):
            return file_data
        else:
            raise ValueError("file_data must be a list or string")
    
    def _validate_context(self, context: RequestContext) -> tuple[str, RequestContext]:
        """Validate and normalize context"""
        session_id = context.session_id or str(uuid.uuid4())
        
        if not context.client_account_id or not context.engagement_id:
            raise ValueError(f"Missing required context: client_account_id={context.client_account_id}, engagement_id={context.engagement_id}")
        
        # Validate UUID formats
        try:
            client_account_uuid = uuid.UUID(context.client_account_id)
            engagement_uuid = uuid.UUID(context.engagement_id)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid UUID format in context: {e}")
        
        # Update context with validated UUIDs
        context.client_account_id = str(client_account_uuid)
        context.engagement_id = str(engagement_uuid)
        
        return session_id, context
    
    async def _create_and_execute_flow(
        self,
        session_id: str,
        context: RequestContext,
        cmdb_data: Dict[str, Any],
        metadata: Dict[str, Any],
        flow_id: str
    ) -> UnifiedDiscoveryFlow:
        """Create and execute the CrewAI Flow"""
        async with self._flow_creation_lock:
            # Create the CrewAI Flow using proper factory function
            if CREWAI_FLOW_AVAILABLE:
                flow = create_unified_discovery_flow(
                    session_id=session_id,
                    client_account_id=context.client_account_id,
                    engagement_id=context.engagement_id,
                    user_id=context.user_id or "anonymous",
                    raw_data=cmdb_data.get("file_data", []),
                    metadata=metadata,
                    crewai_service=self,
                    context=context
                )
                
                # Execute in background (non-blocking)
                asyncio.create_task(self._run_workflow_background(flow, context))
                
                return flow
            else:
                # Fallback for when CrewAI Flow is not available
                logger.warning("⚠️ CrewAI Flow not available - using fallback")
                return None
    
    async def _run_workflow_background(self, flow: UnifiedDiscoveryFlow, context: RequestContext):
        """Run workflow in background with proper error handling"""
        try:
            logger.info(f"🚀 Starting CrewAI Flow execution for session: {flow.state.session_id}")
            
            # Execute the CrewAI Flow (this triggers @start and @listen methods)
            result = flow.kickoff()
            
            logger.info(f"✅ CrewAI Flow completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"❌ CrewAI Flow execution failed: {e}")
            # V2 Discovery Flow architecture - no workflow state service needed
            logger.error(f"Error that would have been recorded: {e}")
    
    # Delegation methods to handlers
    
    async def get_flow_state_by_session(self, session_id: str, context: RequestContext) -> Optional[Dict[str, Any]]:
        """Get flow state using status handler"""
        if session_id in self._active_flows:
            flow = self._active_flows[session_id]
            if HANDLERS_AVAILABLE:
                return self.status_handler.get_current_status(flow.state, {})
            else:
                return {"session_id": session_id, "status": "running"}
        
        # V2 Discovery Flow architecture - use V2 API instead
        logger.warning("⚠️ Flow state lookup - use V2 Discovery Flow API")
        return None
    
    def get_active_flows(self, context: Optional[RequestContext] = None) -> List[Dict[str, Any]]:
        """Get summary of active flows"""
        flows = []
        for flow_id, flow in self._active_flows.items():
            flows.append({
                "flow_id": flow_id,
                "session_id": getattr(flow.state, 'session_id', 'unknown'),
                "status": getattr(flow.state, 'status', 'unknown'),
                "current_phase": getattr(flow.state, 'current_phase', 'unknown')
            })
        return flows
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get service health status"""
        return {
            "service_name": "CrewAI Flow Service",
            "status": "healthy" if self.service_available else "degraded",
            "active_flows": len(self._active_flows),
            "features": {
                "crewai_flow": self.service_available,
                "handlers": HANDLERS_AVAILABLE,
                "v2_architecture": True
            }
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {"active_flows": len(self._active_flows), "registry_size": len(self._flow_registry)}
    
    def cleanup_resources(self) -> Dict[str, Any]:
        """Clean up service resources"""
        cleaned_flows = len(self._active_flows)
        self._active_flows.clear()
        self._flow_registry.clear()
        
        return {
            "cleaned_flows": cleaned_flows,
            "status": "cleanup_completed",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def generate_flow_id(self, flow_type: str, session_id: str, 
                        client_account_id: str, engagement_id: str) -> str:
        """Generate unique flow ID"""
        base_id = f"{flow_type}_{session_id}_{client_account_id}_{engagement_id}"
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, base_id))
    
    def register_flow(self, flow_id: str, flow_type: str, metadata: Dict[str, Any]):
        """Register flow in registry"""
        self._flow_registry[flow_id] = {
            "flow_type": flow_type,
            "metadata": metadata,
            "created_at": datetime.utcnow().isoformat()
        }
    
    def get_flow_info(self, flow_id: str) -> Dict[str, Any]:
        """Get flow information from registry"""
        return self._flow_registry.get(flow_id, {})
    
    async def _ensure_data_import_session_exists(
        self, 
        session_id: str, 
        context: RequestContext, 
        metadata: Dict[str, Any]
    ):
        """Ensure data import session exists - simplified for V2 architecture"""
        # V2 Discovery Flow architecture - simplified session management
        logger.info(f"✅ Session management simplified for V2 architecture: {session_id}")


def create_crewai_flow_service(db: AsyncSession) -> CrewAIFlowService:
    """Factory function to create CrewAI Flow Service"""
    return CrewAIFlowService(db)

def get_crewai_flow_service() -> CrewAIFlowService:
    """Get CrewAI Flow Service instance"""
    return CrewAIFlowService() 