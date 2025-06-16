"""
Main service for orchestrating CrewAI agentic flows.
This service acts as a core registry for agents and LLM configurations.
"""

import logging
import asyncio
import uuid
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import base64
import csv
import io
import os
from sqlalchemy.ext.asyncio import AsyncSession

# Pydantic and Core Components
from pydantic import BaseModel, Field, ValidationError
from app.core.config import settings
from app.core.context import RequestContext, get_current_context
from app.services.llm_usage_tracker import LLMUsageTracker
from app.schemas.flow_schemas import DiscoveryFlowState

# Conditional import for LangChain components
try:
    import langchain_openai
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

# Conditional import for CrewAI
try:
    import crewai
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False

# Conditional import for LiteLLM
try:
    import litellm
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False

# Local Imports
from app.services.crewai_flow_handlers.discovery_handlers.discovery_workflow_manager import DiscoveryWorkflowManager

logger = logging.getLogger(__name__)

class MockAgent:
    """Mock agent for when CrewAI is not available."""
    def __init__(self, role: str, goal: str):
        self.role = role
        self.goal = goal
        self.backstory = "Mock agent for testing"
        
    def __str__(self):
        return f"MockAgent({self.role})"

class CrewAIFlowService:
    """A stateful service registry for core CrewAI components and active flows."""
    
    def __init__(self, db: AsyncSession):
        from app.services.workflow_state_service import WorkflowStateService
        
        # Initialize service state
        self.db = db
        self.state_service = WorkflowStateService(self.db)
        self.service_available = LANGCHAIN_AVAILABLE and CREWAI_AVAILABLE and LITELLM_AVAILABLE
        
        # Agent lifecycle management
        self._agents_initialized = False
        self._agent_creation_lock = asyncio.Lock()
        self._active_tasks = {}
        self._task_timeouts = {}
        
        # LLM and agent initialization
        self.llm = None
        if self.service_available:
            # Configure LLM for DeepInfra
            self.llm = langchain_openai.ChatOpenAI(
                api_key=os.getenv("DEEPINFRA_API_KEY"),
                base_url="https://api.deepinfra.com/v1/openai/chat/completions",
                model_name="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
                temperature=0.1,
                max_tokens=4096
            )

        self.settings = settings
        self.agents = self._initialize_agents() if self.llm else {}
        
        # Initialize the workflow manager AFTER agents are initialized
        self.manager = DiscoveryWorkflowManager(self)
        self.initialized = True

        logger.info("Initializing CrewAIFlowService...")
        
        if self.service_available:
            logger.info("CrewAIFlowService initialized successfully with state management.")
        else:
            logger.warning("CrewAI Flow Service running in limited capacity due to missing configuration.")

    def _initialize_agents(self):
        """Initialize agents only once to prevent creation loops."""
        if self._agents_initialized:
            logger.info("Agents already initialized, returning existing agents.")
            return self.agents
            
        agents = {
            'data_validator': self._create_agent("Data Quality Analyst", "Ensures data quality and consistency."),
            'field_mapper': self._create_agent("Field Mapping Specialist", "Maps source data fields to the target schema."),
            'asset_classifier': self._create_agent("Asset Classification Expert", "Classifies assets and suggests 6R strategies."),
            'dependency_analyzer': self._create_agent("Dependency Analysis Specialist", "Identifies relationships between assets."),
        }
        
        self._agents_initialized = True
        logger.info(f"Created {len(agents)} specialized agents.")
        return agents

    def _create_agent(self, role: str, goal: str) -> 'crewai.Agent':
        """Create a single agent with timeout and error handling."""
        if not CREWAI_AVAILABLE:
            logger.warning(f"CrewAI not available, creating mock agent for {role}")
            return MockAgent(role=role, goal=goal)
            
        return crewai.Agent(
            role=role,
            goal=goal,
            backstory="An expert in cloud migration planning.",
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_execution_time=300  # 5 minute timeout per agent
        )

    async def run_crew_with_timeout(self, crew, timeout_seconds: int = 300) -> Any:
        """Run crew with timeout to prevent hanging."""
        try:
            # Create a task with timeout
            task = asyncio.create_task(
                asyncio.to_thread(crew.kickoff)
            )
            
            # Wait for completion or timeout
            result = await asyncio.wait_for(task, timeout=timeout_seconds)
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Crew execution timed out after {timeout_seconds} seconds")
            # Cancel the task
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            raise Exception(f"Agent processing timed out after {timeout_seconds} seconds")
        except Exception as e:
            logger.error(f"Crew execution failed: {e}")
            raise

    async def cleanup_stuck_tasks(self):
        """Clean up any stuck or hanging tasks."""
        current_time = datetime.now()
        stuck_tasks = []
        
        for task_id, task_info in self._active_tasks.items():
            if current_time - task_info['start_time'] > timedelta(minutes=10):
                stuck_tasks.append(task_id)
        
        for task_id in stuck_tasks:
            logger.warning(f"Cleaning up stuck task: {task_id}")
            if task_id in self._active_tasks:
                task_info = self._active_tasks[task_id]
                if 'task' in task_info:
                    task_info['task'].cancel()
                del self._active_tasks[task_id]
            if task_id in self._task_timeouts:
                del self._task_timeouts[task_id]

    async def run_workflow_background(self, manager: DiscoveryWorkflowManager, flow_state: DiscoveryFlowState, cmdb_data: Dict[str, Any], context: RequestContext):
        """Helper to run the workflow in the background and update state."""
        task_id = f"workflow_{flow_state.session_id}_{datetime.now().strftime('%H%M%S')}"
        
        try:
            # Track this task
            self._active_tasks[task_id] = {
                'start_time': datetime.now(),
                'session_id': flow_state.session_id,
                'type': 'workflow'
            }
            
            logger.info(f"Starting background workflow for session: {flow_state.session_id}")
            
            # Run the workflow with timeout
            try:
                final_state = await asyncio.wait_for(
                    manager.run_workflow(
                        flow_state=flow_state,
                        cmdb_data=cmdb_data,
                        client_account_id=context.client_account_id,
                        engagement_id=context.engagement_id,
                        user_id=context.user_id
                    ),
                    timeout=600  # 10 minute timeout for entire workflow
                )
            except asyncio.TimeoutError:
                logger.error(f"Workflow timed out for session: {flow_state.session_id}")
                flow_state.status = "failed"
                flow_state.current_phase = "timeout"
                error_state_data = {
                    "session_id": flow_state.session_id,
                    "client_account_id": str(flow_state.client_account_id),
                    "engagement_id": str(flow_state.engagement_id),
                    "status": "failed",
                    "current_phase": "timeout",
                    "status_message": "Workflow timed out after 10 minutes",
                }
                if self.state_service:
                    await self.state_service.update_workflow_state(
                        session_id=flow_state.session_id,
                        client_account_id=flow_state.client_account_id,
                        engagement_id=flow_state.engagement_id,
                        status="failed",
                        current_phase="timeout",
                        state_data=error_state_data
                    )
                return
            
            # Update the state upon completion
            # Persist the final state using WorkflowStateService
            if self.state_service:
                await self.state_service.update_workflow_state(
                    session_id=flow_state.session_id,
                    client_account_id=flow_state.client_account_id,
                    engagement_id=flow_state.engagement_id,
                    status="completed",
                    current_phase=final_state.current_phase,
                    state_data=final_state.dict()
                )
            logger.info(f"Background workflow {flow_state.session_id} completed.")
        except Exception as e:
            logger.error(f"Error in background workflow {flow_state.session_id}: {e}", exc_info=True)
            # Persist the error state using WorkflowStateService
            if self.state_service:
                # Construct a minimal state for saving on error
                error_state_data = {
                    "session_id": flow_state.session_id,
                    "client_account_id": str(flow_state.client_account_id),
                    "engagement_id": str(flow_state.engagement_id),
                    "status": "failed",
                    "current_phase": "error",
                    "status_message": str(e),
                }
                await self.state_service.update_workflow_state(
                    session_id=flow_state.session_id,
                    client_account_id=flow_state.client_account_id,
                    engagement_id=flow_state.engagement_id,
                    status="failed",
                    current_phase="error",
                    state_data=error_state_data
                )
        finally:
            # Clean up task tracking
            if task_id in self._active_tasks:
                del self._active_tasks[task_id]

    async def initiate_data_source_analysis(
        self,
        data_source: Dict[str, Any],
        context: RequestContext
    ) -> Dict[str, Any]:
        """
        Entry point for the discovery workflow. Delegates to the workflow manager.
        """
        if not self.service_available:
            return {"status": "error", "message": "CrewAI service is not available."}

        try:
            # 1. Parse Input Data
            file_data = data_source.get("file_data")
            if not file_data:
                raise ValueError("file_data is required for analysis")

            # Accept both array-of-objects (CSV rows) and string (Base64 or raw)
            if isinstance(file_data, str):
                # Try to decode base64 or parse as needed (for non-CSV files)
                try:
                    decoded = base64.b64decode(file_data)
                    # Optionally: try to parse as CSV if needed
                except Exception:
                    # Not base64, treat as raw string
                    decoded = file_data
                # Process decoded string as needed
                if isinstance(decoded, bytes):
                    decoded = decoded.decode('utf-8')
                if isinstance(decoded, str):
                    if decoded.strip().startswith('[') and decoded.strip().endswith(']'):
                        # Try to parse as JSON array
                        try:
                            parsed_data = json.loads(decoded)
                        except json.JSONDecodeError:
                            raise ValueError("Invalid JSON format")
                    else:
                        # Try to parse as CSV
                        try:
                            string_io = io.StringIO(decoded)
                            parsed_data = list(csv.DictReader(string_io))
                        except csv.Error:
                            raise ValueError("Invalid CSV format")
                else:
                    raise ValueError("Invalid file_data format")
            elif isinstance(file_data, list):
                # Already parsed rows (CSV upload)
                parsed_data = file_data
            else:
                raise ValueError("file_data must be either a list of records or a base64 string")

            metadata = data_source.get("metadata", {})
            cmdb_data = {"file_data": parsed_data, "metadata": metadata}

            # 2. Create Initial State and store it
            flow_state = self._create_new_flow_state(context, metadata)
            
            # Ensure the session exists before creating workflow state
            if self.state_service:
                # Check if session exists, create if it doesn't
                await self._ensure_session_exists(flow_state, metadata)
                
                await self.state_service.create_workflow_state(
                    session_id=flow_state.session_id,
                    client_account_id=flow_state.client_account_id,
                    engagement_id=flow_state.engagement_id,
                    workflow_type="discovery",
                    status=flow_state.status,
                    current_phase=flow_state.current_phase,
                    state_data=flow_state.dict()
                )

            # 3. Initialize the manager and run the workflow in the background
            workflow_manager = DiscoveryWorkflowManager(self)
            asyncio.create_task(self.run_workflow_background(
                manager=workflow_manager,
                flow_state=flow_state,
                cmdb_data=cmdb_data,
                context=context
            ))
            
            logger.info(f"Initiated discovery workflow for session_id: {flow_state.session_id}")
            return flow_state.dict()

        except ValidationError as e:
            logger.error(f"Failed to create discovery flow state due to validation error: {e}")
            error_details = [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
            return {
                "status": "error",
                "message": "Failed to start analysis due to missing context. Please ensure you are logged in and have selected a client and engagement.",
                "details": error_details
            }
        except Exception as e:
            logger.critical(f"Critical error in discovery workflow orchestration: {e}", exc_info=True)
            return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}

    def _create_new_flow_state(self, context: RequestContext, metadata: Dict) -> DiscoveryFlowState:
        user_id = context.user_id or context.session_id
        if not user_id:
            logger.warning(f"Could not determine user_id or session_id for the context. Generating a fallback flow_id.")
            user_id = f"anonymous_user_{uuid.uuid4().hex[:8]}"

        # Always use the context session_id (which should be the user's default session)
        # Ignore any import_session_id from the frontend - we want to use user's default session
        session_id = context.session_id
        
        return DiscoveryFlowState(
            session_id=session_id,
            flow_id=session_id,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            user_id=user_id,
            import_session_id=session_id,  # Same as session_id
            status="running",
            current_phase="initialization",
            metadata=metadata
        )

    async def _ensure_session_exists(self, flow_state: DiscoveryFlowState, metadata: Dict) -> None:
        """Ensure the session exists in the database, use user's default session if it doesn't."""
        try:
            # Try to import session management service
            from app.services.session_management_service import create_session_management_service
            from app.core.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as db:
                session_service = create_session_management_service(db)
                
                # Check if session exists
                existing_session = await session_service.get_session(flow_state.session_id)
                
                if not existing_session:
                    # Session doesn't exist, try to find user's default session
                    logger.warning(f"Session {flow_state.session_id} not found, looking for user's default session")
                    
                    # Try to find user's default session
                    from sqlalchemy import select
                    from app.models.data_import_session import DataImportSession
                    from app.models.client_account import User
                    
                    # Get user's default session
                    query = (
                        select(DataImportSession)
                        .join(User, DataImportSession.created_by == User.id)
                        .where(
                            User.id == flow_state.user_id,
                            DataImportSession.is_default == True
                        )
                    )
                    result = await db.execute(query)
                    user_default_session = result.scalar_one_or_none()
                    
                    if user_default_session:
                        logger.info(f"Using user's default session: {user_default_session.id}")
                        # Update flow state to use user's default session
                        flow_state.session_id = str(user_default_session.id)
                        flow_state.flow_id = str(user_default_session.id)
                        flow_state.import_session_id = str(user_default_session.id)
                    else:
                        # Fall back to demo session as last resort
                        logger.warning(f"No default session found for user {flow_state.user_id}, falling back to demo session")
                        demo_session_id = "33333333-3333-3333-3333-333333333333"
                        
                        # Update the flow state to use the demo session
                        flow_state.session_id = demo_session_id
                        flow_state.flow_id = demo_session_id
                        flow_state.import_session_id = demo_session_id
                        
                        logger.info(f"Updated flow state to use demo session: {demo_session_id}")
                
        except ImportError:
            logger.warning("Session management service not available, using demo session")
            # Fallback to demo session
            demo_session_id = "33333333-3333-3333-3333-333333333333"
            flow_state.session_id = demo_session_id
            flow_state.flow_id = demo_session_id
            flow_state.import_session_id = demo_session_id
        except Exception as e:
            logger.error(f"Failed to check session exists: {e}")
            # Fallback to demo session
            demo_session_id = "33333333-3333-3333-3333-333333333333"
            flow_state.session_id = demo_session_id
            flow_state.flow_id = demo_session_id
            flow_state.import_session_id = demo_session_id

    def get_flow_state(self, flow_id: str, context: RequestContext) -> Optional[DiscoveryFlowState]:
        """
        Retrieves the state of a specific workflow.
        
        Args:
            flow_id: The ID of the workflow to retrieve
            context: Request context containing client and engagement info
            
        Returns:
            DiscoveryFlowState if found, None otherwise
        """
        if not self.state_service or not flow_id or not context:
            return None
            
        ws = self.state_service.get_workflow_state_by_session_id(
            session_id=flow_id,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id
        )
        return DiscoveryFlowState(**ws.state_data) if ws and hasattr(ws, 'state_data') else None

    async def get_flow_state_by_session(self, session_id: str, context: RequestContext) -> Optional[DiscoveryFlowState]:
        """
        Retrieves the state of a flow by its session ID from the persistent storage.
        """
        if not self.state_service:
            logger.error("State service is not available.")
            return None
        
        workflow_state = await self.state_service.get_workflow_state_by_session_id(
            session_id=session_id,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id
        )

        if workflow_state:
            return DiscoveryFlowState(**workflow_state.state_data)
        
        return None

    async def get_all_active_flows(self, context: RequestContext) -> List[DiscoveryFlowState]:
        """
        Retrieves all active flows for the current engagement from persistent storage.
        """
        if not self.state_service:
            logger.error("State service is not available.")
            return []

        workflow_states = await self.state_service.list_workflow_states_by_engagement(
            engagement_id=context.engagement_id,
            client_account_id=context.client_account_id
        )

        active_flow_states = [
            DiscoveryFlowState(**ws.state_data) 
            for ws in workflow_states 
            if ws.status == "running"
        ]
        return active_flow_states

    def _get_llm(self):
        """Returns the configured LLM instance."""
        if not self.llm:
            logger.warning("LLM is not available. CrewAI service is in limited mode.")
        return self.llm

    async def call_ai_agent(self, prompt: str) -> str:
        if not self.service_available:
            logger.warning("CrewAI/LiteLLM not available. Skipping agentic call.")
            return {"error": "AI services not available"}

        try:
            # Use LiteLLM's completion for provider-agnostic calls
            response = await litellm.completion(
                model="openai/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
                messages=[{"role": "user", "content": prompt}],
                api_key=os.getenv("DEEPINFRA_API_KEY"),
                base_url="https://api.deepinfra.com/v1/openai"
            )
            # Assuming the response format is consistent with OpenAI's
            if response.choices and response.choices[0].message:
                return response.choices[0].message.content
            return None
        except Exception as e:
            logger.error(f"Error calling LiteLLM: {e}")
            raise
            
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get the health status of the CrewAI Flow Service.
        
        Returns:
            Dict containing health status information including:
            - status: Overall service status (healthy, degraded, unhealthy)
            - components: Status of individual components
            - active_flows: Number of currently active flows
            - service_available: Whether the service is available
            - llm_configured: Whether the LLM is properly configured
        """
        try:
            components = {
                "llm_configured": self.llm is not None,
                "langchain_available": LANGCHAIN_AVAILABLE,
                "litellm_available": LITELLM_AVAILABLE,
                "agents_initialized": len(self.agents) > 0 if hasattr(self, 'agents') else False,
                "workflow_manager_initialized": hasattr(self, 'manager') and self.manager is not None
            }
            
            # Determine overall status
            critical_components = [
                components["llm_configured"],
                components["langchain_available"],
                components["litellm_available"]
            ]
            
            if all(critical_components):
                status = "healthy"
            elif any(critical_components):
                status = "degraded"
            else:
                status = "unhealthy"
            
            return {
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
                "service": "crewai_flow_service",
                "version": "1.0.0",
                "components": components,
                "active_flows": len(self.active_flows) if hasattr(self, 'active_flows') else 0,
                "service_available": self.service_available,
                "llm_configured": components["llm_configured"],
                "missing_configuration": [
                    k for k, v in {
                        "DEEPINFRA_API_KEY": bool(os.getenv("DEEPINFRA_API_KEY")),
                    }.items() if not v
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting health status: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def get_service_status(self):
        """Returns a brief status of the service availability."""
        return {
            "service_available": self.service_available,
            "langchain_available": LANGCHAIN_AVAILABLE,
            "litellm_available": LITELLM_AVAILABLE,
            "llm_configured": self.llm is not None,
            "agents_initialized": bool(self.agents),
            "manager_initialized": self.manager is not None
        }

# Single, shared instance of the service
# This will be replaced by dependency injection
# crewai_flow_service = CrewAIFlowService() 