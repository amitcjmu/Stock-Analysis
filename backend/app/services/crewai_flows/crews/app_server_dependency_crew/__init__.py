"""
App-Server Dependency Crew - Public API

This module provides the public API for the App-Server Dependency Crew package.
It maintains backward compatibility by exporting all classes and functions that
were previously available from app_server_dependency_crew.py.

MIGRATION: This modularization preserves all existing functionality while
splitting the 567-line file into maintainable modules:

OLD STRUCTURE (single file - 567 lines):
----------------------------------------
backend/app/services/crewai_flows/crews/app_server_dependency_crew.py
    - Imports and fallback classes (lines 1-42)
    - AppServerDependencyCrew class (lines 45-303)
        - __init__ method (lines 48-66)
        - _setup_shared_memory method (lines 68-84)
        - _setup_knowledge_base method (lines 86-104)
        - create_agents method (lines 106-158)
        - create_tasks method (lines 160-240)
        - create_crew method (lines 242-293)
        - Tool placeholder methods (lines 295-303)
    - create_app_server_dependency_crew function (lines 305-488)
    - Tool creation helper functions (lines 490-557)
    - _create_fallback_app_server_dependency_crew function (lines 559-567)

NEW STRUCTURE (modularized - <400 lines each):
----------------------------------------------
backend/app/services/crewai_flows/crews/app_server_dependency_crew/
    - tools.py (~315 lines) - Tool classes and helper functions
    - agents.py (~170 lines) - Agent creation logic
    - tasks.py (~267 lines) - Task creation and crew factory
    - crew.py (~206 lines) - Main AppServerDependencyCrew class
    - __init__.py (~120 lines) - Public API exports

BACKWARD COMPATIBILITY:
-----------------------
All existing imports continue to work without changes:
    ✅ from app.services.crewai_flows.crews.app_server_dependency_crew import AppServerDependencyCrew
    ✅ from app.services.crewai_flows.crews.app_server_dependency_crew import create_app_server_dependency_crew
    ✅ from app.services.crewai_flows.crews import app_server_dependency_crew

No code changes required in consuming modules!

Usage:
    from app.services.crewai_flows.crews.app_server_dependency_crew import (
        AppServerDependencyCrew,  # Main crew class (recommended)
        create_app_server_dependency_crew,  # Legacy factory function

        # Optional: Advanced usage
        create_app_server_dependency_agents,
        create_app_server_dependency_tasks,
        create_app_server_dependency_crew_instance,

        # Optional: Tool classes (for custom tool development)
        HostingAnalysisTool,
        TopologyMappingTool,
        RelationshipValidationTool,
        MigrationComplexityTool,
        CapacityAnalysisTool,
        ImpactAssessmentTool,

        # Optional: Tool helper functions
        _create_hosting_analysis_tool,
        _create_topology_mapping_tool,
        _create_relationship_validation_tool,
        _create_migration_complexity_tool,
        _create_capacity_analysis_tool,
        _create_impact_assessment_tool,
    )

References:
- docs/analysis/Notes/coding-agent-guide.md
- CLAUDE.md (Modularization Patterns section)
"""

# Import main crew class from crew module
from app.services.crewai_flows.crews.app_server_dependency_crew.crew import (
    AppServerDependencyCrew,
)

# Import factory functions for advanced usage
from app.services.crewai_flows.crews.app_server_dependency_crew.agents import (
    create_app_server_dependency_agents,
)
from app.services.crewai_flows.crews.app_server_dependency_crew.tasks import (
    create_app_server_dependency_crew_instance,
    create_app_server_dependency_tasks,
)

# Import tool classes for custom tool development
from app.services.crewai_flows.crews.app_server_dependency_crew.tools import (
    CapacityAnalysisTool,
    HostingAnalysisTool,
    ImpactAssessmentTool,
    MigrationComplexityTool,
    RelationshipValidationTool,
    TopologyMappingTool,
    _create_capacity_analysis_tool,
    _create_hosting_analysis_tool,
    _create_impact_assessment_tool,
    _create_migration_complexity_tool,
    _create_relationship_validation_tool,
    _create_topology_mapping_tool,
)

# Backward compatibility alias for the legacy factory function
# This ensures existing code that calls create_app_server_dependency_crew() continues to work
create_app_server_dependency_crew = create_app_server_dependency_crew_instance


# Export all public APIs for backward compatibility
__all__ = [
    # Main crew class (primary export)
    "AppServerDependencyCrew",
    # Factory functions (legacy and advanced usage)
    "create_app_server_dependency_crew",  # Legacy function name
    "create_app_server_dependency_crew_instance",  # New function name
    "create_app_server_dependency_agents",
    "create_app_server_dependency_tasks",
    # Tool classes (custom tool development)
    "HostingAnalysisTool",
    "TopologyMappingTool",
    "RelationshipValidationTool",
    "MigrationComplexityTool",
    "CapacityAnalysisTool",
    "ImpactAssessmentTool",
    # Tool helper functions (internal use)
    "_create_hosting_analysis_tool",
    "_create_topology_mapping_tool",
    "_create_relationship_validation_tool",
    "_create_migration_complexity_tool",
    "_create_capacity_analysis_tool",
    "_create_impact_assessment_tool",
]
