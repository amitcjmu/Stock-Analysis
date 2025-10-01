"""
CrewAI Factory Pattern - Public API

This module maintains backward compatibility by exporting all public APIs
that were previously available from crew_factory.py.

MIGRATION: This file ensures that existing imports continue to work:
    OLD: from app.services.crewai_flows.config.crew_factory import create_agent
    NEW: from app.services.crewai_flows.config.crew_factory import create_agent
    (same import path, modularized internals)

Usage:
    from app.services.crewai_flows.config.crew_factory import (
        # Convenience functions (recommended)
        create_agent,
        create_crew,
        create_task,

        # Classes (for advanced usage)
        CrewFactory,
        CrewConfig,
        CrewMemoryManager,

        # Default factory instance
        default_factory,
    )

References:
- docs/code-reviews/2025-10-01_discovery_flow_over_abstraction_review.md
- ADR-019: DeepInfra Embeddings
"""

# Import from modularized structure
from app.services.crewai_flows.config.crew_factory.config import CrewConfig
from app.services.crewai_flows.config.crew_factory.factory import (
    CrewFactory,
    CrewMemoryManager,
    default_factory,
)

# Convenience functions using default factory
from app.services.crewai_flows.config.crew_factory.factory import (
    default_factory as _default_factory,
)


def create_agent(*args, **kwargs):
    """
    Convenience function for creating agents with default factory.

    Usage:
        from app.services.crewai_flows.config.crew_factory import create_agent

        agent = create_agent(
            role="Data Analyst",
            goal="Analyze data patterns",
            backstory="Expert in data analysis",
            llm=my_llm,
        )

    Returns:
        Configured Agent instance with factory defaults applied
    """
    return _default_factory.create_agent(*args, **kwargs)


def create_crew(*args, **kwargs):
    """
    Convenience function for creating crews with default factory.

    Usage:
        from app.services.crewai_flows.config.crew_factory import create_crew

        crew = create_crew(
            agents=[agent1, agent2],
            tasks=[task1, task2],
            process=Process.sequential,
        )

    Returns:
        Configured Crew instance with factory defaults applied
    """
    return _default_factory.create_crew(*args, **kwargs)


def create_task(*args, **kwargs):
    """
    Convenience function for creating tasks.

    Usage:
        from app.services.crewai_flows.config.crew_factory import create_task

        task = create_task(
            description="Analyze the data",
            agent=analyst_agent,
            expected_output="Detailed analysis report",
        )

    Returns:
        Configured Task instance
    """
    return _default_factory.create_task(*args, **kwargs)


# Export all public APIs for backward compatibility
__all__ = [
    # Configuration classes
    "CrewConfig",
    "CrewFactory",
    "CrewMemoryManager",
    # Convenience functions
    "create_agent",
    "create_crew",
    "create_task",
    # Default factory instance
    "default_factory",
]


# Migration guide for reference
__doc__ += """

MIGRATION GUIDE: Modularized Structure
========================================

The crew_factory.py file has been split into a modular structure:

crew_factory/
├── __init__.py     - This file: Public API exports (backward compatible)
├── config.py       - CrewConfig class and configuration constants
├── factory.py      - CrewFactory, CrewMemoryManager, and default_factory

OLD STRUCTURE (single file - 576 lines):
-----------------------------------------
backend/app/services/crewai_flows/config/crew_factory.py
    - CrewConfig (lines 1-157)
    - CrewFactory (lines 159-371)
    - CrewMemoryManager (lines 373-425)
    - Convenience functions (lines 427-481)
    - Documentation (lines 483-577)

NEW STRUCTURE (modularized - <400 lines each):
----------------------------------------------
backend/app/services/crewai_flows/config/crew_factory/
    - config.py (~160 lines)
    - factory.py (~310 lines)
    - __init__.py (~140 lines)

BACKWARD COMPATIBILITY:
-----------------------
All existing imports continue to work without changes:
    ✅ from app.services.crewai_flows.config.crew_factory import create_agent
    ✅ from app.services.crewai_flows.config.crew_factory import CrewFactory
    ✅ from app.services.crewai_flows.config.crew_factory import CrewConfig
    ✅ from app.services.crewai_flows.config.crew_factory import default_factory

No code changes required in consuming modules!
"""
