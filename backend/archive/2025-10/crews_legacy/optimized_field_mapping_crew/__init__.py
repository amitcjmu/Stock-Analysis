"""
Optimized Field Mapping Crew - Public API

This module provides the public API for the Optimized Field Mapping Crew package.
It maintains backward compatibility by exporting the OptimizedFieldMappingCrew class
that was previously available from optimized_field_mapping_crew.py.

MIGRATION: This modularization preserves all existing functionality while
splitting the 537-line file into maintainable modules:

OLD STRUCTURE (single file - 537 lines):
----------------------------------------
backend/app/services/crewai_flows/crews/optimized_field_mapping_crew.py
    - Imports and configuration (lines 1-61)
    - OptimizedFieldMappingCrew class (lines 32-537)
        - __init__ method (lines 35-61)
        - create_memory_enhanced_agents method (lines 62-135)
        - create_memory_enhanced_tasks method (lines 137-229)
        - execute_enhanced_mapping method (lines 231-264)
        - _process_mapping_result method (lines 266-321)
        - _calculate_confidence_distribution method (lines 323-338)
        - _learn_from_mappings method (lines 340-392)
        - _store_execution_memory method (lines 393-429)
        - _calculate_avg_confidence method (lines 430-436)
        - get_mapping_intelligence_report method (lines 438-487)
        - _generate_intelligence_recommendations method (lines 489-534)

NEW STRUCTURE (modularized - <400 lines each):
----------------------------------------------
backend/app/services/crewai_flows/crews/optimized_field_mapping_crew/
    - memory_helpers.py (~290 lines) - Memory integration and intelligence
    - agents.py (~105 lines) - Agent creation with memory enhancement
    - tasks.py (~135 lines) - Task creation with learned patterns
    - execution.py (~185 lines) - Execution orchestration and result processing
    - crew.py (~235 lines) - Main OptimizedFieldMappingCrew class
    - __init__.py (~125 lines) - Public API exports

BACKWARD COMPATIBILITY:
-----------------------
All existing imports continue to work without changes:
    from app.services.crewai_flows.crews.optimized_field_mapping_crew import OptimizedFieldMappingCrew
    from app.services.crewai_flows.crews import optimized_field_mapping_crew

No code changes required in consuming modules!

Usage:
    from app.services.crewai_flows.crews.optimized_field_mapping_crew import (
        OptimizedFieldMappingCrew,  # Main crew class (recommended)

        # Optional: Advanced usage
        create_memory_enhanced_agents,
        create_memory_enhanced_tasks,
        execute_enhanced_mapping,

        # Optional: Memory and intelligence helpers
        get_past_mapping_experiences,
        get_similar_data_structures,
        learn_from_mappings,
        get_mapping_intelligence_report,
    )

References:
- docs/analysis/Notes/coding-agent-guide.md
- CLAUDE.md (Modularization Patterns section)
- backend/app/services/crewai_flows/crews/component_analysis_crew/__init__.py
"""

# Import main crew class from crew module
from .crew import OptimizedFieldMappingCrew

# Import factory functions for advanced usage
from .agents import create_memory_enhanced_agents, get_standard_fields
from .execution import (
    execute_enhanced_mapping,
    extract_mapping_metrics,
    parse_json_result,
    process_mapping_result,
    validate_mapping_result,
)
from .tasks import create_memory_enhanced_tasks, create_task_description

# Import memory and intelligence helpers
from .memory_helpers import (
    calculate_avg_confidence,
    calculate_confidence_distribution,
    generate_intelligence_recommendations,
    get_mapping_intelligence_report,
    get_past_mapping_experiences,
    get_similar_data_structures,
    learn_from_mappings,
    store_execution_memory,
)

# Export all public APIs for backward compatibility
__all__ = [
    # Main crew class (primary export)
    "OptimizedFieldMappingCrew",
    # Agent creation functions
    "create_memory_enhanced_agents",
    "get_standard_fields",
    # Task creation functions
    "create_memory_enhanced_tasks",
    "create_task_description",
    # Execution functions
    "execute_enhanced_mapping",
    "process_mapping_result",
    "parse_json_result",
    "validate_mapping_result",
    "extract_mapping_metrics",
    # Memory and intelligence helpers
    "get_past_mapping_experiences",
    "get_similar_data_structures",
    "learn_from_mappings",
    "store_execution_memory",
    "calculate_avg_confidence",
    "calculate_confidence_distribution",
    "get_mapping_intelligence_report",
    "generate_intelligence_recommendations",
]
