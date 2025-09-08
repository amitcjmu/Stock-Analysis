"""
CrewAI Crews Package - Performance Optimized

This package enforces global performance optimizations:
- NO delegation between agents
- Single pass execution (no iterations)
- 10 minute timeout for complex analysis workflows (configurable via CREWAI_TIMEOUT_SECONDS)
"""

import logging
import os

logger = logging.getLogger(__name__)

# Monkey patch CrewAI to enforce performance settings
try:
    from crewai import Agent, Crew

    # Store original constructors
    _original_agent_init = Agent.__init__
    _original_crew_init = Crew.__init__

    def optimized_agent_init(self, *args, **kwargs):
        """Force all agents to have no delegation"""
        # Override delegation settings
        kwargs["allow_delegation"] = False
        kwargs["max_delegation"] = 0
        kwargs["max_iter"] = 1
        kwargs["verbose"] = kwargs.get("verbose", False)

        # Call original constructor
        _original_agent_init(self, *args, **kwargs)

    def optimized_crew_init(self, *args, **kwargs):
        """Force all crews to have single iteration and configurable timeout"""
        # Override crew settings
        kwargs["max_iterations"] = 1
        kwargs["verbose"] = kwargs.get("verbose", False)
        # MEMORY RE-ENABLED: Remove global memory disable
        # kwargs['memory'] = False  # REMOVED - Memory system is working correctly
        kwargs["embedder"] = None  # No embedding overhead

        # Set timeout if not specified - Allow longer timeouts for complex analysis
        if "max_execution_time" not in kwargs:
            # Default to 10 minutes, but allow override via environment variable
            # For specific long-running agents, set max_execution_time explicitly when creating the crew
            default_timeout = int(os.getenv("CREWAI_TIMEOUT_SECONDS", "600"))
            kwargs["max_execution_time"] = default_timeout

        # Call original constructor
        _original_crew_init(self, *args, **kwargs)

    # Apply monkey patches
    Agent.__init__ = optimized_agent_init
    Crew.__init__ = optimized_crew_init

    # Log the actual configured timeout
    default_timeout = int(os.getenv("CREWAI_TIMEOUT_SECONDS", "600"))
    timeout_minutes = default_timeout // 60

    logger.info("✅ CrewAI performance optimizations applied globally")
    logger.info("   - No delegation allowed")
    logger.info("   - Single pass execution")
    logger.info(
        f"   - {timeout_minutes} minute timeout for complex analysis (CREWAI_TIMEOUT_SECONDS={default_timeout})"
    )
    logger.info("   - Memory system RE-ENABLED (global disable removed)")

except ImportError:
    logger.warning("CrewAI not available - performance optimizations not applied")
except Exception as e:
    logger.error(f"Failed to apply CrewAI optimizations: {e}")
