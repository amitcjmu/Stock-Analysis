"""
Architecture Standards Crew - Public API

This module provides the public API for the Architecture Standards Crew package.
It maintains backward compatibility by exporting the ArchitectureStandardsCrew class
that was previously available from architecture_standards_crew.py.

MIGRATION: This modularization preserves all existing functionality while
splitting the 660-line file into maintainable modules:

OLD STRUCTURE (single file - 660 lines):
----------------------------------------
backend/app/services/crewai_flows/crews/architecture_standards_crew.py
    - Imports and fallback classes (lines 1-58)
    - ArchitectureStandardsCrew class (lines 61-660)
        - __init__ method (lines 64-77)
        - _create_agents method (lines 79-197)
        - _create_crew method (lines 199-450)
        - execute method (lines 452-488)
        - _execute_fallback method (lines 490-597)
        - _process_crew_results method (lines 599-660)

NEW STRUCTURE (modularized - <400 lines each):
----------------------------------------------
backend/app/services/crewai_flows/crews/architecture_standards_crew/
    - tools.py (~107 lines) - Tool placeholder classes
    - agents.py (~195 lines) - Agent creation logic
    - tasks.py (~397 lines) - Task and crew creation logic
    - fallback.py (~184 lines) - Fallback implementation
    - crew.py (~274 lines) - Main ArchitectureStandardsCrew class
    - __init__.py (~97 lines) - Public API exports

BACKWARD COMPATIBILITY:
-----------------------
All existing imports continue to work without changes:
    ✅ from app.services.crewai_flows.crews.architecture_standards_crew import ArchitectureStandardsCrew
    ✅ from app.services.crewai_flows.crews import architecture_standards_crew

No code changes required in consuming modules!

Usage:
    from app.services.crewai_flows.crews.architecture_standards_crew import (
        ArchitectureStandardsCrew,  # Main crew class (recommended)

        # Optional: Advanced usage
        create_architecture_standards_agents,
        create_architecture_standards_tasks,
        create_architecture_standards_crew_instance,

        # Optional: Tool classes (for custom tool development)
        TechnologyVersionAnalyzer,
        ComplianceChecker,
        StandardsTemplateGenerator,

        # Optional: Fallback function
        execute_fallback_architecture_standards,
    )

References:
- docs/analysis/Notes/coding-agent-guide.md
- CLAUDE.md (Modularization Patterns section)
"""

# Import main crew class from crew module
from app.services.crewai_flows.crews.architecture_standards_crew.crew import (
    ArchitectureStandardsCrew,
)

# Import factory functions for advanced usage
from app.services.crewai_flows.crews.architecture_standards_crew.agents import (
    create_architecture_standards_agents,
)
from app.services.crewai_flows.crews.architecture_standards_crew.tasks import (
    create_architecture_standards_crew_instance,
    create_architecture_standards_tasks,
)

# Import tool classes for custom tool development
from app.services.crewai_flows.crews.architecture_standards_crew.tools import (
    ComplianceChecker,
    StandardsTemplateGenerator,
    TechnologyVersionAnalyzer,
)

# Import fallback function for testing/debugging
from app.services.crewai_flows.crews.architecture_standards_crew.fallback import (
    execute_fallback_architecture_standards,
)

# Export all public APIs for backward compatibility
__all__ = [
    # Main crew class (primary export)
    "ArchitectureStandardsCrew",
    # Factory functions (advanced usage)
    "create_architecture_standards_agents",
    "create_architecture_standards_tasks",
    "create_architecture_standards_crew_instance",
    # Tool classes (custom tool development)
    "TechnologyVersionAnalyzer",
    "ComplianceChecker",
    "StandardsTemplateGenerator",
    # Fallback function (testing/debugging)
    "execute_fallback_architecture_standards",
]
