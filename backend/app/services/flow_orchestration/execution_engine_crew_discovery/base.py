"""
Core base classes for Discovery Flow Execution Engine.
Contains DictStateAdapter and ExecutionEngineDiscoveryCrews base functionality.
"""

from typing import Any, Dict, List

from app.core.logging import get_logger

logger = get_logger(__name__)


class DictStateAdapter:
    """Adapter to make a dict work as a state object for UnifiedFlowCrewManager."""

    def __init__(self, data: Dict[str, Any]):
        """Initialize adapter with dict data as attributes."""
        self._errors: List[Dict[str, str]] = []
        # Prevent overwriting internal attributes
        for k, v in data.items():
            if k.startswith("_"):
                continue
            setattr(self, k, v)

    def add_error(self, key: str, message: str):
        """Add an error to the state."""
        self._errors.append({"key": key, "message": message})


class ExecutionEngineDiscoveryCrewsBase:
    """Base class for Discovery flow CrewAI execution handlers."""

    def __init__(self, crew_utils, context=None, db_session=None):
        """Initialize the discovery crews execution engine."""
        self.crew_utils = crew_utils
        self.context = context
        self.service_registry = None
        self.db_session = db_session

        # Initialize specialized components
        from ..field_mapping_logic import FieldMappingLogic
        from ..discovery_phase_handlers import DiscoveryPhaseHandlers

        self.field_mapping_logic = FieldMappingLogic()
        self.phase_handlers = DiscoveryPhaseHandlers(context)

    def set_service_registry(self, service_registry):
        """Set the ServiceRegistry for this discovery crews instance."""
        self.service_registry = service_registry
