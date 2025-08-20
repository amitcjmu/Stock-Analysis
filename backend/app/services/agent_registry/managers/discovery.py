"""
Discovery Agent Manager

Manager for Discovery phase agents.
"""

import logging

from .base import BasePhaseAgentManager
from ..base import AgentPhase
from ..registry_core import AgentRegistryCore

logger = logging.getLogger(__name__)


class DiscoveryAgentManager(BasePhaseAgentManager):
    """Manager for Discovery phase agents"""

    def __init__(self, registry_core: AgentRegistryCore):
        super().__init__(registry_core, AgentPhase.DISCOVERY)

    def register_phase_agents(self) -> None:
        """Register Discovery phase agents - disabled per Discovery Flow Redesign"""
        # 🚨 DISCOVERY FLOW REDESIGN: Disable old agent registry
        # The Discovery Flow Redesign (Tasks 1.1-2.2 completed) uses individual specialized agents
        # instead of the old registry system with 17 competing agents

        logger.info(
            "🔄 Discovery Flow Redesign: Using individual specialized agents instead of registry"
        )
        logger.info(
            "📋 Active individual agents: DataImportValidationAgent, AttributeMappingAgent, DataCleansingAgent, etc."
        )
