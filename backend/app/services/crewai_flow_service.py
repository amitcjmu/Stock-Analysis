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
from app.services.crewai_flows.discovery_flow import (
    create_discovery_flow,
    DiscoveryFlow,
    DiscoveryFlowState,
    CREWAI_FLOW_AVAILABLE
)

# Import existing handlers
from app.services.crewai_flows.handlers.initialization_handler import InitializationHandler
from app.services.crewai_flows.handlers.session_handler import SessionHandler
from app.services.crewai_flows.handlers.status_handler import StatusHandler
from app.services.crewai_flows.handlers.error_handler import ErrorHandler
from app.services.crewai_flows.handlers.callback_handler import CallbackHandler
from app.services.crewai_flows.handlers.planning_coordination_handler import PlanningCoordinationHandler
from app.services.crewai_flows.handlers.learning_management_handler import LearningManagementHandler
from app.services.crewai_flows.handlers.collaboration_tracking_handler import CollaborationTrackingHandler

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
    Modular CrewAI Flow Service using existing handlers.
    
    This service orchestrates the CrewAI Flow while delegating specific
    responsibilities to specialized handlers following the platform's
    modular handler pattern.
    """
    
    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        
        # Initialize state service if database is available
        if db:
            from app.services.workflow_state_service import WorkflowStateService
            self.state_service = WorkflowStateService(self.db)
        else:
            self.state_service = None
        
        self.service_available = CREWAI_FLOW_AVAILABLE
        
        # Active flows tracking
        self._active_flows: Dict[str, DiscoveryFlow] = {}
        self._flow_creation_lock = asyncio.Lock()
        self._flow_registry: Dict[str, Dict[str, Any]] = {}
        
        # Initialize modular handlers
        self._initialize_handlers()
        
        # Initialize agents using existing logic
        self.agents = self._initialize_agents()
        
        logger.info("✅ Modular CrewAI Flow Service initialized with existing handlers")
        if not self.service_available:
            logger.warning("⚠️ CrewAI Flow not available - using fallback mode")
    
    def _initialize_handlers(self):
        """Initialize all modular handlers"""
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
        if not self.db or not self.state_service:
            return self.error_handler.handle_crew_error(
                "initialization", 
                Exception("Database not available for workflow state management"),
                None
            )
        
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
            initialization_handler = InitializationHandler(self, validated_context)
            flow_id = initialization_handler.setup_flow_id(
                session_id, 
                validated_context.client_account_id,
                validated_context.engagement_id,
                parsed_data
            )
            
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
            return self.error_handler.handle_crew_error("initialization", e, None)
    
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
    ) -> DiscoveryFlow:
        """Create and execute the CrewAI Flow"""
        async with self._flow_creation_lock:
            # Create the CrewAI Flow using proper factory function
            flow = create_discovery_flow(
                session_id=session_id,
                client_account_id=context.client_account_id,
                engagement_id=context.engagement_id,
                user_id=context.user_id or "anonymous",
                cmdb_data=cmdb_data,
                metadata=metadata,
                crewai_service=self,
                context=context
            )
            
            # Execute flow in background using session handler
            await self.session_handler.execute_with_session(
                "discovery_flow",
                lambda session: self._run_workflow_background(flow, context)
            )
            
            return flow
    
    async def _run_workflow_background(self, flow: DiscoveryFlow, context: RequestContext):
        """Run workflow in background with proper error handling"""
        try:
            logger.info(f"🚀 Starting CrewAI Flow execution for session: {flow.state.session_id}")
            
            # Execute the CrewAI Flow (this triggers @start and @listen methods)
            result = flow.kickoff()
            
            logger.info(f"✅ CrewAI Flow completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"❌ CrewAI Flow execution failed: {e}")
            error_result = self.error_handler.handle_crew_error("flow_execution", e, flow.state)
            
            # Update workflow state with error
            if self.state_service:
                await self._update_workflow_state_with_error(flow.state.session_id, str(e))
            
            return error_result
    
    # Delegation methods to handlers
    
    async def get_flow_state_by_session(self, session_id: str, context: RequestContext) -> Optional[Dict[str, Any]]:
        """Get flow state using status handler"""
        if session_id in self._active_flows:
            flow = self._active_flows[session_id]
            return self.status_handler.get_current_status(flow.state, {})
        
        # Fallback to database lookup
        if self.state_service:
            return await self.state_service.get_workflow_state(session_id)
        
        return None
    
    def get_active_flows(self, context: Optional[RequestContext] = None) -> List[Dict[str, Any]]:
        """Get active flows using status handler"""
        active_flows = []
        for flow_id, flow in self._active_flows.items():
            flow_status = self.status_handler.get_current_status(flow.state, {})
            active_flows.append({
                "flow_id": flow_id,
                "session_id": flow.state.session_id,
                "status": flow_status,
                "created_at": flow.state.created_at
            })
        return active_flows
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get service health status"""
        return {
            "service_available": self.service_available,
            "active_flows": len(self._active_flows),
            "database_available": self.db is not None,
            "handlers_initialized": True,
            "session_handler_status": self.session_handler.get_session_status(),
            "error_summary": self.error_handler.get_error_summary()
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics using callback handler"""
        return self.callback_handler.get_callback_metrics()
    
    def cleanup_resources(self) -> Dict[str, Any]:
        """Cleanup resources using session handler"""
        cleanup_count = len(self._active_flows)
        self._active_flows.clear()
        
        # Cleanup sessions
        asyncio.create_task(self.session_handler.cleanup_all_sessions())
        
        return {
            "cleaned_flows": cleanup_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Flow ID management
    
    def generate_flow_id(self, flow_type: str, session_id: str, 
                        client_account_id: str, engagement_id: str) -> str:
        """Generate unique flow ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        short_uuid = str(uuid.uuid4())[:8]
        return f"{flow_type}_{timestamp}_{short_uuid}"
    
    def register_flow(self, flow_id: str, flow_type: str, metadata: Dict[str, Any]):
        """Register flow in registry"""
        self._flow_registry[flow_id] = {
            "flow_type": flow_type,
            "metadata": metadata,
            "registered_at": datetime.utcnow().isoformat()
        }
    
    def get_flow_info(self, flow_id: str) -> Dict[str, Any]:
        """Get flow information"""
        return self._flow_registry.get(flow_id, {})
    
    # Helper methods
    
    async def _ensure_data_import_session_exists(
        self, 
        session_id: str, 
        context: RequestContext, 
        metadata: Dict[str, Any]
    ):
        """Ensure data import session exists to satisfy foreign key constraints"""
        try:
            from app.models.data_import_session import DataImportSession
            from app.core.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as db_session:
                # Check if session already exists
                existing_session = await db_session.get(DataImportSession, session_id)
                
                if not existing_session:
                    # Create new session
                    new_session = DataImportSession(
                        id=session_id,
                        client_account_id=uuid.UUID(context.client_account_id),
                        engagement_id=uuid.UUID(context.engagement_id),
                        user_id=uuid.UUID(context.user_id) if context.user_id != "anonymous" else None,
                        session_metadata=metadata,
                        created_at=datetime.utcnow()
                    )
                    
                    db_session.add(new_session)
                    await db_session.commit()
                    logger.info(f"✅ Created data import session: {session_id}")
                else:
                    logger.info(f"✅ Data import session already exists: {session_id}")
                    
        except Exception as e:
            logger.error(f"❌ Failed to ensure data import session exists: {e}")
            raise
    
    async def _update_workflow_state_with_error(self, session_id: str, error: str):
        """Update workflow state with error information"""
        if self.state_service:
            try:
                await self.state_service.update_workflow_state(
                    session_id=session_id,
                    status="failed",
                    current_phase="error",
                    state_data={"error": error, "timestamp": datetime.utcnow().isoformat()}
                )
            except Exception as e:
                logger.error(f"Failed to update workflow state with error: {e}")


def create_crewai_flow_service(db: AsyncSession) -> CrewAIFlowService:
    """Factory function to create CrewAI Flow Service"""
    return CrewAIFlowService(db)


def get_crewai_flow_service() -> CrewAIFlowService:
    """Dependency injection for FastAPI"""
    from app.core.database import AsyncSessionLocal
    return CrewAIFlowService(AsyncSessionLocal) 