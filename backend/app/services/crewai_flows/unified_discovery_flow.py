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

@persist()  # Enable CrewAI state persistence
class UnifiedDiscoveryFlow(Flow[UnifiedDiscoveryFlowState]):
    """
    Unified Discovery Flow following CrewAI documentation patterns.
    Single source of truth for all discovery flow operations.
    
    Handles all discovery phases with proper state management:
    1. Field Mapping
    2. Data Cleansing  
    3. Asset Inventory
    4. Dependency Analysis
    5. Technical Debt Analysis
    """
    
    def __init__(self, crewai_service, context: RequestContext, **kwargs):
        """Initialize unified discovery flow with proper state management"""
        
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
        
        # Initialize state if not exists
        if not hasattr(self, 'state') or self.state is None:
            self.state = UnifiedDiscoveryFlowState()
        
        # Initialize modular handlers
        self.crew_manager = UnifiedFlowCrewManager(crewai_service, self.state)
        self.phase_executor = PhaseExecutionManager(self.state, self.crew_manager)
        self.flow_management = UnifiedFlowManagement(self.state)
        
        logger.info(f"✅ Unified Discovery Flow initialized with session: {self._init_session_id}")
    
    @start()
    def initialize_discovery(self):
        """Initialize the unified discovery workflow"""
        logger.info("🚀 Starting Unified Discovery Flow initialization")
        
        # Set core state fields
        self.state.session_id = self._init_session_id
        self.state.client_account_id = self._init_client_account_id
        self.state.engagement_id = self._init_engagement_id
        self.state.user_id = self._init_user_id
        self.state.raw_data = self._init_raw_data
        self.state.metadata = self._init_metadata
        
        # Set flow status
        self.state.current_phase = "initialization"
        self.state.status = "running"
        self.state.started_at = datetime.utcnow().isoformat()
        
        # Validate input data
        if not self.state.raw_data:
            self.state.add_error("initialization", "No raw data provided")
            return "initialization_failed"
        
        self.state.log_entry(f"Discovery Flow initialized with {len(self.state.raw_data)} records")
        logger.info(f"✅ Unified Discovery Flow initialized with {len(self.state.raw_data)} records")
        
        return "initialized"
    
    @listen(initialize_discovery)
    def execute_field_mapping_crew(self, previous_result):
        """Execute field mapping using CrewAI crew"""
        if previous_result == "initialization_failed":
            logger.error("❌ Skipping field mapping due to initialization failure")
            return "field_mapping_skipped"
        
        return self.phase_executor.execute_field_mapping_phase(previous_result)
    
    @listen(execute_field_mapping_crew)
    def execute_data_cleansing_crew(self, previous_result):
        """Execute data cleansing using CrewAI crew"""
        if previous_result in ["field_mapping_skipped", "field_mapping_failed"]:
            logger.error("❌ Skipping data cleansing due to field mapping issues")
            return "data_cleansing_skipped"
        
        return self.phase_executor.execute_data_cleansing_phase(previous_result)
    
    @listen(execute_data_cleansing_crew)
    def execute_asset_inventory_crew(self, previous_result):
        """Execute asset inventory using CrewAI crew"""
        if previous_result in ["data_cleansing_skipped", "data_cleansing_failed"]:
            logger.error("❌ Skipping asset inventory due to data cleansing issues")
            return "asset_inventory_skipped"
        
        return self.phase_executor.execute_asset_inventory_phase(previous_result)
    
    @listen(execute_asset_inventory_crew)
    def execute_dependency_analysis_crew(self, previous_result):
        """Execute dependency analysis using CrewAI crew"""
        if previous_result in ["asset_inventory_skipped", "asset_inventory_failed"]:
            logger.error("❌ Skipping dependency analysis due to asset inventory issues")
            return "dependency_analysis_skipped"
        
        return self.phase_executor.execute_dependency_analysis_phase(previous_result)
    
    @listen(execute_dependency_analysis_crew)
    def execute_tech_debt_analysis_crew(self, previous_result):
        """Execute technical debt analysis using CrewAI crew"""
        if previous_result in ["dependency_analysis_skipped", "dependency_analysis_failed"]:
            logger.error("❌ Skipping tech debt analysis due to dependency analysis issues")
            return "tech_debt_analysis_skipped"
        
        return self.phase_executor.execute_tech_debt_analysis_phase(previous_result)
    
    @listen(execute_tech_debt_analysis_crew)
    def finalize_discovery(self, previous_result):
        """Finalize the discovery flow and provide comprehensive summary"""
        logger.info("🎯 Finalizing Unified Discovery Flow")
        self.state.current_phase = "finalization"
        self.state.progress_percentage = 100.0
        
        try:
            # Generate final summary
            summary = self.state.finalize_flow()
            
            # Validate overall success
            total_assets = self.state.asset_inventory.get("total_assets", 0)
            if total_assets == 0:
                logger.error("❌ Discovery Flow FAILED: No assets were processed")
                self.state.status = "failed"
                self.state.add_error("finalization", "No assets were processed during discovery")
                return "discovery_failed"
            
            # Mark as completed
            self.state.status = "completed"
            self.state.current_phase = "completed"
            
            logger.info(f"✅ Unified Discovery Flow completed successfully")
            logger.info(f"📊 Summary: {total_assets} assets, {len(self.state.errors)} errors, {len(self.state.warnings)} warnings")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Discovery flow finalization failed: {e}")
            self.state.add_error("finalization", str(e))
            self.state.status = "failed"
            return "discovery_failed"
    
    # ========================================
    # FLOW MANAGEMENT METHODS (Delegated)
    # ========================================

    def pause_flow(self, reason: str = "user_requested"):
        """Pause the discovery flow with proper state preservation"""
        return self.flow_management.pause_flow(reason)

    def resume_flow_from_state(self, resume_context: Dict[str, Any]):
        """Resume flow from persisted state with CrewAI Flow continuity"""
        return self.flow_management.resume_flow_from_state(resume_context)

    def get_flow_management_info(self) -> Dict[str, Any]:
        """Get comprehensive flow information for management UI"""
        return self.flow_management.get_flow_management_info()


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
    properly configured CrewAI Flow instance.
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
    
    logger.info(f"✅ Unified Discovery Flow created: {session_id}")
    return flow 