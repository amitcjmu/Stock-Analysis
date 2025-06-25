"""
Tech Debt Executor  
Handles tech debt analysis phase execution for the Unified Discovery Flow.
"""

from typing import Dict, Any
from .base_phase_executor import BasePhaseExecutor


class TechDebtExecutor(BasePhaseExecutor):
    def get_phase_name(self) -> str:
        return "tech_debt"  # FIX: Map to correct DB phase name
    
    def get_progress_percentage(self) -> float:
        return 83.3  # 5/6 phases
    
    def execute_with_crew(self, crew_input: Dict[str, Any]) -> Dict[str, Any]:
        crew = self.crew_manager.create_crew_on_demand("tech_debt", **self._get_crew_context())
        crew_result = crew.kickoff(inputs=crew_input)
        return self._process_crew_result(crew_result)
    
    async def execute_fallback(self) -> Dict[str, Any]:
        # 🚀 DATA VALIDATION: Check if we have data to process  
        asset_inventory = getattr(self.state, 'asset_inventory', {})
        if not asset_inventory or asset_inventory.get('total_assets', 0) == 0:
            return {"status": "skipped", "reason": "no_data", "recommendations": []}
        
        # Basic tech debt analysis based on asset inventory
        total_assets = asset_inventory.get('total_assets', 0)
        return {
            "debt_scores": {"fallback_used": True},
            "modernization_recommendations": [],
            "risk_assessments": {"fallback_used": True},
            "six_r_preparation": {"fallback_used": True},
            "fallback_used": True, 
            "assets_analyzed": total_assets
        }
    
    def _prepare_crew_input(self) -> Dict[str, Any]:
        return {"asset_inventory": getattr(self.state, 'asset_inventory', {})}
    
    def _store_results(self, results: Dict[str, Any]):
        self.state.technical_debt = results 