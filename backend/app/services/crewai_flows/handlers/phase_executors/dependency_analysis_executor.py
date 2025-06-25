"""
Dependency Analysis Executor
Handles dependency analysis phase execution for the Unified Discovery Flow.
"""

from typing import Dict, Any
from .base_phase_executor import BasePhaseExecutor


class DependencyAnalysisExecutor(BasePhaseExecutor):
    def get_phase_name(self) -> str:
        return "dependencies"  # FIX: Map to correct DB phase name
    
    def get_progress_percentage(self) -> float:
        return 66.7  # 4/6 phases
    
    def execute_with_crew(self, crew_input: Dict[str, Any]) -> Dict[str, Any]:
        crew = self.crew_manager.create_crew_on_demand("dependency_analysis", **self._get_crew_context())
        crew_result = crew.kickoff(inputs=crew_input)
        return self._process_crew_result(crew_result)
    
    async def execute_fallback(self) -> Dict[str, Any]:
        # 🚀 DATA VALIDATION: Check if we have data to process
        if not hasattr(self.state, 'processed_assets') or not self.state.processed_assets:
            return {"status": "skipped", "reason": "no_data", "dependencies": []}
        
        return {"dependencies": [], "fallback_used": True, "assets_analyzed": len(self.state.processed_assets)}
    
    def _prepare_crew_input(self) -> Dict[str, Any]:
        return {"asset_inventory": getattr(self.state, 'asset_inventory', {})}
    
    def _store_results(self, results: Dict[str, Any]):
        self.state.dependency_analysis = results 