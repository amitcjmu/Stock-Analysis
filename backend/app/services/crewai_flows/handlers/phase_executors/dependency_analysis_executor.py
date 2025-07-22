"""
Dependency Analysis Executor
Handles dependency analysis phase execution for the Unified Discovery Flow.
"""

from typing import Any, Dict

from .base_phase_executor import BasePhaseExecutor


class DependencyAnalysisExecutor(BasePhaseExecutor):
    def get_phase_name(self) -> str:
        return "dependencies"  # FIX: Map to correct DB phase name
    
    def get_progress_percentage(self) -> float:
        return 66.7  # 4/6 phases
    
    async def execute_with_crew(self, crew_input: Dict[str, Any]) -> Dict[str, Any]:
        # Get required data for dependencies crew
        asset_inventory = getattr(self.state, 'asset_inventory', {})
        
        crew = self.crew_manager.create_crew_on_demand(
            "dependencies", 
            asset_inventory=asset_inventory,
            **self._get_crew_context()
        )
        # Run crew in thread to avoid blocking async execution
        import asyncio
        crew_result = await asyncio.to_thread(crew.kickoff, inputs=crew_input)
        return self._process_crew_result(crew_result)
    
    async def execute_fallback(self) -> Dict[str, Any]:
        # 🚀 DATA VALIDATION: Check if we have data to process
        asset_inventory = getattr(self.state, 'asset_inventory', {})
        if not asset_inventory or asset_inventory.get('total_assets', 0) == 0:
            return {"status": "skipped", "reason": "no_data", "dependencies": []}
        
        # Basic dependency analysis based on asset inventory
        total_assets = asset_inventory.get('total_assets', 0)
        return {
            "app_server_dependencies": {
                "hosting_relationships": [],
                "resource_mappings": [],
                "topology_insights": {"fallback_used": True}
            },
            "app_app_dependencies": {
                "communication_patterns": [],
                "api_dependencies": [],
                "integration_complexity": {"fallback_used": True},
                "dependency_graph": {"nodes": [], "edges": []}
            },
            "fallback_used": True, 
            "assets_analyzed": total_assets
        }
    
    def _prepare_crew_input(self) -> Dict[str, Any]:
        return {"asset_inventory": getattr(self.state, 'asset_inventory', {})}
    
    def _store_results(self, results: Dict[str, Any]):
        self.state.dependencies = results 