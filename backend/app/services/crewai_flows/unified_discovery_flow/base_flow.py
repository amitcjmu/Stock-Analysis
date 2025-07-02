"""
Base Flow Module

The main UnifiedDiscoveryFlow class that orchestrates all phases.
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
        
        # Initialize base flow
        if CREWAI_FLOW_AVAILABLE:
            super().__init__()
        else:
            self.state = None
            
        logger.info("🚀 Initializing Unified Discovery Flow with Agent-First Architecture")
        
        # Store context and service
        self.crewai_service = crewai_service
        self.context = context
        
        # Use initializer for setup
        self.initializer = FlowInitializer(crewai_service, context, **kwargs)
        self._init_context = self.initializer.init_context
        
        # Initialize flow state - CrewAI Flow manages state internally
        if CREWAI_FLOW_AVAILABLE:
            # For CrewAI Flow, state is managed by the base class
            # We'll update it in the initialize_discovery method
            pass
        else:
            # For fallback mode, we manage state directly
            self.state = self.initializer.create_initial_state()
        
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
        logger.info("🎯 Starting Unified Discovery Flow")
        
        try:
            # Initialize state from initializer if not already set by CrewAI
            if not hasattr(self, 'state') or self.state is None:
                initial_state = self.initializer.create_initial_state()
                # For CrewAI Flow, we update the managed state attributes
                if CREWAI_FLOW_AVAILABLE and hasattr(super(), 'state'):
                    # Copy attributes from initial state
                    for key, value in initial_state.__dict__.items():
                        setattr(self.state, key, value)
                else:
                    self.state = initial_state
            
            # Update component references to use actual state
            self.flow_management.state = self.state
            self.state_manager.state = self.state
            self.flow_manager.state = self.state
            self.flow_finalizer.state = self.state
            
            # Initialize UnifiedFlowCrewManager now that we have state
            from ..handlers.unified_flow_crew_manager import UnifiedFlowCrewManager
            self.crew_manager = UnifiedFlowCrewManager(self.crewai_service, self.state)
            
            # Initialize PhaseExecutionManager now that we have state
            from ..handlers.phase_executors.phase_execution_manager import PhaseExecutionManager
            self.phase_executor = PhaseExecutionManager(self.state, self.crew_manager, self.flow_bridge)
            
            # Re-initialize phases with actual state
            agents = {
                'data_validation_agent': self.data_validation_agent,
                'attribute_mapping_agent': self.attribute_mapping_agent,
                'data_cleansing_agent': self.data_cleansing_agent,
                'asset_inventory_agent': self.asset_inventory_agent,
                'dependency_analysis_agent': self.dependency_analysis_agent,
                'tech_debt_analysis_agent': self.tech_debt_analysis_agent
            }
            phases = self.initializer.initialize_phases(self.state, agents, self.flow_bridge)
            self.data_validation_phase = phases['data_validation_phase']
            self.field_mapping_phase = phases['field_mapping_phase']
            self.data_cleansing_phase = phases['data_cleansing_phase']
            self.asset_inventory_phase = phases['asset_inventory_phase']
            self.dependency_analysis_phase = phases['dependency_analysis_phase']
            self.tech_debt_assessment_phase = phases['tech_debt_assessment_phase']
            
            # Set initial state
            self.state.status = "initializing"
            self.state.current_phase = "initialization"
            self.state.created_at = datetime.utcnow()
            self.state.updated_at = datetime.utcnow()
            
            # Generate flow_id if not set
            if not hasattr(self.state, 'flow_id') or not self.state.flow_id:
                self.state.flow_id = self._init_context.get('flow_id') or str(uuid.uuid4())
            
            # Initialize with flow bridge
            if self.flow_bridge:
                await self.flow_bridge.initialize_flow(self.state)
                logger.info(f"✅ Flow initialized with PostgreSQL bridge - Flow ID: {self.state.flow_id}")
            
            # Update state
            await self.state_manager.safe_update_flow_state()
            
            logger.info("✅ Discovery flow initialization completed")
            return "initialization_completed"
            
        except Exception as e:
            logger.error(f"❌ Discovery flow initialization failed: {e}")
            if hasattr(self, 'state_manager') and self.state_manager:
                self.state_manager.add_error("initialization", str(e))
            return "initialization_failed"
    
    @listen(initialize_discovery)
    async def execute_data_import_validation_agent(self, previous_result):
        """Execute data import validation phase"""
        result = await self.data_validation_phase.execute(previous_result)
        await self.state_manager.safe_update_flow_state()
        return result
    
    @listen(execute_data_import_validation_agent)
    async def execute_attribute_mapping_agent(self, previous_result):
        """Execute field mapping phase"""
        result = await self.field_mapping_phase.execute(previous_result)
        await self.state_manager.safe_update_flow_state()
        return result
    
    @listen(execute_attribute_mapping_agent)
    async def execute_data_cleansing_agent(self, previous_result):
        """Execute data cleansing phase"""
        result = await self.data_cleansing_phase.execute(previous_result)
        await self.state_manager.safe_update_flow_state()
        return result
    
    @listen(execute_data_cleansing_agent)
    async def create_discovery_assets_from_cleaned_data(self, previous_result):
        """Create discovery assets from cleaned data"""
        result = await self.asset_inventory_phase.execute(previous_result)
        await self.state_manager.safe_update_flow_state()
        return result
    
    @listen(create_discovery_assets_from_cleaned_data)
    async def promote_discovery_assets_to_assets(self, previous_result):
        """Promote discovery assets to main assets table"""
        # This is handled within asset_inventory_phase
        return "assets_promoted"
    
    @listen(promote_discovery_assets_to_assets)
    async def execute_parallel_analysis_agents(self, previous_result):
        """Execute dependency and tech debt analysis in parallel"""
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
    return UnifiedDiscoveryFlow(
        crewai_service=crewai_service,
        context=context,
        raw_data=raw_data,
        **kwargs
    )