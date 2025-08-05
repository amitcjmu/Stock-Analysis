"""
Tech Debt Executor
Handles tech debt analysis phase execution for the Unified Discovery Flow.
"""

from typing import Any, Dict

from .base_phase_executor import BasePhaseExecutor


class TechDebtExecutor(BasePhaseExecutor):
    def get_phase_name(self) -> str:
        return "tech_debt"  # FIX: Map to correct DB phase name

    def get_progress_percentage(self) -> float:
        return 83.3  # 5/6 phases

    async def execute_with_crew(self, crew_input: Dict[str, Any]) -> Dict[str, Any]:
        # Get required data for tech debt crew
        asset_inventory = getattr(self.state, "asset_inventory", {})
        dependencies = getattr(self.state, "dependencies", {})

        crew = self.crew_manager.create_crew_on_demand(
            "tech_debt",
            asset_inventory=asset_inventory,
            dependencies=dependencies,
            **self._get_crew_context()
        )
        # Run crew in thread to avoid blocking async execution
        import asyncio

        crew_result = await asyncio.to_thread(crew.kickoff, inputs=crew_input)
        return self._process_crew_result(crew_result)

    async def execute_fallback(self) -> Dict[str, Any]:
        """
        Fallback execution is disabled for this phase.
        This design choice ensures that the system relies on the more capable
        CrewAI-driven analysis and avoids producing potentially misleading or
        superficial results from a rule-based fallback.
        """
        # self.logger.warning("FALLBACK EXECUTION DISABLED for tech debt analysis.")
        raise RuntimeError(
            "Tech Debt Analysis fallback disabled. "
            "CrewAI execution is required for this phase."
        )

    def _prepare_crew_input(self) -> Dict[str, Any]:
        return {"asset_inventory": getattr(self.state, "asset_inventory", {})}

    async def _store_results(self, results: Dict[str, Any]):
        self.state.technical_debt = results
