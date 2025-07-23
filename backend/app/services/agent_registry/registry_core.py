"""
Agent Registry Core

Core functionality for agent registration, lookup, and management.
"""

import logging
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import AgentPhase, AgentRegistration, AgentStatus

logger = logging.getLogger(__name__)


class AgentRegistryCore:
    """Core agent registry functionality"""

    def __init__(self):
        self.agents: Dict[str, AgentRegistration] = {}
        logger.info("Agent Registry Core initialized")

    def register_agent(self, agent: AgentRegistration) -> None:
        """Register a new agent in the registry"""
        if agent.registration_time is None:
            agent.registration_time = datetime.utcnow()
        agent.last_heartbeat = datetime.utcnow()

        self.agents[agent.agent_id] = agent
        logger.info(
            f"Registered agent: {agent.name} ({agent.agent_id}) in {agent.phase.value} phase"
        )

    def get_agent(self, agent_id: str) -> Optional[AgentRegistration]:
        """Get agent by ID"""
        return self.agents.get(agent_id)

    def get_agents_by_phase(self, phase: AgentPhase) -> List[AgentRegistration]:
        """Get all agents for a specific phase"""
        return [agent for agent in self.agents.values() if agent.phase == phase]

    def get_active_agents(self) -> List[AgentRegistration]:
        """Get all active agents"""
        return [
            agent
            for agent in self.agents.values()
            if agent.status == AgentStatus.ACTIVE
        ]

    def get_agents_by_status(self, status: AgentStatus) -> List[AgentRegistration]:
        """Get all agents with specific status"""
        return [agent for agent in self.agents.values() if agent.status == status]

    def update_agent_status(self, agent_id: str, status: AgentStatus, **kwargs) -> None:
        """Update agent status and metrics"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            agent.status = status
            agent.last_heartbeat = datetime.utcnow()

            # Update metrics if provided
            for key, value in kwargs.items():
                if hasattr(agent, key):
                    setattr(agent, key, value)

    def get_phase_summary(self) -> Dict[str, Dict[str, int]]:
        """Get summary of agents by phase and status"""
        summary = {}
        for phase in AgentPhase:
            phase_agents = self.get_agents_by_phase(phase)
            summary[phase.value] = {
                "total": len(phase_agents),
                "active": len(
                    [a for a in phase_agents if a.status == AgentStatus.ACTIVE]
                ),
                "planned": len(
                    [a for a in phase_agents if a.status == AgentStatus.PLANNED]
                ),
                "in_development": len(
                    [a for a in phase_agents if a.status == AgentStatus.IN_DEVELOPMENT]
                ),
            }
        return summary

    def get_registry_status(self) -> Dict[str, Any]:
        """Get comprehensive registry status"""
        total_agents = len(self.agents)
        active_agents = len(self.get_active_agents())
        learning_enabled = len([a for a in self.agents.values() if a.learning_enabled])
        cross_page_enabled = len(
            [a for a in self.agents.values() if a.cross_page_communication]
        )
        modular_agents = len([a for a in self.agents.values() if a.modular_handlers])

        return {
            "registry_status": "healthy",
            "total_agents": total_agents,
            "active_agents": active_agents,
            "learning_enabled_agents": learning_enabled,
            "cross_page_communication_agents": cross_page_enabled,
            "modular_handler_agents": modular_agents,
            "phase_distribution": self.get_phase_summary(),
            "last_updated": datetime.utcnow().isoformat(),
        }

    def get_agent_capabilities_formatted(self) -> Dict[str, Dict[str, Any]]:
        """Get agent capabilities in monitoring endpoint format"""
        capabilities = {}
        for agent_id, agent in self.agents.items():
            capabilities[agent.name.lower().replace(" ", "_")] = {
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
                    "last_heartbeat": (
                        agent.last_heartbeat.isoformat()
                        if agent.last_heartbeat
                        else None
                    ),
                },
            }
        return capabilities

    def to_dict(self) -> Dict[str, Any]:
        """Convert registry to dictionary format"""
        return {
            "agents": {
                agent_id: asdict(agent) for agent_id, agent in self.agents.items()
            },
            "summary": self.get_registry_status(),
        }

    def clear_agents(self) -> None:
        """Clear all agents from registry"""
        self.agents.clear()
        logger.info("Agent registry cleared")

    def get_agents_count(self) -> int:
        """Get total number of registered agents"""
        return len(self.agents)
