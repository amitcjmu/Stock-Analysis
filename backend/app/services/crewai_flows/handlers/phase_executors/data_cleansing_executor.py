"""
Data Cleansing Executor
Handles data cleansing phase execution for the Unified Discovery Flow.
Split from unified_flow_phase_executor.py for better modularity.
"""

import logging
from typing import Dict, Any
from .base_phase_executor import BasePhaseExecutor

logger = logging.getLogger(__name__)


class DataCleansingExecutor(BasePhaseExecutor):
    """
    Executes data cleansing phase for the Unified Discovery Flow.
    Cleans and validates data using CrewAI crew or fallback logic.
    """
    
    def get_phase_name(self) -> str:
        return "data_cleansing"
    
    def get_progress_percentage(self) -> float:
        return 33.3  # 2/6 phases
    
    def execute_with_crew(self, crew_input: Dict[str, Any]) -> Dict[str, Any]:
        crew = self.crew_manager.create_crew_on_demand("data_cleansing", **self._get_crew_context())
        crew_result = crew.kickoff(inputs=crew_input)
        return self._process_crew_result(crew_result)
    
    def execute_fallback(self) -> Dict[str, Any]:
        return {
            "cleaned_data": self.state.raw_data,
            "quality_metrics": {"fallback_used": True}
        }
    
    def _prepare_crew_input(self) -> Dict[str, Any]:
        return {
            "raw_data": self.state.raw_data,
            "field_mappings": getattr(self.state, 'field_mappings', {}),
            "cleansing_type": "comprehensive_data_cleansing"
        }
    
    def _store_results(self, results: Dict[str, Any]):
        self.state.cleaned_data = results.get("cleaned_data", [])
        self.state.data_quality_metrics = results.get("quality_metrics", {}) 