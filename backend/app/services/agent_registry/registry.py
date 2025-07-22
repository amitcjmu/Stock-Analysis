"""
Main Agent Registry

Complete agent registry implementation combining all modular components.
"""

import logging
from typing import Any, Dict

from .lifecycle_manager import AgentLifecycleManager
from .phase_agents import (
    AssessmentAgentManager,
    DecommissionAgentManager,
    DiscoveryAgentManager,
    FinOpsAgentManager,
    LearningContextAgentManager,
    MigrationAgentManager,
    ModernizationAgentManager,
    ObservabilityAgentManager,
    PlanningAgentManager,
)
from .registry_core import AgentRegistryCore

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Complete agent registry combining all modular components.
    Central registry for all platform agents with lifecycle management.
    """
    
    def __init__(self):
        # Initialize core components
        self.core = AgentRegistryCore()
        self.lifecycle = AgentLifecycleManager(self.core)
        
        # Initialize phase-specific managers
        self.discovery_manager = DiscoveryAgentManager(self.core)
        self.assessment_manager = AssessmentAgentManager(self.core)
        self.planning_manager = PlanningAgentManager(self.core)
        self.migration_manager = MigrationAgentManager(self.core)
        self.modernization_manager = ModernizationAgentManager(self.core)
        self.decommission_manager = DecommissionAgentManager(self.core)
        self.finops_manager = FinOpsAgentManager(self.core)
        self.learning_context_manager = LearningContextAgentManager(self.core)
        self.observability_manager = ObservabilityAgentManager(self.core)
        
        # Defer agent initialization to avoid circular imports
        self._agents_initialized = False
        
        logger.info("Agent Registry initialized (agents will be registered on first use)")
    
    def _ensure_agents_initialized(self):
        """Ensure agents are initialized (lazy initialization)"""
        if not self._agents_initialized:
            self._initialize_all_agents()
            self._agents_initialized = True
    
    def _initialize_all_agents(self):
        """Initialize all agents across all phases"""
        try:
            # Register agents by phase
            self.discovery_manager.register_phase_agents()
            self.assessment_manager.register_phase_agents()
            self.planning_manager.register_phase_agents()
            self.migration_manager.register_phase_agents()
            self.modernization_manager.register_phase_agents()
            self.decommission_manager.register_phase_agents()
            self.finops_manager.register_phase_agents()
            self.learning_context_manager.register_phase_agents()
            self.observability_manager.register_phase_agents()
            
            logger.info(f"All agents initialized successfully - {self.core.get_agents_count()} agents registered")
        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}")
            # Don't re-raise to allow the registry to function partially
    
    # Delegate core registry methods
    def register_agent(self, agent):
        """Register a new agent"""
        self._ensure_agents_initialized()
        return self.core.register_agent(agent)
    
    def get_agent(self, agent_id: str):
        """Get agent by ID"""
        self._ensure_agents_initialized()
        return self.core.get_agent(agent_id)
    
    def get_agents_by_phase(self, phase):
        """Get all agents for a specific phase"""
        self._ensure_agents_initialized()
        return self.core.get_agents_by_phase(phase)
    
    def get_active_agents(self):
        """Get all active agents"""
        self._ensure_agents_initialized()
        return self.core.get_active_agents()
    
    def get_agents_by_status(self, status):
        """Get all agents with specific status"""
        self._ensure_agents_initialized()
        return self.core.get_agents_by_status(status)
    
    def update_agent_status(self, agent_id: str, status, **kwargs):
        """Update agent status and metrics"""
        self._ensure_agents_initialized()
        return self.core.update_agent_status(agent_id, status, **kwargs)
    
    def get_phase_summary(self):
        """Get summary of agents by phase and status"""
        self._ensure_agents_initialized()
        return self.core.get_phase_summary()
    
    def get_registry_status(self):
        """Get comprehensive registry status"""
        self._ensure_agents_initialized()
        return self.core.get_registry_status()
    
    def get_agent_capabilities_formatted(self):
        """Get agent capabilities in monitoring endpoint format"""
        self._ensure_agents_initialized()
        return self.core.get_agent_capabilities_formatted()
    
    def to_dict(self):
        """Convert registry to dictionary format"""
        self._ensure_agents_initialized()
        return self.core.to_dict()
    
    # Delegate lifecycle management methods
    def update_agent_performance(self, agent_id: str, task_duration: float, task_success: bool, memory_used: float = 0.0, confidence: float = 0.0):
        """Update agent performance metrics from actual task completion"""
        return self.lifecycle.update_agent_performance(agent_id, task_duration, task_success, memory_used, confidence)
    
    def record_task_completion(self, agent_name: str, crew_name: str, task_info: Dict[str, Any]):
        """Record task completion from CrewAI callback system"""
        return self.lifecycle.record_task_completion(agent_name, crew_name, task_info)
    
    def get_agent_health_summary(self):
        """Get summary of agent health and performance"""
        return self.lifecycle.get_agent_health_summary()
    
    # Phase-specific access methods
    def get_discovery_agents(self):
        """Get Discovery phase agents"""
        return self.discovery_manager.get_phase_agents()
    
    def get_assessment_agents(self):
        """Get Assessment phase agents"""
        return self.assessment_manager.get_phase_agents()
    
    def get_planning_agents(self):
        """Get Planning phase agents"""
        return self.planning_manager.get_phase_agents()
    
    def get_migration_agents(self):
        """Get Migration phase agents"""
        return self.migration_manager.get_phase_agents()
    
    def get_modernization_agents(self):
        """Get Modernization phase agents"""
        return self.modernization_manager.get_phase_agents()
    
    def get_decommission_agents(self):
        """Get Decommission phase agents"""
        return self.decommission_manager.get_phase_agents()
    
    def get_finops_agents(self):
        """Get FinOps phase agents"""
        return self.finops_manager.get_phase_agents()
    
    def get_learning_context_agents(self):
        """Get Learning & Context Management agents"""
        return self.learning_context_manager.get_phase_agents()
    
    def get_observability_agents(self):
        """Get Observability phase agents"""
        return self.observability_manager.get_phase_agents()
    
    # Convenience properties for backward compatibility
    @property
    def agents(self):
        """Access to agents dict for backward compatibility"""
        return self.core.agents