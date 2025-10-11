"""
Tech Debt Analysis Crew - Public API

This module provides the public API for the Tech Debt Analysis Crew package.
It maintains backward compatibility by exporting the TechDebtAnalysisCrew class
and factory function that were previously available from tech_debt_analysis_crew.py.

MIGRATION: This modularization preserves all existing functionality while
splitting the 760-line file into maintainable modules:

OLD STRUCTURE (single file - 760 lines):
----------------------------------------
backend/app/services/crewai_flows/crews/tech_debt_analysis_crew.py
    - Imports and models (lines 1-33)
    - LegacySystemAnalysisTool class (lines 35-205)
    - SixRStrategyTool class (lines 207-444)
    - TechDebtAnalysisCrew class (lines 446-747)
    - Factory function and exports (lines 749-760)

NEW STRUCTURE (modularized - <400 lines each):
----------------------------------------------
backend/app/services/crewai_flows/crews/tech_debt_analysis_crew/
    - tools.py (~440 lines) - LegacySystemAnalysisTool and SixRStrategyTool
    - agents.py (~120 lines) - Agent creation logic
    - tasks.py (~65 lines) - Crew creation factory
    - crew.py (~330 lines) - Main TechDebtAnalysisCrew class
    - __init__.py (~95 lines) - Public API exports

BACKWARD COMPATIBILITY:
-----------------------
All existing imports continue to work without changes:
    ✅ from app.services.crewai_flows.crews.tech_debt_analysis_crew import TechDebtAnalysisCrew
    ✅ from app.services.crewai_flows.crews.tech_debt_analysis_crew import create_tech_debt_analysis_crew
    ✅ from app.services.crewai_flows.crews import tech_debt_analysis_crew

No code changes required in consuming modules!

Usage:
    from app.services.crewai_flows.crews.tech_debt_analysis_crew import (
        TechDebtAnalysisCrew,           # Main crew class (recommended)
        create_tech_debt_analysis_crew, # Factory function (recommended)
        TechDebtAnalysisResult,         # Result model

        # Optional: Advanced usage
        create_tech_debt_analysis_agents,
        create_tech_debt_analysis_crew_instance,

        # Optional: Tool classes (for custom tool development)
        LegacySystemAnalysisTool,
        SixRStrategyTool,
    )

References:
- docs/analysis/Notes/coding-agent-guide.md
- CLAUDE.md (Modularization Patterns section)
"""

# Import main crew class and factory from crew module
from app.services.crewai_flows.crews.tech_debt_analysis_crew.crew import (
    TechDebtAnalysisCrew,
    TechDebtAnalysisResult,
    create_tech_debt_analysis_crew,
)

# Import factory functions for advanced usage
from app.services.crewai_flows.crews.tech_debt_analysis_crew.agents import (
    create_tech_debt_analysis_agents,
)
from app.services.crewai_flows.crews.tech_debt_analysis_crew.tasks import (
    create_tech_debt_analysis_crew_instance,
)

# Import tool classes for custom tool development
from app.services.crewai_flows.crews.tech_debt_analysis_crew.tools import (
    LegacySystemAnalysisTool,
    SixRStrategyTool,
)

# Export all public APIs for backward compatibility
__all__ = [
    # Main crew class (primary export)
    "TechDebtAnalysisCrew",
    # Factory function (primary export)
    "create_tech_debt_analysis_crew",
    # Result model (commonly used)
    "TechDebtAnalysisResult",
    # Factory functions (advanced usage)
    "create_tech_debt_analysis_agents",
    "create_tech_debt_analysis_crew_instance",
    # Tool classes (custom tool development)
    "LegacySystemAnalysisTool",
    "SixRStrategyTool",
]
