"""
Observability Agent Manager

Manager for Observability agents.
"""

import logging

from .base import BasePhaseAgentManager
from ..base import AgentPhase, AgentRegistration, AgentStatus
from ..registry_core import AgentRegistryCore

logger = logging.getLogger(__name__)


class ObservabilityAgentManager(BasePhaseAgentManager):
    """Manager for Observability agents"""

    def __init__(self, registry_core: AgentRegistryCore):
        super().__init__(
            registry_core, AgentPhase.MIGRATION
        )  # Observability agents support migration

    def register_phase_agents(self) -> None:
        """Register Observability agents"""

        # Agent Health Monitor
        self.registry_core.register_agent(
            AgentRegistration(
                agent_id="agent_health_monitor_001",
                name="Agent Health Monitor",
                role="System Health Specialist",
                phase=AgentPhase.MIGRATION,
                status=AgentStatus.ACTIVE,
                expertise="Real-time agent performance monitoring and health assessment",
                specialization="Performance metrics, health diagnostics, system optimization",
                key_skills=[
                    "Performance monitoring",
                    "Health diagnostics",
                    "System optimization",
                    "Alert management",
                    "Capacity planning",
                ],
                capabilities=[
                    "Real-time performance tracking",
                    "Automated health assessments",
                    "Predictive failure detection",
                    "Performance optimization recommendations",
                ],
                api_endpoints=[
                    "/api/v1/observability/health",
                    "/api/v1/observability/performance",
                ],
                description="Comprehensive agent health monitoring with predictive analytics.",
            )
        )
