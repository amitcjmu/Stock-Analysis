"""
Phase Execution Manager
Coordinates execution of discovery phases for the Unified Discovery Flow.
Split from unified_flow_phase_executor.py for better modularity.
"""

import logging
from typing import Dict, Any

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
    """
    
    def __init__(self, state, crew_manager):
        """Initialize phase execution manager with state and crew manager references"""
        self.state = state
        self.crew_manager = crew_manager
        
        # Initialize phase executors
        from .field_mapping_executor import FieldMappingExecutor
        from .data_cleansing_executor import DataCleansingExecutor
        from .asset_inventory_executor import AssetInventoryExecutor
        from .dependency_analysis_executor import DependencyAnalysisExecutor
        from .tech_debt_executor import TechDebtExecutor
        
        self.field_mapping_executor = FieldMappingExecutor(state, crew_manager)
        self.data_cleansing_executor = DataCleansingExecutor(state, crew_manager)
        self.asset_inventory_executor = AssetInventoryExecutor(state, crew_manager)
        self.dependency_analysis_executor = DependencyAnalysisExecutor(state, crew_manager)
        self.tech_debt_executor = TechDebtExecutor(state, crew_manager)
    
    def execute_field_mapping_phase(self, previous_result):
        """Execute field mapping phase"""
        return self.field_mapping_executor.execute(previous_result)
    
    def execute_data_cleansing_phase(self, previous_result):
        """Execute data cleansing phase"""
        return self.data_cleansing_executor.execute(previous_result)
    
    def execute_asset_inventory_phase(self, previous_result):
        """Execute asset inventory phase"""
        return self.asset_inventory_executor.execute(previous_result)
    
    def execute_dependency_analysis_phase(self, previous_result):
        """Execute dependency analysis phase"""
        return self.dependency_analysis_executor.execute(previous_result)
    
    def execute_tech_debt_analysis_phase(self, previous_result):
        """Execute tech debt analysis phase"""
        return self.tech_debt_executor.execute(previous_result)
    
    def get_phase_executor(self, phase_name: str):
        """Get specific phase executor by name"""
        executors = {
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
                "field_mapping", "data_cleansing", "asset_inventory",
                "dependency_analysis", "tech_debt_analysis"
            ],
            "crewai_available": CREWAI_FLOW_AVAILABLE
        } 