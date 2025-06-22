"""
Dependency Analysis Executor
Handles dependency analysis phase execution for the Unified Discovery Flow.
"""

from typing import Dict, Any
from .base_phase_executor import BasePhaseExecutor


class DependencyAnalysisExecutor(BasePhaseExecutor):
    def get_phase_name(self) -> str:
        return "dependency_analysis"
    
    def get_progress_percentage(self) -> float:
        return 66.7  # 4/6 phases
    
    def execute_with_crew(self, crew_input: Dict[str, Any]) -> Dict[str, Any]:
        crew = self.crew_manager.create_crew_on_demand("dependency_analysis", **self._get_crew_context())
        crew_result = crew.kickoff(inputs=crew_input)
        return self._process_crew_result(crew_result)
    
    def execute_fallback(self) -> Dict[str, Any]:
        return {"dependencies": [], "fallback_used": True}
    
    def _prepare_crew_input(self) -> Dict[str, Any]:
        return {"asset_inventory": getattr(self.state, 'asset_inventory', {})}
    
    def _store_results(self, results: Dict[str, Any]):
        self.state.dependency_analysis = results 