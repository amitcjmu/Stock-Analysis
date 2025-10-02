"""
Component Analysis Crew - Public API

This module provides the public API for the Component Analysis Crew package.
It maintains backward compatibility by exporting the ComponentAnalysisCrew class
that was previously available from component_analysis_crew.py.

MIGRATION: This modularization preserves all existing functionality while
splitting the 796-line file into maintainable modules:

OLD STRUCTURE (single file - 796 lines):
----------------------------------------
backend/app/services/crewai_flows/crews/component_analysis_crew.py
    - Imports and fallback classes (lines 1-67)
    - ComponentAnalysisCrew class (lines 69-796)
        - __init__ method (lines 72-86)
        - _create_agents method (lines 88-213)
        - _create_crew method (lines 215-537)
        - execute method (lines 539-579)
        - _execute_fallback method (lines 581-698)
        - _process_crew_results method (lines 700-796)

NEW STRUCTURE (modularized - <400 lines each):
----------------------------------------------
backend/app/services/crewai_flows/crews/component_analysis_crew/
    - tools.py (~145 lines) - Tool placeholder classes
    - agents.py (~165 lines) - Agent creation logic
    - tasks.py (~375 lines) - Task and crew creation logic
    - crew.py (~395 lines) - Main ComponentAnalysisCrew class
    - __init__.py (~85 lines) - Public API exports

BACKWARD COMPATIBILITY:
-----------------------
All existing imports continue to work without changes:
    ✅ from app.services.crewai_flows.crews.component_analysis_crew import ComponentAnalysisCrew
    ✅ from app.services.crewai_flows.crews import component_analysis_crew

No code changes required in consuming modules!

Usage:
    from app.services.crewai_flows.crews.component_analysis_crew import (
        ComponentAnalysisCrew,  # Main crew class (recommended)

        # Optional: Advanced usage
        create_component_analysis_agents,
        create_component_analysis_tasks,
        create_component_analysis_crew_instance,

        # Optional: Tool classes (for custom tool development)
        ComponentDiscoveryTool,
        MetadataAnalyzer,
        DependencyMapper,
        TechDebtCalculator,
    )

References:
- docs/analysis/Notes/coding-agent-guide.md
- CLAUDE.md (Modularization Patterns section)
"""

# Import main crew class from crew module
from app.services.crewai_flows.crews.component_analysis_crew.crew import (
    ComponentAnalysisCrew,
)

# Import factory functions for advanced usage
from app.services.crewai_flows.crews.component_analysis_crew.agents import (
    create_component_analysis_agents,
)
from app.services.crewai_flows.crews.component_analysis_crew.tasks import (
    create_component_analysis_crew_instance,
    create_component_analysis_tasks,
)

# Import tool classes for custom tool development
from app.services.crewai_flows.crews.component_analysis_crew.tools import (
    ComponentDiscoveryTool,
    DependencyMapper,
    MetadataAnalyzer,
    TechDebtCalculator,
)

# Export all public APIs for backward compatibility
__all__ = [
    # Main crew class (primary export)
    "ComponentAnalysisCrew",
    # Factory functions (advanced usage)
    "create_component_analysis_agents",
    "create_component_analysis_tasks",
    "create_component_analysis_crew_instance",
    # Tool classes (custom tool development)
    "ComponentDiscoveryTool",
    "MetadataAnalyzer",
    "DependencyMapper",
    "TechDebtCalculator",
]
