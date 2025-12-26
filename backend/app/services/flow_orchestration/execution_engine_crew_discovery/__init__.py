"""
Discovery Flow Execution Engine - Modularized Version.

This module preserves backward compatibility by exposing all public classes
and functions from the original execution_engine_crew_discovery.py file.

Main entry point for discovery-specific CrewAI execution methods and phase handlers.
"""

# Import all base classes and mixins
from .base import DictStateAdapter, ExecutionEngineDiscoveryCrewsBase
from .database_queries import DatabaseQueryMixin
from .data_normalization import DataNormalizationMixin
from .persistent_agents import PersistentAgentsMixin
from .phase_executors import PhaseExecutorsMixin
from .phase_orchestration import PhaseOrchestrationMixin

# Import external dependencies that were imported in original file
# REMOVED: Field mapping logic - field mapping functionality was removed
# from ..field_mapping_logic import FieldMappingLogic
from ..discovery_phase_handlers import DiscoveryPhaseHandlers
from ..asset_creation_tools import AssetCreationToolsExecutor


class ExecutionEngineDiscoveryCrews(
    ExecutionEngineDiscoveryCrewsBase,
    DatabaseQueryMixin,
    DataNormalizationMixin,
    PersistentAgentsMixin,
    PhaseExecutorsMixin,
    PhaseOrchestrationMixin,
):
    """
    Discovery flow CrewAI execution handlers.

    This class combines all functionality from the original file using multiple inheritance
    to maintain the exact same public API while organizing code into logical modules.
    """

    def __init__(self, crew_utils, context=None, db_session=None):
        """Initialize the discovery crews execution engine."""
        # Call the base class initializer
        super().__init__(crew_utils, context, db_session)


# Export all public classes and functions to maintain backward compatibility
__all__ = [
    "DictStateAdapter",
    "ExecutionEngineDiscoveryCrews",
    "ExecutionEngineDiscoveryCrewsBase",
    "DatabaseQueryMixin",
    "DataNormalizationMixin",
    "PersistentAgentsMixin",
    "PhaseExecutorsMixin",
    "PhaseOrchestrationMixin",
    # "FieldMappingLogic",  # REMOVED
    "DiscoveryPhaseHandlers",
    "AssetCreationToolsExecutor",
]
