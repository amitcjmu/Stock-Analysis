"""
CrewAI Configuration Module

Provides centralized configuration for CrewAI agents and crews.
This replaces global monkey patches with explicit, testable configuration.

References:
- docs/code-reviews/2025-10-01_discovery_flow_over_abstraction_review.md
- ADR-019: DeepInfra Embeddings (separate concern)
"""

import logging
import os
from typing import Any, Dict, Optional

try:
    from crewai import Process  # type: ignore[import-not-found]

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False

    # Create a mock Process enum for type hints
    class Process:  # type: ignore[no-redef]
        sequential = "sequential"
        hierarchical = "hierarchical"


logger = logging.getLogger(__name__)


class CrewConfig:
    """
    Centralized configuration for CrewAI agents and crews.

    This class encapsulates default settings that were previously
    applied via global monkey patches.
    """

    # Default agent settings
    DEFAULT_AGENT_CONFIG = {
        "allow_delegation": False,
        "max_delegation": 0,
        "max_iter": 1,
        "verbose": False,
    }

    # Default crew settings
    DEFAULT_CREW_CONFIG = {
        "max_iterations": 1,
        "verbose": False,
        "max_execution_time": None,  # Will be set from env or param
    }

    @staticmethod
    def get_default_timeout() -> int:
        """
        Get default timeout for crew execution from environment.

        Returns:
            Timeout in seconds (default: 600 = 10 minutes)
        """
        return int(os.getenv("CREWAI_TIMEOUT_SECONDS", "600"))

    @staticmethod
    def get_agent_defaults(
        allow_delegation: Optional[bool] = None,
        max_iter: Optional[int] = None,
        verbose: Optional[bool] = None,
        memory: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Get default agent configuration with optional overrides.

        Args:
            allow_delegation: Override default delegation setting
            max_iter: Override default max iterations
            verbose: Override default verbose setting
            memory: Override default memory setting

        Returns:
            Configuration dictionary for Agent constructor
        """
        config = CrewConfig.DEFAULT_AGENT_CONFIG.copy()

        if allow_delegation is not None:
            config["allow_delegation"] = allow_delegation
            config["max_delegation"] = 1 if allow_delegation else 0

        if max_iter is not None:
            config["max_iter"] = max_iter

        if verbose is not None:
            config["verbose"] = verbose

        # Memory is enabled by default, but can be disabled per agent
        if memory is not None:
            config["memory"] = memory

        return config

    @staticmethod
    def get_crew_defaults(
        max_execution_time: Optional[int] = None,
        max_iterations: Optional[int] = None,
        verbose: Optional[bool] = None,
        memory: Optional[bool] = None,
        process: Optional[Process] = None,
    ) -> Dict[str, Any]:
        """
        Get default crew configuration with optional overrides.

        Args:
            max_execution_time: Timeout in seconds (default: from env)
            max_iterations: Override default max iterations
            verbose: Override default verbose setting
            memory: Override default memory setting
            process: Crew process type (sequential/hierarchical)

        Returns:
            Configuration dictionary for Crew constructor
        """
        config = CrewConfig.DEFAULT_CREW_CONFIG.copy()

        # Set timeout from parameter or environment
        if max_execution_time is not None:
            config["max_execution_time"] = max_execution_time
        else:
            config["max_execution_time"] = CrewConfig.get_default_timeout()

        if max_iterations is not None:
            config["max_iterations"] = max_iterations

        if verbose is not None:
            config["verbose"] = verbose

        if process is not None:
            config["process"] = process

        # Memory configuration (embedder will be set separately)
        if memory is not None:
            config["memory"] = memory
        else:
            # Memory is enabled by default
            config["memory"] = True

        return config
