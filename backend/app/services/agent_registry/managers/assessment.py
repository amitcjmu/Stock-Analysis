"""
Assessment Agent Manager

Manager for Assessment phase agents.
"""

import logging

from .base import BasePhaseAgentManager
from ..base import AgentPhase, AgentRegistration, AgentStatus
from ..registry_core import AgentRegistryCore

logger = logging.getLogger(__name__)


class AssessmentAgentManager(BasePhaseAgentManager):
    """Manager for Assessment phase agents"""

    def __init__(self, registry_core: AgentRegistryCore):
        super().__init__(registry_core, AgentPhase.ASSESSMENT)

    def register_phase_agents(self) -> None:
        """Register Assessment phase agents"""

        # Migration Strategy Expert Agent
        self.registry_core.register_agent(
            AgentRegistration(
                agent_id="migration_strategist_001",
                name="Migration Strategy Expert Agent",
                role="Migration Strategy Expert",
                phase=AgentPhase.ASSESSMENT,
                status=AgentStatus.ACTIVE,
                expertise="6R strategy analysis and migration planning",
                specialization="Rehost, Replatform, Refactor, Rearchitect, Retire, Retain analysis",
                key_skills=[
                    "Strategy recommendation",
                    "Complexity assessment",
                    "Migration planning",
                    "6R framework expertise",
                    "Business value analysis",
                ],
                capabilities=[
                    "Comprehensive 6R analysis",
                    "Strategy recommendation engine",
                    "Risk-aware planning",
                    "Business impact assessment",
                ],
                api_endpoints=[
                    "/api/v1/assessment/6r-analysis",
                    "/api/v1/assessment/strategy-recommendation",
                ],
                description="Expert 6R strategist with comprehensive migration planning capabilities.",
            )
        )

        # Risk Assessment Specialist Agent
        self.registry_core.register_agent(
            AgentRegistration(
                agent_id="risk_assessor_001",
                name="Risk Assessment Specialist Agent",
                role="Risk Assessment Specialist",
                phase=AgentPhase.ASSESSMENT,
                status=AgentStatus.ACTIVE,
                expertise="Migration risk analysis and mitigation planning",
                specialization="Technical, business, security, and operational risk assessment",
                key_skills=[
                    "Risk identification",
                    "Impact analysis",
                    "Mitigation strategies",
                    "Security assessment",
                    "Operational risk evaluation",
                ],
                capabilities=[
                    "Multi-dimensional risk analysis",
                    "Automated risk scoring",
                    "Mitigation recommendation",
                    "Risk trend analysis",
                ],
                api_endpoints=[
                    "/api/v1/assessment/risk-analysis",
                    "/api/v1/assessment/risk-mitigation",
                ],
                description="Comprehensive risk assessment specialist for migration planning.",
            )
        )
