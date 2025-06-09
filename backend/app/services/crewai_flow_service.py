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

# Pydantic and Core Components
from pydantic import BaseModel, Field
from app.core.config import settings
from app.core.context import RequestContext, get_current_context
from app.services.llm_usage_tracker import LLMUsageTracker
from app.schemas.flow_schemas import DiscoveryFlowState

# CrewAI and Langchain
from langchain_openai import ChatOpenAI
from crewai import Agent, Task, Crew, Process

# Local Imports
from .crewai_flow_handlers.discovery_handlers.discovery_workflow_manager import DiscoveryWorkflowManager

logger = logging.getLogger(__name__)

class CrewAIFlowService:
    """A stateful service registry for core CrewAI components and active flows."""
    
    def __init__(self):
        logger.info("Initializing CrewAIFlowService...")
        self.settings = settings
        self.llm = self._initialize_llm()
        self.agents = self._initialize_agents() if self.llm else {}
        self.service_available = bool(self.llm and self.agents)
        
        # State management for active workflows
        self.active_flows: Dict[str, DiscoveryFlowState] = {}
        
        if self.service_available:
            logger.info("CrewAIFlowService initialized successfully with state management.")
        else:
            logger.warning("CrewAI Flow Service running in limited capacity due to missing configuration.")
    
    def _initialize_llm(self):
        if not self.settings.DEEPINFRA_API_KEY:
            logger.error("DEEPINFRA_API_KEY not found in settings.")
            return None
        try:
            return ChatOpenAI(
                model="meta-llama/Llama-3-70b-chat-hf",
                temperature=0.1,
                max_tokens=4096,
                base_url="https://api.deepinfra.com/v1/openai",
                api_key=self.settings.DEEPINFRA_API_KEY
            )
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            return None

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
            file_data_b64 = data_source.get("file_data")
            metadata = data_source.get("metadata", {})
            if not file_data_b64:
                raise ValueError("file_data is required for analysis")
            
            decoded_content = base64.b64decode(file_data_b64).decode('utf-8')
            if metadata.get('filename', '').endswith('.csv'):
                string_io = io.StringIO(decoded_content)
                parsed_data = list(csv.DictReader(string_io))
            else:
                parsed_data = json.loads(decoded_content)
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

        except Exception as e:
            logger.critical(f"Critical error in discovery workflow orchestration: {e}", exc_info=True)
            return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}

    def _create_new_flow_state(self, context: RequestContext, metadata: Dict) -> DiscoveryFlowState:
        user_id = context.user_id or context.session_id
        if not user_id:
            logger.warning(f"Could not determine user_id or session_id for the context. Generating a fallback flow_id.")
            user_id = f"anonymous_user_{uuid.uuid4().hex[:8]}"

        return DiscoveryFlowState(
            flow_id=str(uuid.uuid4()),
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

# Singleton instance
crewai_flow_service = CrewAIFlowService() 