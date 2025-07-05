"""
Phase Execution Manager
Coordinates execution of discovery phases for the Unified Discovery Flow.
Split from unified_flow_phase_executor.py for better modularity.
Now integrated with Flow State Bridge for PostgreSQL persistence.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# CrewAI Flow imports with graceful fallback
CREWAI_FLOW_AVAILABLE = False
try:
    from crewai import Flow
    CREWAI_FLOW_AVAILABLE = True
except ImportError:
    logger.warning("CrewAI Flow not available")


class PhaseExecutionManager:
    """
    Manages execution of discovery phases for the Unified Discovery Flow.
    Coordinates between different phase executors and handles results.
    Now integrated with Flow State Bridge for PostgreSQL persistence.
    """
    
    def __init__(self, state, crew_manager, flow_bridge: Optional[Any] = None):
        """Initialize phase execution manager with state, crew manager, and flow bridge"""
        self.state = state
        self.crew_manager = crew_manager
        self.flow_bridge = flow_bridge  # FlowStateBridge for PostgreSQL persistence
        
        # Initialize phase executors with flow bridge
        from .data_import_validation_executor import DataImportValidationExecutor
        from .field_mapping_executor import FieldMappingExecutor
        from .data_cleansing_executor import DataCleansingExecutor
        from .asset_inventory_executor import AssetInventoryExecutor
        from .dependency_analysis_executor import DependencyAnalysisExecutor
        from .tech_debt_executor import TechDebtExecutor
        
        self.data_import_validation_executor = DataImportValidationExecutor(state, crew_manager, flow_bridge)
        self.field_mapping_executor = FieldMappingExecutor(state, crew_manager, flow_bridge)
        self.data_cleansing_executor = DataCleansingExecutor(state, crew_manager, flow_bridge)
        self.asset_inventory_executor = AssetInventoryExecutor(state, crew_manager, flow_bridge)
        self.dependency_analysis_executor = DependencyAnalysisExecutor(state, crew_manager, flow_bridge)
        self.tech_debt_executor = TechDebtExecutor(state, crew_manager, flow_bridge)
    
    async def execute_data_import_validation_phase(self, previous_result):
        """Execute data import validation phase with PostgreSQL persistence"""
        return await self.data_import_validation_executor.execute(previous_result)
    
    async def execute_field_mapping_phase(self, previous_result, mode: str = "full"):
        """Execute field mapping phase with PostgreSQL persistence
        
        Args:
            previous_result: Result from previous phase
            mode: Execution mode - 'full' or 'suggestions_only'
        """
        logger.info(f"🔍 DEBUG: execute_field_mapping_phase called with mode: {mode}")
        
        # Pass mode to executor if it's suggestions_only
        if mode == "suggestions_only":
            logger.info("🔍 DEBUG: Calling execute_suggestions_only")
            result = await self.field_mapping_executor.execute_suggestions_only(previous_result)
            logger.info(f"🔍 DEBUG: execute_suggestions_only returned: {result}")
            logger.info(f"🔍 DEBUG: Return result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            return result
        else:
            logger.info("🔍 DEBUG: Calling execute (full mode)")
            return await self.field_mapping_executor.execute(previous_result)
    
    async def execute_data_cleansing_phase(self, previous_result):
        """Execute data cleansing phase with PostgreSQL persistence"""
        return await self.data_cleansing_executor.execute(previous_result)
    
    async def execute_asset_inventory_phase(self, previous_result):
        """Execute asset inventory phase with PostgreSQL persistence"""
        return await self.asset_inventory_executor.execute(previous_result)
    
    async def execute_dependency_analysis_phase(self, previous_result):
        """Execute dependency analysis phase with PostgreSQL persistence"""
        return await self.dependency_analysis_executor.execute(previous_result)
    
    async def execute_tech_debt_analysis_phase(self, previous_result):
        """Execute tech debt analysis phase with PostgreSQL persistence"""
        return await self.tech_debt_executor.execute(previous_result)
    
    def get_phase_executor(self, phase_name: str):
        """Get specific phase executor by name"""
        executors = {
            "data_import_validation": self.data_import_validation_executor,
            "field_mapping": self.field_mapping_executor,
            "data_cleansing": self.data_cleansing_executor,
            "asset_inventory": self.asset_inventory_executor,
            "dependency_analysis": self.dependency_analysis_executor,
            "tech_debt_analysis": self.tech_debt_executor
        }
        return executors.get(phase_name)
    
    def get_execution_status(self) -> Dict[str, Any]:
        """Get status of all phase executors"""
        return {
            "current_phase": self.state.current_phase,
            "progress_percentage": self.state.progress_percentage,
            "phase_completion": self.state.phase_completion,
            "available_executors": [
                "data_import_validation", "field_mapping", "data_cleansing", "asset_inventory",
                "dependency_analysis", "tech_debt_analysis"
            ],
            "crewai_available": CREWAI_FLOW_AVAILABLE,
            "postgresql_bridge_available": self.flow_bridge is not None
        }
    
    async def validate_phase_integrity(self, session_id: str) -> Dict[str, Any]:
        """
        Validate integrity of all phases using the Flow State Bridge.
        Comprehensive health check across all phase executors.
        """
        if not self.flow_bridge:
            return {
                "status": "bridge_unavailable",
                "message": "Flow State Bridge not available for validation"
            }
        
        try:
            validation_result = await self.flow_bridge.validate_state_integrity(session_id)
            
            # Add phase-specific validation
            phase_status = {}
            for phase_name in ["data_import_validation", "field_mapping", "data_cleansing", "asset_inventory", "dependency_analysis", "tech_debt_analysis"]:
                executor = self.get_phase_executor(phase_name)
                if executor:
                    phase_status[phase_name] = {
                        "executor_available": True,
                        "bridge_integrated": executor.flow_bridge is not None
                    }
                else:
                    phase_status[phase_name] = {
                        "executor_available": False,
                        "bridge_integrated": False
                    }
            
            validation_result["phase_executors"] = phase_status
            return validation_result
            
        except Exception as e:
            logger.error(f"❌ Phase integrity validation failed: {e}")
            return {
                "status": "validation_error",
                "error": str(e)
            }
    
    async def cleanup_phase_states(self, session_id: str, expiration_hours: int = 72) -> Dict[str, Any]:
        """
        Clean up expired phase states using the Flow State Bridge.
        Removes stale state data across all phases.
        """
        if not self.flow_bridge:
            return {
                "status": "bridge_unavailable",
                "message": "Flow State Bridge not available for cleanup"
            }
        
        try:
            cleanup_result = await self.flow_bridge.cleanup_expired_states(expiration_hours)
            
            logger.info(f"✅ Phase states cleanup completed for session: {session_id}")
            return cleanup_result
            
        except Exception as e:
            logger.error(f"❌ Phase states cleanup failed: {e}")
            return {
                "status": "cleanup_error",
                "error": str(e)
            } 