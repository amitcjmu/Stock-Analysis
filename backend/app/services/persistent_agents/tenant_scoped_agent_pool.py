"""
Tenant-Scoped Agent Pool

Implements persistent multi-tenant agent architecture where CrewAI agents are maintained
as singletons per (client_account_id, engagement_id) tuple, enabling true agent learning
and intelligence accumulation.

This addresses ADR-015: Persistent Multi-Tenant Agent Architecture
"""

import asyncio
import atexit
import logging
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

# Make psutil optional - not critical for core functionality
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.getLogger(__name__).warning(
        "psutil not available - memory monitoring disabled. Install with: pip install psutil"
    )

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


from app.services.agentic_memory.three_tier_memory_manager import ThreeTierMemoryManager

# Move all tool imports to module level to avoid per-call dynamic imports
# This improves performance and avoids repeated import overhead
try:
    from app.services.crewai_flows.tools.asset_creation_tool import (
        create_asset_creation_tools,
    )
    from app.services.crewai_flows.tools.task_completion_tools import (
        create_task_completion_tools,
    )
    from app.services.crewai_flows.tools.data_validation_tool import (
        create_data_validation_tools,
    )
    from app.services.crewai_flows.tools.critical_attributes_tool import (
        create_critical_attributes_tools,
    )
    from app.services.crewai_flows.tools.dependency_analysis_tool import (
        create_dependency_analysis_tools,
    )
    from app.services.crewai_flows.tools.mapping_confidence_tool import (
        MappingConfidenceTool,
    )
    from app.services.tools.asset_intelligence_tools import (
        get_asset_intelligence_tools,
    )

    TOOLS_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Some tools not available: {e}")
    TOOLS_AVAILABLE = False
    # Define placeholders for missing imports
    create_asset_creation_tools = None
    create_task_completion_tools = None
    create_data_validation_tools = None
    create_critical_attributes_tools = None
    create_dependency_analysis_tools = None
    MappingConfidenceTool = None
    get_asset_intelligence_tools = None

logger = logging.getLogger(__name__)


@dataclass
class AgentHealth:
    """Health status of a persistent agent"""

    is_healthy: bool
    memory_status: bool = True
    last_used: Optional[datetime] = None
    total_executions: int = 0
    error_count: int = 0
    error: Optional[str] = None


