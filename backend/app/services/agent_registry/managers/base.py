"""
Base Phase Agent Manager

Base class for phase-specific agent managers.
"""

import logging
from typing import List

from ..base import AgentPhase, AgentRegistration
from ..registry_core import AgentRegistryCore

logger = logging.getLogger(__name__)


class BasePhaseAgentManager:
    """Base class for phase-specific agent managers"""

    def __init__(self, registry_core: AgentRegistryCore, phase: AgentPhase):
        self.registry_core = registry_core
        self.phase = phase

    def register_phase_agents(self) -> None:
        """Register all agents for this phase - to be implemented by subclasses"""
        pass

    def get_phase_agents(self) -> List[AgentRegistration]:
        """Get all agents for this phase"""
        return self.registry_core.get_agents_by_phase(self.phase)
