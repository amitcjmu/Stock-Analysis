"""
FinOps Agent Manager

Manager for FinOps phase agents.
"""

import logging

from .base import BasePhaseAgentManager
from ..base import AgentPhase, AgentRegistration, AgentStatus
from ..registry_core import AgentRegistryCore

logger = logging.getLogger(__name__)


class FinOpsAgentManager(BasePhaseAgentManager):
    """Manager for FinOps phase agents"""

    def __init__(self, registry_core: AgentRegistryCore):
        super().__init__(registry_core, AgentPhase.FINOPS)

    def register_phase_agents(self) -> None:
        """Register FinOps phase agents"""

        # FinOps Optimization Specialist Agent
        self.registry_core.register_agent(
            AgentRegistration(
                agent_id="finops_optimizer_001",
                name="FinOps Optimization Specialist Agent",
                role="FinOps Optimization Specialist",
                phase=AgentPhase.FINOPS,
                status=AgentStatus.ACTIVE,
                expertise="Cloud cost optimization and financial operations",
                specialization="Cost analysis, optimization recommendations, budget management",
                key_skills=[
                    "Cost analysis",
                    "Budget optimization",
                    "Resource rightsizing",
                    "Reserved instance planning",
                    "Cost forecasting",
                ],
                capabilities=[
                    "Automated cost analysis",
                    "Optimization recommendations",
                    "Budget tracking",
                    "Cost forecasting",
                ],
                api_endpoints=[
                    "/api/v1/finops/analyze",
                    "/api/v1/finops/optimize",
                ],
                description="Expert FinOps specialist for cloud cost optimization and financial management.",
            )
        )
