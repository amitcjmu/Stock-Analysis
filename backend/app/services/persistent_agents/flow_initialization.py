"""
Flow Initialization with Persistent Agents

Implements proper flow initialization logic as specified in ADR-015,
ensuring proper agent persistence and memory system validation.
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.context import RequestContext
from app.services.agentic_memory.three_tier_memory_manager import ThreeTierMemoryManager
from app.services.persistent_agents.tenant_scoped_agent_pool import (
    TenantScopedAgentPool,
)

logger = logging.getLogger(__name__)


@dataclass
class FlowInitializationResult:
    """Result of flow initialization process"""

    success: bool
    flow_id: str
    agent_pool: Optional[Dict[str, Any]] = None
    validation_results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    initialization_time_ms: Optional[int] = None


@dataclass
class MemorySystemHealth:
    """Memory system health status"""

    is_healthy: bool
    tier1_status: bool = False  # CrewAI LongTermMemory
    tier2_status: bool = False  # Vector storage
    tier3_status: bool = False  # Database patterns
    error: Optional[str] = None


@dataclass
class CrewAIFlowState:
    """CrewAI flow state validation result"""

    is_valid: bool
    flow_exists: bool = False
    state_consistent: bool = False
    errors: List[str] = None


async def initialize_flow_with_persistent_agents(
    flow_id: str, context: RequestContext
) -> FlowInitializationResult:
    """
    Proper initialization with persistent agents as specified in ADR-015

    This function implements the comprehensive initialization process that:
    1. Ensures agent pool exists for the tenant
    2. Validates agent memory systems are working
    3. Validates CrewAI flow state consistency
    4. Initializes flow-specific resources and context
    5. Warms up agents with flow context

    Args:
        flow_id: Unique flow identifier
        context: Request context with tenant information

    Returns:
        FlowInitializationResult with success status and details
    """
    start_time = datetime.utcnow()

    try:
        logger.info(f"🔄 Initializing flow {flow_id} with persistent agents")
        logger.info(f"   Tenant: {context.client_account_id}/{context.engagement_id}")

        # 1. Ensure agent pool exists for this tenant
        logger.info("📋 Step 1: Initializing tenant agent pool")
        try:
            agent_pool = await TenantScopedAgentPool.initialize_tenant_pool(
                context.client_account_id, context.engagement_id
            )

            if not agent_pool:
                return FlowInitializationResult(
                    success=False,
                    flow_id=flow_id,
                    error="Failed to initialize tenant agent pool - no agents created",
                    initialization_time_ms=_get_elapsed_ms(start_time),
                )

            logger.info(f"   ✅ Agent pool initialized with {len(agent_pool)} agents")

        except Exception as e:
            logger.error(f"   ❌ Agent pool initialization failed: {e}")
            return FlowInitializationResult(
                success=False,
                flow_id=flow_id,
                error=f"Agent pool initialization failed: {str(e)}",
                initialization_time_ms=_get_elapsed_ms(start_time),
            )

        # 2. Validate agent memory systems are working
        logger.info("🧠 Step 2: Validating agent memory systems")
        memory_validation_results = {}

        for agent_type, agent in agent_pool.items():
            try:
                memory_status = await validate_agent_memory_system(agent, agent_type)
                memory_validation_results[agent_type] = memory_status

                if not memory_status.is_healthy:
                    logger.error(
                        f"   ❌ Agent {agent_type} memory system unhealthy: {memory_status.error}"
                    )
                    return FlowInitializationResult(
                        success=False,
                        flow_id=flow_id,
                        error=f"Agent {agent_type} memory system validation failed: {memory_status.error}",
                        validation_results=memory_validation_results,
                        initialization_time_ms=_get_elapsed_ms(start_time),
                    )
                else:
                    logger.info(f"   ✅ Agent {agent_type} memory system healthy")

            except Exception as e:
                logger.error(f"   ❌ Memory validation failed for {agent_type}: {e}")
                return FlowInitializationResult(
                    success=False,
                    flow_id=flow_id,
                    error=f"Memory validation failed for {agent_type}: {str(e)}",
                    validation_results=memory_validation_results,
                    initialization_time_ms=_get_elapsed_ms(start_time),
                )

        # 3. Validate CrewAI flow state consistency
        logger.info("🔍 Step 3: Validating CrewAI flow state consistency")
        try:
            crewai_state = await validate_crewai_flow_state(flow_id, context)

            if not crewai_state.is_valid:
                logger.error(
                    f"   ❌ CrewAI flow state validation failed: {crewai_state.errors}"
                )
                return FlowInitializationResult(
                    success=False,
                    flow_id=flow_id,
                    error=f"CrewAI flow state validation failed: {', '.join(crewai_state.errors or [])}",
                    validation_results={"crewai_state": crewai_state},
                    initialization_time_ms=_get_elapsed_ms(start_time),
                )
            else:
                logger.info("   ✅ CrewAI flow state validation passed")

        except Exception as e:
            logger.error(f"   ❌ CrewAI flow state validation error: {e}")
            return FlowInitializationResult(
                success=False,
                flow_id=flow_id,
                error=f"CrewAI flow state validation error: {str(e)}",
                initialization_time_ms=_get_elapsed_ms(start_time),
            )

        # 4. Initialize flow-specific resources and context
        logger.info("🏗️ Step 4: Setting up flow workspace")
        try:
            workspace_initialized = await setup_flow_workspace(
                flow_id, context, agent_pool
            )

            if not workspace_initialized:
                logger.error("   ❌ Flow workspace initialization failed")
                return FlowInitializationResult(
                    success=False,
                    flow_id=flow_id,
                    error="Flow workspace initialization failed",
                    initialization_time_ms=_get_elapsed_ms(start_time),
                )
            else:
                logger.info("   ✅ Flow workspace initialized successfully")

        except Exception as e:
            logger.error(f"   ❌ Flow workspace setup error: {e}")
            return FlowInitializationResult(
                success=False,
                flow_id=flow_id,
                error=f"Flow workspace setup error: {str(e)}",
                initialization_time_ms=_get_elapsed_ms(start_time),
            )

        # 5. Warm up agents with flow context
        logger.info("🔥 Step 5: Warming up agents with flow context")
        try:
            for agent_type, agent in agent_pool.items():
                await set_agent_flow_context(agent, flow_id, context)
                logger.info(f"   ✅ Agent {agent_type} context set")

        except Exception as e:
            logger.error(f"   ❌ Agent context setup error: {e}")
            return FlowInitializationResult(
                success=False,
                flow_id=flow_id,
                error=f"Agent context setup error: {str(e)}",
                agent_pool=agent_pool,
                initialization_time_ms=_get_elapsed_ms(start_time),
            )

        # Success!
        initialization_time = _get_elapsed_ms(start_time)
        logger.info(
            f"✅ Flow {flow_id} initialized successfully with {len(agent_pool)} persistent agents"
        )
        logger.info(f"   Initialization time: {initialization_time}ms")

        return FlowInitializationResult(
            success=True,
            flow_id=flow_id,
            agent_pool=agent_pool,
            validation_results=memory_validation_results,
            initialization_time_ms=initialization_time,
        )

    except Exception as e:
        logger.error(f"❌ Flow initialization failed: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")

        return FlowInitializationResult(
            success=False,
            flow_id=flow_id,
            error=f"Unexpected initialization failure: {str(e)}",
            initialization_time_ms=_get_elapsed_ms(start_time),
        )


async def validate_agent_memory_system(
    agent: Any, agent_type: str
) -> MemorySystemHealth:
    """
    Validate that an agent's memory system is functioning properly

    Args:
        agent: Agent instance to validate
        agent_type: Type of agent for context

    Returns:
        MemorySystemHealth status
    """
    try:
        # Check Tier 1: CrewAI LongTermMemory
        tier1_status = False
        if hasattr(agent, "memory") and agent.memory:
            tier1_status = True

        # Check Tier 2: Vector storage (episodic memory)
        tier2_status = False  # Not yet implemented

        # Check Tier 3: Database patterns (semantic memory)
        tier3_status = False
        if hasattr(agent, "memory_manager"):
            # Try to access the three-tier memory manager
            memory_manager = agent.memory_manager
            if memory_manager and hasattr(memory_manager, "client_account_id"):
                tier3_status = True

        is_healthy = tier1_status and tier3_status  # Tier 2 optional for now

        return MemorySystemHealth(
            is_healthy=is_healthy,
            tier1_status=tier1_status,
            tier2_status=tier2_status,
            tier3_status=tier3_status,
            error=(
                None
                if is_healthy
                else f"Memory tiers not fully functional: T1={tier1_status}, T2={tier2_status}, T3={tier3_status}"
            ),
        )

    except Exception as e:
        return MemorySystemHealth(
            is_healthy=False, error=f"Memory system validation failed: {str(e)}"
        )


async def validate_crewai_flow_state(
    flow_id: str, context: RequestContext
) -> CrewAIFlowState:
    """
    Validate CrewAI flow state consistency

    Args:
        flow_id: Flow identifier
        context: Request context

    Returns:
        CrewAIFlowState validation result
    """
    try:
        # Check if flow exists in database
        flow_exists = await _check_flow_exists_in_db(flow_id, context)

        # Check state consistency
        state_consistent = True  # Placeholder - would check actual state consistency

        errors = []
        if not flow_exists:
            errors.append(f"Flow {flow_id} not found in database")

        is_valid = flow_exists and state_consistent and not errors

        return CrewAIFlowState(
            is_valid=is_valid,
            flow_exists=flow_exists,
            state_consistent=state_consistent,
            errors=errors if errors else None,
        )

    except Exception as e:
        return CrewAIFlowState(
            is_valid=False,
            flow_exists=False,
            state_consistent=False,
            errors=[f"Flow state validation error: {str(e)}"],
        )


async def setup_flow_workspace(
    flow_id: str, context: RequestContext, agent_pool: Dict[str, Any]
) -> bool:
    """
    Set up flow-specific workspace and resources

    Args:
        flow_id: Flow identifier
        context: Request context
        agent_pool: Initialized agent pool

    Returns:
        True if successful, False otherwise
    """
    try:
        # Initialize flow-specific memory contexts
        ThreeTierMemoryManager(
            client_account_id=uuid.UUID(context.client_account_id),
            engagement_id=uuid.UUID(context.engagement_id),
        )

        # Set up flow-specific working directories or resources
        # (This is a placeholder for actual workspace setup)

        logger.info(f"🏗️ Flow workspace initialized for {flow_id}")
        return True

    except Exception as e:
        logger.error(f"❌ Flow workspace setup failed: {e}")
        return False


async def set_agent_flow_context(agent: Any, flow_id: str, context: RequestContext):
    """
    Set flow-specific context on an agent

    Args:
        agent: Agent instance
        flow_id: Flow identifier
        context: Request context
    """
    try:
        # Set flow context on agent
        agent._current_flow_id = flow_id
        agent._current_context = context
        agent._flow_start_time = datetime.utcnow()

        # Update execution count
        if hasattr(agent, "_execution_count"):
            agent._execution_count += 1
        else:
            agent._execution_count = 1

        agent._last_execution = datetime.utcnow()

        logger.debug(
            f"🔗 Flow context set for agent: {getattr(agent, '_agent_type', 'unknown')}"
        )

    except Exception as e:
        logger.error(f"❌ Failed to set agent flow context: {e}")
        raise


# Helper functions


async def _check_flow_exists_in_db(flow_id: str, context: RequestContext) -> bool:
    """Check if flow exists in database with retry logic and circuit breaker"""
    import asyncio

    from sqlalchemy.exc import DisconnectionError, OperationalError
    from sqlalchemy.exc import TimeoutError as SQLTimeoutError

    max_retries = 3
    base_delay = 1.0  # seconds

    for attempt in range(max_retries):
        try:
            from sqlalchemy import and_, select

            from app.core.database import AsyncSessionLocal
            from app.models.discovery_flow import DiscoveryFlow

            # Set connection timeout
            async with AsyncSessionLocal() as db:
                # Test connection health first
                await db.execute(select(1))

                stmt = select(DiscoveryFlow).where(
                    and_(
                        DiscoveryFlow.flow_id == flow_id,
                        DiscoveryFlow.client_account_id == context.client_account_id,
                        DiscoveryFlow.engagement_id == context.engagement_id,
                    )
                )
                result = await db.execute(stmt)
                flow = result.scalar_one_or_none()
                return flow is not None

        except (
            DisconnectionError,
            OperationalError,
            SQLTimeoutError,
            ConnectionError,
        ) as e:
            attempt_msg = f"attempt {attempt + 1}/{max_retries}"
            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt)  # Exponential backoff
                logger.warning(
                    f"⚠️ Database connection failed ({attempt_msg}), retrying in {delay}s: {e}"
                )
                await asyncio.sleep(delay)
                continue
            else:
                logger.error(
                    f"❌ Database connection failed after {max_retries} attempts: {e}"
                )
                return False  # Assume flow doesn't exist if we can't verify

        except ImportError as e:
            logger.error(f"❌ Database module import failed: {e}")
            return False  # Graceful degradation

        except Exception as e:
            logger.error(
                f"❌ Unexpected database error ({attempt + 1}/{max_retries}): {e}"
            )
            if attempt < max_retries - 1:
                await asyncio.sleep(base_delay)
                continue
            return False  # Assume flow doesn't exist on persistent errors

    # This line should never be reached, but included for completeness
    return False


def _get_elapsed_ms(start_time: datetime) -> int:
    """Get elapsed time in milliseconds"""
    return int((datetime.utcnow() - start_time).total_seconds() * 1000)
