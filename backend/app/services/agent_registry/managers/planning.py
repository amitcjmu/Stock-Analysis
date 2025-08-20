"""
Planning Agent Manager

Manager for Planning phase agents.
"""

import logging

from .base import BasePhaseAgentManager
from ..base import AgentPhase, AgentRegistration, AgentStatus
from ..registry_core import AgentRegistryCore

logger = logging.getLogger(__name__)


class PlanningAgentManager(BasePhaseAgentManager):
    """Manager for Planning phase agents"""

    def __init__(self, registry_core: AgentRegistryCore):
        super().__init__(registry_core, AgentPhase.PLANNING)

    def register_phase_agents(self) -> None:
        """Register Planning phase agents"""

        # Migration Planning Specialist Agent
        self.registry_core.register_agent(
            AgentRegistration(
                agent_id="migration_planner_001",
                name="Migration Planning Specialist Agent",
                role="Migration Planning Specialist",
                phase=AgentPhase.PLANNING,
                status=AgentStatus.ACTIVE,
                expertise="Detailed migration planning and timeline creation",
                specialization="Wave planning, dependency mapping, timeline optimization",
                key_skills=[
                    "Wave planning",
                    "Dependency analysis",
                    "Timeline optimization",
                    "Resource planning",
                    "Risk-aware scheduling",
                ],
                capabilities=[
                    "Automated wave generation",
                    "Critical path analysis",
                    "Resource allocation optimization",
                    "Timeline validation",
                ],
                api_endpoints=[
                    "/api/v1/planning/waves",
                    "/api/v1/planning/timeline",
                ],
                description="Expert migration planner with advanced timeline and wave optimization.",
            )
        )
