"""
Unified CrewAI Flow Service
Consolidates all CrewAI flow functionality with proper modular handler architecture.
Implements agentic-first discovery workflow with CrewAI Flow state management.
"""

import logging
import asyncio
import uuid
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_fixed
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
import base64
import csv
import io

# Import handlers
from .crewai_flow_handlers import (
    CrewAIFlowConfig, 
    ParsingHandler, 
    ExecutionHandler,
    ValidationHandler, 
    FlowStateHandler,
    UIInteractionHandler,
    DataCleanupHandler
)
from app.models.asset import Asset, AssetType
from app.models.data_import import RawImportRecord
from app.core.database import AsyncSessionLocal
from app.services.llm_usage_tracker import LLMUsageTracker
from app.schemas.agent_schemas import CrewTask, Agent, Crew, TaskOutput, CrewProcess, TaskContext
from app.schemas.discovery_schemas import CMDBData, FieldMapping, DiscoveredAsset
from app.core.context import RequestContext

logger = logging.getLogger(__name__)

class DiscoveryFlowState(BaseModel):
    """Enhanced state for Discovery phase workflow with CrewAI Flow state management."""
    id: str = Field(default_factory=lambda: f"discovery_{uuid.uuid4().hex[:8]}")
    cmdb_data: Dict[str, Any] = {}
    filename: str = ""
    headers: List[str] = []
    sample_data: List[Dict[str, Any]] = []
    import_session_id: str = ""
    current_phase: str = "initialization"
    workflow_phases: List[str] = Field(default_factory=lambda: [
        "initialization", "data_validation", "data_quality_analysis", "field_mapping", 
        "asset_classification", "readiness_assessment", "database_integration",
        "workflow_progression", "completion"
    ])
    phase_progress: Dict[str, float] = Field(default_factory=dict)
    data_validation_complete: bool = False
    field_mapping_complete: bool = False
    asset_classification_complete: bool = False
    readiness_assessment_complete: bool = False
    database_integration_complete: bool = False
    workflow_progression_complete: bool = False
    validated_structure: Dict[str, Any] = {}
    suggested_field_mappings: Dict[str, str] = {}
    asset_classifications: List[Dict[str, Any]] = []
    readiness_scores: Dict[str, float] = {}
    processed_assets: List[str] = []
    updated_records: List[str] = []
    workflow_records: List[str] = []
    progress_percentage: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    agent_insights: Dict[str, Any] = {}
    recommendations: List[str] = []
    error_analysis: Dict[str, Any] = {}
    feedback_processed: List[Dict[str, Any]] = []
    flow_context: Dict[str, Any] = Field(default_factory=dict)
    agent_memory: Dict[str, Any] = Field(default_factory=dict)
    learning_patterns: List[Dict[str, Any]] = Field(default_factory=list)


