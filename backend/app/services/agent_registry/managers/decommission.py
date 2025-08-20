"""
Decommission Agent Manager

Manager for Decommission phase agents.
"""

import logging

from .base import BasePhaseAgentManager
from ..base import AgentPhase, AgentRegistration, AgentStatus
from ..registry_core import AgentRegistryCore

logger = logging.getLogger(__name__)


class DecommissionAgentManager(BasePhaseAgentManager):
    """Manager for Decommission phase agents"""

    def __init__(self, registry_core: AgentRegistryCore):
        super().__init__(registry_core, AgentPhase.DECOMMISSION)

    def register_phase_agents(self) -> None:
        """Register Decommission phase agents"""

        # Decommission Specialist Agent
        self.registry_core.register_agent(
            AgentRegistration(
                agent_id="decommission_specialist_001",
                name="Decommission Specialist Agent",
                role="Decommission Specialist",
                phase=AgentPhase.DECOMMISSION,
                status=AgentStatus.ACTIVE,
                expertise="Safe and compliant decommissioning of legacy systems",
                specialization="Data backup, security compliance, clean shutdown procedures",
                key_skills=[
                    "Data backup and archival",
                    "Security compliance",
                    "Clean shutdown procedures",
                    "Audit trail maintenance",
                    "Regulatory compliance",
                ],
                capabilities=[
                    "Automated backup procedures",
                    "Compliance validation",
                    "Audit trail generation",
                    "Safe shutdown orchestration",
                ],
                api_endpoints=[
                    "/api/v1/decommission/backup",
                    "/api/v1/decommission/shutdown",
                ],
                description="Expert decommission specialist ensuring safe and compliant system retirement.",
            )
        )
