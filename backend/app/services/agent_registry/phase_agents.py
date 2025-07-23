"""
Phase-Specific Agent Managers

Managers for registering and organizing agents by their execution phase.
"""

import logging
from typing import List

from .base import AgentPhase, AgentRegistration, AgentStatus
from .registry_core import AgentRegistryCore

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


class PlanningAgentManager(BasePhaseAgentManager):
    """Manager for Planning phase agents"""

    def __init__(self, registry_core: AgentRegistryCore):
        super().__init__(registry_core, AgentPhase.PLANNING)

    def register_phase_agents(self) -> None:
        """Register Planning phase agents"""

        # Wave Planning Coordinator Agent
        self.registry_core.register_agent(
            AgentRegistration(
                agent_id="wave_planner_001",
                name="Wave Planning Coordinator Agent",
                role="Wave Planning Coordinator",
                phase=AgentPhase.PLANNING,
                status=AgentStatus.ACTIVE,
                expertise="Migration sequencing and dependency management",
                specialization="Wave optimization, resource planning, timeline management",
                key_skills=[
                    "Dependency analysis",
                    "Wave sequencing",
                    "Resource optimization",
                    "Timeline management",
                    "Critical path analysis",
                ],
                capabilities=[
                    "Advanced dependency mapping",
                    "Optimal wave sequencing",
                    "Resource allocation optimization",
                    "Timeline optimization",
                ],
                api_endpoints=[
                    "/api/v1/planning/wave-planning",
                    "/api/v1/planning/dependency-analysis",
                ],
                description="Advanced wave planning with dependency management and resource optimization.",
            )
        )


class MigrationAgentManager(BasePhaseAgentManager):
    """Manager for Migration phase agents"""

    def __init__(self, registry_core: AgentRegistryCore):
        super().__init__(registry_core, AgentPhase.MIGRATION)

    def register_phase_agents(self) -> None:
        """Register Migration phase agents"""

        # Migration Execution Coordinator (Planned)
        self.registry_core.register_agent(
            AgentRegistration(
                agent_id="execution_coordinator_001",
                name="Migration Execution Coordinator",
                role="Migration Execution Coordinator",
                phase=AgentPhase.MIGRATION,
                status=AgentStatus.PLANNED,
                expertise="Real-time migration orchestration and monitoring",
                specialization="Migration execution, monitoring, rollback management",
                key_skills=[
                    "Real-time orchestration",
                    "Migration monitoring",
                    "Rollback management",
                    "Execution coordination",
                    "Quality validation",
                ],
                capabilities=[
                    "Real-time migration orchestration",
                    "Automated monitoring",
                    "Intelligent rollback",
                    "Quality validation",
                ],
                api_endpoints=[
                    "/api/v1/migration/execute",
                    "/api/v1/migration/monitor",
                ],
                description="Real-time migration execution with intelligent monitoring and rollback capabilities.",
            )
        )


class ModernizationAgentManager(BasePhaseAgentManager):
    """Manager for Modernization phase agents"""

    def __init__(self, registry_core: AgentRegistryCore):
        super().__init__(registry_core, AgentPhase.MODERNIZATION)

    def register_phase_agents(self) -> None:
        """Register Modernization phase agents"""

        # Containerization Specialist (Planned)
        self.registry_core.register_agent(
            AgentRegistration(
                agent_id="containerization_specialist_001",
                name="Containerization Specialist Agent",
                role="Containerization Specialist",
                phase=AgentPhase.MODERNIZATION,
                status=AgentStatus.PLANNED,
                expertise="Application containerization and Kubernetes deployment",
                specialization="Docker containerization, Kubernetes orchestration, cloud-native architecture",
                key_skills=[
                    "Container architecture",
                    "Kubernetes deployment",
                    "Cloud-native design",
                    "Microservices patterns",
                    "DevOps integration",
                ],
                capabilities=[
                    "Automated containerization",
                    "Kubernetes optimization",
                    "Cloud-native transformation",
                    "Performance optimization",
                ],
                api_endpoints=[
                    "/api/v1/modernization/containerize",
                    "/api/v1/modernization/kubernetes-deploy",
                ],
                description="Expert containerization and cloud-native transformation specialist.",
            )
        )


