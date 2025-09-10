"""
DEPRECATED: Inventory Building Crew - Minimal Backward Compatibility Version

⚠️  WARNING: This file is DEPRECATED as of September 2025
⚠️  Asset inventory now uses persistent agents via TenantScopedAgentPool
⚠️  See: backend/app/services/flow_orchestration/execution_engine_crew_discovery.py
⚠️  This file is kept for backward compatibility but should not be used

MIGRATION NOTES:
- Asset inventory phase now handled by persistent agents in execution_engine_crew_discovery.py (lines 324-412)
- Intelligence endpoint updated to use persistent agents in intelligence.py
- All crew factory references commented out in managers and config files
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class DeprecatedCrewPlaceholder:
    """Placeholder crew class for deprecated inventory building crew."""

    def __init__(self, crewai_service, shared_memory=None, knowledge_base=None):
        logger.warning(
            "⚠️ InventoryBuildingCrew is deprecated - use persistent agents instead"
        )
        self.crewai_service = crewai_service

    def create_crew(self, cleaned_data, field_mappings, context_info=None):
        """Return a placeholder crew that does nothing."""
        logger.warning("⚠️ create_crew called on deprecated InventoryBuildingCrew")

        # Return minimal crew structure that won't crash existing code
        return type(
            "DeprecatedCrew",
            (),
            {
                "kickoff": lambda: {
                    "status": "deprecated",
                    "message": "Inventory building now uses persistent agents",
                    "assets_processed": 0,
                }
            },
        )()


def create_inventory_building_crew(
    crewai_service,
    cleaned_data: List[Dict[str, Any]],
    field_mappings: Dict[str, Any],
    shared_memory=None,
    knowledge_base=None,
    context_info: Dict[str, Any] = None,
):
    """DEPRECATED: Factory function for inventory building crew - returns placeholder."""
    logger.warning(
        "⚠️ create_inventory_building_crew is deprecated - use persistent agents instead"
    )
    crew_instance = DeprecatedCrewPlaceholder(
        crewai_service, shared_memory, knowledge_base
    )
    return crew_instance.create_crew(cleaned_data, field_mappings, context_info)
