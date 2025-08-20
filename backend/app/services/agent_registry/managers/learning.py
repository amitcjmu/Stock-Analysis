"""
Learning Context Agent Manager

Manager for Learning Context agents.
"""

import logging

from .base import BasePhaseAgentManager
from ..base import AgentPhase, AgentRegistration, AgentStatus
from ..registry_core import AgentRegistryCore

logger = logging.getLogger(__name__)


class LearningContextAgentManager(BasePhaseAgentManager):
    """Manager for Learning Context agents"""

    def __init__(self, registry_core: AgentRegistryCore):
        super().__init__(
            registry_core, AgentPhase.ASSESSMENT
        )  # Learning agents support assessment

    def register_phase_agents(self) -> None:
        """Register Learning Context agents"""

        # Asset Intelligence Agent
        self.registry_core.register_agent(
            AgentRegistration(
                agent_id="asset_intelligence_001",
                name="Asset Intelligence Agent",
                role="Asset Intelligence Specialist",
                phase=AgentPhase.ASSESSMENT,
                status=AgentStatus.ACTIVE,
                expertise="AI-powered asset analysis and intelligent classification",
                specialization="Machine learning asset patterns, intelligent bulk operations",
                key_skills=[
                    "AI-powered asset analysis",
                    "Intelligent pattern recognition",
                    "Machine learning classification",
                    "Bulk operations optimization",
                    "Asset lifecycle management",
                    "Relationship mapping",
                    "Quality assessment",
                ],
                capabilities=[
                    "AI-powered pattern recognition (not hard-coded heuristics)",
                    "Integration with discovery endpoints for seamless experience",
                    "Real-time asset intelligence monitoring and updates",
                    "Quality assessment with actionable recommendations",
                    "Continuous learning from user interactions and feedback",
                ],
                api_endpoints=[
                    "/api/v1/flows/assets/analyze",
                    "/api/v1/flows/assets/auto-classify",
                    "/api/v1/flows/assets/intelligence-status",
                    "/api/v1/inventory/analyze",
                ],
                description=(
                    "Revolutionary asset intelligence with AI-powered classification, bulk operations "
                    "optimization, and continuous learning capabilities."
                ),
                learning_enabled=True,
            )
        )