class DecommissionAgentManager(BasePhaseAgentManager):
    """Manager for Decommission phase agents"""

    def __init__(self, registry_core: AgentRegistryCore):
        super().__init__(registry_core, AgentPhase.DECOMMISSION)

    def register_phase_agents(self) -> None:
        """Register Decommission phase agents"""

        # Decommission Coordinator (Planned)
        self.registry_core.register_agent(
            AgentRegistration(
                agent_id="decommission_coordinator_001",
                name="Decommission Coordinator Agent",
                role="Decommission Coordinator",
                phase=AgentPhase.DECOMMISSION,
                status=AgentStatus.PLANNED,
                expertise="Safe asset retirement and data archival",
                specialization="Asset decommissioning, data archival, compliance validation",
                key_skills=[
                    "Safe asset retirement",
                    "Data archival",
                    "Compliance validation",
                    "Security cleanup",
                    "Documentation management",
                ],
                capabilities=[
                    "Automated decommissioning",
                    "Secure data archival",
                    "Compliance verification",
                    "Asset cleanup validation",
                ],
                api_endpoints=[
                    "/api/v1/decommission/plan",
                    "/api/v1/decommission/execute",
                ],
                description="Comprehensive decommissioning specialist with compliance and security focus.",
            )
        )


class FinOpsAgentManager(BasePhaseAgentManager):
    """Manager for FinOps phase agents"""

    def __init__(self, registry_core: AgentRegistryCore):
        super().__init__(registry_core, AgentPhase.FINOPS)

    def register_phase_agents(self) -> None:
        """Register FinOps phase agents"""

        # Cost Optimization Agent (Planned)
        self.registry_core.register_agent(
            AgentRegistration(
                agent_id="cost_optimizer_001",
                name="Cost Optimization Agent",
                role="Cost Optimization Specialist",
                phase=AgentPhase.FINOPS,
                status=AgentStatus.PLANNED,
                expertise="Cloud cost analysis and optimization recommendations",
                specialization="Cost analysis, ROI calculation, savings identification",
                key_skills=[
                    "Cost analysis",
                    "ROI calculation",
                    "Savings identification",
                    "Budget optimization",
                    "Performance-cost correlation",
                ],
                capabilities=[
                    "Automated cost analysis",
                    "ROI calculation engine",
                    "Savings recommendation",
                    "Budget optimization",
                ],
                api_endpoints=[
                    "/api/v1/finops/cost-analysis",
                    "/api/v1/finops/optimization-recommendations",
                ],
                description="Advanced cost optimization specialist with ROI focus and savings identification.",
            )
        )


class LearningContextAgentManager(BasePhaseAgentManager):
    """Manager for Learning & Context Management agents"""

    def __init__(self, registry_core: AgentRegistryCore):
        super().__init__(registry_core, AgentPhase.LEARNING_CONTEXT)

    def register_phase_agents(self) -> None:
        """Register Learning & Context Management agents"""

        # Agent Learning System
        self.registry_core.register_agent(
            AgentRegistration(
                agent_id="agent_learning_system_001",
                name="Agent Learning System",
                role="Platform-Wide Learning Infrastructure",
                phase=AgentPhase.LEARNING_CONTEXT,
                status=AgentStatus.ACTIVE,
                expertise="Pattern recognition, field mapping learning, performance tracking",
                specialization="Field mapping pattern learning with fuzzy matching, data source pattern learning, quality assessment learning, user preference learning",
                key_skills=[
                    "Field mapping pattern learning",
                    "Data source pattern recognition",
                    "Quality assessment learning",
                    "User preference adaptation",
                    "Performance tracking",
                    "Accuracy metrics calculation",
                ],
                capabilities=[
                    "JSON-based persistent learning data storage",
                    "Confidence scoring for mapping accuracy",
                    "Cross-system learning integration",
                    "Fuzzy matching algorithms",
                    "Threshold optimization",
                ],
                api_endpoints=[
                    "/api/v1/agent-learning/learning/field-mapping",
                    "/api/v1/agent-learning/learning/data-source-pattern",
                    "/api/v1/agent-learning/learning/quality-assessment",
                    "/api/v1/agent-learning/learning/user-preferences",
                    "/api/v1/agent-learning/learning/statistics",
                ],
                description="Comprehensive learning infrastructure enabling all agents to learn from user feedback and improve over time.",
                learning_enabled=True,
                cross_page_communication=True,
            )
        )

        # Client Context Manager
        self.registry_core.register_agent(
            AgentRegistration(
                agent_id="client_context_manager_001",
                name="Client Context Manager",
                role="Client/Engagement-Specific Context Management",
                phase=AgentPhase.LEARNING_CONTEXT,
                status=AgentStatus.ACTIVE,
                expertise="Organizational pattern learning, engagement-specific preferences",
                specialization="Client-specific organizational pattern learning, engagement-specific preferences and clarification history, migration preference learning and agent behavior adaptation",
                key_skills=[
                    "Organizational pattern recognition",
                    "Engagement-specific context management",
                    "Clarification history tracking",
                    "Agent behavior adaptation",
                    "Migration preference learning",
                    "Multi-tenant context isolation",
                ],
                capabilities=[
                    "Client/engagement context storage and retrieval",
                    "Organizational pattern recognition and learning",
                    "Agent behavior adaptation based on client preferences",
                    "Multi-tenant context isolation with client account scoping",
                ],
                api_endpoints=[
                    "/api/v1/agent-learning/context/client/{client_id}",
                    "/api/v1/agent-learning/context/engagement/{engagement_id}",
                    "/api/v1/agent-learning/context/organizational-pattern",
                    "/api/v1/agent-learning/context/combined/{engagement_id}",
                ],
                description="Client and engagement-specific context management enabling personalized agent behavior and organizational intelligence.",
                learning_enabled=True,
                cross_page_communication=True,
            )
        )