@dataclass
class TenantPoolStats:
    """Statistics for a tenant agent pool"""

    tenant_key: Tuple[str, str]
    agent_count: int
    total_executions: int
    creation_time: datetime
    last_activity: Optional[datetime]
    memory_usage_mb: float = 0.0


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
    async def get_or_create_agent(
        cls,
        client_id: str,
        engagement_id: str,
        agent_type: str,
        force_recreate: bool = False,
        service_registry: Optional["ServiceRegistry"] = None,
    ) -> Agent:
        """
        Get existing agent or create new one with full memory integration

        Args:
            client_id: Client account identifier
            engagement_id: Engagement identifier
            agent_type: Type of agent (data_analyst, field_mapper, etc.)
            force_recreate: Force recreation of agent (for testing/recovery)

        Returns:
            Persistent CrewAI agent instance
        """
        if not CREWAI_AVAILABLE:
            raise RuntimeError(
                "CrewAI is not available - cannot create persistent agents"
            )

        async with cls._pool_lock:
            tenant_key = (client_id, engagement_id)

            # Initialize tenant pool if it doesn't exist
            if tenant_key not in cls._agent_pools:
                cls._agent_pools[tenant_key] = {}
                cls._pool_metadata[tenant_key] = TenantPoolStats(
                    tenant_key=tenant_key,
                    agent_count=0,
                    total_executions=0,
                    creation_time=datetime.utcnow(),
                    last_activity=None,  # Will be updated when agents are used
                )
                logger.info(
                    f"🆕 Created new agent pool for tenant: {client_id}/{engagement_id}"
                )

            # Check if agent already exists and is healthy (unless force_recreate)
            if not force_recreate and agent_type in cls._agent_pools[tenant_key]:

                existing_agent = cls._agent_pools[tenant_key][agent_type]
                health = await cls._check_agent_health(existing_agent)

                if health.is_healthy:
                    # Update usage stats in metadata
                    agent_id = id(existing_agent)
                    if (
                        hasattr(cls, "_agent_metadata")
                        and agent_id in cls._agent_metadata
                    ):
                        cls._agent_metadata[agent_id]["execution_count"] += 1
                        cls._agent_metadata[agent_id][
                            "last_execution"
                        ] = datetime.utcnow()

                    cls._pool_metadata[tenant_key].last_activity = datetime.utcnow()
                    cls._pool_metadata[tenant_key].total_executions += 1

                    logger.info(
                        f"🔄 Reusing healthy persistent agent: {agent_type} for {client_id}/{engagement_id}"
                    )
                    return existing_agent
                else:
                    logger.warning(
                        f"⚠️ Existing agent unhealthy, recreating: {health.error}"
                    )

            # Create new agent with memory integration
            logger.info(
                f"🛠️ Creating new persistent agent: {agent_type} for {client_id}/{engagement_id}"
            )

            try:
                # Initialize memory manager for this tenant
                memory_manager = ThreeTierMemoryManager(
                    client_account_id=uuid.UUID(client_id),
                    engagement_id=uuid.UUID(engagement_id),
                )

                # Create agent with memory enabled and ServiceRegistry if available
                agent = await cls._create_agent_with_memory(
                    agent_type, memory_manager, service_registry=service_registry
                )

                # Store in pool
                cls._agent_pools[tenant_key][agent_type] = agent

                # Update metadata
                cls._pool_metadata[tenant_key].agent_count = len(
                    cls._agent_pools[tenant_key]
                )
                cls._pool_metadata[tenant_key].last_activity = datetime.utcnow()

                logger.info(
                    f"✅ Created and cached persistent agent: {agent_type} for {client_id}/{engagement_id}"
                )
                return agent

            except Exception as e:
                logger.error(f"❌ Failed to create persistent agent {agent_type}: {e}")
                raise

    @classmethod
    async def initialize_tenant_pool(
        cls,
        client_id: str,
        engagement_id: str,
        service_registry: Optional["ServiceRegistry"] = None,
    ) -> Dict[str, Agent]:
        """
        Pre-initialize common agents for a tenant with optional ServiceRegistry support

        Args:
            client_id: Client account identifier
            engagement_id: Engagement identifier
            service_registry: Optional ServiceRegistry for tool management

        Returns:
            Dictionary of initialized agents by type
        """
        logger.info(f"🚀 Initializing tenant pool for: {client_id}/{engagement_id}")

        # Define required agents for discovery flows
        required_agents = [
            "data_analyst",
            "field_mapper",
            "quality_assessor",
            "business_value_analyst",
            "risk_assessment_agent",
            "pattern_discovery_agent",
        ]

        pool = {}
        initialization_errors = []

        for agent_type in required_agents:
            try:
                agent = await cls.get_or_create_agent(
                    client_id,
                    engagement_id,
                    agent_type,
                    service_registry=service_registry,
                )
                await cls._warm_up_agent(agent, agent_type)
                pool[agent_type] = agent
                logger.info(f"   ✅ {agent_type} initialized and warmed up")

            except Exception as e:
                error_msg = f"Failed to initialize {agent_type}: {e}"
                logger.error(f"   ❌ {error_msg}")
                initialization_errors.append(error_msg)

        if initialization_errors:
            logger.warning(
                f"⚠️ Tenant pool initialization completed with {len(initialization_errors)} errors"
            )
            for error in initialization_errors:
                logger.warning(f"   - {error}")
        else:
            logger.info(f"✅ Tenant pool fully initialized with {len(pool)} agents")

        return pool

    @classmethod
    async def _create_agent_with_memory(
        cls,
        agent_type: str,
        memory_manager: ThreeTierMemoryManager,
        service_registry: Optional["ServiceRegistry"] = None,
    ) -> Agent:
        """
        Create agent with memory bugs fixed and full memory integration

        Args:
            agent_type: Type of agent to create
            memory_manager: Three-tier memory manager instance

        Returns:
            CrewAI agent with memory enabled
        """
        # Get agent configuration
        agent_config = cls._get_agent_config(agent_type)

        # Get tools for this agent type with ServiceRegistry if available
        tools = cls._get_agent_tools(agent_type, memory_manager, service_registry)

        # Fix 1: Resolve API compatibility issues with proper config
        memory_config = {
            "provider": "DeepInfra",
            "config": {
                "response_format": "fixed",  # Fix APIStatusError
                "timeout": 30,
                "max_retries": 3,
            },
        }

        # Fix 2: Create agent with memory enabled and proper error handling
        try:
            agent = Agent(
                role=agent_config["role"],
                goal=agent_config["goal"],
                backstory=agent_config["backstory"],
                memory=True,  # Re-enable memory
                memory_config=memory_config,
                tools=tools,  # Use the actual tools instead of empty array
                allow_delegation=False,  # Performance optimization
                max_iter=1,  # Single iteration for performance
                verbose=False,  # Reduce noise
            )

            # Fix 3: Store memory manager and metadata separately
            # CrewAI Agent doesn't support custom attributes, so we store them externally

            # Store agent metadata separately since we can't add attributes to CrewAI Agent
            agent_id = id(agent)
            cls._agent_metadata[agent_id] = {
                "memory_manager": memory_manager,
                "agent_type": agent_type,
                "creation_time": datetime.utcnow(),
                "execution_count": 0,
                "last_execution": None,
            }

            logger.info(f"🧠 Agent {agent_type} created with memory enabled")
            return agent

        except Exception as e:
            logger.error(f"❌ Failed to create agent {agent_type}: {e}")
            raise

    @classmethod
    async def _warm_up_agent(cls, agent: Agent, agent_type: str):
        """
        Warm up agent by loading memory and preparing for execution

        Args:
            agent: Agent instance to warm up
            agent_type: Type of agent for context
        """
        try:
            # Get agent metadata
            agent_id = id(agent)
            if hasattr(cls, "_agent_metadata") and agent_id in cls._agent_metadata:
                metadata = cls._agent_metadata[agent_id]

                # Load persistent patterns from memory if available
                if metadata.get("memory_manager"):
                    logger.info(f"🔥 Warming up {agent_type} - loading memory patterns")
                    # TODO: Implement actual memory loading when memory manager supports it

                # Update warm-up status
                metadata["warmed_up"] = True
                metadata["warm_up_time"] = datetime.utcnow()

            logger.info(f"✅ Agent {agent_type} warmed up successfully")

        except Exception as e:
            logger.warning(f"⚠️ Failed to warm up agent {agent_type}: {e}")
            # Don't fail - agent can still function without warm-up

    @classmethod
    async def _check_agent_health(cls, agent: Agent) -> AgentHealth:
        """
        Check health status of a persistent agent

        Args:
            agent: Agent instance to check

        Returns:
            AgentHealth status object
        """
        try:
            # Basic health checks
            is_healthy = True
            error = None
            last_used = None
            execution_count = 0

            # Get agent metadata
            agent_id = id(agent)
            metadata = None
            if hasattr(cls, "_agent_metadata") and agent_id in cls._agent_metadata:
                metadata = cls._agent_metadata[agent_id]

                # Check 1: Agent has metadata
                if not metadata.get("agent_type"):
                    is_healthy = False
                    error = "Agent missing type metadata"

                # Check 2: Memory system health
                memory_status = bool(metadata.get("memory_manager"))

                # Check 3: Recent activity (agents idle >24h might need refresh)
                last_used = metadata.get("last_execution")
                if last_used and (datetime.utcnow() - last_used).days > 1:
                    logger.info("⏰ Agent has been idle for >24h")

                execution_count = metadata.get("execution_count", 0)
            else:
                is_healthy = False
                error = "Agent metadata not found"
                memory_status = False

            return AgentHealth(
                is_healthy=is_healthy,
                memory_status=memory_status,
                last_used=last_used,
                total_executions=execution_count,
                error=error,
            )

        except Exception as e:
            return AgentHealth(is_healthy=False, error=f"Health check failed: {e}")

    @classmethod
    def _extract_context_info(
        cls, memory_manager: ThreeTierMemoryManager
    ) -> Dict[str, Any]:
        """Extract context information from memory manager."""
        return {
            "client_account_id": (
                str(memory_manager.client_account_id)
                if hasattr(memory_manager, "client_account_id")
                else None
            ),
            "engagement_id": (
                str(memory_manager.engagement_id)
                if hasattr(memory_manager, "engagement_id")
                else None
            ),
        }

    @classmethod
    def _add_tools_with_registry(
        cls,
        agent_type: str,
        context_info: Dict[str, Any],
        service_registry: "ServiceRegistry",
        tools: List,
    ) -> None:
        """Add tools using ServiceRegistry pattern."""
        if not TOOLS_AVAILABLE:
            logger.warning(f"Tools not available at module level for {agent_type}")
            return

        # Asset creation tools for specific agents
        if agent_type in [
            "data_analyst",
            "pattern_discovery_agent",
            "field_mapper",
            "quality_assessor",
        ]:
            if create_asset_creation_tools:
                asset_tools = create_asset_creation_tools(
                    context_info, registry=service_registry
                )
                if isinstance(asset_tools, list):
                    tools.extend(asset_tools)
                    logger.info(
                        f"Added {len(asset_tools)} asset creation tools via ServiceRegistry"
                    )

        # Task completion tools (common)
        if create_task_completion_tools:
            cls._safe_extend_tools(
                tools,
                lambda: create_task_completion_tools(context_info),
                "task completion tools",
            )

        # Agent-specific tool additions
        cls._add_agent_specific_tools(agent_type, context_info, tools)

    @classmethod
    def _add_agent_specific_tools(
        cls,
        agent_type: str,
        context_info: Dict[str, Any],
        tools: List,
    ) -> None:
        """Add tools specific to each agent type."""
        if agent_type in ["data_analyst", "pattern_discovery_agent"]:
            if create_data_validation_tools:
                cls._safe_extend_tools(
                    tools,
                    lambda: create_data_validation_tools(context_info),
                    "data validation tools",
                )
            if (
                agent_type == "pattern_discovery_agent"
                and create_dependency_analysis_tools
            ):
                cls._safe_extend_tools(
                    tools,
                    lambda: create_dependency_analysis_tools(context_info),
                    "dependency analysis tools",
                )

        elif agent_type == "field_mapper":
            if create_critical_attributes_tools:
                cls._safe_extend_tools(
                    tools,
                    lambda: create_critical_attributes_tools(context_info),
                    "critical attributes tools",
                )

        elif agent_type in ["business_value_analyst", "risk_assessment_agent"]:
            if create_dependency_analysis_tools:
                cls._safe_extend_tools(
                    tools,
                    lambda: create_dependency_analysis_tools(context_info),
                    "dependency analysis tools",
                )

    @classmethod
    def _add_legacy_tools(
        cls,
        agent_type: str,
        context_info: Dict[str, Any],
        tools: List,
    ) -> None:
        """Add tools using legacy pattern (without ServiceRegistry)."""
        if not TOOLS_AVAILABLE:
            logger.warning(f"Tools not available at module level for {agent_type}")
            return

        # Common tools
        if create_task_completion_tools:
            cls._safe_extend_tools(
                tools,
                lambda: create_task_completion_tools(context_info),
                "task completion tools",
            )

        # Agent-specific tool loading
        if agent_type in ["data_analyst", "pattern_discovery_agent"]:
            cls._add_data_analysis_tools(agent_type, context_info, tools)
        elif agent_type == "quality_assessor":
            cls._add_quality_tools(context_info, tools)
        elif agent_type in ["business_value_analyst", "risk_assessment_agent"]:
            cls._add_business_analysis_tools(context_info, tools)
        elif agent_type == "field_mapper":
            cls._add_field_mapper_tools(context_info, tools)

    @classmethod
    def _add_data_analysis_tools(
        cls,
        agent_type: str,
        context_info: Dict[str, Any],
        tools: List,
    ) -> None:
        """Add tools for data analysis agents."""
        if create_data_validation_tools:
            cls._safe_extend_tools(
                tools,
                lambda: create_data_validation_tools(context_info),
                "data validation tools",
            )
        if create_asset_creation_tools:
            cls._safe_extend_tools(
                tools,
                lambda: create_asset_creation_tools(context_info),
                "asset creation tools",
            )
        if get_asset_intelligence_tools:
            cls._safe_extend_tools(
                tools,
                lambda: get_asset_intelligence_tools(),
                "asset intelligence tools",
            )
        if agent_type == "pattern_discovery_agent" and create_dependency_analysis_tools:
            cls._safe_extend_tools(
                tools,
                lambda: create_dependency_analysis_tools(context_info),
                "dependency analysis tools",
            )

    @classmethod
    def _add_quality_tools(cls, context_info: Dict[str, Any], tools: List) -> None:
        """Add tools for quality assessor agent."""
        if get_asset_intelligence_tools:
            cls._safe_extend_tools(
                tools,
                lambda: get_asset_intelligence_tools(),
                "asset intelligence tools",
            )

    @classmethod
    def _add_business_analysis_tools(
        cls, context_info: Dict[str, Any], tools: List
    ) -> None:
        """Add tools for business analysis agents."""
        if get_asset_intelligence_tools:
            cls._safe_extend_tools(
                tools,
                lambda: get_asset_intelligence_tools(),
                "asset intelligence tools",
            )
        if create_dependency_analysis_tools:
            cls._safe_extend_tools(
                tools,
                lambda: create_dependency_analysis_tools(context_info),
                "dependency analysis tools",
            )

    @classmethod
    def _add_field_mapper_tools(cls, context_info: Dict[str, Any], tools: List) -> None:
        """Add tools for field mapper agent."""
        if MappingConfidenceTool:
            try:
                mapping_tool = MappingConfidenceTool()
                tools.append(mapping_tool)
            except Exception as e:
                logger.debug(f"Failed to create MappingConfidenceTool: {e}")

        if create_critical_attributes_tools:
            try:
                critical_tools = create_critical_attributes_tools(context_info)
                if isinstance(critical_tools, list):
                    tools.extend(critical_tools)
                else:
                    logger.warning("Critical attributes tools returned non-list")
            except Exception as e:
                logger.warning(f"Failed to load critical attributes tools: {e}")

    @classmethod
    def _safe_extend_tools(cls, tools: List, getter, tool_name: str = "tools") -> int:
        """Safely extend tools list with error handling."""
        try:
            result = getter()
            if isinstance(result, list):
                tools.extend(result)
                return len(result)
            else:
                logger.warning(f"{tool_name} returned non-list type: {type(result)}")
                return 0
        except Exception as e:
            logger.debug(f"Skipping {tool_name} due to error: {e}")
            return 0

    @classmethod
    def _get_agent_tools(
        cls,
        agent_type: str,
        memory_manager: ThreeTierMemoryManager,
        service_registry: Optional["ServiceRegistry"] = None,
    ) -> List:
        """
        Get tools for different agent types with optional ServiceRegistry support

        Args:
            agent_type: Type of agent
            memory_manager: Memory manager for context
            service_registry: Optional ServiceRegistry for centralized tool management

        Returns:
            List of CrewAI tools for the agent
        """
        try:
            context_info = cls._extract_context_info(memory_manager)
            context_info["agent_type"] = agent_type
            tools = []

            if service_registry:
                logger.info(f"Using ServiceRegistry for {agent_type} tools")
                cls._add_tools_with_registry(
                    agent_type, context_info, service_registry, tools
                )
            else:
                logger.info(f"Using legacy tool creation for {agent_type}")
                logger.warning(
                    f"ServiceRegistry not provided for {agent_type} tools - using legacy pattern. "
                    f"Consider enabling USE_SERVICE_REGISTRY=true for better performance."
                )
                cls._add_legacy_tools(agent_type, context_info, tools)

            logger.info(f"✅ Loaded {len(tools)} tools for {agent_type} agent")
            return tools

        except Exception as e:
            logger.error(f"❌ Failed to load tools for {agent_type}: {e}")
            return []

    @classmethod
    def _get_agent_config(cls, agent_type: str) -> Dict[str, Any]:
        """
        Get configuration for different agent types

        Args:
            agent_type: Type of agent

        Returns:
            Agent configuration dictionary
        """
        agent_configs = {
            "data_analyst": {
                "role": "Senior Data Analyst",
                "goal": "Analyze and validate data quality with expertise that improves over time",
                "backstory": "You are a senior data analyst with deep expertise in data validation, "
                "quality assessment, and pattern recognition. You learn from each analysis "
                "to improve future recommendations and build client-specific expertise.",
                "tools": [],
            },
            "field_mapper": {
                "role": "Expert Field Mapping Specialist",
                "goal": "Create accurate field mappings with increasing precision through experience",
                "backstory": "You specialize in field mapping and data transformation. You remember "
                "successful mapping patterns and adapt your recommendations based on "
                "client-specific data structures and business contexts.",
                "tools": [],
            },
            "quality_assessor": {
                "role": "Data Quality Assessment Expert",
                "goal": "Assess data quality and provide improvement recommendations",
                "backstory": "You are an expert in data quality assessment with the ability to "
                "identify patterns and build client-specific quality frameworks that "
                "improve over multiple engagements.",
                "tools": [],
            },
            "business_value_analyst": {
                "role": "Business Value Analysis Specialist",
                "goal": "Analyze business value and ROI with accumulating domain expertise",
                "backstory": "You specialize in business value analysis and have developed expertise "
                "in various industries. Your recommendations improve as you learn "
                "client-specific business contexts and successful value patterns.",
                "tools": [],
            },
            "risk_assessment_agent": {
                "role": "Risk Assessment and Mitigation Expert",
                "goal": "Identify risks and develop mitigation strategies with learned expertise",
                "backstory": "You are a risk assessment expert who builds knowledge of client-specific "
                "risk patterns and develops increasingly sophisticated mitigation strategies "
                "based on past successful implementations.",
                "tools": [],
            },
            "pattern_discovery_agent": {
                "role": "Pattern Discovery and Learning Specialist",
                "goal": "Discover patterns in data and processes with evolving recognition capabilities",
                "backstory": "You specialize in discovering patterns across data, processes, and "
                "business contexts. Your pattern recognition improves with each engagement "
                "as you build a comprehensive understanding of client environments.",
                "tools": [],
            },
        }

        if agent_type not in agent_configs:
            logger.warning(f"⚠️ Unknown agent type: {agent_type}, using generic config")
            return {
                "role": f"Generic {agent_type.replace('_', ' ').title()}",
                "goal": f"Perform {agent_type} tasks with learning capabilities",
                "backstory": f"You are a specialized {agent_type} agent with memory and learning capabilities.",
                "tools": [],
            }

        return agent_configs[agent_type]

    @classmethod
    async def get_pool_statistics(cls) -> List[TenantPoolStats]:
        """
        Get statistics for all tenant pools

        Returns:
            List of tenant pool statistics
        """
        async with cls._pool_lock:
            return list(cls._pool_metadata.values())

    @classmethod
    async def cleanup_idle_pools(cls, max_idle_hours: int = 24):
        """
        Clean up idle agent pools to free memory

        Args:
            max_idle_hours: Maximum hours of inactivity before cleanup
        """
        cleanup_count = 0
        cutoff_time = datetime.utcnow() - timedelta(hours=max_idle_hours)

        async with cls._pool_lock:
            pools_to_remove = []

            for tenant_key, stats in cls._pool_metadata.items():
                if stats.last_activity and stats.last_activity < cutoff_time:
                    pools_to_remove.append(tenant_key)

            for tenant_key in pools_to_remove:
                # Clean up agent pool
                if tenant_key in cls._agent_pools:
                    agent_count = len(cls._agent_pools[tenant_key])
                    del cls._agent_pools[tenant_key]
                    del cls._pool_metadata[tenant_key]
                    cleanup_count += agent_count

                    logger.info(
                        f"🧹 Cleaned up idle pool: {tenant_key[0]}/{tenant_key[1]} ({agent_count} agents)"
                    )

        if cleanup_count > 0:
            logger.info(f"✅ Cleanup completed: removed {cleanup_count} idle agents")

        return cleanup_count

    @classmethod
    def _get_current_memory_usage(cls) -> float:
        """Get current memory usage in MB"""
        if not PSUTIL_AVAILABLE:
            # Return 0 if psutil is not available
            return 0.0
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            return memory_info.rss / (1024 * 1024)  # Convert to MB
        except Exception as e:
            logger.warning(f"⚠️ Failed to get memory usage: {e}")
            return 0.0

    @classmethod
    def _schedule_automatic_cleanup(cls):
        """Schedule automatic cleanup to run periodically"""

        def run_cleanup():
            try:
                # Check memory usage
                current_memory = cls._get_current_memory_usage()
                pool_count = len(cls._agent_pools)

                # Skip memory-based cleanup if psutil is not available
                if PSUTIL_AVAILABLE:
                    logger.info(
                        f"🔍 Memory check: {current_memory:.1f}MB, {pool_count} pools"
                    )
                else:
                    logger.info(
                        f"🔍 Pool check: {pool_count} pools (memory monitoring disabled)"
                    )

                # Trigger cleanup if memory threshold exceeded or routine maintenance
                # Without psutil, only use pool count for cleanup decision
                should_cleanup = (
                    PSUTIL_AVAILABLE and current_memory > cls._memory_threshold_mb
                ) or pool_count > 50
                if should_cleanup:
                    logger.info(
                        f"🧹 Triggering cleanup - Memory: {current_memory:.1f}MB"
                    )
                    # Run cleanup in thread-safe manner
                    loop = None
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                    if loop:
                        loop.create_task(cls.cleanup_idle_pools(cls._max_idle_hours))
                        # Don't wait for completion to avoid blocking

                # Schedule next cleanup
                cls._cleanup_scheduler = threading.Timer(
                    cls._cleanup_interval_minutes * 60, run_cleanup
                )
                cls._cleanup_scheduler.start()

            except Exception as e:
                logger.error(f"❌ Automatic cleanup failed: {e}")
                # Reschedule despite error
                cls._cleanup_scheduler = threading.Timer(
                    cls._cleanup_interval_minutes * 60, run_cleanup
                )
                cls._cleanup_scheduler.start()

        # Start the first cleanup cycle
        run_cleanup()

    @classmethod
    def start_memory_monitoring(cls):
        """Start automatic memory monitoring and cleanup"""
        if cls._cleanup_scheduler is None:
            logger.info(
                f"🚀 Starting automatic cleanup every {cls._cleanup_interval_minutes} minutes"
            )
            cls._schedule_automatic_cleanup()
        else:
            logger.info("🔄 Automatic cleanup already running")

    @classmethod
    def stop_memory_monitoring(cls):
        """Stop automatic memory monitoring and cleanup"""
        if cls._cleanup_scheduler:
            cls._cleanup_scheduler.cancel()
            cls._cleanup_scheduler = None
            logger.info("⏹️ Stopped automatic cleanup")


# Utility functions for testing and debugging
async def validate_agent_pool_health(
    client_id: str, engagement_id: str
) -> Dict[str, Any]:
    """
    Validate health of a specific tenant's agent pool

    Returns:
        Health report dictionary
    """
    tenant_key = (client_id, engagement_id)

    if tenant_key not in TenantScopedAgentPool._agent_pools:
        return {"pool_exists": False, "message": "No agent pool found for this tenant"}

    agents = TenantScopedAgentPool._agent_pools[tenant_key]
    health_report = {"pool_exists": True, "agent_count": len(agents), "agents": {}}

    for agent_type, agent in agents.items():
        health = await TenantScopedAgentPool._check_agent_health(agent)
        health_report["agents"][agent_type] = {
            "healthy": health.is_healthy,
            "memory_status": health.memory_status,
            "total_executions": health.total_executions,
            "last_used": health.last_used.isoformat() if health.last_used else None,
            "error": health.error,
        }

    return health_report


# Automatic cleanup initialization - start monitoring when module loads
# Register cleanup on application shutdown
atexit.register(TenantScopedAgentPool.stop_memory_monitoring)
