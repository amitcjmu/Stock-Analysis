"""
Inventory Building Crew - Public API

This module provides the public API for the Inventory Building Crew package.
It maintains backward compatibility by exporting the InventoryBuildingCrew class
and factory function that were previously available from inventory_building_crew_original.py.

⚠️  DEPRECATION WARNING:
This crew is DEPRECATED as of September 2025. Asset inventory now uses persistent
agents via TenantScopedAgentPool. See:
- backend/app/services/flow_orchestration/execution_engine_crew_discovery.py (lines 324-412)
- backend/app/services/persistent_agents/tenant_scoped_agent_pool.py

This implementation is kept for backward compatibility only and should not be used
for new deployments.

MIGRATION NOTES:
----------------
OLD STRUCTURE (single file - 564 lines):
backend/app/services/crewai_flows/crews/inventory_building_crew_original.py
    - Imports and fallback classes (lines 1-56)
    - InventoryBuildingCrew class (lines 58-553)
        - __init__ method (lines 61-80)
        - _setup_shared_memory method (lines 82-100)
        - _setup_knowledge_base method (lines 102-116)
        - create_agents method (lines 118-282)
        - create_tasks method (lines 284-403)
        - create_crew method (lines 405-470)
        - Helper methods (lines 472-551)
    - Factory function (lines 554-564)

NEW STRUCTURE (modularized - all files <400 lines):
backend/app/services/crewai_flows/crews/inventory_building_crew_original/
    - tools.py (177 lines) - Tool creation functions and helper utilities
    - agents.py (231 lines) - Agent creation logic with domain expertise
    - tasks.py (160 lines) - Task creation with sequential-then-parallel flow
    - crew.py (250 lines) - Main InventoryBuildingCrew class and factory
    - __init__.py (this file) - Public API exports for backward compatibility

BACKWARD COMPATIBILITY:
-----------------------
All existing imports continue to work without changes:
    ✅ from app.services.crewai_flows.crews.inventory_building_crew_original import InventoryBuildingCrew
    ✅ from app.services.crewai_flows.crews.inventory_building_crew_original import create_inventory_building_crew
    ✅ from app.services.crewai_flows.crews import inventory_building_crew_original

No code changes required in consuming modules!

Usage:
------
    from app.services.crewai_flows.crews.inventory_building_crew_original import (
        InventoryBuildingCrew,              # Main crew class (recommended)
        create_inventory_building_crew,     # Factory function

        # Optional: Advanced usage
        create_inventory_agents,
        create_inventory_tasks,

        # Optional: Tool utilities
        _create_server_classification_tools,
        _create_app_classification_tools,
        _create_device_classification_tools,
        _identify_asset_type_indicators,
        _filter_infrastructure_mappings,
        _filter_application_mappings,
        _filter_device_mappings,
    )

References:
-----------
- docs/analysis/Notes/coding-agent-guide.md (Modularization Patterns)
- CLAUDE.md (Modularization section)
- backend/app/services/crewai_flows/crews/component_analysis_crew/ (Reference pattern)
"""

# Import main crew class and factory from crew module
from app.services.crewai_flows.crews.inventory_building_crew_original.crew import (
    InventoryBuildingCrew,
    create_inventory_building_crew,
)

# Import factory functions for advanced usage
from app.services.crewai_flows.crews.inventory_building_crew_original.agents import (
    CREWAI_ADVANCED_AVAILABLE,
    create_inventory_agents,
)
from app.services.crewai_flows.crews.inventory_building_crew_original.tasks import (
    create_inventory_tasks,
)

# Import tool utilities for custom tool development
from app.services.crewai_flows.crews.inventory_building_crew_original.tools import (
    _create_app_classification_tools,
    _create_device_classification_tools,
    _create_server_classification_tools,
    _filter_application_mappings,
    _filter_device_mappings,
    _filter_infrastructure_mappings,
    _identify_asset_type_indicators,
)

# Export all public APIs for backward compatibility
__all__ = [
    # Main crew class and factory (primary exports)
    "InventoryBuildingCrew",
    "create_inventory_building_crew",
    # Factory functions (advanced usage)
    "create_inventory_agents",
    "create_inventory_tasks",
    # Tool utilities (custom tool development)
    "_create_server_classification_tools",
    "_create_app_classification_tools",
    "_create_device_classification_tools",
    "_identify_asset_type_indicators",
    "_filter_infrastructure_mappings",
    "_filter_application_mappings",
    "_filter_device_mappings",
    # Feature flags
    "CREWAI_ADVANCED_AVAILABLE",
]
