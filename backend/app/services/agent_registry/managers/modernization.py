"""
Modernization Agent Manager

Manager for Modernization phase agents.
"""

import logging

from .base import BasePhaseAgentManager
from ..base import AgentPhase, AgentRegistration, AgentStatus
from ..registry_core import AgentRegistryCore

logger = logging.getLogger(__name__)


class ModernizationAgentManager(BasePhaseAgentManager):
    """Manager for Modernization phase agents"""

    def __init__(self, registry_core: AgentRegistryCore):
        super().__init__(registry_core, AgentPhase.MODERNIZATION)

    def register_phase_agents(self) -> None:
        """Register Modernization phase agents"""

        # Modernization Specialist Agent
        self.registry_core.register_agent(
            AgentRegistration(
                agent_id="modernization_specialist_001",
                name="Modernization Specialist Agent",
                role="Modernization Specialist",
                phase=AgentPhase.MODERNIZATION,
                status=AgentStatus.ACTIVE,
                expertise="Application modernization and cloud-native transformation",
                specialization="Containerization, microservices, serverless, cloud-native patterns",
                key_skills=[
                    "Containerization",
                    "Microservices architecture",
                    "Serverless patterns",
                    "Cloud-native design",
                    "API modernization",
                ],
                capabilities=[
                    "Automated containerization",
                    "Microservices decomposition",
                    "Serverless migration",
                    "API gateway setup",
                ],
                api_endpoints=[
                    "/api/v1/modernization/containerize",
                    "/api/v1/modernization/microservices",
                ],
                description="Expert modernization specialist for cloud-native transformation.",
            )
        )
