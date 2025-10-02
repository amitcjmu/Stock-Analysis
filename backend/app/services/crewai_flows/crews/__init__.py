"""
CrewAI Crews Package

This package provides crew implementations for various workflows.

IMPORTANT: Global monkey patches have been REMOVED as of 2025-10-01.
Use the explicit factory pattern instead:

    from app.services.crewai_flows.config.crew_factory import create_agent, create_crew

    agent = create_agent(
        role="Analyst",
        goal="Analyze data",
        backstory="Expert analyst",
        # Explicit defaults: allow_delegation=False, max_iter=1, memory=True
    )

    crew = create_crew(
        agents=[agent],
        tasks=[task],
        # Explicit defaults: max_iterations=1, timeout=600s, memory=True
    )

See crew_factory.py for full migration guide and usage examples.

Configuration via environment variables:
- CREWAI_TIMEOUT_SECONDS: Default crew execution timeout (default: 600)
- CREWAI_DISABLE_MEMORY: Disable memory globally (default: false)
- CREWAI_VERBOSE: Enable verbose logging (default: false)
- DEEPINFRA_API_KEY: Required for memory/embeddings support

References:
- docs/code-reviews/2025-10-01_discovery_flow_over_abstraction_review.md
- ADR-019: CrewAI DeepInfra Embeddings (separate embedder adapter, still active)
"""

import logging

logger = logging.getLogger(__name__)

# NO MORE MONKEY PATCHES
# Use explicit factory pattern from app.services.crewai_flows.config.crew_factory

try:
    import crewai  # noqa: F401 - Import check only

    logger.info("✅ CrewAI available - use factory pattern for configuration")
    logger.info(
        "   Import: from app.services.crewai_flows.config.crew_factory import create_agent, create_crew"
    )
    logger.info("   See crew_factory.py for migration guide")

except ImportError:
    logger.warning("CrewAI not available")
except Exception as e:
    logger.error(f"Error importing CrewAI: {e}")