class CrewAIFlowService:
    """Unified CrewAI Flow Service with modular handler architecture."""
    
    def __init__(self):
        self.config = CrewAIFlowConfig()
        self.service_available = False
        self.llm = None
        self.agents = {}
        self.active_flows = {}
        
        self.parsing_handler = None
        self.execution_handler = None
        self.validation_handler = None
        self.flow_state_handler = None
        self.ui_interaction_handler = None
        self.data_cleanup_handler = None
        self.llm_usage_tracker = LLMUsageTracker()
        
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize CrewAI Flow components with enhanced configuration."""
        try:
            from crewai import Agent, Task, Crew, Process
            
            self.Agent = Agent
            self.Task = Task
            self.Crew = Crew
            self.Process = Process
            
            self._initialize_llm()
            
            if self.llm:
                self._create_discovery_agents()
                self.service_available = True
                logger.info("Unified CrewAI Flow Service initialized successfully")
            else:
                logger.warning("LLM not available. CrewAI Flow Service running in limited capacity.")
            
            # Handlers must be initialized after agents are potentially created
            self._initialize_handlers()
            
        except ImportError as e:
            logger.warning(f"CrewAI Flow not available: {e}")
            self._initialize_fallback_service()
    
    def _initialize_llm(self):
        """Initialize LLM with proper configuration."""
        try:
            from langchain_openai import ChatOpenAI
            
            llm_config = self.config.llm_config
            self.llm = ChatOpenAI(
                model=llm_config["model"],
                temperature=llm_config["temperature"],
                max_tokens=llm_config["max_tokens"],
                base_url=llm_config["base_url"],
                api_key=self.config.settings.DEEPINFRA_API_KEY if self.config.settings else None
            )
            logger.info(f"LLM initialized: {llm_config['model']}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            self.llm = None
    
    def _initialize_handlers(self):
        """Initialize modular handlers."""
        # These handlers are essential for state and UI, and do not depend on an LLM.
        # They must be available even in fallback mode.
        self.ui_interaction_handler = UIInteractionHandler(self.config)
        self.flow_state_handler = FlowStateHandler(self.config)

        if self.llm:
            self.parsing_handler = ParsingHandler()
            self.execution_handler = ExecutionHandler(self.config, self.agents)
            self.validation_handler = ValidationHandler()
            logger.info("Initialized core agentic handlers.")
        else:
            logger.warning("LLM not configured. Core agentic handlers are disabled.")
    
    def _create_discovery_agents(self):
        """Create specialized discovery agents."""
        if not self.llm:
            return
            
        try:
            self.agents['data_validator'] = self.Agent(
                role='CMDB Data Quality Specialist',
                goal='Validate and assess the quality of CMDB import data',
                backstory='Expert in CMDB data structures with deep knowledge of asset discovery patterns and data quality requirements.',
                verbose=False,
                allow_delegation=False,
                llm=self.llm
            )
            self.agents['field_mapper'] = self.Agent(
                role='Intelligent Field Mapping Specialist',
                goal='Create optimal field mappings between source data and target schema',
                backstory='Specialist in data transformation with extensive experience in CMDB field mapping and schema alignment.',
                verbose=False,
                allow_delegation=False,
                llm=self.llm
            )
            self.agents['asset_classifier'] = self.Agent(
                role='AI Asset Classification Expert',
                goal='Intelligently classify assets and determine migration strategies',
                backstory='Expert in asset classification with deep knowledge of infrastructure patterns and migration methodologies.',
                verbose=False,
                allow_delegation=False,
                llm=self.llm
            )
            logger.info(f"Created {len(self.agents)} specialized discovery agents")
            
        except Exception as e:
            logger.error(f"Failed to create agents: {e}")
            self.agents = {}
    
    async def run_discovery_flow_with_state(
        self, 
        cmdb_data: Dict[str, Any],
        client_account_id: str = None,
        engagement_id: str = None,
        user_id: str = None
    ) -> Dict[str, Any]:
        """Enhanced discovery flow with state management and database integration."""
        
        if not self.service_available:
            return await self._run_fallback_discovery_flow(cmdb_data, client_account_id, engagement_id, user_id)
        
        flow_state = DiscoveryFlowState(
            cmdb_data=cmdb_data,
            import_session_id=cmdb_data.get("import_session_id", ""),
            started_at=datetime.utcnow()
        )
        
        try:
            return await self._execute_agentic_flow_with_state(
                flow_state, cmdb_data, client_account_id, engagement_id, user_id
            )
            
        except Exception as e:
            logger.error(f"Discovery flow failed: {e}")
            return await self._execute_fallback_flow_with_state(flow_state, cmdb_data)
    
    async def _execute_agentic_flow_with_state(
        self,
        flow_state: DiscoveryFlowState,
        cmdb_data: Dict[str, Any],
        client_account_id: str,
        engagement_id: str,
        user_id: str
    ):
        # LATE IMPORTS TO PREVENT CIRCULAR DEPENDENCIES
        from app.services.asset_processing_service import asset_processing_service
        from app.services.agent_learning_system import get_agent_learning_system

        agent_learning_system = get_agent_learning_system()

        # Phase 1: Data Validation
        self._update_flow_phase(flow_state, "data_validation")
        flow_state.validated_structure = await self._run_data_validation_async(cmdb_data)
        flow_state.data_validation_complete = True
        
        # Phase 2: Field Mapping
        self._update_flow_phase(flow_state, "field_mapping")
        flow_state.suggested_field_mappings = await self._run_field_mapping_async(cmdb_data)
        flow_state.field_mapping_complete = True
        
        # Phase 3: Asset Classification
        self._update_flow_phase(flow_state, "asset_classification")
        flow_state.asset_classifications = await self._run_asset_classification_async(flow_state)
        flow_state.asset_classification_complete = True
        
        # Phase 4: Database Integration
        self._update_flow_phase(flow_state, "database_integration")
        await self._create_assets_with_workflow(flow_state, client_account_id, engagement_id, user_id)
        flow_state.database_integration_complete = True

        # Final Phase
        self._update_flow_phase(flow_state, "completion")
        flow_state.completed_at = datetime.utcnow()
        
        # Agentic Analysis (if enabled)
        if self.llm:
            analysis_result = await data_source_intelligence_agent.analyze_data_source(
                data_source=cmdb_data,
                flow_state=flow_state,
                page_context=flow_state.page_context,
            )
            flow_state.agent_analysis = analysis_result
        
        return self._format_flow_state_results(flow_state)

    async def _load_raw_data_from_session(self, flow_state: DiscoveryFlowState, client_account_id: str):
        pass

    async def _create_assets_with_workflow(
        self, 
        flow_state: DiscoveryFlowState, 
        client_account_id: str,
        engagement_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        # LATE IMPORT TO PREVENT CIRCULAR DEPENDENCIES
        from app.services.asset_processing_service import asset_processing_service

        created_assets = []
        for asset_data in flow_state.asset_classifications:
            asset_create_data = {
                "client_account_id": client_account_id,
                "engagement_id": engagement_id,
                "created_by": user_id,
                **asset_data
            }
            created_asset = await asset_processing_service.create_asset(asset_create_data)
            created_assets.append(created_asset)
        flow_state.processed_assets = [asset.id for asset in created_assets]
        return {"created_assets": len(created_assets)}

    async def _progress_workflow_agentic(
        self, 
        flow_state: DiscoveryFlowState,
        client_account_id: str,
        engagement_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        pass

    def _update_flow_phase(self, flow_state: DiscoveryFlowState, phase: str):
        flow_state.current_phase = phase
        num_phases = len(flow_state.workflow_phases)
        current_index = flow_state.workflow_phases.index(phase)
        flow_state.progress_percentage = (current_index + 1) / num_phases * 100

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    async def _run_data_validation_async(self, cmdb_data: Dict[str, Any]) -> Dict[str, Any]:
        task = self.Task(
            description="Analyze the provided CMDB data structure, validate its quality, and identify any structural issues.",
            agent=self.agents['data_validator'],
            expected_output="A JSON object summarizing data quality, including column analysis and validation status."
        )
        crew = self.Crew(agents=[self.agents['data_validator']], tasks=[task], verbose=1)
        result = crew.kickoff(inputs={'cmdb_data': cmdb_data})
        return json.loads(result)

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    async def _run_field_mapping_async(self, cmdb_data: Dict[str, Any]) -> Dict[str, Any]:
        task = self.Task(
            description="Based on the source columns, suggest the best field mappings to the target asset schema.",
            agent=self.agents['field_mapper'],
            expected_output="A JSON object with suggested field mappings from source to target."
        )
        crew = self.Crew(agents=[self.agents['field_mapper']], tasks=[task], verbose=1)
        result = crew.kickoff(inputs={'cmdb_data': cmdb_data})
        return json.loads(result)

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    async def _run_asset_classification_async(self, flow_state: DiscoveryFlowState) -> Dict[str, Any]:
        task = self.Task(
            description="Classify each asset based on its properties and suggest a 6R migration strategy.",
            agent=self.agents['asset_classifier'],
            expected_output="A list of JSON objects, each representing an asset with its classification and recommended 6R strategy."
        )
        crew = self.Crew(agents=[self.agents['asset_classifier']], tasks=[task], verbose=1)
        result = crew.kickoff(inputs={'validated_data': flow_state.validated_structure})
        return json.loads(result)

    async def _execute_fallback_flow_with_state(
        self, 
        flow_state: DiscoveryFlowState, 
        cmdb_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a basic, non-agentic fallback flow."""
        logger.warning("Executing discovery flow in fallback mode")
        # Simulate basic processing
        flow_state.validated_structure = {"status": "ok", "message": "Fallback validation"}
        flow_state.completed_at = datetime.utcnow()
        
        return self._format_flow_state_results(flow_state)

    def _format_flow_state_results(self, flow_state: DiscoveryFlowState) -> Dict[str, Any]:
        """Formats the final state into a structured response."""
        return {
            "flow_id": flow_state.id,
            "status": "completed" if flow_state.completed_at else "in_progress",
            "progress": flow_state.progress_percentage,
            "current_phase": flow_state.current_phase,
            "results": {
                "validated_structure": flow_state.validated_structure,
                "suggested_mappings": flow_state.suggested_field_mappings,
                "classified_assets": flow_state.asset_classifications,
                "processed_asset_count": len(flow_state.processed_assets)
            },
            "started_at": flow_state.started_at,
            "completed_at": flow_state.completed_at,
            "error_analysis": flow_state.error_analysis
        }

    async def run_discovery_flow(
        self, 
        cmdb_data: Dict[str, Any],
        client_account_id: str = None,
        engagement_id: str = None,
        user_id: str = None
    ) -> Dict[str, Any]:
        # This is now a wrapper for the stateful flow
        return await self.run_discovery_flow_with_state(cmdb_data, client_account_id, engagement_id, user_id)

    async def _run_fallback_discovery_flow(
        self, 
        cmdb_data: Dict[str, Any],
        client_account_id: str = None,
        engagement_id: str = None,
        user_id: str = None
    ) -> Dict[str, Any]:
        logger.warning("Running fallback discovery flow due to unavailable CrewAI service.")
        # Basic, non-AI processing
        return {
            "status": "completed_fallback",
            "message": "CrewAI service is not available. Only basic data processing was performed.",
            "processed_record_count": len(cmdb_data.get("records", [])),
        }

    def _initialize_fallback_service(self):
        """Initialize a non-agentic fallback service."""
        self.service_available = False
        # Ensure handlers that don't depend on LLM are still available
        self.parsing_handler = ParsingHandler()
        self.ui_interaction_handler = UIInteractionHandler(self.config)
        self.data_cleanup_handler = None
        self.llm_usage_tracker = LLMUsageTracker()
        logger.warning("CrewAI Flow Service running in fallback mode. Limited functionality.")
    
    def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """Get the status of an active discovery flow."""
        return self.active_flows.get(flow_id, {"status": "not_found"})

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the CrewAI service."""
        return {
            "service_available": self.service_available,
            "llm_initialized": self.llm is not None,
            "agents_created": len(self.agents) > 0,
            "active_flows": len(self.active_flows),
            "llm_config": self.config.llm_config if self.config else "Not configured",
        }

    def is_available(self) -> bool:
        return self.service_available

    async def initiate_data_source_analysis(
        self,
        data_source: Dict[str, Any],
        context: RequestContext,
        page_context: str
    ) -> Dict[str, Any]:
        """Initiate data source analysis with the specialized agent."""
        if not self.service_available:
            return {"error": "CrewAI service is not available for data source analysis"}

        # Late import to break circular dependency
        from app.services.discovery_agents.data_source_intelligence_agent import data_source_intelligence_agent

        try:
            # --- Robust Data Parsing Logic ---
            raw_file_data = data_source.get("file_data")
            metadata = data_source.get("metadata", {})
            file_name = metadata.get("fileName", "")
            
            # Check if the data is a string and appears to be a CSV that needs parsing.
            if isinstance(raw_file_data, str) and file_name.lower().endswith('.csv'):
                logger.info(f"CSV file detected ('{file_name}'). Attempting to parse.")
                try:
                    # The raw_file_data is expected to be a base64 encoded string from the frontend.
                    decoded_data = base64.b64decode(raw_file_data).decode('utf-8-sig') # Use utf-8-sig to handle potential BOM
                    csv_reader = csv.DictReader(io.StringIO(decoded_data))
                    parsed_data = [row for row in csv_reader]
                    
                    if parsed_data:
                        data_source["file_data"] = parsed_data
                        logger.info(f"Successfully parsed '{file_name}' into {len(parsed_data)} records.")
                    else:
                        logger.warning(f"CSV file '{file_name}' was parsed but resulted in no data records.")

                except (base64.binascii.Error, UnicodeDecodeError) as e:
                    logger.error(f"Failed to decode base64/UTF-8 for '{file_name}': {e}. Passing raw data to agent.", exc_info=True)
                except Exception as e:
                    logger.error(f"An unexpected error occurred during CSV parsing for '{file_name}': {e}. Passing raw data to agent.", exc_info=True)
            
            logger.info("Delegating data source analysis to Data Source Intelligence Agent")
            
            # Find the relevant flow state or create a placeholder if none exists
            flow_state = self.get_flow_status(context.session_id) if context.session_id and self.flow_state_handler.get_flow(context.session_id) else {}

            # The agent's analyze_data_source method manages its own state
            analysis_result = await data_source_intelligence_agent.analyze_data_source(
                data_source=data_source, 
                flow_state=flow_state,
                page_context=page_context
            )
            return analysis_result

        except Exception as e:
            logger.error(f"Error during data source analysis delegation: {e}", exc_info=True)
            return {"error": f"Failed to perform data source analysis: {e}"}

crewai_flow_service = CrewAIFlowService() 