"""
Unified Discovery Flow Implementation
Single CrewAI Flow consolidating all competing discovery flow implementations.
Follows CrewAI Flow documentation patterns from:
https://docs.crewai.com/guides/flows/mastering-flow-state

Replaces:
- backend/app/services/crewai_flows/discovery_flow.py
- backend/app/services/crewai_flows/models/flow_state.py
- Multiple competing flow implementations
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid

# CrewAI Flow imports with graceful fallback
CREWAI_FLOW_AVAILABLE = False
try:
    from crewai import Flow
    from crewai.flow.flow import listen, start
    from crewai.flow.persistence import persist
    CREWAI_FLOW_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ CrewAI Flow imports successful")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"CrewAI Flow not available: {e}")
    
    # Fallback implementations
    class Flow:
        def __init__(self): 
            self.state = None
        def __class_getitem__(cls, item):
            return cls
        def kickoff(self):
            return {}
    
    def listen(condition):
        def decorator(func):
            return func
        return decorator
    
    def start():
        def decorator(func):
            return func
        return decorator
    
    def persist():
        def decorator(func):
            return func
        return decorator

# Import unified state model
from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState
from app.core.context import RequestContext

# Import modular handlers
from .handlers.unified_flow_crew_manager import UnifiedFlowCrewManager
from .handlers.phase_executors import PhaseExecutionManager
from .handlers.unified_flow_management import UnifiedFlowManagement

# Import Flow State Bridge for PostgreSQL persistence
from .flow_state_bridge import FlowStateBridge, managed_flow_bridge

# 🤖 AGENT-FIRST ARCHITECTURE: Import individual specialized agents (Tasks 1.1-1.2)
# These are the correct agents for the optimized agentic design per Discovery Flow Redesign
from app.services.agents.data_import_validation_agent import DataImportValidationAgent
from app.services.agents.attribute_mapping_agent import AttributeMappingAgent  
from app.services.agents.data_cleansing_agent import DataCleansingAgent
from app.services.agents.asset_inventory_agent import AssetInventoryAgent
from app.services.agents.dependency_analysis_agent import DependencyAnalysisAgent
from app.services.agents.tech_debt_analysis_agent import TechDebtAnalysisAgent
from app.services.agents.discovery_agent_orchestrator import DiscoveryAgentOrchestrator

@persist()  # Enable CrewAI state persistence
class UnifiedDiscoveryFlow(Flow[UnifiedDiscoveryFlowState]):
    """
    Unified Discovery Flow following CrewAI documentation patterns.
    Single source of truth for all discovery flow operations.
    
    Now integrated with Flow State Bridge for hybrid CrewAI + PostgreSQL persistence.
    Addresses gaps from the consolidation plan:
    - Gap #1: CrewAI @persist() + PostgreSQL multi-tenancy
    - Gap #2: Manager-level state updates during crew execution
    - Gap #3: State validation and integrity checks
    - Gap #4: Advanced recovery and reconstruction capabilities
    - Gap #5: Performance monitoring and analytics integration
    
    Handles all discovery phases with proper state management:
    1. Field Mapping
    2. Data Cleansing  
    3. Asset Inventory
    4. Dependency Analysis
    5. Technical Debt Analysis
    """
    
    def __init__(self, crewai_service, context: RequestContext, **kwargs):
        """Initialize unified discovery flow with agent-first architecture"""
        
        # Store initialization parameters
        self._init_session_id = kwargs.get('session_id', str(uuid.uuid4()))
        self._init_client_account_id = kwargs.get('client_account_id', '')
        self._init_engagement_id = kwargs.get('engagement_id', '')
        self._init_user_id = kwargs.get('user_id', '')
        self._init_raw_data = kwargs.get('raw_data', [])
        self._init_metadata = kwargs.get('metadata', {})
        self._init_context = context
        
        super().__init__()
        
        # Store services and context
        self.crewai_service = crewai_service
        self.context = context
        
        # Initialize Flow State Bridge for PostgreSQL persistence
        self.flow_bridge = FlowStateBridge(context)
        
        # Initialize state if not exists
        if not hasattr(self, 'state') or self.state is None:
            self.state = UnifiedDiscoveryFlowState()
        
        # ✅ CRITICAL FIX: Set the flow_id from the CrewAI Flow instance
        if hasattr(self, 'flow_id') and self.flow_id:
            self.state.flow_id = str(self.flow_id)
            logger.info(f"🎯 State flow_id set from CrewAI Flow: {self.state.flow_id}")
        else:
            # Check alternative flow ID attributes
            for attr in ['id', '_id', '_flow_id', 'execution_id']:
                if hasattr(self, attr):
                    flow_id_value = getattr(self, attr)
                    if flow_id_value:
                        self.state.flow_id = str(flow_id_value)
                        logger.info(f"🎯 State flow_id set from {attr}: {self.state.flow_id}")
                        break
            else:
                logger.warning("⚠️ CrewAI Flow ID not yet available - will be set after kickoff")
        
        # 🤖 AGENT-FIRST ARCHITECTURE: Initialize individual specialized agents (Tasks 1.1-1.2)
        # These are the correct agents for the optimized agentic design per Discovery Flow Redesign
        self.data_validation_agent = DataImportValidationAgent()
        self.attribute_mapping_agent = AttributeMappingAgent()
        self.data_cleansing_agent = DataCleansingAgent()
        self.asset_inventory_agent = AssetInventoryAgent()
        self.dependency_analysis_agent = DependencyAnalysisAgent()
        self.tech_debt_analysis_agent = TechDebtAnalysisAgent()
        
        # Initialize agent orchestrator for coordination
        self.agent_orchestrator = DiscoveryAgentOrchestrator()
        
        # Initialize agent confidence tracking in state
        self.state.agent_confidences = {}
        self.state.user_clarifications = []
        self.state.agent_insights = []
        self.state.crew_escalations = []
        
        # Initialize modular handlers (keep for legacy compatibility)
        self.crew_manager = UnifiedFlowCrewManager(crewai_service, self.state)
        self.phase_executor = PhaseExecutionManager(self.state, self.crew_manager, self.flow_bridge)
        self.flow_management = UnifiedFlowManagement(self.state)
        
        logger.info(f"✅ Unified Discovery Flow initialized with AGENT-FIRST architecture: session={self._init_session_id}")
    
    def _ensure_uuid_serialization_safety(self):
        """Ensure all UUID fields in state are strings for JSON serialization"""
        try:
            # Convert core identification fields
            if hasattr(self.state, 'flow_id') and isinstance(self.state.flow_id, uuid.UUID):
                self.state.flow_id = str(self.state.flow_id)
            if hasattr(self.state, 'session_id') and isinstance(self.state.session_id, uuid.UUID):
                self.state.session_id = str(self.state.session_id)
            if hasattr(self.state, 'client_account_id') and isinstance(self.state.client_account_id, uuid.UUID):
                self.state.client_account_id = str(self.state.client_account_id)
            if hasattr(self.state, 'engagement_id') and isinstance(self.state.engagement_id, uuid.UUID):
                self.state.engagement_id = str(self.state.engagement_id)
            if hasattr(self.state, 'user_id') and isinstance(self.state.user_id, uuid.UUID):
                self.state.user_id = str(self.state.user_id)
                
            # Convert any UUID objects in nested data structures recursively
            def convert_nested_uuids(obj):
                if isinstance(obj, dict):
                    return {k: convert_nested_uuids(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_nested_uuids(item) for item in obj]
                elif isinstance(obj, uuid.UUID):
                    return str(obj)
                elif hasattr(obj, '__dict__'):
                    # Handle objects with attributes that might contain UUIDs
                    for attr_name in dir(obj):
                        if not attr_name.startswith('_'):
                            try:
                                attr_value = getattr(obj, attr_name)
                                if isinstance(attr_value, uuid.UUID):
                                    setattr(obj, attr_name, str(attr_value))
                            except (AttributeError, TypeError):
                                continue
                    return obj
                else:
                    return obj
            
            # Apply to all state attributes that might contain UUIDs
            # Use model fields if available (Pydantic models), otherwise use dir()
            if hasattr(self.state, '__fields__') or hasattr(self.state, 'model_fields'):
                # Handle Pydantic models safely
                fields = getattr(self.state, 'model_fields', getattr(self.state, '__fields__', {}))
                for attr_name in fields.keys():
                    try:
                        attr_value = getattr(self.state, attr_name)
                        if attr_value is not None:
                            converted_value = convert_nested_uuids(attr_value)
                            setattr(self.state, attr_name, converted_value)
                    except (AttributeError, TypeError) as e:
                        logger.debug(f"Could not convert Pydantic field {attr_name}: {e}")
                        continue
            else:
                # Handle regular objects
                for attr_name in dir(self.state):
                    if not attr_name.startswith('_'):
                        try:
                            attr_value = getattr(self.state, attr_name)
                            if attr_value is not None and not callable(attr_value):
                                converted_value = convert_nested_uuids(attr_value)
                                setattr(self.state, attr_name, converted_value)
                        except (AttributeError, TypeError) as e:
                            logger.debug(f"Could not convert attribute {attr_name}: {e}")
                            continue
                
        except Exception as e:
            logger.warning(f"⚠️ UUID serialization safety check failed: {e}")
            # Try to convert the most common problematic fields manually
            try:
                if hasattr(self.state, 'flow_id'):
                    self.state.flow_id = str(self.state.flow_id) if self.state.flow_id else ""
                if hasattr(self.state, 'session_id'):
                    self.state.session_id = str(self.state.session_id) if self.state.session_id else ""
                if hasattr(self.state, 'client_account_id'):
                    self.state.client_account_id = str(self.state.client_account_id) if self.state.client_account_id else ""
                if hasattr(self.state, 'engagement_id'):
                    self.state.engagement_id = str(self.state.engagement_id) if self.state.engagement_id else ""
                if hasattr(self.state, 'user_id'):
                    self.state.user_id = str(self.state.user_id) if self.state.user_id else ""
            except Exception as fallback_error:
                logger.error(f"❌ Even fallback UUID conversion failed: {fallback_error}")
    
    def _ensure_uuid_serialization_safety_for_dict(self, data_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure UUID serialization safety for a specific dictionary"""
        try:
            def convert_nested_uuids(obj):
                if isinstance(obj, dict):
                    return {k: convert_nested_uuids(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_nested_uuids(item) for item in obj]
                elif isinstance(obj, uuid.UUID):
                    return str(obj)
                elif hasattr(obj, '__dict__'):
                    # Handle objects with attributes that might contain UUIDs
                    result = {}
                    for attr_name in dir(obj):
                        if not attr_name.startswith('_'):
                            try:
                                attr_value = getattr(obj, attr_name)
                                if isinstance(attr_value, uuid.UUID):
                                    result[attr_name] = str(attr_value)
                                elif not callable(attr_value):
                                    result[attr_name] = convert_nested_uuids(attr_value)
                            except (AttributeError, TypeError):
                                continue
                    return result
                else:
                    return obj
            
            return convert_nested_uuids(data_dict)
            
        except Exception as e:
            logger.warning(f"⚠️ UUID serialization safety for dict failed: {e}")
            # Return original dict as fallback
            return data_dict
    
    async def _safe_update_flow_state(self):
        """Safely update flow state with UUID serialization safety"""
        if self.flow_bridge:
            self._ensure_uuid_serialization_safety()
            await self.flow_bridge.update_flow_state(self.state)
    
    @start()
    async def initialize_discovery(self):
        """Initialize the unified discovery workflow with PostgreSQL persistence"""
        logger.info("🚀 Starting Unified Discovery Flow initialization with hybrid persistence")
        logger.info(f"📋 Flow Context: session={self._init_session_id}, client={self._init_client_account_id}, engagement={self._init_engagement_id}")
        
        # ✅ CRITICAL FIX: Set the flow_id from CrewAI Flow (now available after @start)
        flow_id_found = False
        
        # Try all possible flow ID attributes in priority order
        flow_id_attrs = ['flow_id', 'id', '_id', '_flow_id', 'execution_id', '_execution_id']
        
        for attr in flow_id_attrs:
            if hasattr(self, attr):
                flow_id_value = getattr(self, attr)
                if flow_id_value:
                    self.state.flow_id = str(flow_id_value)
                    logger.info(f"🎯 REAL CrewAI Flow ID set from {attr}: {self.state.flow_id}")
                    flow_id_found = True
                    break
        
        if not flow_id_found:
            logger.error("❌ CrewAI Flow ID still not available - this is a critical issue")
            # Log all available attributes for debugging
            available_attrs = [attr for attr in dir(self) if not attr.startswith('__')]
            logger.error(f"Available attributes: {available_attrs}")
            
            # Use session_id as fallback but log warning
            if self._init_session_id:
                self.state.flow_id = self._init_session_id
                logger.warning(f"⚠️ FALLBACK: Using session_id as flow_id: {self.state.flow_id}")
            else:
                # Generate a flow ID as last resort
                import uuid
                self.state.flow_id = str(uuid.uuid4())
                logger.error(f"❌ EMERGENCY: Generated new flow_id: {self.state.flow_id}")
        
        # Set core state fields (ensure all UUIDs are strings for JSON serialization)
        self.state.session_id = str(self._init_session_id) if self._init_session_id else ""
        self.state.client_account_id = str(self._init_client_account_id) if self._init_client_account_id else ""
        self.state.engagement_id = str(self._init_engagement_id) if self._init_engagement_id else ""
        self.state.user_id = str(self._init_user_id) if self._init_user_id else ""
        self.state.raw_data = self._init_raw_data
        self.state.metadata = self._init_metadata
        
        # Set flow status
        self.state.current_phase = "data_import"
        self.state.status = "running"
        self.state.started_at = datetime.utcnow().isoformat()
        
        logger.info(f"🔄 Flow State Initialized: phase={self.state.current_phase}, status={self.state.status}, progress={self.state.progress_percentage}%")
        
        # Validate input data
        if not self.state.raw_data:
            self.state.add_error("data_import", "No raw data provided")
            logger.error("❌ Flow initialization failed: No raw data provided")
            return "initialization_failed"
        
        # Initialize PostgreSQL persistence
        try:
            # Ensure UUID serialization safety before persistence
            self._ensure_uuid_serialization_safety()
            bridge_result = await self.flow_bridge.initialize_flow_state(self.state)
            logger.info(f"✅ Flow State Bridge initialized: {bridge_result}")
        except Exception as e:
            logger.warning(f"⚠️ Flow State Bridge initialization failed (non-critical): {e}")
        
        self.state.log_entry(f"Discovery Flow initialized with {len(self.state.raw_data)} records")
        logger.info(f"✅ Unified Discovery Flow initialized with {len(self.state.raw_data)} records")
        logger.info(f"🎯 Next Phase: data_import_validation")
        
        return "initialized"
    
    @listen(initialize_discovery)
    async def execute_data_import_validation_agent(self, previous_result):
        """Execute data import validation using individual agent"""
        if previous_result == "initialization_failed":
            logger.error("❌ Skipping data validation due to initialization failure")
            return "data_validation_skipped"
        
        logger.info("🤖 Starting Data Import Validation with Agent-First Architecture")
        self.state.current_phase = "data_import"
        self.state.status = "running"
        self.state.progress_percentage = 10.0  # Start with 10% progress
        
        # Store record count for proper tracking
        total_records = len(self.state.raw_data) if self.state.raw_data else 0
        self.state.records_processed = 0
        self.state.records_total = total_records
        
        # REAL-TIME UPDATE: Update database immediately when phase starts
        await self._safe_update_flow_state()
        
        # Add real-time processing update
        try:
            from app.services.agent_ui_bridge import agent_ui_bridge
            agent_ui_bridge.add_agent_insight(
                agent_id="data_import_agent",
                agent_name="Data Import Agent",
                insight_type="processing",
                page=f"flow_{self.state.flow_id}",
                title="Starting Data Import Validation",
                description=f"Beginning validation of {total_records} records",
                supporting_data={
                    'phase': 'data_import',
                    'records_total': total_records,
                    'records_processed': 0,
                    'progress_percentage': 10.0,
                    'start_time': datetime.utcnow().isoformat(),
                    'estimated_duration': '2-3 minutes'
                },
                confidence="high"
            )
        except Exception as e:
            logger.warning(f"⚠️ Could not add real-time update: {e}")
        
        try:
            # Prepare agent data
            agent_data = {
                'raw_data': self.state.raw_data,
                'source_columns': list(self.state.raw_data[0].keys()) if self.state.raw_data else [],
                'file_info': self.state.metadata.get('file_info', {}),
                'flow_metadata': {
                    'session_id': self.state.session_id,
                    'flow_id': self.state.flow_id
                }
            }
            
            # Add progress update
            try:
                agent_ui_bridge.add_agent_insight(
                    agent_id="data_import_agent",
                    agent_name="Data Import Agent",
                    insight_type="progress",
                    page=f"flow_{self.state.flow_id}",
                    title="Processing Data Records",
                    description=f"Analyzing {len(self.state.raw_data)} records for format validation, security scanning, and data quality assessment",
                    supporting_data={
                        'phase': 'data_import',
                        'progress_percentage': 10.0,
                        'records_processed': len(self.state.raw_data) // 2,  # Mock progress
                        'validation_checks': ['format', 'security', 'quality']
                    },
                    confidence="high"
                )
            except Exception:
                pass
            
            # Execute data validation agent
            validation_result = await self.data_validation_agent.execute_analysis(agent_data, self._init_context)
            
            # Store agent results and confidence
            self.state.data_validation_results = validation_result.data
            self.state.agent_confidences['data_validation'] = validation_result.confidence_score
            
            # Collect insights and clarifications
            if validation_result.insights_generated:
                self.state.agent_insights.extend([insight.model_dump() for insight in validation_result.insights_generated])
            if validation_result.clarifications_requested:
                self.state.user_clarifications.extend([req.model_dump() for req in validation_result.clarifications_requested])
            
            # Update phase completion
            self.state.phase_completion['data_import'] = True
            self.state.progress_percentage = 20.0
            self.state.records_processed = len(self.state.raw_data)
            self.state.records_valid = len(self.state.raw_data)  # Assume all valid for now
            
            # Add completion update
            try:
                agent_ui_bridge.add_agent_insight(
                    agent_id="data_import_agent",
                    agent_name="Data Import Agent",
                    insight_type="success",
                    page=f"flow_{self.state.flow_id}",
                    title="Data Import Validation Completed",
                    description=f"Successfully validated {len(self.state.raw_data)} records with {validation_result.confidence_score:.1f}% confidence",
                    supporting_data={
                        'phase': 'data_import',
                        'progress_percentage': 20.0,
                        'records_processed': len(self.state.raw_data),
                        'records_total': self.state.records_total,
                        'confidence_score': validation_result.confidence_score,
                        'validation_results': validation_result.data,
                        'completion_time': datetime.utcnow().isoformat()
                    },
                    confidence="high"
                )
            except Exception:
                pass
            
            # REAL-TIME UPDATE: Persist state with agent insights and progress
            await self._safe_update_flow_state()
            
            logger.info(f"✅ Data validation agent completed (confidence: {validation_result.confidence_score:.1f}%)")
            return "data_validation_completed"
            
        except Exception as e:
            logger.error(f"❌ Data validation agent failed: {e}")
            self.state.add_error("data_import", f"Agent execution failed: {str(e)}")
            
            # Add error update
            try:
                agent_ui_bridge.add_agent_insight(
                    agent_id="data_import_agent",
                    agent_name="Data Import Agent",
                    insight_type="error",
                    page=f"flow_{self.state.flow_id}",
                    title="Data Import Validation Failed",
                    description=f"Validation failed: {str(e)}",
                    supporting_data={
                        'phase': 'data_import',
                        'error_type': 'agent_execution_failure',
                        'error_message': str(e),
                        'failure_time': datetime.utcnow().isoformat()
                    },
                    confidence="high"
                )
            except Exception:
                pass
            
            # REAL-TIME UPDATE: Update database even on failure
            await self._safe_update_flow_state()
            
            return "data_validation_failed"

    @listen(execute_data_import_validation_agent)
    async def execute_attribute_mapping_agent(self, previous_result):
        """Execute attribute mapping using individual agent"""
        if previous_result in ["data_validation_skipped", "data_validation_failed"]:
            logger.warning("⚠️ Proceeding with attribute mapping despite validation issues")
        
        logger.info("🤖 Starting Attribute Mapping with Agent-First Architecture")
        self.state.current_phase = "attribute_mapping"
        
        # REAL-TIME UPDATE: Update database immediately when phase starts
        if self.flow_bridge:
            await self.flow_bridge.update_flow_state(self.state)
        
        try:
            # Prepare agent data
            agent_data = {
                'raw_data': self.state.raw_data,
                'source_columns': list(self.state.raw_data[0].keys()) if self.state.raw_data else [],
                'validation_results': self.state.data_validation_results,
                'flow_metadata': {
                    'session_id': self.state.session_id,
                    'flow_id': self.state.flow_id
                }
            }
            
            # Execute attribute mapping agent
            mapping_result = await self.attribute_mapping_agent.execute_analysis(agent_data, self._init_context)
            
            # Store agent results and confidence
            self.state.field_mappings = mapping_result.data
            self.state.agent_confidences['attribute_mapping'] = mapping_result.confidence_score
            
            # Collect insights and clarifications
            if mapping_result.insights_generated:
                self.state.agent_insights.extend([insight.model_dump() for insight in mapping_result.insights_generated])
            if mapping_result.clarifications_requested:
                self.state.user_clarifications.extend([req.model_dump() for req in mapping_result.clarifications_requested])
            
            # Update phase completion
            self.state.phase_completion['attribute_mapping'] = True
            self.state.progress_percentage = 40.0
            
            # REAL-TIME UPDATE: Persist state with agent insights and progress
            if self.flow_bridge:
                await self.flow_bridge.update_flow_state(self.state)
            
            logger.info(f"✅ Attribute mapping agent completed (confidence: {mapping_result.confidence_score:.1f}%)")
            return "field_mapping_completed"
            
        except Exception as e:
            logger.error(f"❌ Attribute mapping agent failed: {e}")
            self.state.add_error("attribute_mapping", f"Agent execution failed: {str(e)}")
            
            # REAL-TIME UPDATE: Update database even on failure
            if self.flow_bridge:
                await self.flow_bridge.update_flow_state(self.state)
            
            return "attribute_mapping_failed"

    @listen(execute_attribute_mapping_agent)
    async def execute_data_cleansing_agent(self, previous_result):
        """Execute data cleansing using individual agent"""
        logger.info("🤖 Starting Data Cleansing with Agent-First Architecture")
        self.state.current_phase = "data_cleansing"
        
        # REAL-TIME UPDATE: Update database immediately when phase starts
        if self.flow_bridge:
            await self.flow_bridge.update_flow_state(self.state)
        
        try:
            # Prepare agent data
            agent_data = {
                'raw_data': self.state.raw_data,
                'field_mappings': self.state.field_mappings,
                'validation_results': self.state.data_validation_results,
                'flow_metadata': {
                    'session_id': self.state.session_id,
                    'flow_id': self.state.flow_id
                }
            }
            
            # Execute data cleansing agent
            cleansing_result = await self.data_cleansing_agent.execute_analysis(agent_data, self._init_context)
            
            # Store agent results and confidence
            self.state.cleaned_data = cleansing_result.data.get('cleaned_data', self.state.raw_data)
            self.state.data_cleansing_results = cleansing_result.data
            self.state.agent_confidences['data_cleansing'] = cleansing_result.confidence_score
            
            # Collect insights and clarifications
            if cleansing_result.insights_generated:
                self.state.agent_insights.extend([insight.model_dump() for insight in cleansing_result.insights_generated])
            if cleansing_result.clarifications_requested:
                self.state.user_clarifications.extend([req.model_dump() for req in cleansing_result.clarifications_requested])
            
            # Update phase completion
            self.state.phase_completion['data_cleansing'] = True
            self.state.progress_percentage = 60.0
            
            # REAL-TIME UPDATE: Persist state with agent insights and progress
            if self.flow_bridge:
                await self.flow_bridge.update_flow_state(self.state)
            
            logger.info(f"✅ Data cleansing agent completed (confidence: {cleansing_result.confidence_score:.1f}%)")
            return "data_cleansing_completed"
            
        except Exception as e:
            logger.error(f"❌ Data cleansing agent failed: {e}")
            self.state.add_error("data_cleansing", f"Agent execution failed: {str(e)}")
            
            # REAL-TIME UPDATE: Update database even on failure
            if self.flow_bridge:
                await self.flow_bridge.update_flow_state(self.state)
            
            return "data_cleansing_failed"

    @listen(execute_data_cleansing_agent)
    async def create_discovery_assets_from_cleaned_data(self, previous_result):
        """Create discovery assets from cleaned data after data cleansing (proper relational approach)"""
        logger.info("🏗️ Creating Discovery Assets from Cleaned Data")
        self.state.current_phase = "inventory"
        
        # REAL-TIME UPDATE: Update database immediately when phase starts
        if self.flow_bridge:
            await self.flow_bridge.update_flow_state(self.state)
        
        try:
            # Check if we have cleaned data to process
            if not self.state.cleaned_data:
                logger.warning("⚠️ No cleaned data available for asset creation")
                return "asset_creation_skipped"
            
            logger.info(f"📊 Creating assets from {len(self.state.cleaned_data)} cleaned records")
            
            # Import required modules
            from app.core.database import AsyncSessionLocal
            from app.models.discovery_asset import DiscoveryAsset
            from app.models.discovery_flow import DiscoveryFlow
            from app.models.data_import import RawImportRecord
            from sqlalchemy import select, update
            import uuid as uuid_pkg
            from datetime import datetime
            
            discovery_assets_created = 0
            records_processed = 0
            
            async with AsyncSessionLocal() as db_session:
                try:
                    # Get the discovery flow record
                    flow_query = select(DiscoveryFlow).where(
                        DiscoveryFlow.flow_id == uuid_pkg.UUID(self.state.flow_id)
                    )
                    flow_result = await db_session.execute(flow_query)
                    discovery_flow = flow_result.scalar_one_or_none()
                    
                    if not discovery_flow:
                        logger.error(f"❌ Discovery flow not found: {self.state.flow_id}")
                        return "discovery_flow_not_found"
                    
                    # Get approved field mappings for intelligent mapping
                    field_mappings = self.state.field_mappings.get("mappings", {})
                    
                    # Process each cleaned record into a discovery asset
                    for index, cleaned_record in enumerate(self.state.cleaned_data):
                        try:
                            # Apply intelligent field mapping
                            mapped_data = self._apply_field_mappings_to_record(cleaned_record, field_mappings)
                            
                            # Create discovery asset with proper relational structure
                            discovery_asset = DiscoveryAsset(
                                # Foreign key relationship
                                discovery_flow_id=discovery_flow.id,
                                
                                # Multi-tenant isolation
                                client_account_id=uuid_pkg.UUID(self.state.client_account_id) if self.state.client_account_id else None,
                                engagement_id=uuid_pkg.UUID(self.state.engagement_id) if self.state.engagement_id else None,
                                
                                # Core identification
                                asset_name=self._extract_asset_name(mapped_data, cleaned_record, index),
                                asset_type=self._determine_asset_type_from_data(mapped_data, cleaned_record),
                                asset_subtype=mapped_data.get("asset_subtype") or cleaned_record.get("asset_subtype"),
                                
                                # Data storage (proper JSONB structure)
                                raw_data=cleaned_record,
                                normalized_data={
                                    **mapped_data,
                                    "hostname": mapped_data.get("hostname") or cleaned_record.get("hostname"),
                                    "ip_address": mapped_data.get("ip_address") or cleaned_record.get("ip_address"),
                                    "operating_system": mapped_data.get("operating_system") or cleaned_record.get("operating_system"),
                                    "environment": mapped_data.get("environment") or cleaned_record.get("environment", "Unknown"),
                                    "business_owner": mapped_data.get("business_owner") or cleaned_record.get("business_owner"),
                                    "department": mapped_data.get("department") or cleaned_record.get("department"),
                                    "criticality": mapped_data.get("criticality") or cleaned_record.get("criticality", "Medium")
                                },
                                
                                # Discovery metadata
                                discovered_in_phase="data_cleansing",
                                discovery_method="unified_discovery_flow",
                                confidence_score=self.state.agent_confidences.get('data_cleansing', 0.85),
                                
                                # Migration assessment
                                migration_ready=False,  # Will be determined in later phases
                                migration_complexity="Medium",  # Default until analyzed
                                migration_priority=3,  # Default priority
                                
                                # Status tracking
                                asset_status="discovered",
                                validation_status="pending",
                                
                                # Mock flag
                                is_mock=False
                            )
                            
                            db_session.add(discovery_asset)
                            await db_session.flush()
                            discovery_assets_created += 1
                            
                            logger.info(f"✅ Created discovery asset {discovery_asset.id}: {discovery_asset.asset_name} ({discovery_asset.asset_type})")
                            
                        except Exception as e:
                            logger.error(f"❌ Failed to create discovery asset from record {index}: {e}")
                            continue
                    
                    # Find and update corresponding raw import records
                    if self.state.session_id:
                        # Update raw import records to mark them as processed
                        # Note: RawImportRecord now uses master_flow_id instead of session_id
                        update_query = (
                            update(RawImportRecord)
                            .where(RawImportRecord.master_flow_id == uuid_pkg.UUID(self.state.flow_id))
                            .where(RawImportRecord.is_processed == False)
                            .values(
                                is_processed=True,
                                processed_at=datetime.utcnow(),
                                processing_notes=f"Processed by CrewAI Discovery Flow - {discovery_assets_created} discovery assets created"
                            )
                        )
                        result = await db_session.execute(update_query)
                        records_processed = result.rowcount
                        
                        logger.info(f"📝 Updated {records_processed} raw import records as processed")
                    
                    # Commit all changes
                    await db_session.commit()
                    
                    # Update flow state
                    self.state.asset_creation_results = {
                        "discovery_assets_created": discovery_assets_created,
                        "records_processed": records_processed,
                        "total_records": len(self.state.cleaned_data),
                        "success_rate": discovery_assets_created / len(self.state.cleaned_data) if self.state.cleaned_data else 0,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    self.state.phase_completion['asset_creation'] = True
                    self.state.progress_percentage = 70.0
                    
                    # REAL-TIME UPDATE: Persist state with asset creation results
                    if self.flow_bridge:
                        await self.flow_bridge.update_flow_state(self.state)
                    
                    logger.info(f"✅ Discovery asset creation completed: {discovery_assets_created} discovery assets created from {len(self.state.cleaned_data)} records")
                    return "inventory_completed"
                    
                except Exception as e:
                    await db_session.rollback()
                    logger.error(f"❌ Database error during asset creation: {e}")
                    raise
                    
        except Exception as e:
            logger.error(f"❌ Asset creation failed: {e}")
            self.state.add_error("asset_creation", f"Asset creation failed: {str(e)}")
            
            # REAL-TIME UPDATE: Update database even on failure
            if self.flow_bridge:
                await self.flow_bridge.update_flow_state(self.state)
            
            return "asset_creation_failed"

    def _apply_field_mappings_to_record(self, record: Dict[str, Any], field_mappings: Dict[str, str]) -> Dict[str, Any]:
        """Apply field mappings to transform a record"""
        mapped_data = {}
        
        for source_field, target_field in field_mappings.items():
            if source_field in record:
                # Normalize target field name
                normalized_target = target_field.lower().replace(" ", "_").replace("-", "_")
                mapped_data[normalized_target] = record[source_field]
        
        return mapped_data
    
    def _extract_asset_name(self, mapped_data: Dict[str, Any], original_data: Dict[str, Any], index: int) -> str:
        """Extract the best asset name from available data"""
        # Try mapped data first
        if mapped_data.get("asset_name"):
            return str(mapped_data["asset_name"])
        if mapped_data.get("hostname"):
            return str(mapped_data["hostname"])
        if mapped_data.get("name"):
            return str(mapped_data["name"])
        
        # Fallback to original data
        if original_data.get("asset_name"):
            return str(original_data["asset_name"])
        if original_data.get("hostname"):
            return str(original_data["hostname"])
        if original_data.get("name"):
            return str(original_data["name"])
        if original_data.get("NAME"):
            return str(original_data["NAME"])
        
        # Final fallback
        return f"Asset_{index + 1}"
    
    def _determine_asset_type_from_data(self, mapped_data: Dict[str, Any], original_data: Dict[str, Any]) -> str:
        """Determine asset type from available data"""
        # Check mapped data first
        asset_type = mapped_data.get("asset_type") or original_data.get("asset_type") or original_data.get("TYPE")
        
        if asset_type:
            asset_type_str = str(asset_type).upper()
            # Map common types
            if "SERVER" in asset_type_str or "SRV" in asset_type_str:
                return "SERVER"
            elif "DATABASE" in asset_type_str or "DB" in asset_type_str:
                return "DATABASE"
            elif "NETWORK" in asset_type_str or "NET" in asset_type_str:
                return "NETWORK"
            elif "STORAGE" in asset_type_str:
                return "STORAGE"
            elif "APPLICATION" in asset_type_str or "APP" in asset_type_str:
                return "APPLICATION"
            elif "VIRTUAL" in asset_type_str or "VM" in asset_type_str:
                return "VIRTUAL_MACHINE"
        
        # Default fallback
        return "SERVER"
    
    def _safe_int(self, value) -> Optional[int]:
        """Safely convert value to integer"""
        if value is None:
            return None
        try:
            return int(float(str(value)))
        except (ValueError, TypeError):
            return None
    
    def _safe_float(self, value) -> Optional[float]:
        """Safely convert value to float"""
        if value is None:
            return None
        try:
            return float(str(value))
        except (ValueError, TypeError):
            return None

    @listen(create_discovery_assets_from_cleaned_data)
    async def promote_discovery_assets_to_assets(self, previous_result):
        """Promote discovery assets to final assets table for migration planning"""
        logger.info("🚀 Promoting Discovery Assets to Final Assets Table")
        self.state.current_phase = "dependencies"
        
        # REAL-TIME UPDATE: Update database immediately when phase starts
        if self.flow_bridge:
            await self.flow_bridge.update_flow_state(self.state)
        
        try:
            # Import required modules
            from app.services.asset_creation_bridge_service import AssetCreationBridgeService
            from app.core.database import AsyncSessionLocal
            import uuid as uuid_pkg
            from datetime import datetime
            
            async with AsyncSessionLocal() as db_session:
                try:
                    # Initialize asset creation bridge service
                    bridge_service = AssetCreationBridgeService(db_session, self._init_context)
                    
                    # Create assets from discovery flow
                    creation_result = await bridge_service.create_assets_from_discovery(
                        discovery_flow_id=uuid_pkg.UUID(self.state.flow_id),
                        user_id=uuid_pkg.UUID(self.state.user_id) if self.state.user_id and self.state.user_id != "anonymous" else None
                    )
                    
                    # Ensure UUID serialization safety for creation_result
                    safe_creation_result = self._ensure_uuid_serialization_safety_for_dict(creation_result)
                    
                    # Store results in flow state
                    self.state.asset_inventory = {
                        "assets_promoted": safe_creation_result.get("statistics", {}).get("assets_created", 0),
                        "assets_skipped": safe_creation_result.get("statistics", {}).get("assets_skipped", 0),
                        "assets_errored": safe_creation_result.get("statistics", {}).get("errors", 0),
                        "success": safe_creation_result.get("success", False),
                        "timestamp": datetime.utcnow().isoformat(),
                        "phase": "dependencies",
                        "details": safe_creation_result
                    }
                    
                    # Mark phase as completed
                    self.state.phase_completion["asset_inventory"] = True
                    self.state.progress_percentage = 80.0
                    
                    # Ensure full state UUID safety before persistence
                    self._ensure_uuid_serialization_safety()
                    
                    # REAL-TIME UPDATE: Persist state with asset promotion results
                    if self.flow_bridge:
                        await self.flow_bridge.update_flow_state(self.state)
                    
                    logger.info(f"✅ Asset promotion completed: {safe_creation_result.get('statistics', {}).get('assets_created', 0)} assets created")
                    return f"dependencies_completed_{safe_creation_result.get('statistics', {}).get('assets_created', 0)}_assets"
                    
                except Exception as e:
                    await db_session.rollback()
                    logger.error(f"❌ Database error during asset promotion: {e}")
                    raise
                    
        except Exception as e:
            logger.error(f"❌ Asset promotion failed: {e}")
            self.state.add_error("dependencies", f"Asset promotion failed: {str(e)}")
            
            # Ensure UUID safety even on error
            self._ensure_uuid_serialization_safety()
            
            # REAL-TIME UPDATE: Update database even on failure
            if self.flow_bridge:
                await self.flow_bridge.update_flow_state(self.state)
            
            return "dependencies_failed"

    @listen(promote_discovery_assets_to_assets)
    async def execute_parallel_analysis_agents(self, previous_result):
        """Execute asset inventory, dependency, and tech debt analysis agents in parallel"""
        logger.info("🤖 Starting Parallel Analysis Agents (Asset, Dependency, Tech Debt)")
        self.state.current_phase = "tech_debt"
        
        # REAL-TIME UPDATE: Update database immediately when phase starts
        if self.flow_bridge:
            await self.flow_bridge.update_flow_state(self.state)
        
        try:
            # Prepare common agent data
            agent_data = {
                'raw_data': self.state.cleaned_data or self.state.raw_data,
                'field_mappings': self.state.field_mappings,
                'validation_results': self.state.data_validation_results,
                'cleansing_results': self.state.data_cleansing_results,
                'flow_metadata': {
                    'session_id': self.state.session_id,
                    'flow_id': self.state.flow_id
                }
            }
            
            # Execute agents in parallel
            logger.info("🔄 Executing 3 analysis agents in parallel...")
            results = await asyncio.gather(
                self.asset_inventory_agent.execute_analysis(agent_data, self._init_context),
                self.dependency_analysis_agent.execute_analysis(agent_data, self._init_context),
                self.tech_debt_analysis_agent.execute_analysis(agent_data, self._init_context),
                return_exceptions=True
            )
            
            # Process results
            asset_result, dependency_result, tech_debt_result = results
            
            # Store asset inventory results
            if not isinstance(asset_result, Exception):
                # Ensure UUID safety for agent result data
                safe_asset_data = self._ensure_uuid_serialization_safety_for_dict(asset_result.data) if hasattr(asset_result, 'data') else {}
                self.state.asset_inventory = safe_asset_data
                self.state.agent_confidences['asset_inventory'] = asset_result.confidence_score
                self.state.phase_completion['asset_inventory'] = True
                if asset_result.insights_generated:
                    safe_insights = [self._ensure_uuid_serialization_safety_for_dict(insight.model_dump()) for insight in asset_result.insights_generated]
                    self.state.agent_insights.extend(safe_insights)
                if asset_result.clarifications_requested:
                    safe_clarifications = [self._ensure_uuid_serialization_safety_for_dict(req.model_dump()) for req in asset_result.clarifications_requested]
                    self.state.user_clarifications.extend(safe_clarifications)
                logger.info(f"✅ Asset inventory agent completed (confidence: {asset_result.confidence_score:.1f}%)")
            else:
                logger.error(f"❌ Asset inventory agent failed: {asset_result}")
                self.state.add_error("asset_inventory", f"Agent failed: {str(asset_result)}")
            
            # Store dependency analysis results
            if not isinstance(dependency_result, Exception):
                # Ensure UUID safety for agent result data
                safe_dependency_data = self._ensure_uuid_serialization_safety_for_dict(dependency_result.data) if hasattr(dependency_result, 'data') else {}
                self.state.dependency_analysis = safe_dependency_data
                self.state.agent_confidences['dependency_analysis'] = dependency_result.confidence_score
                self.state.phase_completion['dependency_analysis'] = True
                if dependency_result.insights_generated:
                    safe_insights = [self._ensure_uuid_serialization_safety_for_dict(insight.model_dump()) for insight in dependency_result.insights_generated]
                    self.state.agent_insights.extend(safe_insights)
                if dependency_result.clarifications_requested:
                    safe_clarifications = [self._ensure_uuid_serialization_safety_for_dict(req.model_dump()) for req in dependency_result.clarifications_requested]
                    self.state.user_clarifications.extend(safe_clarifications)
                logger.info(f"✅ Dependency analysis agent completed (confidence: {dependency_result.confidence_score:.1f}%)")
            else:
                logger.error(f"❌ Dependency analysis agent failed: {dependency_result}")
                self.state.add_error("dependency_analysis", f"Agent failed: {str(dependency_result)}")
            
            # Store tech debt analysis results
            if not isinstance(tech_debt_result, Exception):
                # Ensure UUID safety for agent result data
                safe_tech_debt_data = self._ensure_uuid_serialization_safety_for_dict(tech_debt_result.data) if hasattr(tech_debt_result, 'data') else {}
                self.state.tech_debt_analysis = safe_tech_debt_data
                self.state.agent_confidences['tech_debt_analysis'] = tech_debt_result.confidence_score
                self.state.phase_completion['tech_debt_analysis'] = True
                if tech_debt_result.insights_generated:
                    safe_insights = [self._ensure_uuid_serialization_safety_for_dict(insight.model_dump()) for insight in tech_debt_result.insights_generated]
                    self.state.agent_insights.extend(safe_insights)
                if tech_debt_result.clarifications_requested:
                    safe_clarifications = [self._ensure_uuid_serialization_safety_for_dict(req.model_dump()) for req in tech_debt_result.clarifications_requested]
                    self.state.user_clarifications.extend(safe_clarifications)
                logger.info(f"✅ Tech debt analysis agent completed (confidence: {tech_debt_result.confidence_score:.1f}%)")
                return "parallel_analysis_completed"
            else:
                logger.error(f"❌ Tech debt analysis agent failed: {tech_debt_result}")
                self.state.add_error("tech_debt_analysis", f"Agent failed: {str(tech_debt_result)}")
                return "tech_debt_analysis_failed"
            
            # Update progress after all agents complete
            self.state.progress_percentage = 90.0
            
            # Ensure UUID safety before persistence
            self._ensure_uuid_serialization_safety()
            
            # REAL-TIME UPDATE: Persist state with all agent insights and progress
            if self.flow_bridge:
                await self.flow_bridge.update_flow_state(self.state)
            
            return "parallel_analysis_completed"
            
        except Exception as e:
            logger.error(f"❌ Parallel analysis agents failed: {e}")
            self.state.add_error("analysis", f"Parallel execution failed: {str(e)}")
            
            # Ensure UUID safety even on error
            self._ensure_uuid_serialization_safety()
            
            # REAL-TIME UPDATE: Update database even on failure
            if self.flow_bridge:
                await self.flow_bridge.update_flow_state(self.state)
            
            return "parallel_analysis_failed"

    # Add new agent execution methods
    async def execute_data_import_validation_agent_method(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute data import validation agent"""
        result = await self.data_validation_agent.execute_analysis(data, context)
        return result.to_dict()
    
    async def execute_attribute_mapping_agent_method(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute attribute mapping agent"""
        result = await self.attribute_mapping_agent.execute_analysis(data, context)
        return result.to_dict()
    
    async def execute_data_cleansing_agent_method(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute data cleansing agent"""
        result = await self.data_cleansing_agent.execute_analysis(data, context)
        return result.to_dict()
    
    async def execute_parallel_analysis_agents_method(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute asset inventory, dependency, and tech debt analysis agents in parallel"""
        results = await asyncio.gather(
            self.asset_inventory_agent.execute_analysis(data, context),
            self.dependency_analysis_agent.execute_analysis(data, context),
            self.tech_debt_analysis_agent.execute_analysis(data, context),
            return_exceptions=True
        )
        
        return {
            'asset_inventory': results[0].to_dict() if not isinstance(results[0], Exception) else {'error': str(results[0])},
            'dependency_analysis': results[1].to_dict() if not isinstance(results[1], Exception) else {'error': str(results[1])},
            'tech_debt_analysis': results[2].to_dict() if not isinstance(results[2], Exception) else {'error': str(results[2])}
        }

    async def approve_attribute_mapping_and_complete(self, user_approval_data: Dict[str, Any] = None):
        """Called when user approves attribute mapping - completes the discovery flow"""
        logger.info("👍 User approved attribute mapping - completing discovery flow")
        
        # Store user approval data if provided
        if user_approval_data:
            self.state.user_approval_data = user_approval_data
            logger.info(f"📝 User approval data stored: {len(user_approval_data)} items")
        
        # Mark that user approval has been received
        self.state.user_approval_received = True
        self.state.awaiting_user_approval = False
        
        # Call the finalize discovery method
        result = await self.finalize_discovery_internal("user_approved_attribute_mapping")
        
        return result

    @listen(execute_parallel_analysis_agents)
    async def check_user_approval_needed(self, previous_result):
        """Check if user approval is needed after parallel analysis"""
        logger.info("🔍 Checking if user approval is needed for attribute mapping...")
        
        # Always require user approval for attribute mapping validation
        needs_approval = await self._check_if_user_approval_needed(previous_result)
        
        if needs_approval:
            logger.info("⏸️ User approval required - pausing flow for attribute mapping validation")
            await self._pause_for_user_approval(previous_result)
            return "awaiting_user_approval_in_attribute_mapping"
        else:
            logger.info("✅ No user approval needed - proceeding to finalization")
            return await self.finalize_discovery_internal(previous_result)

    async def _check_if_user_approval_needed(self, previous_result: str) -> bool:
        """
        Determine if user approval is needed based on flow state and results
        
        For Discovery Flow, we ALWAYS require user approval for attribute mapping
        to ensure users can review and validate the field mappings before proceeding.
        """
        logger.info("🔍 Evaluating need for user approval...")
        
        # ALWAYS require user approval for attribute mapping phase
        # This ensures users can review field mappings and data quality
        approval_required = True
        
        # Log the decision
        if approval_required:
            logger.info("⏸️ User approval REQUIRED for attribute mapping validation")
            logger.info("📋 User needs to review:")
            logger.info("   - Field mapping accuracy and completeness")
            logger.info("   - Data quality assessment results")
            logger.info("   - Asset classification confidence")
            logger.info("   - Any validation warnings or issues")
        else:
            logger.info("✅ User approval NOT required - proceeding automatically")
        
        return approval_required

    async def _pause_for_user_approval(self, previous_result: str):
        """
        Pause the flow for user approval and set appropriate state
        """
        logger.info("⏸️ Pausing Discovery Flow for user approval...")
        
        # Update flow state to indicate waiting for user approval
        self.state.status = "waiting_for_user"
        self.state.awaiting_user_approval = True
        self.state.current_phase = "attribute_mapping"
        self.state.progress_percentage = 85.0  # High progress but not complete
        
        # Add comprehensive approval context
        approval_context = {
            "approval_type": "attribute_mapping_validation",
            "required_reviews": [
                "field_mapping_accuracy",
                "data_quality_assessment", 
                "asset_classification_confidence",
                "validation_warnings"
            ],
            "field_mappings": self.state.field_mappings,
            "data_validation_results": self.state.data_validation_results,
            "agent_insights": self.state.agent_insights[-10:],  # Last 10 insights
            "user_clarifications": self.state.user_clarifications,
            "next_phase": "data_cleansing",
            "estimated_completion_time": "5-10 minutes after approval"
        }
        
        self.state.user_approval_data = approval_context
        
        # Add user-facing insight about the pause
        try:
            from app.services.agent_ui_bridge import agent_ui_bridge
            agent_ui_bridge.add_agent_insight(
                agent_id="discovery_flow_manager",
                agent_name="Discovery Flow Manager",
                insight_type="user_action_required",
                page=f"flow_{self.state.flow_id}",
                title="User Approval Required",
                description="Please review the attribute mapping results and data quality assessment before proceeding to the next phase.",
                supporting_data={
                    'phase': 'attribute_mapping',
                    'approval_type': 'mapping_validation',
                    'progress_percentage': 85.0,
                    'next_action': 'user_review_and_approval',
                    'review_items': approval_context["required_reviews"]
                },
                confidence="high"
            )
        except Exception as e:
            logger.warning(f"⚠️ Could not add user approval insight: {e}")
        
        # CRITICAL: Update the database state to reflect the pause
        await self._safe_update_flow_state()
        
        logger.info("⏸️ Flow successfully paused - waiting for user approval in attribute mapping phase")
        logger.info(f"📋 Approval context prepared with {len(approval_context['required_reviews'])} review items")
    
    async def finalize_discovery_internal(self, previous_result):
        """
        Internal method to finalize discovery flow with conditional logic.
        Makes PostgreSQL flow subservient to CrewAI flow decisions.
        """
        try:
            logger.info(f"🔍 Finalizing discovery flow: {self.state.flow_id}")
            
            # Create comprehensive summary
            total_assets = len(self.state.asset_inventory.get("assets", []))
            summary = {
                "flow_id": self.state.flow_id,
                "total_assets": total_assets,
                "phases_completed": list(self.state.phase_completion.keys()),
                "errors": self.state.errors,
                "warnings": self.state.warnings,
                "agent_insights": self.state.agent_insights,
                "final_status": "awaiting_user_approval_in_attribute_mapping"
            }
            
            # Update final state with summary
            self.state.discovery_summary = summary
            self.state.final_result = "awaiting_user_approval_in_attribute_mapping"
            
            # ✅ CRITICAL FIX: Make PostgreSQL flow subservient to CrewAI conditional logic
            # Instead of completing tech_debt phase (which triggers 100% completion),
            # set flow to waiting_for_user in attribute_mapping with 90% progress
            
            if self.flow_bridge:
                try:
                    from app.services.discovery_flow_service import DiscoveryFlowService
                    from app.core.context import RequestContext
                    from app.core.database import AsyncSessionLocal
                    
                    async with AsyncSessionLocal() as session:
                        context = RequestContext(
                            client_account_id=self.state.client_account_id,
                            engagement_id=self.state.engagement_id,
                            user_id=self.state.user_id
                        )
                        
                        flow_service = DiscoveryFlowService(session, context)
                        
                        # ✅ INSTEAD OF: Updating tech_debt phase (which triggers 100% completion)
                        # ❌ await flow_service.update_phase_completion(
                        # ❌     flow_id=self.state.flow_id,
                        # ❌     phase="tech_debt",  # This would trigger 100% completion
                        # ❌     phase_data={...}
                        # ❌ )
                        
                        # ✅ DO THIS: Update flow to waiting_for_user in attribute_mapping with 90% progress
                        # This keeps the flow from auto-completing while preserving all CrewAI analysis results
                        
                        # First, store the CrewAI analysis results in the flow state
                        crewai_analysis_results = {
                            "crewai_summary": summary,
                            "total_assets": total_assets,
                            "asset_inventory": self.state.asset_inventory,
                            "dependencies": self.state.dependencies,
                            "technical_debt": self.state.technical_debt,
                            "field_mappings": self.state.field_mappings,
                            "analysis_complete": True,
                            "awaiting_user_approval": True,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        # Update flow to waiting_for_user status with high progress but not 100%
                        flow = await flow_service.get_flow_by_id(self.state.flow_id)
                        if flow:
                            # Use repository directly to set custom status and progress
                            from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
                            flow_repo = DiscoveryFlowRepository(session, self.state.client_account_id, self.state.engagement_id)
                            
                            # Custom update that doesn't trigger auto-completion
                            from sqlalchemy import update
                            from app.models.discovery_flow import DiscoveryFlow
                            
                            await session.execute(
                                update(DiscoveryFlow).where(
                                    DiscoveryFlow.flow_id == self.state.flow_id
                                ).values(
                                    status="waiting_for_user",
                                    progress_percentage=90.0,  # High progress but not 100%
                                    crewai_state_data=crewai_analysis_results,
                                    updated_at=datetime.utcnow()
                                )
                            )
                            await session.commit()
                            
                            logger.info(f"✅ PostgreSQL flow set to waiting_for_user in attribute_mapping (90% progress)")
                            logger.info(f"📊 CrewAI analysis results stored for user review")
                        
                        next_phase = "attribute_mapping"
                        
                        # Update CrewAI state - CrewAI flow completes but PostgreSQL flow waits for user
                        self.state.status = "completed"  # CrewAI flow completes
                        self.state.current_phase = "completed"  # CrewAI flow is done
                        
                        logger.info(f"✅ PostgreSQL discovery flow updated - next phase: {next_phase}")
                        logger.info(f"🎯 Flow will wait for user approval in {next_phase} phase")
                        
                except Exception as update_error:
                    logger.warning(f"⚠️ Failed to update PostgreSQL flow state: {update_error}")
                    # Fallback: CrewAI flow completes, PostgreSQL flow waits for user
                    self.state.status = "completed"
                    self.state.current_phase = "completed"
            else:
                # Fallback if no flow bridge - CrewAI flow completes
                self.state.status = "completed" 
                self.state.current_phase = "completed"
                
            logger.info(f"✅ Unified Discovery Flow CrewAI processing completed successfully")
            logger.info(f"📊 CrewAI Analysis Summary: {total_assets} assets, {len(self.state.errors)} errors, {len(self.state.warnings)} warnings")
            logger.info(f"🔄 Flow Status: {self.state.status.upper()}")
            logger.info(f"➡️  Next Phase: {self.state.current_phase}")
            
            logger.info(f"🎉 CrewAI Discovery Flow completed successfully")
            logger.info(f"⏸️  PostgreSQL Discovery Flow set to waiting_for_user in attribute_mapping phase")
            logger.info(f"👥 Users can now review discovered assets and approve field mappings")
            logger.info(f"🔄 Next: User approval will trigger final discovery flow completion")
            
            # ✅ CRITICAL FIX: Return the exact string that the event listener expects
            # This ensures the FlowFinishedEvent handler recognizes the flow should pause for user approval
            return "awaiting_user_approval_in_attribute_mapping"
            
        except Exception as e:
            logger.error(f"❌ Discovery flow finalization failed: {e}")
            self.state.add_error("finalization", str(e))
            self.state.status = "failed"
            return "discovery_failed"
    


    # ========================================
    # FLOW MANAGEMENT METHODS (Enhanced with PostgreSQL Bridge)
    # ========================================

    async def pause_flow(self, reason: str = "user_requested"):
        """Pause the discovery flow with PostgreSQL persistence"""
        logger.info(f"⏸️ Pausing Unified Discovery Flow: {reason}")
        self.state.status = "paused"
        
        # Sync pause state to PostgreSQL
        if self.flow_bridge:
            try:
                await self.flow_bridge.sync_state_update(
                    self.state, 
                    self.state.current_phase, 
                    crew_results={"action": "paused", "reason": reason}
                )
            except Exception as e:
                logger.warning(f"⚠️ Failed to sync pause state: {e}")
        
        # Delegate to flow management for additional handling
        return self.flow_management.pause_flow(reason)

    async def resume_flow_from_state(self, resume_context: Dict[str, Any]):
        """Resume flow from saved state with PostgreSQL recovery"""
        logger.info("▶️ Resuming Unified Discovery Flow from saved state")
        
        # Try to recover state from PostgreSQL if needed
        if self.flow_bridge and resume_context.get("recover_from_postgresql", False):
            try:
                recovered_state = await self.flow_bridge.recover_flow_state(self.state.session_id)
                if recovered_state:
                    self.state = recovered_state
                    logger.info("✅ State recovered from PostgreSQL")
            except Exception as e:
                logger.warning(f"⚠️ Failed to recover state from PostgreSQL: {e}")
        
        self.state.status = "running"
        
        # Sync resume state to PostgreSQL
        if self.flow_bridge:
            try:
                await self.flow_bridge.sync_state_update(
                    self.state, 
                    self.state.current_phase, 
                    crew_results={"action": "resumed", "context": resume_context}
                )
            except Exception as e:
                logger.warning(f"⚠️ Failed to sync resume state: {e}")
        
        # Delegate to flow management for additional handling
        return self.flow_management.resume_flow_from_state(resume_context)

    async def get_flow_management_info(self) -> Dict[str, Any]:
        """Get flow management information with PostgreSQL validation"""
        # Get base info from flow management
        base_info = self.flow_management.get_flow_management_info()
        
        # Add PostgreSQL persistence status
        if self.flow_bridge:
            try:
                validation_result = await self.flow_bridge.validate_state_integrity(self.state.session_id)
                base_info["postgresql_persistence"] = {
                    "available": True,
                    "state_valid": validation_result.get("overall_valid", False),
                    "last_validation": validation_result.get("validation_timestamp")
                }
            except Exception as e:
                base_info["postgresql_persistence"] = {
                    "available": False,
                    "error": str(e)
                }
        else:
            base_info["postgresql_persistence"] = {"available": False}
        
        return base_info
    
    async def validate_flow_integrity(self) -> Dict[str, Any]:
        """Validate flow integrity across CrewAI and PostgreSQL persistence layers"""
        if not self.flow_bridge:
            return {
                "status": "bridge_unavailable",
                "message": "Flow State Bridge not available for validation"
            }
        
        try:
            # Validate overall flow integrity
            validation_result = await self.flow_bridge.validate_state_integrity(self.state.session_id)
            
            # Add phase executor validation
            phase_validation = await self.phase_executor.validate_phase_integrity(self.state.session_id)
            validation_result["phase_executors"] = phase_validation.get("phase_executors", {})
            
            return validation_result
            
        except Exception as e:
            logger.error(f"❌ Flow integrity validation failed: {e}")
            return {
                "status": "validation_error",
                "error": str(e)
            }
    
    async def cleanup_flow_state(self, expiration_hours: int = 72) -> Dict[str, Any]:
        """Clean up expired flow state data"""
        if not self.flow_bridge:
            return {
                "status": "bridge_unavailable",
                "message": "Flow State Bridge not available for cleanup"
            }
        
        try:
            cleanup_result = await self.phase_executor.cleanup_phase_states(
                self.state.session_id, 
                expiration_hours
            )
            
            logger.info(f"✅ Flow state cleanup completed: {cleanup_result}")
            return cleanup_result
            
        except Exception as e:
            logger.error(f"❌ Flow state cleanup failed: {e}")
            return {
                "status": "cleanup_error",
                "error": str(e)
            }
    
    # === CREW ESCALATION METHODS (Task 2.3) ===
    
    async def get_flow_state(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Get flow state for escalation validation"""
        try:
            if self.state.session_id == flow_id:
                return {
                    "flow_id": flow_id,
                    "session_id": self.state.session_id,
                    "status": "active",
                    "current_phase": getattr(self.state, 'current_phase', 'unknown'),
                    "client_account_id": self.state.client_account_id,
                    "engagement_id": self.state.engagement_id,
                    "user_id": self.state.user_id
                }
            return None
        except Exception as e:
            logger.error(f"❌ Error getting flow state: {e}")
            return None
    
    async def update_escalation_status(self, flow_id: str, escalation_id: str, 
                                     status: str, crew_type: str = None, 
                                     collaboration_crews: List[str] = None) -> bool:
        """Update flow state with escalation information"""
        try:
            if not hasattr(self.state, 'escalations'):
                self.state.escalations = {}
            
            self.state.escalations[escalation_id] = {
                "escalation_id": escalation_id,
                "status": status,
                "crew_type": crew_type,
                "collaboration_crews": collaboration_crews or [],
                "updated_at": datetime.utcnow().isoformat(),
                "flow_id": flow_id
            }
            
            # Persist escalation state if bridge is available
            if self.flow_bridge:
                await self.flow_bridge.persist_escalation_state(
                    self.state.session_id, 
                    escalation_id, 
                    self.state.escalations[escalation_id]
                )
            
            logger.info(f"✅ Updated escalation status: {escalation_id} -> {status}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating escalation status: {e}")
            return False
    
    def plot(self, filename: str = "unified_discovery_flow"):
        """
        Generate a visualization of the Discovery Flow structure.
        Creates an HTML file showing the flow steps, relationships, and data flow.
        
        Args:
            filename: Name of the output HTML file (without extension)
        """
        try:
            # Use CrewAI's built-in plot functionality if available
            if hasattr(super(), 'plot'):
                super().plot(filename)
                logger.info(f"✅ Flow visualization saved to {filename}.html")
            else:
                logger.warning("⚠️ CrewAI plot functionality not available - creating custom visualization")
                self._create_custom_plot(filename)
        except Exception as e:
            logger.error(f"❌ Failed to create flow plot: {e}")
            # Fallback to custom visualization
            self._create_custom_plot(filename)
    
    def _create_custom_plot(self, filename: str):
        """Create a custom HTML visualization of the flow"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Force Migration Platform - Discovery Flow</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .flow-container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .flow-title {{ text-align: center; color: #2c3e50; margin-bottom: 30px; }}
                .phase {{ margin: 20px 0; padding: 15px; border-radius: 8px; position: relative; }}
                .phase-start {{ background: #e8f5e8; border-left: 4px solid #27ae60; }}
                .phase-validation {{ background: #e3f2fd; border-left: 4px solid #2196f3; }}
                .phase-mapping {{ background: #fff3e0; border-left: 4px solid #ff9800; }}
                .phase-cleansing {{ background: #fce4ec; border-left: 4px solid #e91e63; }}
                .phase-inventory {{ background: #f3e5f5; border-left: 4px solid #9c27b0; }}
                .phase-dependencies {{ background: #e0f2f1; border-left: 4px solid #009688; }}
                .phase-techdebt {{ background: #fff8e1; border-left: 4px solid #ffc107; }}
                .phase-finalize {{ background: #efebe9; border-left: 4px solid #795548; }}
                .phase-title {{ font-weight: bold; font-size: 1.2em; margin-bottom: 10px; }}
                .phase-description {{ color: #666; margin-bottom: 10px; }}
                .phase-details {{ font-size: 0.9em; color: #777; }}
                .flow-arrow {{ text-align: center; font-size: 1.5em; color: #3498db; margin: 10px 0; }}
                .data-flow {{ background: #f8f9fa; padding: 10px; margin: 10px 0; border-radius: 4px; border-left: 3px solid #6c757d; }}
                .crew-info {{ background: #e7f3ff; padding: 8px; margin: 5px 0; border-radius: 4px; font-size: 0.85em; }}
                .state-info {{ background: #f0f8f0; padding: 8px; margin: 5px 0; border-radius: 4px; font-size: 0.85em; }}
            </style>
        </head>
        <body>
            <div class="flow-container">
                <h1 class="flow-title">🚀 AI Force Migration Platform - Discovery Flow</h1>
                <p style="text-align: center; color: #666; margin-bottom: 40px;">
                    Comprehensive asset discovery workflow with CrewAI agents and PostgreSQL persistence
                </p>
                
                <div class="phase phase-start">
                    <div class="phase-title">🎯 1. Initialize Discovery (@start)</div>
                    <div class="phase-description">Set up flow state and validate input data</div>
                    <div class="state-info">
                        <strong>State Updates:</strong> flow_id, session_id, client_account_id, engagement_id, user_id, raw_data, metadata
                    </div>
                    <div class="phase-details">
                        • PostgreSQL persistence initialization<br>
                        • Flow State Bridge setup<br>
                        • Input data validation<br>
                        • Context establishment
                    </div>
                </div>
                
                <div class="flow-arrow">⬇️</div>
                
                <div class="phase phase-validation">
                    <div class="phase-title">🔍 2. Data Import Validation (@listen)</div>
                    <div class="phase-description">PII detection, security scanning, and data type validation</div>
                    <div class="crew-info">
                        <strong>Crew:</strong> Data Import Validation Crew (data_import_validation)
                    </div>
                    <div class="data-flow">
                        <strong>Input:</strong> raw_data, metadata<br>
                        <strong>Output:</strong> validation_results, security_status, detected_fields
                    </div>
                    <div class="phase-details">
                        • File type detection and analysis<br>
                        • Security threat assessment<br>
                        • Data quality metrics<br>
                        • Field structure analysis
                    </div>
                </div>
                
                <div class="flow-arrow">⬇️</div>
                
                <div class="phase phase-mapping">
                    <div class="phase-title">🗺️ 3. Field Mapping (@listen)</div>
                    <div class="phase-description">Intelligent field mapping to critical migration attributes</div>
                    <div class="crew-info">
                        <strong>Crew:</strong> Field Mapping Crew (attribute_mapping) - OPTIMIZED
                    </div>
                    <div class="data-flow">
                        <strong>Input:</strong> raw_data, validation_results<br>
                        <strong>Output:</strong> field_mappings, confidence_scores
                    </div>
                    <div class="phase-details">
                        • 20+ critical attribute mapping<br>
                        • AI-powered field recognition<br>
                        • Confidence scoring<br>
                        • Learning pattern integration
                    </div>
                </div>
                
                <div class="flow-arrow">⬇️</div>
                
                <div class="phase phase-cleansing">
                    <div class="phase-title">🧹 4. Data Cleansing (@listen)</div>
                    <div class="phase-description">Data quality improvement and standardization</div>
                    <div class="crew-info">
                        <strong>Crew:</strong> Data Cleansing Crew (data_cleansing) - OPTIMIZED
                    </div>
                    <div class="data-flow">
                        <strong>Input:</strong> raw_data, field_mappings<br>
                        <strong>Output:</strong> cleaned_data, quality_metrics
                    </div>
                    <div class="phase-details">
                        • Data standardization<br>
                        • Quality metrics generation<br>
                        • Format normalization<br>
                        • Completeness assessment
                    </div>
                </div>
                
                <div class="flow-arrow">⬇️</div>
                
                <div class="phase phase-inventory">
                    <div class="phase-title">📦 5. Asset Inventory (@listen)</div>
                    <div class="phase-description">Asset classification and inventory building</div>
                    <div class="crew-info">
                        <strong>Crew:</strong> Inventory Building Crew (inventory)
                    </div>
                    <div class="data-flow">
                        <strong>Input:</strong> cleaned_data, field_mappings<br>
                        <strong>Output:</strong> asset_inventory (servers, applications, devices)
                    </div>
                    <div class="phase-details">
                        • Asset type classification<br>
                        • Inventory categorization<br>
                        • Metadata enrichment<br>
                        • Asset counting and validation
                    </div>
                </div>
                
                <div class="flow-arrow">⬇️</div>
                
                <div class="phase phase-dependencies">
                    <div class="phase-title">🔗 6. Dependency Analysis (@listen)</div>
                    <div class="phase-description">Application and infrastructure dependency mapping</div>
                    <div class="crew-info">
                        <strong>Crew:</strong> App Server Dependency Crew (dependencies)
                    </div>
                    <div class="data-flow">
                        <strong>Input:</strong> asset_inventory<br>
                        <strong>Output:</strong> dependencies, dependency_map
                    </div>
                    <div class="phase-details">
                        • Dependency relationship mapping<br>
                        • Critical path identification<br>
                        • Migration impact analysis<br>
                        • Risk assessment preparation
                    </div>
                </div>
                
                <div class="flow-arrow">⬇️</div>
                
                <div class="phase phase-techdebt">
                    <div class="phase-title">⚠️ 7. Tech Debt Analysis (@listen)</div>
                    <div class="phase-description">Technical debt assessment and modernization recommendations</div>
                    <div class="crew-info">
                        <strong>Crew:</strong> Technical Debt Crew (tech_debt)
                    </div>
                    <div class="data-flow">
                        <strong>Input:</strong> asset_inventory, dependencies<br>
                        <strong>Output:</strong> technical_debt, modernization_recommendations
                    </div>
                    <div class="phase-details">
                        • Technical debt scoring<br>
                        • Modernization opportunity identification<br>
                        • 6R strategy preparation<br>
                        • Risk and complexity assessment
                    </div>
                </div>
                
                <div class="flow-arrow">⬇️</div>
                
                <div class="phase phase-finalize">
                    <div class="phase-title">🎯 8. Finalize Discovery (@listen)</div>
                    <div class="phase-description">Comprehensive summary and validation</div>
                    <div class="state-info">
                        <strong>Final State:</strong> status=completed, progress=100%, comprehensive summary
                    </div>
                    <div class="phase-details">
                        • Asset count validation<br>
                        • Quality metrics compilation<br>
                        • Error and warning summary<br>
                        • Discovery completion certification
                    </div>
                </div>
                
                <div style="margin-top: 40px; padding: 20px; background: #f8f9fa; border-radius: 8px;">
                    <h3>🔧 Technical Architecture</h3>
                    <ul>
                        <li><strong>Flow Pattern:</strong> Event-driven with @start and @listen decorators</li>
                        <li><strong>State Management:</strong> UnifiedDiscoveryFlowState with PostgreSQL persistence</li>
                        <li><strong>Crew Integration:</strong> 6 specialized crews for different phases</li>
                        <li><strong>Async Execution:</strong> Non-blocking crew operations with asyncio.to_thread</li>
                        <li><strong>Error Handling:</strong> Comprehensive fallback mechanisms</li>
                        <li><strong>Data Flow:</strong> raw_data → cleaned_data → asset_inventory → analysis results</li>
                    </ul>
                </div>
                
                <div style="margin-top: 20px; padding: 20px; background: #e7f3ff; border-radius: 8px;">
                    <h3>📊 Performance Metrics</h3>
                    <ul>
                        <li><strong>Processing Time:</strong> 30-45 seconds (optimized from 180+ seconds)</li>
                        <li><strong>Crew Utilization:</strong> 100% (all crews initialize successfully)</li>
                        <li><strong>Memory Efficiency:</strong> Memory system disabled for performance</li>
                        <li><strong>Delegation:</strong> Disabled for streamlined execution</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        
        try:
            with open(f"{filename}.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info(f"✅ Custom flow visualization saved to {filename}.html")
        except Exception as e:
            logger.error(f"❌ Failed to create custom plot: {e}")


# ========================================
# FACTORY FUNCTION
# ========================================

def create_unified_discovery_flow(
    session_id: str,
    client_account_id: str,
    engagement_id: str,
    user_id: str,
    raw_data: List[Dict[str, Any]],
    metadata: Dict[str, Any],
    crewai_service,
    context: RequestContext
) -> UnifiedDiscoveryFlow:
    """
    Factory function to create and initialize a Unified Discovery Flow.
    
    This replaces all previous factory functions and creates a single,
    properly configured CrewAI Flow instance with hybrid persistence.
    
    Features:
    - CrewAI @persist() for flow execution continuity
    - PostgreSQL persistence for multi-tenant enterprise requirements
    - Flow State Bridge for seamless integration
    - Comprehensive state validation and recovery
    """
    
    flow = UnifiedDiscoveryFlow(
        crewai_service=crewai_service,
        context=context,
        session_id=session_id,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        user_id=user_id,
        raw_data=raw_data,
        metadata=metadata
    )
    
    logger.info(f"✅ Unified Discovery Flow created with hybrid persistence: {session_id}")
    logger.info(f"🔄 Flow State Bridge: {'enabled' if flow.flow_bridge else 'disabled'}")
    logger.info(f"📊 Data records: {len(raw_data)}")
    
    return flow 