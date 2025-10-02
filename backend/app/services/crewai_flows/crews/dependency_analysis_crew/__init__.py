"""
Dependency Analysis Crew - Public API

This module provides the public API for the Dependency Analysis Crew package.
It maintains backward compatibility by exporting the DependencyAnalysisCrew class
that was previously available from dependency_analysis_crew.py.

MIGRATION: This modularization preserves all existing functionality while
splitting the 764-line file into maintainable modules:

OLD STRUCTURE (single file - 764 lines):
----------------------------------------
backend/app/services/crewai_flows/crews/dependency_analysis_crew.py
    - Imports and classes (lines 1-38)
    - NetworkTopologyTool class (lines 40-162)
    - DependencyAnalysisCrew class (lines 164-746)
        - __init__ method (lines 170-194)
        - _create_network_architecture_specialist (lines 196-217)
        - _create_application_dependency_analyst (lines 219-237)
        - _create_infrastructure_dependency_mapper (lines 239-257)
        - kickoff method (lines 259-372)
        - _create_tasks method (lines 374-504)
        - _process_crew_results method (lines 506-692)
        - _determine_architecture_type_from_asset (lines 694-710)
        - _generate_dependency_summary (lines 712-746)
    - Factory function (lines 748-757)
    - Exports (lines 759-764)

NEW STRUCTURE (modularized - <400 lines each):
----------------------------------------------
backend/app/services/crewai_flows/crews/dependency_analysis_crew/
    - tools.py (~172 lines) - NetworkTopologyTool and DependencyAnalysisResult
    - agents.py (~157 lines) - Agent creation logic
    - tasks.py (~223 lines) - Task creation logic
    - crew.py (~393 lines) - Main DependencyAnalysisCrew class
    - __init__.py (~97 lines) - Public API exports

BACKWARD COMPATIBILITY:
-----------------------
All existing imports continue to work without changes:
    ✅ from app.services.crewai_flows.crews.dependency_analysis_crew import DependencyAnalysisCrew
    ✅ from app.services.crewai_flows.crews.dependency_analysis_crew import create_dependency_analysis_crew
    ✅ from app.services.crewai_flows.crews import dependency_analysis_crew

No code changes required in consuming modules!

Usage:
    from app.services.crewai_flows.crews.dependency_analysis_crew import (
        DependencyAnalysisCrew,  # Main crew class (recommended)
        create_dependency_analysis_crew,  # Factory function

        # Optional: Advanced usage
        create_dependency_analysis_agents,
        create_dependency_analysis_tasks,
        create_dependency_analysis_crew_instance,

        # Optional: Tool and model classes
        NetworkTopologyTool,
        DependencyAnalysisResult,
    )

References:
- docs/analysis/Notes/coding-agent-guide.md
- CLAUDE.md (Modularization Patterns section)
"""

# Import main crew class and factory function
from app.services.crewai_flows.crews.dependency_analysis_crew.crew import (
    DependencyAnalysisCrew,
    create_dependency_analysis_crew,
)

# Import factory functions for advanced usage
from app.services.crewai_flows.crews.dependency_analysis_crew.agents import (
    create_application_dependency_analyst,
    create_dependency_analysis_agents,
    create_infrastructure_dependency_mapper,
    create_network_architecture_specialist,
)
from app.services.crewai_flows.crews.dependency_analysis_crew.tasks import (
    create_dependency_analysis_crew_instance,
    create_dependency_analysis_tasks,
)

# Import tool and model classes
from app.services.crewai_flows.crews.dependency_analysis_crew.tools import (
    DependencyAnalysisResult,
    NetworkTopologyTool,
)

# Export all public APIs for backward compatibility
__all__ = [
    # Main crew class and factory (primary exports)
    "DependencyAnalysisCrew",
    "create_dependency_analysis_crew",
    # Result model
    "DependencyAnalysisResult",
    # Factory functions (advanced usage)
    "create_dependency_analysis_agents",
    "create_dependency_analysis_tasks",
    "create_dependency_analysis_crew_instance",
    "create_network_architecture_specialist",
    "create_application_dependency_analyst",
    "create_infrastructure_dependency_mapper",
    # Tool classes
    "NetworkTopologyTool",
]
