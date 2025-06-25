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
        """Initialize unified discovery flow with hybrid persistence"""
        
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
        
        # Initialize modular handlers with flow bridge
        self.crew_manager = UnifiedFlowCrewManager(crewai_service, self.state)
        self.phase_executor = PhaseExecutionManager(self.state, self.crew_manager, self.flow_bridge)
        self.flow_management = UnifiedFlowManagement(self.state)
        
        logger.info(f"✅ Unified Discovery Flow initialized with hybrid persistence: session={self._init_session_id}")
    
    @start()
    async def initialize_discovery(self):
        """Initialize the unified discovery workflow with PostgreSQL persistence"""
        logger.info("🚀 Starting Unified Discovery Flow initialization with hybrid persistence")
        logger.info(f"📋 Flow Context: session={self._init_session_id}, client={self._init_client_account_id}, engagement={self._init_engagement_id}")
        
        # Set core state fields
        self.state.session_id = self._init_session_id
        self.state.client_account_id = self._init_client_account_id
        self.state.engagement_id = self._init_engagement_id
        self.state.user_id = self._init_user_id
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
            bridge_result = await self.flow_bridge.initialize_flow_state(self.state)
            logger.info(f"✅ Flow State Bridge initialized: {bridge_result}")
        except Exception as e:
            logger.warning(f"⚠️ Flow State Bridge initialization failed (non-critical): {e}")
        
        self.state.log_entry(f"Discovery Flow initialized with {len(self.state.raw_data)} records")
        logger.info(f"✅ Unified Discovery Flow initialized with {len(self.state.raw_data)} records")
        logger.info(f"🎯 Next Phase: data_import_validation")
        
        return "initialized"
    
    @listen(initialize_discovery)
    async def execute_data_import_validation(self, previous_result):
        """Execute data import validation: PII detection, malicious payload scanning, data type validation"""
        if previous_result == "initialization_failed":
            logger.error("❌ Skipping data validation due to initialization failure")
            return "data_validation_skipped"
        
        logger.info("🔍 Starting Data Import Validation Phase")
        self.state.current_phase = "data_import"
        
        try:
            # Execute data validation phase
            validation_result = await self.phase_executor.execute_data_import_validation_phase(previous_result)
            
            if validation_result in ["data_validation_failed", "data_validation_skipped"]:
                logger.error("❌ Data validation failed - flow cannot proceed")
                self.state.status = "validation_failed"
                self.state.add_error("data_import", "Data validation failed")
                return "data_validation_failed"
            
            # Update phase completion
            self.state.phase_completion["data_import"] = True
            self.state.update_progress()
            
            logger.info("✅ Data Import Validation completed successfully")
            
            # PAUSE FLOW FOR USER APPROVAL
            logger.info("⏸️ Flow paused - awaiting user approval to proceed to field mapping")
            self.state.status = "awaiting_user_approval"
            self.state.current_phase = "data_validation_complete"
            
            # Store validation results for user review
            validation_data = self.state.phase_data.get("data_import", {})
            file_analysis = validation_data.get("file_analysis", {})
            recommended_agent = file_analysis.get("recommended_agent", "CMDB_Data_Analyst_Agent")
            
            # Log comprehensive report for user
            logger.info("📊 DATA IMPORT VALIDATION REPORT:")
            logger.info(f"   📁 File Type: {file_analysis.get('detected_type', 'unknown')}")
            logger.info(f"   🎯 Recommended Agent: {recommended_agent}")
            logger.info(f"   📈 Confidence: {file_analysis.get('confidence', 0):.1%}")
            logger.info(f"   🔒 Security Status: {validation_data.get('security_status', 'unknown')}")
            logger.info(f"   📋 Total Records: {validation_data.get('total_records', 0)}")
            logger.info(f"   🏷️ Total Fields: {len(validation_data.get('detected_fields', []))}")
            
            detailed_report = validation_data.get("detailed_report", {})
            if detailed_report:
                logger.info("📄 DETAILED ANALYSIS:")
                content_analysis = detailed_report.get("content_analysis", {})
                logger.info(f"   🔍 Content Type: {content_analysis.get('detected_type', 'unknown')}")
                logger.info(f"   🤖 Recommended Agent: {content_analysis.get('recommended_agent', 'unknown')}")
                
                security_assessment = detailed_report.get("security_assessment", {})
                logger.info(f"   🛡️ Security Status: {security_assessment.get('status', 'unknown')}")
                logger.info(f"   🔐 PII Detected: {security_assessment.get('pii_detected', False)}")
                
                data_quality = detailed_report.get("data_quality", {})
                logger.info(f"   📊 Quality Score: {data_quality.get('overall_score', '0%')}")
            
            logger.info("⏳ USER ACTION REQUIRED:")
            logger.info("   1. Review the file analysis above")
            logger.info("   2. Confirm the recommended agent selection")
            logger.info("   3. Approve proceeding to field mapping phase")
            logger.info("   4. Or request different agent if file type was misidentified")
            
            # Return a special status that indicates user approval is needed
            return "data_validation_complete_awaiting_approval"
            
        except Exception as e:
            logger.error(f"❌ Data validation phase failed: {e}")
            self.state.add_error("data_import", f"Data validation error: {str(e)}")
            return "data_validation_failed"
    
    @listen(execute_data_import_validation)
    async def execute_field_mapping_crew(self, previous_result):
        """Execute field mapping using CrewAI crew with PostgreSQL persistence and user approval"""
        # Only proceed if user has approved the data validation
        if previous_result == "data_validation_complete_awaiting_approval":
            logger.info("⏸️ Data validation complete - flow paused for user approval")
            logger.info("🚫 Field mapping will NOT start until user approval is received")
            
            # Set status to indicate waiting for user input
            self.state.status = "awaiting_user_approval"
            self.state.current_phase = "data_validation_complete"
            
            # Return a status that prevents further automatic progression
            return "field_mapping_pending_user_approval"
        
        if previous_result in ["initialization_failed", "data_validation_failed", "data_validation_skipped"]:
            logger.error("❌ Skipping field mapping due to previous phase failure")
            return "field_mapping_skipped"
        
        # Only proceed if we have explicit user approval (this would be set by a separate approval endpoint)
        if self.state.status != "user_approved":
            logger.warning("⚠️ Field mapping attempted without user approval - blocking execution")
            return "field_mapping_blocked_no_approval"
        
        logger.info("🔄 Starting Field Mapping Phase with User Approval")
        self.state.current_phase = "attribute_mapping"
        self.state.status = "running"
        
        # Get the recommended agent from validation results
        validation_data = self.state.phase_data.get("data_import", {})
        file_analysis = validation_data.get("file_analysis", {})
        recommended_agent = file_analysis.get("recommended_agent", "CMDB_Data_Analyst_Agent")
        
        logger.info(f"🤖 Using recommended agent: {recommended_agent}")
        logger.info(f"📁 Processing {file_analysis.get('detected_type', 'unknown')} data")
        
        # The field mapping crew will use the recommended agent
        return await self.phase_executor.execute_field_mapping_phase(previous_result)
    
    @listen(execute_field_mapping_crew)
    async def execute_data_cleansing_crew(self, previous_result):
        """Execute data cleansing using CrewAI crew with PostgreSQL persistence"""
        if previous_result in ["field_mapping_skipped", "field_mapping_failed"]:
            logger.error("❌ Skipping data cleansing due to field mapping issues")
            return "data_cleansing_skipped"
        
        logger.info("🔄 Starting Data Cleansing Phase")
        self.state.current_phase = "data_cleansing"
        return await self.phase_executor.execute_data_cleansing_phase(previous_result)
    
    @listen(execute_data_cleansing_crew)
    async def execute_asset_inventory_crew(self, previous_result):
        """Execute asset inventory using CrewAI crew with PostgreSQL persistence"""
        if previous_result in ["data_cleansing_skipped", "data_cleansing_failed"]:
            logger.error("❌ Skipping asset inventory due to previous phase issues")
            return "asset_inventory_skipped"
        
        logger.info("🔄 Starting Asset Inventory Phase")
        self.state.current_phase = "inventory"
        return await self.phase_executor.execute_asset_inventory_phase(previous_result)
    
    @listen(execute_asset_inventory_crew)
    async def execute_dependency_analysis_crew(self, previous_result):
        """Execute dependency analysis using CrewAI crew with PostgreSQL persistence"""
        if previous_result in ["asset_inventory_skipped", "asset_inventory_failed"]:
            logger.error("❌ Skipping dependency analysis due to previous phase issues")
            return "dependency_analysis_skipped"
        
        logger.info("🔄 Starting Dependency Analysis Phase")
        self.state.current_phase = "dependencies"
        return await self.phase_executor.execute_dependency_analysis_phase(previous_result)
    
    @listen(execute_dependency_analysis_crew)
    async def execute_tech_debt_analysis_crew(self, previous_result):
        """Execute technical debt analysis using CrewAI crew with PostgreSQL persistence"""
        if previous_result in ["dependency_analysis_skipped", "dependency_analysis_failed"]:
            logger.error("❌ Skipping tech debt analysis due to previous phase issues")
            return "tech_debt_analysis_skipped"
        
        logger.info("🔄 Starting Tech Debt Analysis Phase")
        self.state.current_phase = "tech_debt"
        return await self.phase_executor.execute_tech_debt_analysis_phase(previous_result)
    
    @listen(execute_tech_debt_analysis_crew)
    async def finalize_discovery(self, previous_result):
        """Finalize the discovery flow and provide comprehensive summary"""
        if previous_result in ["tech_debt_analysis_skipped", "tech_debt_analysis_failed"]:
            logger.warning(f"⚠️ Finalizing with incomplete tech debt analysis: {previous_result}")
        
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