"""
Agent Pool Core Module

This module contains the core agent creation and management functionality extracted from
tenant_scoped_agent_pool.py to reduce file length and improve maintainability.

🤖 Generated with Claude Code (CC)

Co-Authored-By: Claude <noreply@anthropic.com>
"""

import logging
from datetime import datetime
from typing import Dict, Optional, TYPE_CHECKING

# Import agent-related classes
try:
    from crewai import Agent

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False

    class Agent:
        def __init__(self, **kwargs):
            pass


if TYPE_CHECKING:
    from app.services.service_registry import ServiceRegistry

from app.services.agentic_memory.three_tier_memory_manager import ThreeTierMemoryManager
from .pool_statistics import AgentHealth

logger = logging.getLogger(__name__)


class AgentPoolCore:
    """Core functionality for agent creation and management"""

    @classmethod
    async def get_or_create_agent(
        cls,
        agent_pools: Dict,
        client_account_id: str,
        engagement_id: str,
        agent_type: str,
        context,
        service_registry: Optional["ServiceRegistry"] = None,
        db_session=None,
    ):
        """
        Get or create persistent agent for tenant with comprehensive error handling

        This method handles the complex logic of agent creation, memory initialization,
        tool assignment, and pool management.
        """
        pool_key = (client_account_id, engagement_id)

        try:
            # Initialize tenant pool if it doesn't exist
            if pool_key not in agent_pools:
                await cls.initialize_tenant_pool(
                    agent_pools, pool_key, context, db_session
                )

            tenant_pool = agent_pools[pool_key]

            # Check if agent already exists
            if agent_type in tenant_pool["agents"]:
                logger.info(
                    f"♻️ Reusing existing {agent_type} agent for tenant {client_account_id}"
                )

                agent_data = tenant_pool["agents"][agent_type]
                agent = agent_data["instance"]

                # Update usage tracking
                agent_data["last_used"] = datetime.now()
                agent_data["execution_count"] = agent_data.get("execution_count", 0) + 1
                tenant_pool["last_used"] = datetime.now()

                return agent

            # Create new agent
            logger.info(
                f"🔧 Creating new {agent_type} agent for tenant {client_account_id}"
            )

            # Create agent with memory
            agent = await cls._create_agent_with_memory(
                agent_type=agent_type,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                context=context,
                service_registry=service_registry,
                db_session=db_session,
            )

            if not agent:
                logger.error(f"❌ Failed to create {agent_type} agent")
                return None

            # Warm up agent
            await cls._warm_up_agent(agent, agent_type)

            # Store in pool
            tenant_pool["agents"][agent_type] = {
                "instance": agent,
                "created_at": datetime.now(),
                "last_used": datetime.now(),
                "execution_count": 1,
                "agent_type": agent_type,
            }

            # Update pool metadata
            tenant_pool["last_used"] = datetime.now()
            tenant_pool["total_agents"] = len(tenant_pool["agents"])

            logger.info(f"✅ Successfully created and stored {agent_type} agent")
            return agent

        except Exception as e:
            logger.error(f"❌ Agent creation failed for {agent_type}: {e}")

            # Try to clean up any partial state
            try:
                if (
                    pool_key in agent_pools
                    and agent_type in agent_pools[pool_key]["agents"]
                ):
                    del agent_pools[pool_key]["agents"][agent_type]
            except Exception as cleanup_error:
                logger.error(f"Cleanup failed: {cleanup_error}")

            return None

    @classmethod
    async def initialize_tenant_pool(
        cls, agent_pools: Dict, pool_key: tuple, context, db_session=None
    ):
        """Initialize a new tenant agent pool with memory manager"""
        client_account_id, engagement_id = pool_key

        try:
            logger.info(f"🏗️ Initializing agent pool for tenant {client_account_id}")

            # Initialize memory manager for this tenant
            memory_manager = None
            try:
                memory_manager = ThreeTierMemoryManager(
                    client_account_id=client_account_id,
                    engagement_id=engagement_id,
                )
                # Memory manager initializes synchronously in __init__, no async initialize() needed
                logger.info(
                    f"💾 Memory manager initialized for tenant {client_account_id}"
                )

            except Exception as memory_error:
                logger.warning(f"Memory manager initialization failed: {memory_error}")
                # Continue without memory - agents can still function

            # Create tenant pool structure
            agent_pools[pool_key] = {
                "client_account_id": client_account_id,
                "engagement_id": engagement_id,
                "agents": {},  # Will hold agent_type -> agent_data mappings
                "memory_manager": memory_manager,
                "created_at": datetime.now(),
                "last_used": datetime.now(),
                "total_agents": 0,
                "context": context,
            }

            logger.info(
                f"✅ Tenant pool initialized for {client_account_id} with "
                f"{'memory' if memory_manager else 'no memory'}"
            )

        except Exception as e:
            logger.error(f"❌ Tenant pool initialization failed: {e}")
            # Clean up partial initialization
            if pool_key in agent_pools:
                del agent_pools[pool_key]
            raise

    @classmethod
    async def _create_agent_with_memory(
        cls,
        agent_type: str,
        client_account_id: str,
        engagement_id: str,
        context,
        service_registry: Optional["ServiceRegistry"] = None,
        db_session=None,
    ):
        """Create agent with memory capabilities and tool integration"""
        try:
            if not CREWAI_AVAILABLE:
                logger.warning("CrewAI not available - creating placeholder agent")
                return Agent()  # Return placeholder

            # Get agent configuration
            from .agent_configuration import AgentConfiguration

            config = AgentConfiguration.get_agent_config(agent_type)

            # Extract context information
            context_info = AgentConfiguration.extract_context_info(context)
            context_info.update(
                {
                    "client_account_id": client_account_id,
                    "engagement_id": engagement_id,
                    "agent_type": agent_type,
                }
            )

            # Get tools for this agent type
            from .agent_tools import AgentToolsManager

            tools = AgentToolsManager.get_agent_tools(agent_type, context_info)

            # Create agent with configuration
            agent_params = {
                "role": config["role"],
                "goal": config["goal"],
                "backstory": config["backstory"],
                "verbose": True,
                "allow_delegation": False,  # Prevent delegation loops
                "max_iter": 3,  # Limit iterations
            }

            # Add tools if available
            if tools:
                agent_params["tools"] = tools
                logger.debug(f"Added {len(tools)} tools to {agent_type} agent")

            # Create the agent
            agent = Agent(**agent_params)

            # Add metadata for tracking
            agent._client_account_id = client_account_id
            agent._engagement_id = engagement_id
            agent._agent_type = agent_type
            agent._created_at = datetime.now()
            agent._execution_count = 0

            logger.info(f"🤖 Created {agent_type} agent with {len(tools)} tools")
            return agent

        except Exception as e:
            logger.error(f"❌ Agent creation failed for {agent_type}: {e}")
            return None

    @classmethod
    async def _warm_up_agent(cls, agent, agent_type: str):
        """Warm up agent with initial context and capabilities"""
        try:
            logger.debug(f"🔥 Warming up {agent_type} agent")

            # Set execution count if not present
            if not hasattr(agent, "_execution_count"):
                agent._execution_count = 0

            # Initialize any agent-specific warm-up logic here
            # This could include loading cached context, setting up connections, etc.

            logger.info(f"✅ {agent_type} agent warmed up and ready")

        except Exception as e:
            logger.error(f"❌ Agent warm-up failed for {agent_type}: {e}")
            # Don't raise - agent can still function without warm-up

    @classmethod
    async def check_agent_health(cls, agent) -> AgentHealth:
        """Check the health status of an agent"""
        try:
            # Basic health checks
            is_healthy = True
            error_msg = None

            if not agent:
                return AgentHealth(
                    is_healthy=False,
                    memory_status=False,
                    last_used=datetime.now(),
                    total_executions=0,
                    error_count=1,
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

            # Check execution count
            execution_count = getattr(agent, "_execution_count", 0)
            last_used = getattr(agent, "_last_used", datetime.now())

            return AgentHealth(
                is_healthy=is_healthy,
                memory_status=True,  # Assume memory is working if no errors
                last_used=last_used,
                total_executions=execution_count,
                error_count=0 if is_healthy else 1,
                error=error_msg,
            )

        except Exception as e:
            logger.error(f"❌ Agent health check failed: {e}")
            return AgentHealth(
                is_healthy=False,
                memory_status=False,
                last_used=datetime.now(),
                total_executions=0,
                error_count=1,
                error=f"Health check exception: {str(e)}",
            )
