"""
Agent Lifecycle Manager

Manages agent performance tracking, task completion recording, and lifecycle events.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from .base import AgentStatus
from .registry_core import AgentRegistryCore

logger = logging.getLogger(__name__)


class AgentLifecycleManager:
    """Manages agent lifecycle and performance tracking"""
    
    def __init__(self, registry_core: AgentRegistryCore):
        self.registry_core = registry_core
    
    def update_agent_performance(
        self, 
        agent_id: str, 
        task_duration: float, 
        task_success: bool, 
        memory_used: float = 0.0, 
        confidence: float = 0.0
    ) -> None:
        """Update agent performance metrics from actual task completion"""
        agent = self.registry_core.get_agent(agent_id)
        if not agent:
            logger.warning(f"Agent {agent_id} not found for performance update")
            return
        
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
    
    def record_task_completion(self, agent_name: str, crew_name: str, task_info: Dict[str, Any]) -> None:
        """Record task completion from CrewAI callback system"""
        # Find agent by name (since callback might not have agent_id)
        agent_id = None
        for aid, agent in self.registry_core.agents.items():
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
    
    def update_agent_heartbeat(self, agent_id: str) -> None:
        """Update agent heartbeat timestamp"""
        agent = self.registry_core.get_agent(agent_id)
        if agent:
            agent.last_heartbeat = datetime.utcnow()
        else:
            logger.warning(f"Agent {agent_id} not found for heartbeat update")
    
    def mark_agent_busy(self, agent_id: str, task_info: Dict[str, Any] = None) -> None:
        """Mark agent as busy with optional task information"""
        self.registry_core.update_agent_status(agent_id, AgentStatus.BUSY)
        if task_info:
            logger.info(f"Agent {agent_id} marked as busy: {task_info.get('task_name', 'unknown task')}")
    
    def mark_agent_available(self, agent_id: str) -> None:
        """Mark agent as available (active)"""
        self.registry_core.update_agent_status(agent_id, AgentStatus.ACTIVE)
        logger.info(f"Agent {agent_id} marked as available")
    
    def mark_agent_error(self, agent_id: str, error_details: Dict[str, Any] = None) -> None:
        """Mark agent as in error state"""
        self.registry_core.update_agent_status(agent_id, AgentStatus.ERROR)
        if error_details:
            logger.error(f"Agent {agent_id} marked as error: {error_details.get('error_message', 'unknown error')}")
    
    def get_agent_health_summary(self) -> Dict[str, Any]:
        """Get summary of agent health and performance"""
        agents = list(self.registry_core.agents.values())
        
        if not agents:
            return {"total_agents": 0, "health_status": "no_agents"}
        
        # Calculate health metrics
        total_tasks = sum(a.tasks_completed for a in agents)
        avg_success_rate = sum(a.success_rate for a in agents) / len(agents)
        avg_execution_time = sum(a.avg_execution_time for a in agents) / len(agents)
        
        # Status distribution
        status_counts = {}
        for status in AgentStatus:
            status_counts[status.value] = len([a for a in agents if a.status == status])
        
        # Performance tiers
        high_performers = len([a for a in agents if a.success_rate > 0.9])
        medium_performers = len([a for a in agents if 0.7 <= a.success_rate <= 0.9])
        low_performers = len([a for a in agents if a.success_rate < 0.7])
        
        return {
            "total_agents": len(agents),
            "total_tasks_completed": total_tasks,
            "average_success_rate": avg_success_rate,
            "average_execution_time": avg_execution_time,
            "status_distribution": status_counts,
            "performance_tiers": {
                "high_performers": high_performers,
                "medium_performers": medium_performers,
                "low_performers": low_performers
            },
            "health_status": self._calculate_overall_health(avg_success_rate, status_counts)
        }
    
    def _calculate_overall_health(self, avg_success_rate: float, status_counts: Dict[str, int]) -> str:
        """Calculate overall health status"""
        error_agents = status_counts.get("error", 0)
        total_agents = sum(status_counts.values())
        
        if error_agents > total_agents * 0.1:  # More than 10% in error
            return "unhealthy"
        elif avg_success_rate < 0.8:  # Average success rate below 80%
            return "degraded"
        elif status_counts.get("active", 0) < total_agents * 0.5:  # Less than 50% active
            return "limited"
        else:
            return "healthy"