class ObservabilityAgentManager(BasePhaseAgentManager):
    """Manager for Observability phase agents"""

    def __init__(self, registry_core: AgentRegistryCore):
        super().__init__(registry_core, AgentPhase.OBSERVABILITY)

    def register_phase_agents(self) -> None:
        """Register Observability phase agents"""

        # Asset Intelligence Agent
        self.registry_core.register_agent(
            AgentRegistration(
                agent_id="asset_intelligence_001",
                name="Asset Intelligence Agent",
                role="Asset Inventory Intelligence Specialist",
                phase=AgentPhase.OBSERVABILITY,
                status=AgentStatus.ACTIVE,
                expertise="Advanced asset inventory management with AI intelligence",
                specialization="Asset classification and categorization patterns using AI, content-based asset analysis using field mapping intelligence, intelligent bulk operations planning",
                key_skills=[
                    "AI-powered asset classification",
                    "Content-based analysis",
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
                    "/api/v1/discovery/assets/analyze",
                    "/api/v1/discovery/assets/auto-classify",
                    "/api/v1/discovery/assets/intelligence-status",
                    "/api/v1/inventory/analyze",
                ],
                description="Revolutionary asset intelligence with AI-powered classification, bulk operations optimization, and continuous learning capabilities.",
                learning_enabled=True,
            )
        )

        # Agent Health Monitor
        self.registry_core.register_agent(
            AgentRegistration(
                agent_id="agent_health_monitor_001",
                name="Agent Health Monitor",
                role="Agent Health Monitor",
                phase=AgentPhase.OBSERVABILITY,
                status=AgentStatus.ACTIVE,
                expertise="Real-time agent performance and health monitoring",
                specialization="Agent performance analysis, health tracking, system observability",
                key_skills=[
                    "Real-time monitoring",
                    "Performance analysis",
                    "Health tracking",
                    "System observability",
                    "Alert management",
                ],
                capabilities=[
                    "Real-time agent performance monitoring",
                    "Health status tracking",
                    "Performance metrics collection",
                    "Alert generation and management",
                ],
                api_endpoints=[
                    "/api/v1/monitoring/status",
                    "/api/v1/monitoring/agents",
                    "/api/v1/monitoring/health",
                ],
                description="Comprehensive agent health monitoring with real-time performance tracking and alerting.",
            )
        )

        # Performance Analytics Agent
        self.registry_core.register_agent(
            AgentRegistration(
                agent_id="performance_analytics_001",
                name="Performance Analytics Agent",
                role="Performance Analytics Specialist",
                phase=AgentPhase.OBSERVABILITY,
                status=AgentStatus.ACTIVE,
                expertise="Agent performance analysis and optimization recommendations",
                specialization="Performance metrics analysis, optimization recommendations, trend analysis",
                key_skills=[
                    "Performance metrics analysis",
                    "Optimization recommendations",
                    "Trend analysis",
                    "Capacity planning",
                    "Resource optimization",
                ],
                capabilities=[
                    "Advanced performance analytics",
                    "Optimization recommendation engine",
                    "Predictive performance analysis",
                    "Resource usage optimization",
                ],
                api_endpoints=[
                    "/api/v1/monitoring/metrics",
                    "/api/v1/monitoring/analytics",
                ],
                description="Advanced performance analytics with optimization recommendations and predictive analysis.",
            )
        )
