"""
Main service for orchestrating CrewAI agentic flows.
This service acts as a core registry for agents and LLM configurations.
"""

import logging
import asyncio
import uuid
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import base64
import csv
import io
import os

# Pydantic and Core Components
from pydantic import BaseModel, Field, ValidationError
from app.core.config import settings
from app.core.context import RequestContext, get_current_context
from app.services.llm_usage_tracker import LLMUsageTracker
from app.schemas.flow_schemas import DiscoveryFlowState

# Conditional import for LangChain components
try:
    from langchain_openai import ChatOpenAI
    from crewai import Agent
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

# Conditional import for LiteLLM
try:
    from litellm import completion as litellm_completion
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False

# Local Imports
from app.services.crewai_flow_handlers.discovery_handlers.discovery_workflow_manager import DiscoveryWorkflowManager

logger = logging.getLogger(__name__)

class CrewAIFlowService:
    """A stateful service registry for core CrewAI components and active flows."""
    
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(CrewAIFlowService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.active_flows = {}
            self.service_available = LANGCHAIN_AVAILABLE and LITELLM_AVAILABLE
            
            if self.service_available:
                # Configure LLM for DeepInfra
                self.llm = ChatOpenAI(
                    api_key=os.getenv("DEEPINFRA_API_KEY"),
                    base_url="https://api.deepinfra.com/v1/openai/chat/completions",
                    model_name="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
                    temperature=0.1,
                    max_tokens=4096
                )
            else:
                self.llm = None

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
        agents = {
            'data_validator': self._create_agent("Data Quality Analyst", "Ensures data quality and consistency."),
            'field_mapper': self._create_agent("Field Mapping Specialist", "Maps source data fields to the target schema."),
            'asset_classifier': self._create_agent("Asset Classification Expert", "Classifies assets and suggests 6R strategies."),
            'dependency_analyzer': self._create_agent("Dependency Analysis Specialist", "Identifies relationships between assets."),
        }
        logger.info(f"Created {len(agents)} specialized agents.")
        return agents

    def _create_agent(self, role: str, goal: str) -> Agent:
        return Agent(
            role=role,
            goal=goal,
            backstory="An expert in cloud migration planning.",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

    async def run_workflow_background(self, manager: DiscoveryWorkflowManager, flow_state: DiscoveryFlowState, cmdb_data: Dict[str, Any], context: RequestContext):
        """Helper to run the workflow in the background and update state."""
        try:
            final_state = await manager.run_workflow(
                flow_state=flow_state,
                cmdb_data=cmdb_data,
                client_account_id=context.client_account_id,
                engagement_id=context.engagement_id,
                user_id=context.user_id
            )
            # Update the state upon completion
            self.active_flows[flow_state.session_id] = final_state
            logger.info(f"Background workflow {flow_state.session_id} completed.")
        except Exception as e:
            logger.error(f"Error in background workflow {flow_state.session_id}: {e}", exc_info=True)
            flow_state.current_phase = "error"
            flow_state.status_message = str(e)
            self.active_flows[flow_state.session_id] = flow_state

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
            self.active_flows[flow_state.session_id] = flow_state

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

        return DiscoveryFlowState(
            session_id=context.session_id,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            user_id=user_id,
            import_session_id=metadata.get("import_session_id", str(uuid.uuid4()))
        )

    def get_flow_state(self, flow_id: str) -> Optional[DiscoveryFlowState]:
        """
        Retrieves the state of a specific workflow.
        """
        return self.active_flows.get(flow_id)

    def get_flow_state_by_session(self, session_id: str) -> Optional[DiscoveryFlowState]:
        """
        Retrieves the state of a workflow for a given session ID.
        """
        if not session_id:
            return None
        for flow_state in self.active_flows.values():
            if flow_state.session_id == session_id:
                return flow_state
        return None

    def get_all_active_flows(self) -> List[DiscoveryFlowState]:
        """
        Returns a list of all active workflow states.
        """
        return list(self.active_flows.values())

    def _get_llm(self):
        return self.llm

    async def call_ai_agent(self, prompt: str) -> str:
        if not self.service_available:
            logger.warning("CrewAI/LiteLLM not available. Skipping agentic call.")
            return {"error": "AI services not available"}

        try:
            # Use LiteLLM's completion for provider-agnostic calls
            response = await litellm_completion(
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

# Singleton instance
crewai_flow_service = CrewAIFlowService() 