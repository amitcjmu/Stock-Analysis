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

        # Migration Planning Specialist Agent (legacy - kept for backward compatibility)
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

        # Wave Planning Specialist Agent
        self.registry_core.register_agent(
            AgentRegistration(
                agent_id="wave_planning_specialist",
                name="Wave Planning Specialist",
                role="Migration Wave Planning Specialist",
                phase=AgentPhase.PLANNING,
                status=AgentStatus.ACTIVE,
                expertise="Application portfolio wave sequencing based on dependency analysis",
                specialization="Dependency graph analysis, wave optimization, parallel migration identification",
                key_skills=[
                    "Dependency graph analysis",
                    "Critical path identification",
                    "Wave sequencing optimization",
                    "Risk mitigation through wave grouping",
                    "Parallel migration opportunity identification",
                ],
                capabilities=[
                    "Dependency-based wave planning",
                    "Wave size balancing for resource optimization",
                    "Cross-wave dependency minimization",
                    "Business criticality consideration",
                    "Compliance requirement enforcement",
                ],
                api_endpoints=[
                    "/api/v1/planning/waves/analyze",
                ],
                description="Expert in organizing applications into optimal migration waves based on dependencies.",
            )
        )

        # Resource Allocation Specialist Agent
        self.registry_core.register_agent(
            AgentRegistration(
                agent_id="resource_allocation_specialist",
                name="Resource Allocation Specialist",
                role="AI Resource Allocation Specialist",
                phase=AgentPhase.PLANNING,
                status=AgentStatus.ACTIVE,
                expertise="AI-driven resource allocation with manual override support",
                specialization="Role-based resource requirements, workload analysis, cost optimization",
                key_skills=[
                    "Role-based resource analysis",
                    "Workload estimation",
                    "Resource leveling and optimization",
                    "Cost-aware allocation",
                    "Capacity planning",
                ],
                capabilities=[
                    "AI-driven baseline allocations",
                    "Application complexity factoring",
                    "Resource requirement calculation per role",
                    "Manual override support",
                    "Learning from human adjustments",
                ],
                api_endpoints=[
                    "/api/v1/planning/resources/allocate",
                ],
                description="AI specialist balancing efficiency with pragmatism in resource allocation.",
            )
        )

        # Timeline Generation Specialist Agent
        self.registry_core.register_agent(
            AgentRegistration(
                agent_id="timeline_generation_specialist",
                name="Timeline Generation Specialist",
                role="Migration Timeline Generation Specialist",
                phase=AgentPhase.PLANNING,
                status=AgentStatus.ACTIVE,
                expertise="Data-driven migration timeline creation with critical path analysis",
                specialization="CPM scheduling, resource-constrained planning, buffer management",
                key_skills=[
                    "Critical path method (CPM)",
                    "Resource-constrained scheduling",
                    "Duration estimation",
                    "Buffer and contingency planning",
                    "Milestone definition",
                ],
                capabilities=[
                    "CPM-based timeline optimization",
                    "Resource availability-based scheduling",
                    "Risk-adjusted buffering",
                    "Business milestone alignment",
                    "Gantt chart data generation",
                ],
                api_endpoints=[
                    "/api/v1/planning/timeline/generate",
                ],
                description="Expert in creating realistic, achievable migration timelines with critical path analysis.",
            )
        )

        # Cost Estimation Specialist Agent
        self.registry_core.register_agent(
            AgentRegistration(
                agent_id="cost_estimation_specialist",
                name="Cost Estimation Specialist",
                role="Migration Cost Estimation Specialist",
                phase=AgentPhase.PLANNING,
                status=AgentStatus.ACTIVE,
                expertise="Comprehensive migration cost calculation across all dimensions",
                specialization="Labor cost modeling, infrastructure TCO, risk contingency estimation",
                key_skills=[
                    "Labor cost calculation",
                    "Infrastructure cost modeling",
                    "Risk contingency estimation",
                    "Total Cost of Ownership (TCO) analysis",
                    "Cost variance tracking",
                ],
                capabilities=[
                    "Multi-dimensional cost calculation",
                    "Transparent assumption documentation",
                    "One-time and recurring cost separation",
                    "Industry benchmark alignment",
                    "Budget planning support",
                ],
                api_endpoints=[
                    "/api/v1/planning/costs/estimate",
                ],
                description=(
                    "Expert in providing accurate, defensible migration "
                    "cost estimates for informed decision-making."
                ),
            )
        )
