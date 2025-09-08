"""
Asset Inventory Executor
Main executor class for asset inventory phase execution in the Unified Discovery Flow.
Uses modularized components for database operations, crew processing, and utilities.
"""

import asyncio
import logging
from typing import Any, Dict

from ..base_phase_executor import BasePhaseExecutor
from .crew_processor import CrewProcessor
from .database_operations import AssetDatabaseOperations

logger = logging.getLogger(__name__)


class AssetInventoryExecutor(BasePhaseExecutor):
    """Main executor for the asset inventory phase"""

    def __init__(self, state, crew_manager, flow_bridge=None):
        """Initialize with modularized components"""
        super().__init__(state, crew_manager, flow_bridge)
        self.crew_processor = CrewProcessor(state)
        self.database_ops = AssetDatabaseOperations(state, flow_bridge)

    def get_phase_name(self) -> str:
        return "inventory"  # FIX: Map to correct DB phase name

    def get_progress_percentage(self) -> float:
        return 50.0  # 3/6 phases

    def _get_phase_timeout(self) -> int:
        """Asset inventory processing has no timeout restrictions for agentic activities"""
        return None  # No timeout for asset classification processing

    async def execute_with_crew(self, crew_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the asset inventory phase with crew"""
        # Get required data for inventory crew
        cleaned_data = getattr(self.state, "cleaned_data", [])
        field_mappings = getattr(self.state, "field_mappings", {})

        logger.info(
            f"🚀 Starting asset inventory crew execution with {len(cleaned_data)} records"
        )

        # Create crew with context
        crew_context = self._get_crew_context()
        crew = self.crew_manager.create_crew_on_demand(
            "inventory",
            cleaned_data=cleaned_data,
            field_mappings=field_mappings,
            **crew_context,
        )

        # Run crew in thread to avoid blocking async execution
        crew_result = await asyncio.to_thread(crew.kickoff, inputs=crew_input)

        # Process crew results
        results = self.crew_processor.process_crew_result(crew_result)

        # Persist assets to database after crew processing
        await self.database_ops.persist_assets_to_database(results)

        return results

    async def execute_fallback(self) -> Dict[str, Any]:
        """NO FALLBACK LOGIC - FAIL FAST TO IDENTIFY REAL ISSUES"""
        logger.error(
            "❌ FALLBACK EXECUTION DISABLED - Asset inventory crew must work properly"
        )
        logger.error("❌ If you see this error, fix the actual crew execution issues")
        raise RuntimeError("Asset inventory fallback disabled - crew execution failed")

    def _get_crew_context(self) -> Dict[str, Any]:
        """Override to provide context for deduplication tools"""
        context = super()._get_crew_context()

        # Get crew-specific context from processor
        crew_context = self.crew_processor.get_crew_context()
        context.update(crew_context)

        # If state attributes are not available, try to get from flow_bridge
        context_info = crew_context.get("context_info", {})
        if (
            not context_info.get("client_account_id")
            and self.flow_bridge
            and hasattr(self.flow_bridge, "context")
        ):
            bridge_context = self.flow_bridge.context
            context_info.update(
                {
                    "client_account_id": bridge_context.client_account_id,
                    "engagement_id": bridge_context.engagement_id,
                    "user_id": bridge_context.user_id,
                    "flow_id": bridge_context.flow_id,
                }
            )
            context["context_info"] = context_info

        return context

    def _prepare_crew_input(self) -> Dict[str, Any]:
        """Prepare input data for the crew"""
        return self.crew_processor.prepare_crew_input()

    async def _store_results(self, results: Dict[str, Any]):
        """Store results in state - persistence is handled in execute_with_crew"""
        self.state.asset_inventory = results

    def _execute_fallback_sync(self) -> Dict[str, Any]:
        """NO SYNC FALLBACK - This method should never be called"""
        logger.error("❌ _execute_fallback_sync called - this method is disabled")
        raise RuntimeError("Sync fallback disabled - crew execution must work properly")
