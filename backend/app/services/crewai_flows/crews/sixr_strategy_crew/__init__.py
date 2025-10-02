"""
Six R Strategy Crew - Public API

This module provides the public API for the Six R Strategy Crew package.
It maintains backward compatibility by exporting the SixRStrategyCrew class
that was previously available from sixr_strategy_crew.py.

MIGRATION: This modularization preserves all existing functionality while
splitting the 767-line file into maintainable modules:

OLD STRUCTURE (single file - 767 lines):
----------------------------------------
backend/app/services/crewai_flows/crews/sixr_strategy_crew.py
    - Imports and fallback classes (lines 1-60)
    - SixRStrategyCrew class (lines 66-767)
        - __init__ method (lines 69-83)
        - _create_agents method (lines 84-241)
        - _create_crew method (lines 243-551)
        - execute method (lines 553-594)
        - _execute_fallback method (lines 596-694)
        - _process_crew_results method (lines 696-767)

NEW STRUCTURE (modularized - <400 lines each):
----------------------------------------------
backend/app/services/crewai_flows/crews/sixr_strategy_crew/
    - tools.py (~245 lines) - Tool placeholder classes
    - agents.py (~193 lines) - Agent creation logic
    - tasks.py (~378 lines) - Task and crew creation logic
    - fallback.py (~211 lines) - Fallback implementation and result processing
    - crew.py (~247 lines) - Main SixRStrategyCrew class
    - __init__.py (~105 lines) - Public API exports

BACKWARD COMPATIBILITY:
-----------------------
All existing imports continue to work without changes:
    ✅ from app.services.crewai_flows.crews.sixr_strategy_crew import SixRStrategyCrew
    ✅ from app.services.crewai_flows.crews import sixr_strategy_crew

No code changes required in consuming modules!

Usage:
    from app.services.crewai_flows.crews.sixr_strategy_crew import (
        SixRStrategyCrew,  # Main crew class (recommended)

        # Optional: Advanced usage
        create_sixr_strategy_agents,
        create_sixr_strategy_tasks,
        create_sixr_strategy_crew_instance,

        # Optional: Tool classes (for custom tool development)
        SixRDecisionEngine,
        ComponentAnalyzer,
        BusinessValueCalculator,
        CompatibilityChecker,
        IntegrationAnalyzer,
        MoveGroupAnalyzer,
        DependencyOptimizer,
    )

References:
- docs/analysis/Notes/coding-agent-guide.md
- CLAUDE.md (Modularization Patterns section)
"""

# Import main crew class from crew module
from app.services.crewai_flows.crews.sixr_strategy_crew.crew import SixRStrategyCrew

# Import factory functions for advanced usage
from app.services.crewai_flows.crews.sixr_strategy_crew.agents import (
    create_sixr_strategy_agents,
)
from app.services.crewai_flows.crews.sixr_strategy_crew.tasks import (
    create_sixr_strategy_crew_instance,
    create_sixr_strategy_tasks,
)

# Import tool classes for custom tool development
from app.services.crewai_flows.crews.sixr_strategy_crew.tools import (
    BusinessValueCalculator,
    CompatibilityChecker,
    ComponentAnalyzer,
    DependencyOptimizer,
    IntegrationAnalyzer,
    MoveGroupAnalyzer,
    SixRDecisionEngine,
)

# Export all public APIs for backward compatibility
__all__ = [
    # Main crew class (primary export)
    "SixRStrategyCrew",
    # Factory functions (advanced usage)
    "create_sixr_strategy_agents",
    "create_sixr_strategy_tasks",
    "create_sixr_strategy_crew_instance",
    # Tool classes (custom tool development)
    "SixRDecisionEngine",
    "ComponentAnalyzer",
    "BusinessValueCalculator",
    "CompatibilityChecker",
    "IntegrationAnalyzer",
    "MoveGroupAnalyzer",
    "DependencyOptimizer",
]
