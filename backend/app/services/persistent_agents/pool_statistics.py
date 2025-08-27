"""
Pool Statistics Module

This module contains pool statistics functionality extracted from
tenant_scoped_agent_pool.py to reduce file length and improve maintainability.

🤖 Generated with Claude Code (CC)

Co-Authored-By: Claude <noreply@anthropic.com>
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class AgentHealth:
    """Agent health status information"""

    healthy: bool
    last_execution: datetime
    execution_count: int
    memory_status: str
    error: str = None


@dataclass
class TenantPoolStats:
    """Statistics for a tenant's agent pool"""

    client_account_id: str
    engagement_id: str
    agent_count: int
    total_executions: int
    last_used: datetime
    memory_manager: str
    agents: Dict[str, Any]


class PoolStatistics:
    """Handles pool statistics and health monitoring"""

    @classmethod
    async def get_pool_statistics(cls, agent_pools: Dict) -> List[TenantPoolStats]:
        """Get statistics for all agent pools"""
        stats = []

        for (client_account_id, engagement_id), pool_data in agent_pools.items():
            agents = pool_data.get("agents", {})

            # Calculate total executions across all agents
            total_executions = sum(
                agent_data.get("execution_count", 0) for agent_data in agents.values()
            )

            stat = TenantPoolStats(
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                agent_count=len(agents),
                total_executions=total_executions,
                last_used=pool_data.get("last_used", datetime.now()),
                memory_manager=pool_data.get("memory_manager", "unknown"),
                agents=agents,
            )
            stats.append(stat)

        return stats

    @classmethod
    async def check_agent_health(cls, agent) -> AgentHealth:
        """Check the health status of an agent with comprehensive diagnostics"""
        try:
            # Basic health checks
            is_healthy = True
            error_msg = None
            memory_status = "unknown"

            if not agent:
                return AgentHealth(
                    healthy=False,
                    last_execution=datetime.now(),
                    execution_count=0,
                    memory_status="agent_missing",
                    error="Agent instance is None",
                )

            # Check if agent has required attributes
            required_attrs = ["role", "goal", "backstory"]
            missing_attrs = []

            for attr in required_attrs:
                if not hasattr(agent, attr) or not getattr(agent, attr):
                    missing_attrs.append(attr)

            if missing_attrs:
                is_healthy = False
                error_msg = f"Missing required attributes: {', '.join(missing_attrs)}"

            # Check memory status if available
            try:
                if hasattr(agent, "_memory") and agent._memory:
                    memory_status = "active"
                elif hasattr(agent, "memory") and agent.memory:
                    memory_status = "active"
                else:
                    memory_status = "not_initialized"
                    # This is a warning, not an error
                    logger.debug(
                        f"Agent {getattr(agent, 'role', 'unknown')} has no memory initialized"
                    )
            except Exception as memory_error:
                memory_status = "error"
                logger.warning(f"Memory check failed for agent: {memory_error}")

            # Try to access basic agent properties
            try:
                _ = agent.role
                _ = agent.goal
                _ = agent.backstory
            except Exception as prop_error:
                is_healthy = False
                error_msg = f"Agent property access failed: {prop_error}"

            return AgentHealth(
                healthy=is_healthy,
                last_execution=datetime.now(),
                execution_count=getattr(agent, "_execution_count", 0),
                memory_status=memory_status,
                error=error_msg,
            )

        except Exception as e:
            logger.error(f"❌ Agent health check failed: {e}")
            return AgentHealth(
                healthy=False,
                last_execution=datetime.now(),
                execution_count=0,
                memory_status="error",
                error=f"Health check exception: {str(e)}",
            )
