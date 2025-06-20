"""
Comprehensive Agent Registry Service
Central registry for all agents across all phases with detailed metadata and observability support.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class AgentPhase(Enum):
    DISCOVERY = "discovery"
    ASSESSMENT = "assessment"  
    PLANNING = "planning"
    MIGRATION = "migration"
    MODERNIZATION = "modernization"
    DECOMMISSION = "decommission"
    FINOPS = "finops"
    LEARNING_CONTEXT = "learning_context"
    OBSERVABILITY = "observability"

class AgentStatus(Enum):
    ACTIVE = "active"
    STANDBY = "standby"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    PLANNED = "planned"
    IN_DEVELOPMENT = "in_development"

@dataclass
class AgentRegistration:
    agent_id: str
    name: str
    role: str
    phase: AgentPhase
    status: AgentStatus
    expertise: str
    specialization: str
    key_skills: List[str]
    capabilities: List[str]
    api_endpoints: List[str]
    description: str
    version: str = "1.0.0"
    registration_time: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    tasks_completed: int = 0
    success_rate: float = 0.0
    avg_execution_time: float = 0.0
    memory_utilization: float = 0.0
    confidence: float = 0.0
    learning_enabled: bool = False
    cross_page_communication: bool = False
    modular_handlers: bool = False

class AgentRegistry:
    """Central registry for all platform agents."""
    
    def __init__(self):
        self.agents: Dict[str, AgentRegistration] = {}
        self._initialize_all_agents()
        logger.info(f"Agent Registry initialized with {len(self.agents)} agents")
    
    def _initialize_all_agents(self):
        """Initialize all agents across all phases."""
        
        # === DISCOVERY PHASE AGENTS ===
        self._register_discovery_crew_agents()
        
        # === ASSESSMENT PHASE AGENTS ===
        self._register_assessment_agents()
        
        # === PLANNING PHASE AGENTS ===
        self._register_planning_agents()
        
        # === MIGRATION PHASE AGENTS ===
        self._register_migration_agents()
        
        # === MODERNIZATION PHASE AGENTS ===
        self._register_modernization_agents()
        
        # === DECOMMISSION PHASE AGENTS ===
        self._register_decommission_agents()
        
        # === FINOPS PHASE AGENTS ===
        self._register_finops_agents()
        
        # === LEARNING & CONTEXT MANAGEMENT AGENTS ===
        self._register_learning_context_agents()
        
        # === OBSERVABILITY PHASE AGENTS ===
        self._register_observability_agents()
    
    def _register_discovery_crew_agents(self):
        """Register all Discovery phase crew-based agents."""
        
        # Data Source Intelligence Agent (NEW - Modular)
        self.register_agent(AgentRegistration(
            agent_id="data_source_intelligence_001",
            name="Data Source Intelligence Agent",
            role="Data Source Intelligence Specialist",
            phase=AgentPhase.DISCOVERY,
            status=AgentStatus.ACTIVE,
            expertise="Analyzes incoming data sources (CMDB, migration tools, documentation) for format, structure, and migration value",
            specialization="Agentic intelligence without hard-coded heuristics, learns from user corrections",
            key_skills=[
                "Source type pattern recognition",
                "Data structure analysis", 
                "Quality assessment intelligence",
                "Insight generation",
                "Clarification question generation"
            ],
            capabilities=[
                "Content-based source type analysis",
                "Relationship and pattern detection",
                "Migration value assessment",
                "Intelligent question generation",
                "Continuous learning from feedback"
            ],
            api_endpoints=[
                "/api/v1/discovery/agents/data-source-analysis",
                "/api/v1/discovery/agents/data-source-insights"
            ],
            description="Revolutionary data source intelligence with modular handlers for source analysis, structure analysis, quality assessment, insight generation, and question generation.",
            learning_enabled=True,
            modular_handlers=True
        ))
        
        # CMDB Data Analyst Agent
        self.register_agent(AgentRegistration(
            agent_id="cmdb_analyst_001",
            name="CMDB Data Analyst Agent",
            role="Senior CMDB Data Analyst",
            phase=AgentPhase.DISCOVERY,
            status=AgentStatus.ACTIVE,
            expertise="15+ years in enterprise asset management and migration readiness assessment",
            specialization="Asset type detection, data quality assessment, migration readiness",
            key_skills=[
                "Asset classification",
                "Field validation",
                "Migration recommendations",
                "Quality assessment",
                "Pattern recognition"
            ],
            capabilities=[
                "Asset type intelligence",
                "Context-aware analysis", 
                "Memory integration",
                "Migration-focused recommendations"
            ],
            api_endpoints=[
                "/api/v1/discovery/analyze-cmdb",
                "/api/v1/discovery/process-cmdb"
            ],
            description="Expert CMDB analyst with deep knowledge of asset management and migration planning."
        ))
        
        # Field Mapping Specialist Agent
        self.register_agent(AgentRegistration(
            agent_id="field_mapping_specialist_001",
            name="Field Mapping Specialist Agent", 
            role="Field Mapping Specialist",
            phase=AgentPhase.DISCOVERY,
            status=AgentStatus.ACTIVE,
            expertise="Intelligent field mapping to 20+ critical migration attributes",
            specialization="Learns organizational field naming conventions, creates custom attributes, provides confidence scoring",
            key_skills=[
                "Semantic field analysis",
                "Critical attribute mapping",
                "Custom attribute creation",
                "Confidence scoring",
                "Pattern learning"
            ],
            capabilities=[
                "Extended critical attributes mapping",
                "Custom attribute creation",
                "Field filtering",
                "Confidence scoring algorithms",
                "Organizational pattern learning"
            ],
            api_endpoints=[
                "/api/v1/data-import/simple-field-mappings",
                "/api/v1/data-import/context-field-mappings"
            ],
            description="Advanced field mapping with learning integration and custom attribute capabilities.",
            learning_enabled=True
        ))
        
        # Learning Specialist Agent (Enhanced)
        self.register_agent(AgentRegistration(
            agent_id="learning_agent_001",
            name="Learning Specialist Agent",
            role="AI Learning Specialist", 
            phase=AgentPhase.DISCOVERY,
            status=AgentStatus.ACTIVE,
            expertise="Cross-platform learning coordination and pattern recognition (Enhanced with asset management learning)",
            specialization="Field mapping learning, data source patterns, quality assessment improvement, user preference adaptation",
            key_skills=[
                "Feedback analysis",
                "Pattern extraction", 
                "Model updates",
                "Cross-platform coordination",
                "Asset management learning"
            ],
            capabilities=[
                "Enhanced asset management learning",
                "Cross-platform learning coordination",
                "Field mapping intelligence",
                "Performance improvement tracking"
            ],
            api_endpoints=[
                "/api/v1/discovery/cmdb-feedback",
                "/api/v1/discovery/learning"
            ],
            description="Enhanced learning specialist with asset management capabilities and cross-platform coordination.",
            learning_enabled=True,
            cross_page_communication=True
        ))
    
    def _register_assessment_agents(self):
        """Register all Assessment phase agents."""
        
        # Migration Strategy Expert Agent
        self.register_agent(AgentRegistration(
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
                "Business value analysis"
            ],
            capabilities=[
                "Comprehensive 6R analysis",
                "Strategy recommendation engine",
                "Risk-aware planning",
                "Business impact assessment"
            ],
            api_endpoints=[
                "/api/v1/assessment/6r-analysis",
                "/api/v1/assessment/strategy-recommendation"
            ],
            description="Expert 6R strategist with comprehensive migration planning capabilities."
        ))
        
        # Risk Assessment Specialist Agent  
        self.register_agent(AgentRegistration(
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
                "Operational risk evaluation"
            ],
            capabilities=[
                "Multi-dimensional risk analysis",
                "Automated risk scoring",
                "Mitigation recommendation",
                "Risk trend analysis"
            ],
            api_endpoints=[
                "/api/v1/assessment/risk-analysis",
                "/api/v1/assessment/risk-mitigation"
            ],
            description="Comprehensive risk assessment specialist for migration planning."
        ))
    
    def _register_planning_agents(self):
        """Register all Planning phase agents."""
        
        # Wave Planning Coordinator Agent
        self.register_agent(AgentRegistration(
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
                "Critical path analysis"
            ],
            capabilities=[
                "Advanced dependency mapping",
                "Optimal wave sequencing",
                "Resource allocation optimization",
                "Timeline optimization"
            ],
            api_endpoints=[
                "/api/v1/planning/wave-planning",
                "/api/v1/planning/dependency-analysis"
            ],
            description="Advanced wave planning with dependency management and resource optimization."
        ))
    
    def _register_migration_agents(self):
        """Register all Migration phase agents."""
        
        # Migration Execution Coordinator (Planned)
        self.register_agent(AgentRegistration(
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
                "Quality validation"
            ],
            capabilities=[
                "Real-time migration orchestration",
                "Automated monitoring",
                "Intelligent rollback",
                "Quality validation"
            ],
            api_endpoints=[
                "/api/v1/migration/execute",
                "/api/v1/migration/monitor"
            ],
            description="Real-time migration execution with intelligent monitoring and rollback capabilities."
        ))
    
    def _register_modernization_agents(self):
        """Register all Modernization phase agents."""
        
        # Containerization Specialist (Planned)
        self.register_agent(AgentRegistration(
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
                "DevOps integration"
            ],
            capabilities=[
                "Automated containerization",
                "Kubernetes optimization",
                "Cloud-native transformation",
                "Performance optimization"
            ],
            api_endpoints=[
                "/api/v1/modernization/containerize",
                "/api/v1/modernization/kubernetes-deploy"
            ],
            description="Expert containerization and cloud-native transformation specialist."
        ))
    
    def _register_decommission_agents(self):
        """Register all Decommission phase agents."""
        
        # Decommission Coordinator (Planned)
        self.register_agent(AgentRegistration(
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
                "Documentation management"
            ],
            capabilities=[
                "Automated decommissioning",
                "Secure data archival",
                "Compliance verification",
                "Asset cleanup validation"
            ],
            api_endpoints=[
                "/api/v1/decommission/plan",
                "/api/v1/decommission/execute"
            ],
            description="Comprehensive decommissioning specialist with compliance and security focus."
        ))
    
    def _register_finops_agents(self):
        """Register all FinOps phase agents."""
        
        # Cost Optimization Agent (Planned)
        self.register_agent(AgentRegistration(
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
                "Performance-cost correlation"
            ],
            capabilities=[
                "Automated cost analysis",
                "ROI calculation engine",
                "Savings recommendation",
                "Budget optimization"
            ],
            api_endpoints=[
                "/api/v1/finops/cost-analysis",
                "/api/v1/finops/optimization-recommendations"
            ],
            description="Advanced cost optimization specialist with ROI focus and savings identification."
        ))
    
    def _register_learning_context_agents(self):
        """Register all Learning & Context Management agents."""
        
        # Agent Learning System (NEW - Task C.1)
        self.register_agent(AgentRegistration(
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
                "Accuracy metrics calculation"
            ],
            capabilities=[
                "JSON-based persistent learning data storage",
                "Confidence scoring for mapping accuracy", 
                "Cross-system learning integration",
                "Fuzzy matching algorithms",
                "Threshold optimization"
            ],
            api_endpoints=[
                "/api/v1/agent-learning/learning/field-mapping",
                "/api/v1/agent-learning/learning/data-source-pattern",
                "/api/v1/agent-learning/learning/quality-assessment",
                "/api/v1/agent-learning/learning/user-preferences",
                "/api/v1/agent-learning/learning/statistics"
            ],
            description="Comprehensive learning infrastructure enabling all agents to learn from user feedback and improve over time.",
            learning_enabled=True,
            cross_page_communication=True
        ))
        
        # Client Context Manager (NEW - Task C.1)
        self.register_agent(AgentRegistration(
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
                "Multi-tenant context isolation"
            ],
            capabilities=[
                "Client/engagement context storage and retrieval",
                "Organizational pattern recognition and learning",
                "Agent behavior adaptation based on client preferences",
                "Multi-tenant context isolation with client account scoping"
            ],
            api_endpoints=[
                "/api/v1/agent-learning/context/client/{client_id}",
                "/api/v1/agent-learning/context/engagement/{engagement_id}",
                "/api/v1/agent-learning/context/organizational-pattern",
                "/api/v1/agent-learning/context/combined/{engagement_id}"
            ],
            description="Client and engagement-specific context management enabling personalized agent behavior and organizational intelligence.",
            learning_enabled=True,
            cross_page_communication=True
        ))
        
        # Enhanced Agent UI Bridge (ENHANCED - Task C.2)
        self.register_agent(AgentRegistration(
            agent_id="agent_ui_bridge_001",
            name="Enhanced Agent UI Bridge",
            role="Cross-Page Agent Communication Coordinator",
            phase=AgentPhase.LEARNING_CONTEXT,
            status=AgentStatus.ACTIVE,
            expertise="Agent state coordination, cross-page context sharing",
            specialization="Cross-page agent communication, agent state coordination across all discovery pages, context sharing and persistence with metadata tracking",
            key_skills=[
                "Cross-page context coordination",
                "Agent state management",
                "Context sharing protocols",
                "Learning experience synchronization",
                "Health monitoring coordination",
                "Stale context cleanup"
            ],
            capabilities=[
                "Agent state coordination across all discovery pages",
                "Context sharing and persistence with metadata tracking",
                "Learning experience storage and retrieval across page navigation", 
                "Coordination health monitoring and summary reporting",
                "Automatic stale context cleanup with configurable aging"
            ],
            api_endpoints=[
                "/api/v1/agent-learning/communication/cross-page-context",
                "/api/v1/agent-learning/communication/agent-state",
                "/api/v1/agent-learning/communication/agent-states",
                "/api/v1/agent-learning/communication/coordination-summary"
            ],
            description="Enhanced cross-page communication system enabling seamless agent coordination and context sharing across all discovery workflows.",
            learning_enabled=True,
            cross_page_communication=True,
            modular_handlers=True
        ))
    
    def _register_observability_agents(self):
        """Register all Observability phase agents."""
        
        # Asset Intelligence Agent (NEW - Discovery Integration)
        self.register_agent(AgentRegistration(
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
                "Quality assessment"
            ],
            capabilities=[
                "AI-powered pattern recognition (not hard-coded heuristics)",
                "Integration with discovery endpoints for seamless experience",
                "Real-time asset intelligence monitoring and updates",
                "Quality assessment with actionable recommendations",
                "Continuous learning from user interactions and feedback"
            ],
            api_endpoints=[
                "/api/v1/discovery/assets/analyze",
                "/api/v1/discovery/assets/auto-classify",
                "/api/v1/discovery/assets/intelligence-status",
                "/api/v1/inventory/analyze"
            ],
            description="Revolutionary asset intelligence with AI-powered classification, bulk operations optimization, and continuous learning capabilities.",
            learning_enabled=True
        ))
        
        # Agent Health Monitor  
        self.register_agent(AgentRegistration(
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
                "Alert management"
            ],
            capabilities=[
                "Real-time agent performance monitoring",
                "Health status tracking",
                "Performance metrics collection",
                "Alert generation and management"
            ],
            api_endpoints=[
                "/api/v1/monitoring/status",
                "/api/v1/monitoring/agents",
                "/api/v1/monitoring/health"
            ],
            description="Comprehensive agent health monitoring with real-time performance tracking and alerting."
        ))
        
        # Performance Analytics Agent
        self.register_agent(AgentRegistration(
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
                "Resource optimization"
            ],
            capabilities=[
                "Advanced performance analytics",
                "Optimization recommendation engine",
                "Predictive performance analysis",
                "Resource usage optimization"
            ],
            api_endpoints=[
                "/api/v1/monitoring/metrics",
                "/api/v1/monitoring/analytics"
            ],
            description="Advanced performance analytics with optimization recommendations and predictive analysis."
        ))
    
    def register_agent(self, agent: AgentRegistration):
        """Register a new agent in the registry."""
        if agent.registration_time is None:
            agent.registration_time = datetime.utcnow()
        agent.last_heartbeat = datetime.utcnow()
        
        self.agents[agent.agent_id] = agent
        logger.info(f"Registered agent: {agent.name} ({agent.agent_id}) in {agent.phase.value} phase")
    
    def update_agent_status(self, agent_id: str, status: AgentStatus, **kwargs):
        """Update agent status and metrics."""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            agent.status = status
            agent.last_heartbeat = datetime.utcnow()
            
            # Update metrics if provided
            for key, value in kwargs.items():
                if hasattr(agent, key):
                    setattr(agent, key, value)
    
    def update_agent_performance(self, agent_id: str, task_duration: float, task_success: bool, memory_used: float = 0.0, confidence: float = 0.0):
        """Update agent performance metrics from actual task completion."""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            
            # Update task completion count
            agent.tasks_completed += 1
            
            # Update success rate (running average)
            if agent.tasks_completed == 1:
                agent.success_rate = 1.0 if task_success else 0.0
            else:
                # Calculate running average
                current_successes = agent.success_rate * (agent.tasks_completed - 1)
                new_successes = current_successes + (1 if task_success else 0)
                agent.success_rate = new_successes / agent.tasks_completed
            
            # Update average execution time (running average)
            if agent.tasks_completed == 1:
                agent.avg_execution_time = task_duration
            else:
                # Calculate running average
                total_time = agent.avg_execution_time * (agent.tasks_completed - 1)
                agent.avg_execution_time = (total_time + task_duration) / agent.tasks_completed
            
            # Update other metrics
            if memory_used > 0:
                agent.memory_utilization = memory_used
            if confidence > 0:
                agent.confidence = confidence
            
            agent.last_heartbeat = datetime.utcnow()
            
            logger.info(f"Updated performance for agent {agent_id}: {agent.tasks_completed} tasks, {agent.success_rate:.2%} success rate")
        else:
            logger.warning(f"Agent {agent_id} not found for performance update")
    
    def record_task_completion(self, agent_name: str, crew_name: str, task_info: Dict[str, Any]):
        """Record task completion from CrewAI callback system."""
        # Find agent by name (since callback might not have agent_name)
        agent_id = None
        for aid, agent in self.agents.items():
            if agent.name.lower() == agent_name.lower() or agent.role.lower() == agent_name.lower():
                agent_id = aid
                break
        
        if agent_id:
            duration = task_info.get("duration", 0.0)
            success = task_info.get("success", True)
            quality_score = task_info.get("quality_score", 0.0)
            
            self.update_agent_performance(
                agent_id=agent_id,
                task_duration=duration,
                task_success=success,
                confidence=quality_score
            )
            
            logger.info(f"Recorded task completion for {agent_name} in {crew_name}: {duration:.2f}s, success={success}")
        else:
            logger.warning(f"Could not find agent for task completion: {agent_name}")
    
    def get_agent(self, agent_id: str) -> Optional[AgentRegistration]:
        """Get agent by ID."""
        return self.agents.get(agent_id)
    
    def get_agents_by_phase(self, phase: AgentPhase) -> List[AgentRegistration]:
        """Get all agents for a specific phase."""
        return [agent for agent in self.agents.values() if agent.phase == phase]
    
    def get_active_agents(self) -> List[AgentRegistration]:
        """Get all active agents."""
        return [agent for agent in self.agents.values() if agent.status == AgentStatus.ACTIVE]
    
    def get_agents_by_status(self, status: AgentStatus) -> List[AgentRegistration]:
        """Get all agents with specific status."""
        return [agent for agent in self.agents.values() if agent.status == status]
    
    def get_phase_summary(self) -> Dict[str, Dict[str, int]]:
        """Get summary of agents by phase and status."""
        summary = {}
        for phase in AgentPhase:
            phase_agents = self.get_agents_by_phase(phase)
            summary[phase.value] = {
                "total": len(phase_agents),
                "active": len([a for a in phase_agents if a.status == AgentStatus.ACTIVE]),
                "planned": len([a for a in phase_agents if a.status == AgentStatus.PLANNED]),
                "in_development": len([a for a in phase_agents if a.status == AgentStatus.IN_DEVELOPMENT])
            }
        return summary
    
    def get_registry_status(self) -> Dict[str, Any]:
        """Get comprehensive registry status."""
        total_agents = len(self.agents)
        active_agents = len(self.get_active_agents())
        learning_enabled = len([a for a in self.agents.values() if a.learning_enabled])
        cross_page_enabled = len([a for a in self.agents.values() if a.cross_page_communication])
        modular_agents = len([a for a in self.agents.values() if a.modular_handlers])
        
        return {
            "registry_status": "healthy",
            "total_agents": total_agents,
            "active_agents": active_agents,
            "learning_enabled_agents": learning_enabled,
            "cross_page_communication_agents": cross_page_enabled,
            "modular_handler_agents": modular_agents,
            "phase_distribution": self.get_phase_summary(),
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def get_agent_capabilities_formatted(self) -> Dict[str, Dict[str, Any]]:
        """Get agent capabilities in monitoring endpoint format."""
        capabilities = {}
        for agent_id, agent in self.agents.items():
            capabilities[agent.name.lower().replace(' ', '_')] = {
                "agent_id": agent.agent_id,
                "role": agent.role,
                "expertise": agent.expertise,
                "specialization": agent.specialization,
                "key_skills": ", ".join(agent.key_skills),
                "phase": agent.phase.value,
                "status": agent.status.value,
                "learning_enabled": agent.learning_enabled,
                "cross_page_communication": agent.cross_page_communication,
                "modular_handlers": agent.modular_handlers,
                "api_endpoints": agent.api_endpoints,
                "performance_metrics": {
                    "tasks_completed": agent.tasks_completed,
                    "success_rate": agent.success_rate,
                    "avg_execution_time": agent.avg_execution_time,
                    "memory_utilization": agent.memory_utilization,
                    "confidence": agent.confidence,
                    "last_heartbeat": agent.last_heartbeat.isoformat() if agent.last_heartbeat else None
                }
            }
        return capabilities
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert registry to dictionary format."""
        return {
            "agents": {agent_id: asdict(agent) for agent_id, agent in self.agents.items()},
            "summary": self.get_registry_status()
        }

# Global registry instance
agent_registry = AgentRegistry() 