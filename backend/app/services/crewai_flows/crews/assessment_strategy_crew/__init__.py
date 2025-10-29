"""
Assessment Strategy Crew - Public API

PHASE 6 MIGRATION (October 2025): Migrated from sixr_strategy_crew
This crew provides 6R recommendation logic for Assessment Flow,
replacing the deprecated 6R Analysis functionality.

This module provides the public API for the Assessment Strategy Crew package.
It exports the AssessmentStrategyCrew class (renamed from SixRStrategyCrew)
that works with Assessment model instead of deprecated SixRAnalysis.

MIGRATION HISTORY:
-----------------
1. Original: sixr_strategy_crew (single file - 767 lines)
2. Modularized: sixr_strategy_crew/ (split into 6 files)
3. Phase 6: assessment_strategy_crew/ (migrated to Assessment Flow)

CURRENT STRUCTURE (modularized - <400 lines each):
--------------------------------------------------
backend/app/services/crewai_flows/crews/assessment_strategy_crew/
    - tools.py (~245 lines) - Tool placeholder classes
    - agents.py (~193 lines) - Agent creation logic
    - tasks.py (~378 lines) - Task and crew creation logic
    - fallback.py (~211 lines) - Fallback implementation and result processing
    - crew.py (~247 lines) - Main AssessmentStrategyCrew class
    - __init__.py (~105 lines) - Public API exports

KEY CHANGES FOR ASSESSMENT FLOW:
--------------------------------
- Works with Assessment model (MFO-integrated)
- No dependency on deprecated SixRAnalysis
- Integrates with Assessment Flow state management
- Provides component-level 6R strategy recommendations

Usage:
    from app.services.crewai_flows.crews.assessment_strategy_crew import (
        AssessmentStrategyCrew,  # Main crew class (recommended)

        # Optional: Advanced usage
        create_assessment_strategy_agents,
        create_assessment_strategy_tasks,
        create_assessment_strategy_crew_instance,

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
- Phase 6 Migration Task (Issue #840)
"""

# Import main crew class from crew module
from app.services.crewai_flows.crews.assessment_strategy_crew.crew import (
    AssessmentStrategyCrew,
)

# Import factory functions for advanced usage
from app.services.crewai_flows.crews.assessment_strategy_crew.agents import (
    create_assessment_strategy_agents,
)
from app.services.crewai_flows.crews.assessment_strategy_crew.tasks import (
    create_assessment_strategy_crew_instance,
    create_assessment_strategy_tasks,
)

# Import tool classes for custom tool development
from app.services.crewai_flows.crews.assessment_strategy_crew.tools import (
    BusinessValueCalculator,
    CompatibilityChecker,
    ComponentAnalyzer,
    DependencyOptimizer,
    IntegrationAnalyzer,
    MoveGroupAnalyzer,
    SixRDecisionEngine,
)

# Export all public APIs
__all__ = [
    # Main crew class (primary export)
    "AssessmentStrategyCrew",
    # Factory functions (advanced usage)
    "create_assessment_strategy_agents",
    "create_assessment_strategy_tasks",
    "create_assessment_strategy_crew_instance",
    # Tool classes (custom tool development)
    "SixRDecisionEngine",
    "ComponentAnalyzer",
    "BusinessValueCalculator",
    "CompatibilityChecker",
    "IntegrationAnalyzer",
    "MoveGroupAnalyzer",
    "DependencyOptimizer",
]
