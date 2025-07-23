"""
Inventory Building Crew Execution Handler
"""

import logging
from typing import Any, Dict

from .base import CrewExecutionBase
from .fallbacks import CrewFallbackHandler
from .parsers import CrewResultParser

logger = logging.getLogger(__name__)


class InventoryBuildingExecutor(CrewExecutionBase):
    """Handles execution of Inventory Building Crew"""

    def __init__(self, crewai_service):
        super().__init__(crewai_service)
        self.parser = CrewResultParser()
        self.fallback_handler = CrewFallbackHandler()

    def execute_inventory_building_crew(self, state) -> Dict[str, Any]:
        """Execute Inventory Building Crew with enhanced CrewAI features"""
        try:
            # Execute enhanced Inventory Building Crew
            try:
                from app.services.crewai_flows.crews.inventory_building_crew import (
                    create_inventory_building_crew,
                )

                # Pass shared memory and cleaned data
                shared_memory = getattr(state, "shared_memory_reference", None)

                # Create and execute the enhanced crew
                crew = create_inventory_building_crew(
                    self.crewai_service,
                    state.cleaned_data,
                    state.field_mappings,
                    shared_memory=shared_memory,
                )
                crew_result = crew.kickoff()

                # Parse crew results
                asset_inventory = self.parser.parse_inventory_results(
                    crew_result, state.cleaned_data
                )

                logger.info("✅ Enhanced Inventory Building Crew executed successfully")

            except Exception as crew_error:
                logger.warning(
                    f"Enhanced Inventory Building Crew execution failed, using fallback: {crew_error}"
                )
                # Fallback classification
                asset_inventory = (
                    self.fallback_handler.intelligent_asset_classification_fallback(
                        state.cleaned_data
                    )
                )

            crew_status = self.create_crew_status(
                status="completed",
                manager="Inventory Manager",
                agents=[
                    "Server Classification Expert",
                    "Application Discovery Expert",
                    "Device Classification Expert",
                ],
                success_criteria_met=True,
            )

            return {"asset_inventory": asset_inventory, "crew_status": crew_status}

        except Exception as e:
            logger.error(f"Inventory Building Crew execution failed: {e}")
            raise
