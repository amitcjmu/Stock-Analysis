"""
Asset Inventory Executor
Handles asset inventory phase execution for the Unified Discovery Flow.
"""

from typing import Dict, Any
from .base_phase_executor import BasePhaseExecutor


class AssetInventoryExecutor(BasePhaseExecutor):
    def get_phase_name(self) -> str:
        return "asset_inventory"
    
    def get_progress_percentage(self) -> float:
        return 50.0  # 3/6 phases
    
    def execute_with_crew(self, crew_input: Dict[str, Any]) -> Dict[str, Any]:
        crew = self.crew_manager.create_crew_on_demand("asset_inventory", **self._get_crew_context())
        crew_result = crew.kickoff(inputs=crew_input)
        return self._process_crew_result(crew_result)
    
    def execute_fallback(self) -> Dict[str, Any]:
        return {"servers": [], "total_assets": 0, "classification_metadata": {"fallback_used": True}}
    
    def _prepare_crew_input(self) -> Dict[str, Any]:
        return {"cleaned_data": getattr(self.state, 'cleaned_data', [])}
    
    def _store_results(self, results: Dict[str, Any]):
        self.state.asset_inventory = results 