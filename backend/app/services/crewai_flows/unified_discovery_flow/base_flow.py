"""
Base Flow Module

The main UnifiedDiscoveryFlow class that orchestrates all phases.
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid

# CrewAI Flow imports - REAL AGENTS ONLY
logger = logging.getLogger(__name__)

try:
    from crewai import Flow
    from crewai.flow.flow import listen, start
    from crewai.flow.persistence import persist
    CREWAI_FLOW_AVAILABLE = True
    logger.info("✅ CrewAI Flow imports successful - REAL AGENTS ENABLED")
except ImportError as e:
    logger.error(f"❌ CrewAI Flow not available: {e}")
    logger.error("❌ CRITICAL: Cannot proceed without real CrewAI agents")
    raise ImportError(f"CrewAI is required for real agent execution: {e}")

# Verify we're not using pseudo-agents
if not CREWAI_FLOW_AVAILABLE:
    raise RuntimeError("❌ CRITICAL: Pseudo-agent fallback detected - real CrewAI required")

# Import state and configuration
from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState
from app.core.context import RequestContext
from .flow_config import FlowConfig, PhaseNames
from .state_management import StateManager
from .crew_coordination import CrewCoordinator
from .flow_management import FlowManager
from .flow_initialization import FlowInitializer
from .flow_finalization import FlowFinalizer

# Import phase modules
from .phases import (
    DataValidationPhase,
    FieldMappingPhase,
    DataCleansingPhase,
    AssetInventoryPhase,
    DependencyAnalysisPhase,
    TechDebtAssessmentPhase
)

# Import handlers for flow management
from ..handlers.unified_flow_management import UnifiedFlowManagement


class UnifiedDiscoveryFlow(Flow[UnifiedDiscoveryFlowState]):
    """
    Unified Discovery Flow with PostgreSQL-only persistence.
    Single source of truth for all discovery flow operations.
    
    This modularized version splits the monolithic flow into:
    - Configuration (flow_config.py)
    - State management (state_management.py)
    - Crew coordination (crew_coordination.py)
    - Individual phases (phases/*.py)
    """
    
    def __init__(self, crewai_service, context: RequestContext, **kwargs):
        """Initialize unified discovery flow with agent-first architecture"""
        
        # Initialize flow_id early to avoid attribute errors
        self._flow_id = kwargs.get('flow_id') or str(uuid.uuid4())
        
        # Initialize base CrewAI Flow - REAL AGENTS ONLY
        super().__init__()
        logger.info("✅ CrewAI Flow base class initialized - real agents active")
            
        logger.info("🚀 Initializing Unified Discovery Flow with Agent-First Architecture")
        
        # Store context and service
        self.crewai_service = crewai_service
        self.context = context
        
        # Use initializer for setup
        self.initializer = FlowInitializer(crewai_service, context, **kwargs)
        self._init_context = self.initializer.init_context
        
        # Initialize flow state - CrewAI Flow manages state internally
        # CrewAI Flow base class manages state - we'll configure it in initialize_discovery
        logger.info("🔄 Flow state will be managed by CrewAI Flow base class")
        
        # Initialize components
        self._initialize_components()
        
        # Initialize phase handlers
        self._initialize_phases()
        
        # Flow ID already set in __init__
        logger.info(f"✅ Unified Discovery Flow initialized - Flow ID: {self._flow_id}")
    
    @property
    def flow_id(self):
        """Get the flow ID"""
        return self._flow_id
    
    @property
    def state(self):
        """Get the flow state"""
        # Return the internal flow state if available, otherwise return a default
        if hasattr(self, '_flow_state'):
            return self._flow_state
        return getattr(self, '_flow_state', UnifiedDiscoveryFlowState())
    
    def _initialize_components(self):
        """Initialize flow components"""
        # Initialize flow bridge
        self.flow_bridge = self.initializer.initialize_flow_bridge()
        
        # Initialize handlers
        handlers = self.initializer.initialize_handlers()
        self.phase_executor = handlers['phase_executor']
        self.crew_manager = handlers['crew_manager']
        
        # Initialize flow management separately (will use state when available)
        self.flow_management = UnifiedFlowManagement(None)
        
        # Initialize state manager (will use state when available)
        self.state_manager = StateManager(None, self.flow_bridge)
        
        # Initialize crew coordinator
        self.crew_coordinator = CrewCoordinator(self.crewai_service, self.context)
        
        # Initialize flow manager (will use state when available)
        self.flow_manager = FlowManager(None, self.state_manager, self.flow_management)
        
        # Initialize flow finalizer (will use state when available)
        self.flow_finalizer = FlowFinalizer(None, self.state_manager)
        
        # Initialize agents
        agents = self.initializer.initialize_agents()
        self.orchestrator = agents['orchestrator']
        self.data_validation_agent = agents['data_validation_agent']
        self.attribute_mapping_agent = agents['attribute_mapping_agent']
        self.data_cleansing_agent = agents['data_cleansing_agent']
        self.asset_inventory_agent = agents['asset_inventory_agent']
        self.dependency_analysis_agent = agents['dependency_analysis_agent']
        self.tech_debt_analysis_agent = agents['tech_debt_analysis_agent']
    
    def _initialize_phases(self):
        """Initialize phase handlers"""
        # Create agents dict for phase initialization
        agents = {
            'data_validation_agent': self.data_validation_agent,
            'attribute_mapping_agent': self.attribute_mapping_agent,
            'data_cleansing_agent': self.data_cleansing_agent,
            'asset_inventory_agent': self.asset_inventory_agent,
            'dependency_analysis_agent': self.dependency_analysis_agent,
            'tech_debt_analysis_agent': self.tech_debt_analysis_agent
        }
        
        # Initialize phases (will use state when available)
        phases = self.initializer.initialize_phases(None, agents, self.flow_bridge)
        
        self.data_validation_phase = phases['data_validation_phase']
        self.field_mapping_phase = phases['field_mapping_phase']
        self.data_cleansing_phase = phases['data_cleansing_phase']
        self.asset_inventory_phase = phases['asset_inventory_phase']
        self.dependency_analysis_phase = phases['dependency_analysis_phase']
        self.tech_debt_assessment_phase = phases['tech_debt_assessment_phase']
    
    # ========================================
    # CREWAI FLOW METHODS (@start and @listen)
    # ========================================
    
    @start()
    async def initialize_discovery(self):
        """Initialize the discovery flow"""
        logger.info(f"🎯 [TRACE] Starting Unified Discovery Flow - @start method called for flow {self._flow_id}")
        logger.info(f"🔍 [TRACE] Flow kickoff initiated - this should trigger the entire flow chain")
        
        try:
            # Initialize state using CrewAI Flow's built-in state management
            # Check if we should load existing state from database first
            existing_state = None
            if hasattr(self, '_flow_id') and self._flow_id and self.flow_bridge:
                logger.info(f"🔍 Checking for existing flow state in database for flow {self._flow_id}")
                try:
                    existing_state = await self.flow_bridge.recover_flow_state(self._flow_id)
                    if existing_state:
                        logger.info(f"✅ Recovered existing flow state from database:")
                        logger.info(f"   - Current phase: {existing_state.current_phase}")
                        logger.info(f"   - Progress: {existing_state.progress_percentage}%")
                        logger.info(f"   - Raw data records: {len(existing_state.raw_data) if existing_state.raw_data else 0}")
                        logger.info(f"   - Field mappings exist: {bool(existing_state.field_mappings)}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not recover existing state: {e}")
            
            # Use existing state if found, otherwise create initial state
            if existing_state:
                initial_state = existing_state
                logger.info("🔄 Using recovered state from database")
                
                # If state doesn't have raw data but we passed it in, use the passed data
                if (not existing_state.raw_data or len(existing_state.raw_data) == 0) and self.initializer.raw_data:
                    logger.info(f"📋 State has no raw data, using {len(self.initializer.raw_data)} records passed to flow")
                    initial_state.raw_data = self.initializer.raw_data
                    
                # Load raw data from database if still empty
                if not initial_state.raw_data or len(initial_state.raw_data) == 0:
                    await self._load_raw_data_from_database(initial_state)
            else:
                initial_state = self.initializer.create_initial_state()
                logger.info("📋 Created new initial state")
            
            # Debug: Check if raw_data is in initial state
            logger.info(f"🔍 DEBUG: Initial state has {len(initial_state.raw_data) if initial_state.raw_data else 0} raw data records")
            if initial_state.raw_data and len(initial_state.raw_data) > 0:
                logger.info(f"✅ Raw data already present in initial state")
            else:
                logger.warning(f"⚠️ No raw data in initial state - data should be passed during flow creation")
            
            # Configure CrewAI Flow state with our initial data
            # CrewAI Flow manages state internally - we need to work with its patterns
            # Instead of setting self.state directly, we'll store our state separately
            self._flow_state = initial_state
            logger.info("✅ CrewAI Flow state initialized with structured state management")
            
            # Update component references to use actual state
            self.flow_management.state = self._flow_state
            self.state_manager.state = self._flow_state
            self.flow_manager.state = self._flow_state
            self.flow_finalizer.state = self._flow_state
            
            # Initialize UnifiedFlowCrewManager now that we have state
            from ..handlers.unified_flow_crew_manager import UnifiedFlowCrewManager
            self.crew_manager = UnifiedFlowCrewManager(self.crewai_service, self._flow_state)
            
            # Initialize PhaseExecutionManager now that we have state
            from ..handlers.phase_executors.phase_execution_manager import PhaseExecutionManager
            self.phase_executor = PhaseExecutionManager(self._flow_state, self.crew_manager, self.flow_bridge)
            
            # Re-initialize phases with actual state
            agents = {
                'data_validation_agent': self.data_validation_agent,
                'attribute_mapping_agent': self.attribute_mapping_agent,
                'data_cleansing_agent': self.data_cleansing_agent,
                'asset_inventory_agent': self.asset_inventory_agent,
                'dependency_analysis_agent': self.dependency_analysis_agent,
                'tech_debt_analysis_agent': self.tech_debt_analysis_agent
            }
            phases = self.initializer.initialize_phases(self._flow_state, agents, self.flow_bridge)
            self.data_validation_phase = phases['data_validation_phase']
            self.field_mapping_phase = phases['field_mapping_phase']
            self.data_cleansing_phase = phases['data_cleansing_phase']
            self.asset_inventory_phase = phases['asset_inventory_phase']
            self.dependency_analysis_phase = phases['dependency_analysis_phase']
            self.tech_debt_assessment_phase = phases['tech_debt_assessment_phase']
            
            # Update phase executor state references
            if hasattr(self, 'phase_executor') and self.phase_executor:
                self.phase_executor.state = self._flow_state
                # Update all individual phase executors
                for executor_name in ['data_import_validation_executor', 'field_mapping_executor', 
                                    'data_cleansing_executor', 'asset_inventory_executor',
                                    'dependency_analysis_executor', 'tech_debt_executor']:
                    if hasattr(self.phase_executor, executor_name):
                        executor = getattr(self.phase_executor, executor_name)
                        if executor:
                            executor.state = self._flow_state
                            logger.info(f"✅ Updated {executor_name} state reference")
            
            # Set initial state only if we didn't load existing state
            if not existing_state:
                self.state.status = "initialized"
                self.state.current_phase = "initialized"
                self.state.created_at = datetime.utcnow()
                self.state.updated_at = datetime.utcnow()
                
                # Generate flow_id if not set
                if not hasattr(self.state, 'flow_id') or not self.state.flow_id:
                    self.state.flow_id = self._init_context.get('flow_id') or str(uuid.uuid4())
            else:
                # Just update the timestamp for existing state
                self.state.updated_at = datetime.utcnow()
                logger.info(f"✅ Continuing existing flow from phase: {self.state.current_phase}")
            
            # Initialize with flow bridge only for new flows
            if self.flow_bridge and not existing_state:
                await self.flow_bridge.initialize_flow(self.state)
                logger.info(f"✅ New flow initialized with PostgreSQL bridge - Flow ID: {self.state.flow_id}")
            elif self.flow_bridge and existing_state:
                # For existing flows, just update the state
                await self.flow_bridge.update_flow_state(self.state)
                logger.info(f"✅ Existing flow state updated in PostgreSQL - Flow ID: {self.state.flow_id}")
            
            # Update state
            await self.state_manager.safe_update_flow_state()
            
            logger.info("✅ Discovery flow initialization completed")
            return "initialization_completed"
            
        except Exception as e:
            logger.error(f"❌ Discovery flow initialization failed: {e}")
            if hasattr(self, 'state_manager') and self.state_manager:
                self.state_manager.add_error("initialized", str(e))
            return "initialization_failed"
    
    @listen(initialize_discovery)
    async def execute_data_import_validation_agent(self, previous_result):
        """Execute data import validation phase using real CrewAI crews"""
        logger.info(f"📊 [TRACE] @listen(initialize_discovery) triggered - data import phase starting for flow {self._flow_id}")
        logger.info(f"🔍 [TRACE] Previous result from initialize_discovery: {previous_result}")
        try:
            # Use PhaseExecutionManager with real CrewAI crews instead of pseudo-agents
            result = await self.phase_executor.execute_data_import_validation_phase(previous_result)
            
            # Mark data import as completed
            self.state.phase_completion[PhaseNames.DATA_IMPORT_VALIDATION] = True
            self.state.data_import_completed = True
            self.state.progress_percentage = 16.7  # 1/6 phases complete
            
            await self.state_manager.safe_update_flow_state()
            
            # Check if phase failed
            if result == "data_validation_failed":
                self.state.status = "failed"
                self.state.final_result = "discovery_failed"
                await self.state_manager.safe_update_flow_state()
                return "discovery_failed"
                
            return result
        except Exception as e:
            logger.error(f"❌ Error in phase '{PhaseNames.DATA_IMPORT_VALIDATION}': {e}")
            self.state_manager.add_error(PhaseNames.DATA_IMPORT_VALIDATION, str(e))
            self.state.status = "failed"
            self.state.final_result = "discovery_failed"
            await self.state_manager.safe_update_flow_state()
            return "discovery_failed"
    
    @listen(execute_data_import_validation_agent)
    async def generate_field_mapping_suggestions(self, previous_result):
        """Generate initial field mapping suggestions before pausing for approval"""
        logger.info("🤖 Generating field mapping suggestions")
        
        # Debug: Check if raw_data is available
        logger.info(f"🔍 DEBUG: Raw data available: {len(self.state.raw_data) if hasattr(self.state, 'raw_data') and self.state.raw_data else 0} records")
        logger.info(f"🔍 DEBUG: Previous result: {previous_result}")
        
        # Debug: Check phase_data for data_import results
        if hasattr(self.state, 'phase_data') and 'data_import' in self.state.phase_data:
            data_import_results = self.state.phase_data['data_import']
            logger.info(f"🔍 DEBUG: Data import phase results: {list(data_import_results.keys()) if isinstance(data_import_results, dict) else 'Not a dict'}")
            logger.info(f"🔍 DEBUG: Total records from data import: {data_import_results.get('total_records', 0)}")
        
        if hasattr(self.state, 'raw_data') and self.state.raw_data and len(self.state.raw_data) > 0:
            logger.info(f"🔍 DEBUG: First record keys: {list(self.state.raw_data[0].keys())}")
        else:
            logger.warning("⚠️ No raw_data available in state, attempting to load from database")
            # Try to load from raw_import_records table
            await self._load_raw_data_from_import_records()
        
        # Update phase
        self.state.current_phase = PhaseNames.FIELD_MAPPING
        
        # Execute field mapping crew to generate suggestions
        mapping_result = await self.phase_executor.execute_field_mapping_phase(
            previous_result, 
            mode="suggestions_only"  # Special mode to only generate suggestions
        )
        
        # Debug: Log the full mapping result to identify structure issue
        logger.info(f"🔍 DEBUG: Full mapping_result structure: {mapping_result}")
        logger.info(f"🔍 DEBUG: mapping_result keys: {list(mapping_result.keys()) if isinstance(mapping_result, dict) else 'Not a dict'}")
        
        # Extract mapping suggestions and clarifications
        suggested_mappings = mapping_result.get("mappings", {})
        clarification_questions = mapping_result.get("clarifications", [])
        confidence_scores = mapping_result.get("confidence_scores", {})
        
        # Debug: Log what we extracted
        logger.info(f"🔍 DEBUG: Extracted mappings: {suggested_mappings}")
        logger.info(f"🔍 DEBUG: Extracted clarifications: {clarification_questions}")
        logger.info(f"🔍 DEBUG: Extracted confidence_scores: {confidence_scores}")
        
        # Store suggestions in state
        self.state.field_mappings = suggested_mappings
        
        # Store individual confidence scores in field mappings
        if isinstance(confidence_scores, dict):
            self.state.field_mappings["confidence_scores"] = confidence_scores
            
            # Calculate overall confidence as average of individual scores
            if confidence_scores:
                total_confidence = sum(confidence_scores.values())
                self.state.field_mapping_confidence = total_confidence / len(confidence_scores)
            else:
                self.state.field_mapping_confidence = 0.0
        else:
            # If confidence_scores is already a float (overall confidence)
            self.state.field_mapping_confidence = float(confidence_scores)
        
        # Add agent insights
        if clarification_questions:
            for question in clarification_questions:
                self.state_manager.add_agent_insight(
                    "Field Mapping Agent",
                    question,
                    confidence=0.7
                )
        
        # Update progress
        self.state.progress_percentage = 25.0  # Field mapping in progress
        
        # Store field mapping data in discovery_flows table
        try:
            from app.core.database import AsyncSessionLocal
            from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
            
            async with AsyncSessionLocal() as db:
                repo = DiscoveryFlowRepository(
                    db, 
                    client_account_id=str(getattr(self.state, 'client_account_id', self.context.client_account_id)),
                    engagement_id=str(getattr(self.state, 'engagement_id', self.context.engagement_id)),
                    user_id=str(getattr(self.state, 'user_id', self.context.user_id))
                )
                
                # Update the flow with field mappings
                await repo.flow_commands.update_phase_completion(
                    flow_id=self.state.flow_id,
                    phase="field_mapping",
                    data={
                        "field_mappings": suggested_mappings,
                        "confidence_scores": confidence_scores if isinstance(confidence_scores, dict) else {"overall": confidence_scores},
                        "confidence": self.state.field_mapping_confidence,
                        "total_fields": len(suggested_mappings),
                        "clarifications": clarification_questions,
                        "awaiting_approval": True
                    },
                    completed=False,  # Not completed yet, awaiting approval
                    agent_insights=self.state.agent_insights
                )
                
                logger.info("✅ Updated discovery_flows table with field mapping suggestions")
        except Exception as e:
            logger.warning(f"Failed to update discovery_flows table: {e}")
        
        await self.state_manager.safe_update_flow_state()
        logger.info(f"✅ Generated {len(suggested_mappings)} mapping suggestions")
        
        return "field_mapping_suggestions_ready"
    
    @listen(generate_field_mapping_suggestions)
    async def pause_for_field_mapping_approval(self, previous_result):
        """Pause flow for user to review and approve field mappings"""
        logger.info("⏸️ Pausing for field mapping approval")
        
        # Update status to waiting
        self.state.status = "waiting_for_approval"
        self.state.awaiting_user_approval = True
        self.state.user_approval_data = {
            "phase": PhaseNames.FIELD_MAPPING,
            "reason": "Please review and approve the suggested field mappings",
            "data_preview": self.state.raw_data[:5] if self.state.raw_data else [],
            "suggested_mappings": self.state.field_mappings,
            "confidence_scores": self.state.field_mapping_confidence,
            "clarifications_needed": len([i for i in self.state.agent_insights if i.get("agent") == "Field Mapping Agent"])
        }
        
        await self.state_manager.safe_update_flow_state()
        
        # Explicitly update Master Flow status to waiting_for_approval
        if hasattr(self, '_flow_state_bridge') and self._flow_state_bridge:
            try:
                from app.services.crewai_flows.persistence.postgres_store import PostgresFlowStateStore
                from app.core.database import AsyncSessionLocal
                
                async with AsyncSessionLocal() as db:
                    store = PostgresFlowStateStore(db, self.context)
                    await store.update_flow_status(self._flow_id, "waiting_for_approval")
                    logger.info("✅ Updated Master Flow status to waiting_for_approval")
            except Exception as e:
                logger.warning(f"⚠️ Failed to update Master Flow status: {e}")
        
        # Update DiscoveryFlow table with current state
        try:
            from app.core.database import AsyncSessionLocal
            from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
            from app.core.context import RequestContext
            
            async with AsyncSessionLocal() as db:
                # Create context from state
                context = RequestContext(
                    client_account_id=self.state.client_account_id,
                    engagement_id=self.state.engagement_id,
                    user_id=self.state.user_id,
                    flow_id=self.state.flow_id
                )
                
                # Log state values for debugging
                logger.info(f"State values - client: {getattr(self.state, 'client_account_id', 'MISSING')}, engagement: {getattr(self.state, 'engagement_id', 'MISSING')}, user: {getattr(self.state, 'user_id', 'MISSING')}")
                
                # Update flow status in discovery_flows table
                repo = DiscoveryFlowRepository(
                    db, 
                    client_account_id=str(getattr(self.state, 'client_account_id', self.context.client_account_id)),
                    engagement_id=str(getattr(self.state, 'engagement_id', self.context.engagement_id)),
                    user_id=str(getattr(self.state, 'user_id', self.context.user_id))
                )
                await repo.flow_commands.update_flow_status(
                    flow_id=self.state.flow_id,
                    status="waiting_for_approval",
                    progress_percentage=self.state.progress_percentage
                )
                
                # Also update the current phase data
                await repo.flow_commands.update_phase_completion(
                    flow_id=self.state.flow_id,
                    phase="field_mapping",
                    data={
                        "field_mappings": self.state.field_mappings,
                        "confidence": self.state.field_mapping_confidence,
                        "awaiting_user_approval": True
                    },
                    completed=False,
                    agent_insights=self.state.agent_insights
                )
                
                logger.info("✅ Updated DiscoveryFlow table with paused state")
        except Exception as e:
            logger.warning(f"Failed to update DiscoveryFlow table: {e}")
        
        logger.info("⏸️ Flow paused - waiting for field mapping approval")
        
        return "paused_for_field_mapping_approval"
    
    @listen(pause_for_field_mapping_approval)
    async def apply_approved_field_mappings(self, previous_result):
        """Apply user-approved field mappings and continue to data cleansing"""
        # Check if we're being called directly during resume (not through normal flow)
        if previous_result == "field_mapping_approved":
            logger.info("✅ Called directly from resume - applying approved field mappings")
            
            # Clear approval flags
            self.state.awaiting_user_approval = False
            self.state.status = "processing"
            
            # Mark phase as completed
            self.state.phase_completion[PhaseNames.FIELD_MAPPING] = True
            self.state.field_mapping_completed = True
            
            # Update current phase to next phase
            self.state.current_phase = PhaseNames.DATA_CLEANSING
            
            # Update progress
            self.state.progress_percentage = 33.3  # 2/6 phases complete
            
            await self.state_manager.safe_update_flow_state()
            
            # Also update the Master Flow status
            try:
                from app.services.crewai_flows.persistence.postgres_store import PostgresFlowStateStore
                from app.core.database import AsyncSessionLocal
                
                async with AsyncSessionLocal() as db:
                    store = PostgresFlowStateStore(db, self.context)
                    await store.update_flow_status(self._flow_id, "processing")
                    logger.info("✅ Updated Master Flow status to processing")
            except Exception as e:
                logger.warning(f"⚠️ Failed to update Master Flow status: {e}")
            
            # Also update DiscoveryFlow table
            try:
                from app.core.database import AsyncSessionLocal
                from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
                
                async with AsyncSessionLocal() as db:
                    repo = DiscoveryFlowRepository(
                        db, 
                        client_account_id=str(getattr(self.state, 'client_account_id', self.context.client_account_id)),
                        engagement_id=str(getattr(self.state, 'engagement_id', self.context.engagement_id)),
                        user_id=str(getattr(self.state, 'user_id', self.context.user_id))
                    )
                    
                    # Update flow status
                    await repo.flow_commands.update_flow_status(
                        flow_id=self.state.flow_id,
                        status="processing",
                        progress_percentage=33.3
                    )
                    
                    # Mark field mapping as completed
                    await repo.flow_commands.update_phase_completion(
                        flow_id=self.state.flow_id,
                        phase="field_mapping",
                        data={
                            "field_mappings": self.state.field_mappings,
                            "confidence": self.state.field_mapping_confidence,
                            "completed": True
                        },
                        completed=True,
                        agent_insights=self.state.agent_insights
                    )
                    
                    logger.info("✅ Updated DiscoveryFlow table with field mapping completion")
            except Exception as e:
                logger.warning(f"Failed to update DiscoveryFlow table: {e}")
            
            return "field_mapping_completed"
        
        # Check if we're resuming from approval
        if self.state.awaiting_user_approval and self.state.current_phase in [PhaseNames.FIELD_MAPPING, "attribute_mapping"]:
            # Check if mappings have been approved (user_approval_data should be updated)
            if hasattr(self.state, 'user_approval_data') and self.state.user_approval_data:
                approval_data = self.state.user_approval_data
                if approval_data.get('approved', False):
                    logger.info("✅ User approved field mappings - applying and continuing flow")
                    
                    # Clear approval flags
                    self.state.awaiting_user_approval = False
                    self.state.status = "processing"
                    
                    # Mark phase as completed
                    self.state.phase_completion[PhaseNames.FIELD_MAPPING] = True
                    self.state.field_mapping_completed = True
                    
                    # Update current phase to next phase
                    self.state.current_phase = PhaseNames.DATA_CLEANSING
                    
                    # Update progress
                    self.state.progress_percentage = 33.3  # 2/6 phases complete
                    
                    await self.state_manager.safe_update_flow_state()
                    
                    # Also update the Master Flow status
                    try:
                        from app.services.crewai_flows.persistence.postgres_store import PostgresFlowStateStore
                        from app.core.database import AsyncSessionLocal
                        
                        async with AsyncSessionLocal() as db:
                            store = PostgresFlowStateStore(db, self.context)
                            await store.update_flow_status(self._flow_id, "processing")
                            logger.info("✅ Updated Master Flow status to processing")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to update Master Flow status: {e}")
                    
                    return "field_mapping_completed"
        
        # This will only run when flow is resumed after approval
        if previous_result == "paused_for_field_mapping_approval":
            logger.info("⏭️ Flow is paused for approval - waiting for user action")
            # Don't propagate the paused state - just return it
            return previous_result
        
        # Normal flow - user has approved, apply the mappings
        logger.info("✅ Applying approved field mappings")
        
        # The mappings are already in state from the suggestions phase
        # Just update the status
        self.state.phase_completion[PhaseNames.FIELD_MAPPING] = True
        self.state.field_mapping_completed = True
        self.state.current_phase = PhaseNames.DATA_CLEANSING
        self.state.progress_percentage = 33.3  # 2/6 phases complete
        
        await self.state_manager.safe_update_flow_state()
        
        return "field_mapping_completed"
    
    @listen(apply_approved_field_mappings)
    async def execute_data_cleansing_agent(self, previous_result):
        """Execute data cleansing phase using real CrewAI crews"""
        # Check if flow is paused
        if previous_result == "paused_for_field_mapping_approval":
            logger.info("⏭️ Flow paused - data cleansing will not execute")
            return previous_result
            
        result = await self.phase_executor.execute_data_cleansing_phase(previous_result)
        await self.state_manager.safe_update_flow_state()
        return result
    
    @listen(execute_data_cleansing_agent)
    async def create_discovery_assets_from_cleaned_data(self, previous_result):
        """Create discovery assets from cleaned data"""
        # Check if flow is paused
        if previous_result == "paused_for_field_mapping_approval":
            logger.info("⏭️ Flow paused - asset inventory will not execute")
            return previous_result
            
        # Use PhaseExecutionManager with real CrewAI crews
        result = await self.phase_executor.execute_asset_inventory_phase(previous_result)
        await self.state_manager.safe_update_flow_state()
        return result
    
    @listen(create_discovery_assets_from_cleaned_data)
    async def promote_discovery_assets_to_assets(self, previous_result):
        """Promote discovery assets to main assets table"""
        # Check if flow is paused
        if previous_result == "paused_for_field_mapping_approval":
            logger.info("⏭️ Flow paused - asset promotion will not execute")
            return previous_result
            
        # This is handled within asset_inventory_phase
        return "assets_promoted"
    
    @listen(promote_discovery_assets_to_assets)
    async def execute_parallel_analysis_agents(self, previous_result):
        """Execute dependency and tech debt analysis in parallel"""
        # Check if flow is paused
        if previous_result == "paused_for_field_mapping_approval":
            logger.info("⏭️ Flow paused - parallel analysis will not execute")
            return previous_result
            
        logger.info("🚀 Starting parallel analysis agents")
        
        try:
            # Prepare input data
            input_data = {
                'assets': self.state.asset_inventory.get('assets', []),
                'field_mappings': self.state.field_mappings,
                'cleaned_data': self.state.cleaned_data
            }
            
            # Execute parallel phases
            results = await self.crew_coordinator.execute_parallel_agents(
                [PhaseNames.DEPENDENCY_ANALYSIS, PhaseNames.TECH_DEBT_ASSESSMENT],
                input_data,
                self._init_context
            )
            
            # Update phase completions
            self.state.phase_completion['dependencies'] = True
            self.state.phase_completion['tech_debt'] = True
            self.state.progress_percentage = 90.0
            
            await self.state_manager.safe_update_flow_state()
            
            logger.info("✅ Parallel analysis completed")
            return "parallel_analysis_completed"
            
        except Exception as e:
            logger.error(f"❌ Parallel analysis failed: {e}")
            self.state_manager.add_error("parallel_analysis", str(e))
            return "parallel_analysis_failed"
    
    @listen(execute_parallel_analysis_agents)
    async def check_user_approval_needed(self, previous_result):
        """Check if user approval is needed and finalize flow"""
        # Check if flow is paused
        if previous_result == "paused_for_field_mapping_approval":
            logger.info("⏭️ Flow paused - finalization will not execute")
            return previous_result
            
        if self.state_manager.is_user_approval_needed():
            await self.flow_finalizer.pause_for_user_approval(previous_result)
            return "awaiting_user_approval_in_attribute_mapping"
        else:
            return await self.flow_finalizer.finalize_flow(previous_result)
    
    # ========================================
    # FLOW MANAGEMENT DELEGATION
    # ========================================
    
    async def pause_flow(self, reason: str = "user_requested"):
        """Pause the discovery flow"""
        return await self.flow_manager.pause_flow(reason)
    
    async def resume_flow_from_state(self, resume_context: Dict[str, Any]):
        """Resume flow from saved state"""
        return await self.flow_manager.resume_flow_from_state(resume_context)
    
    def get_flow_info(self) -> Dict[str, Any]:
        """Get comprehensive flow information"""
        return self.flow_manager.get_flow_info()
    
    async def _load_raw_data_from_database(self, state: UnifiedDiscoveryFlowState):
        """Load raw data from database tables into flow state"""
        try:
            flow_id_to_use = self._flow_id
            logger.info(f"🔍 Loading raw data for flow {flow_id_to_use}")
            
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import select, or_
            from app.models.discovery_flow import DiscoveryFlow
            from app.models.data_import import RawImportRecord, DataImport
            
            async with AsyncSessionLocal() as db:
                # First, try to get the discovery flow record
                flow_query = select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_id_to_use)
                flow_result = await db.execute(flow_query)
                discovery_flow = flow_result.scalar_one_or_none()
                
                data_import_id = None
                
                if discovery_flow and discovery_flow.data_import_id:
                    data_import_id = discovery_flow.data_import_id
                    logger.info(f"🔍 Found discovery flow with data_import_id: {data_import_id}")
                else:
                    # Fallback: Check if flow_id is actually a data_import_id
                    logger.info(f"🔍 No discovery flow found, checking if {flow_id_to_use} is a data_import_id")
                    import_query = select(DataImport).where(DataImport.id == flow_id_to_use)
                    import_result = await db.execute(import_query)
                    data_import = import_result.scalar_one_or_none()
                    
                    if data_import:
                        data_import_id = data_import.id
                        logger.info(f"✅ Found data import directly with id: {data_import_id}")
                
                if data_import_id:
                    # Load raw records from raw_import_records table
                    records_query = select(RawImportRecord).where(
                        RawImportRecord.data_import_id == data_import_id
                    ).order_by(RawImportRecord.row_number)
                    
                    records_result = await db.execute(records_query)
                    raw_records = records_result.scalars().all()
                    
                    # Extract raw_data from records
                    raw_data = [record.raw_data for record in raw_records]
                    
                    if raw_data:
                        state.raw_data = raw_data
                        logger.info(f"✅ Loaded {len(raw_data)} records from database")
                        logger.info(f"🔍 Sample record keys: {list(raw_data[0].keys()) if raw_data else 'None'}")
                        logger.info(f"🔍 First record sample: {raw_data[0] if raw_data else 'None'}")
                    else:
                        logger.warning(f"⚠️ No raw records found for data_import_id: {data_import_id}")
                else:
                    logger.warning(f"⚠️ Could not find data_import_id for flow: {flow_id_to_use}")
                    
        except Exception as e:
            logger.error(f"❌ Failed to load raw data from database: {e}")
            # Don't fail the flow initialization, just log the error
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    async def _load_raw_data_from_import_records(self):
        """Load raw data from raw_import_records table when state doesn't have it"""
        try:
            from app.core.database import AsyncSessionLocal
            from app.models.data_import import RawImportRecord
            from sqlalchemy import select
            
            # Use flow_id as data_import_id (they're the same in the current implementation)
            data_import_id = self._flow_id
            logger.info(f"🔍 Loading raw data for data_import_id: {data_import_id}")
            
            async with AsyncSessionLocal() as db:
                # Load raw records
                records_result = await db.execute(
                    select(RawImportRecord)
                    .where(RawImportRecord.data_import_id == data_import_id)
                    .order_by(RawImportRecord.row_number)
                )
                records = records_result.scalars().all()
                
                if records:
                    # Extract raw_data from records
                    raw_data = [record.raw_data for record in records]
                    self.state.raw_data = raw_data
                    logger.info(f"✅ Loaded {len(raw_data)} records from database")
                    if raw_data and len(raw_data) > 0:
                        logger.info(f"🔍 First record keys: {list(raw_data[0].keys())}")
                        
                    # Also update the flow persistence if bridge is available
                    if self.flow_bridge:
                        await self.state_manager.safe_update_flow_state()
                else:
                    logger.warning(f"⚠️ No raw records found for data_import_id: {data_import_id}")
                    
        except Exception as e:
            logger.error(f"❌ Failed to load raw data from database: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")


def create_unified_discovery_flow(
    crewai_service,
    context: RequestContext,
    raw_data: List[Dict[str, Any]],
    **kwargs
) -> UnifiedDiscoveryFlow:
    """
    Factory function to create a Unified Discovery Flow instance.
    
    Args:
        crewai_service: The CrewAI service instance
        context: Request context for multi-tenant operations
        raw_data: Raw data to process
        **kwargs: Additional flow configuration
        
    Returns:
        UnifiedDiscoveryFlow instance
    """
    logger.info(f"🏗️ Creating UnifiedDiscoveryFlow with {len(raw_data) if raw_data else 0} records")
    
    # Ensure raw_data is included in kwargs
    kwargs['raw_data'] = raw_data
    
    return UnifiedDiscoveryFlow(
        crewai_service=crewai_service,
        context=context,
        **kwargs
    )