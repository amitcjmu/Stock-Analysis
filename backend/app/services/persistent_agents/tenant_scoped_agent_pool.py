"""
Tenant-Scoped Agent Pool

Implements persistent multi-tenant agent architecture where CrewAI agents are maintained
as singletons per (client_account_id, engagement_id) tuple, enabling true agent learning
and intelligence accumulation.

This addresses ADR-015: Persistent Multi-Tenant Agent Architecture
"""

import asyncio
import logging
import threading
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.service_registry import ServiceRegistry

try:
    from crewai import Agent, Crew

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False

    class Agent:
        def __init__(self, **kwargs):
            pass

    class Crew:
        def __init__(self, **kwargs):
            pass


# Import modular components
from .agent_config import AgentConfigManager, AgentHealth
from .pool_management import PoolManager, TenantPoolStats
from .tool_manager import AgentToolManager
from .memory_monitoring import MemoryMonitoring  # noqa: F401

logger = logging.getLogger(__name__)


class TenantScopedAgentPool:
    """
    Maintains persistent agents per tenant context

    This pool ensures that agents persist across flow executions within the same
    tenant boundary, enabling memory accumulation and intelligence development.
    """

    # Class-level storage for persistent agents
    # Structure: {(client_id, engagement_id): {agent_type: agent_instance}}
    _agent_pools: Dict[Tuple[str, str], Dict[str, Agent]] = {}
    _pool_metadata: Dict[Tuple[str, str], TenantPoolStats] = {}
    _agent_metadata: Dict[int, Dict[str, Any]] = {}  # Store metadata by agent ID
    _pool_lock = asyncio.Lock()  # Thread safety for agent pool access

    # Memory monitoring and cleanup scheduling
    _cleanup_scheduler: Optional[threading.Timer] = None
    _memory_threshold_mb: float = 1000.0  # 1GB memory threshold
    _cleanup_interval_minutes: int = 30  # Cleanup every 30 minutes
    _max_idle_hours: int = 24  # Remove agents idle for 24+ hours

    @classmethod
    async def get_agent(
        cls,
        context: Any,  # RequestContext
        agent_type: str,
        force_recreate: bool = False,
        service_registry: Optional["ServiceRegistry"] = None,
    ) -> Agent:
        """
        Convenience method to get agent using RequestContext.

        Args:
            context: RequestContext with client_account_id and engagement_id
            agent_type: Type of agent (data_analyst, field_mapper, etc.)
            force_recreate: Force recreation of agent
            service_registry: Optional service registry

        Returns:
            Persistent CrewAI agent instance
        """
        # Extract IDs from context
        client_id = (
            str(context.client_account_id)
            if hasattr(context, "client_account_id")
            else None
        )
        engagement_id = (
            str(context.engagement_id) if hasattr(context, "engagement_id") else None
        )

        if not client_id or not engagement_id:
            logger.warning(
                f"Missing context info: client_id={client_id}, engagement_id={engagement_id}"
            )
            # Fallback to basic agent creation
            return await cls._create_basic_agent(agent_type)

        return await cls.get_or_create_agent(
            client_id,
            engagement_id,
            agent_type,
            force_recreate,
            {"service_registry": service_registry},
        )

    @classmethod
    async def get_or_create_agent(
        cls,
        client_id: str,
        engagement_id: str,
        agent_type: str,
        force_recreate: bool = False,
        context_info: Optional[Dict[str, Any]] = None,
    ) -> Agent:
        """
        Get or create a persistent agent for the tenant context.

        Args:
            client_id: Client account identifier
            engagement_id: Engagement identifier
            agent_type: Type of agent to retrieve/create
            force_recreate: Force recreation of agent even if exists
            context_info: Additional context information

        Returns:
            Persistent CrewAI agent instance
        """
        pool_key = (client_id, engagement_id)

        async with cls._pool_lock:
            # Check if agent exists and is not being force recreated
            if not force_recreate and pool_key in cls._agent_pools:
                agent_pool = cls._agent_pools[pool_key]
                if agent_type in agent_pool:
                    agent = agent_pool[agent_type]

                    # Update statistics
                    PoolManager.update_pool_stats(
                        client_id,
                        engagement_id,
                        len(agent_pool),
                        increment_requests=True,
                    )

                    logger.info(
                        f"Retrieved existing {agent_type} agent for client {client_id}, "
                        f"engagement {engagement_id}"
                    )
                    return agent

            # Create new agent
            context_info = context_info or {}
            context_info.update(
                {
                    "client_account_id": client_id,
                    "engagement_id": engagement_id,
                    "flow_id": context_info.get("flow_id", str(uuid.uuid4())),
                }
            )

            try:
                agent = await AgentConfigManager.create_agent_with_memory(
                    agent_type, client_id, engagement_id, context_info
                )

                # Initialize pool if doesn't exist
                if pool_key not in cls._agent_pools:
                    cls._agent_pools[pool_key] = {}
                    await cls.initialize_tenant_pool(client_id, engagement_id)

                # Store agent in pool
                cls._agent_pools[pool_key][agent_type] = agent

                # Update statistics
                agent_count = len(cls._agent_pools[pool_key])
                PoolManager.update_pool_stats(client_id, engagement_id, agent_count)

                logger.info(
                    f"Created new {agent_type} agent for client {client_id}, "
                    f"engagement {engagement_id}"
                )
                return agent

            except Exception as e:
                # Update error statistics
                PoolManager.update_pool_stats(
                    client_id, engagement_id, increment_errors=True
                )
                logger.error(
                    f"Failed to create {agent_type} agent for client {client_id}, "
                    f"engagement {engagement_id}: {e}"
                )
                raise

    @classmethod
    async def initialize_tenant_pool(cls, client_id: str, engagement_id: str) -> None:
        """Initialize a new tenant pool with metadata."""
        pool_key = (client_id, engagement_id)

        try:
            # Initialize pool metadata
            cls._pool_metadata[pool_key] = TenantPoolStats(
                client_account_id=client_id,
                engagement_id=engagement_id,
                agent_count=0,
                last_activity=datetime.now(),
                memory_usage=0.0,
                total_requests=0,
                error_count=0,
            )

            # Start cleanup scheduler if not already running
            cls._schedule_cleanup()

            logger.info(
                f"Initialized tenant pool for client {client_id}, engagement {engagement_id}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize tenant pool: {e}")
            raise

    @classmethod
    async def _create_basic_agent(cls, agent_type: str) -> Agent:
        """Create a basic agent without persistence for fallback scenarios."""
        try:
            if not CREWAI_AVAILABLE:
                return Agent()

            config = AgentConfigManager.get_agent_config(agent_type)
            tools = AgentToolManager.get_agent_tools(agent_type, {})

            agent = Agent(
                role=config["role"],
                goal=config["goal"],
                backstory=config["backstory"],
                tools=tools,
                verbose=config.get("verbose", True),
                allow_delegation=config.get("allow_delegation", False),
            )

            logger.warning(f"Created basic (non-persistent) {agent_type} agent")
            return agent

        except Exception as e:
            logger.error(f"Failed to create basic agent: {e}")
            return Agent()

    @classmethod
    def _schedule_cleanup(cls):
        """Schedule automatic cleanup of idle pools."""
        if cls._cleanup_scheduler and cls._cleanup_scheduler.is_alive():
            return  # Already scheduled

        def cleanup_task():
            try:
                # Run async cleanup
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    PoolManager.cleanup_idle_pools(cls._max_idle_hours)
                )
                loop.close()
            except Exception as e:
                logger.error(f"Cleanup task failed: {e}")
            finally:
                # Reschedule
                cls._cleanup_scheduler = threading.Timer(
                    cls._cleanup_interval_minutes * 60, cleanup_task
                )
                cls._cleanup_scheduler.daemon = True
                cls._cleanup_scheduler.start()

        cls._cleanup_scheduler = threading.Timer(
            cls._cleanup_interval_minutes * 60, cleanup_task
        )
        cls._cleanup_scheduler.daemon = True
        cls._cleanup_scheduler.start()

    # Delegate methods to modular components
    @classmethod
    async def get_pool_statistics(cls) -> List[TenantPoolStats]:
        """Get statistics for all tenant pools."""
        return await PoolManager.get_pool_statistics()

    @classmethod
    async def cleanup_idle_pools(cls, max_idle_hours: int = 24):
        """Clean up idle tenant pools that haven't been used recently."""
        return await PoolManager.cleanup_idle_pools(max_idle_hours)

    @classmethod
    def start_memory_monitoring(cls):
        """Start memory monitoring for the agent pool."""
        return PoolManager.start_memory_monitoring()

    @classmethod
    def stop_memory_monitoring(cls):
        """Stop memory monitoring for the agent pool."""
        return PoolManager.stop_memory_monitoring()

    # Backward compatibility methods
    @classmethod
    def _extract_context_info(
        cls, context_info: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[str], Optional["ServiceRegistry"]]:
        """Extract context info - delegate to tool manager."""
        return AgentToolManager.extract_context_info(context_info)

    @classmethod
    def _get_agent_tools(
        cls, agent_type: str, context_info: Dict[str, Any]
    ) -> List[Any]:
        """Get agent tools - delegate to tool manager."""
        return AgentToolManager.get_agent_tools(agent_type, context_info)

    @classmethod
    def _get_agent_config(cls, agent_type: str) -> Dict[str, Any]:
        """Get agent config - delegate to config manager."""
        return AgentConfigManager.get_agent_config(agent_type)

    @classmethod
    async def _create_agent_with_memory(
        cls,
        agent_type: str,
        client_account_id: str,
        engagement_id: str,
        context_info: Dict[str, Any],
    ) -> Agent:
        """Create agent with memory - delegate to config manager."""
        return await AgentConfigManager.create_agent_with_memory(
            agent_type, client_account_id, engagement_id, context_info
        )

    @classmethod
    async def _check_agent_health(cls, agent: Agent) -> AgentHealth:
        """Check agent health - delegate to config manager."""
        return await AgentConfigManager.check_agent_health(agent)


# Deprecated function for backward compatibility
async def validate_agent_pool_health_deprecated(
    client_account_id: str, engagement_id: str
) -> Dict[str, Any]:
    """
    Deprecated health validation function.

    Use TenantScopedAgentPool.get_pool_statistics() instead.
    """
    logger.warning("validate_agent_pool_health_deprecated is deprecated")
    try:
        stats = await PoolManager.get_pool_statistics()
        for stat in stats:
            if (
                stat.client_account_id == client_account_id
                and stat.engagement_id == engagement_id
            ):
                return {
                    "healthy": stat.error_count == 0,
                    "agent_count": stat.agent_count,
                    "last_activity": stat.last_activity,
                    "memory_usage": stat.memory_usage,
                }

        return {
            "healthy": True,
            "agent_count": 0,
            "last_activity": datetime.now(),
            "memory_usage": 0.0,
        }

    except Exception as e:
        logger.error(f"Health validation failed: {e}")
        return {"healthy": False, "error": str(e)}
