"""
Flow Execution Engine Collection Crew - Utilities
Helper functions for agent pool initialization and phase mapping.
"""

from typing import Any, Dict

from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logger = get_logger(__name__)


async def prepare_phase_input(
    master_flow: CrewAIFlowStateExtensions, phase_input: Dict[str, Any]
) -> None:
    """Prepare phase_input with correct flow IDs following MFO Two-Table pattern.

    CRITICAL FIX (Issue #1067): Collection flows must properly distinguish between:
    - Child flow ID (collection_flow.id) - Used for querying collection_flows table
    - Master flow ID (master_flow.flow_id) - Used for MFO routing and state

    This matches the pattern established by discovery flows in:
    execution_engine_crew_discovery/phase_orchestration.py:94-97

    Args:
        master_flow: Master flow state from crewai_flow_state_extensions
        phase_input: Phase input dict to be enriched with correct IDs
    """
    # Ensure flow_id is set to CHILD flow ID (primary key of collection_flows table)
    # This is what phases should use when querying CollectionFlow
    if "flow_id" not in phase_input:
        phase_input["flow_id"] = master_flow.id  # Child flow ID (UUID primary key)
        logger.debug(
            f"📋 Set phase_input['flow_id'] = {master_flow.id} (child flow ID)"
        )

    # Ensure master_flow_id is set to MASTER flow ID (for MFO routing)
    if "master_flow_id" not in phase_input:
        phase_input["master_flow_id"] = master_flow.flow_id  # Master flow ID
        logger.debug(
            f"📋 Set phase_input['master_flow_id'] = {master_flow.flow_id} (master flow ID)"
        )

    # Ensure tenant scoping IDs are set
    if "client_account_id" not in phase_input:
        phase_input["client_account_id"] = str(master_flow.client_account_id)
    if "engagement_id" not in phase_input:
        phase_input["engagement_id"] = str(master_flow.engagement_id)


async def initialize_collection_agent_pool(
    master_flow: CrewAIFlowStateExtensions,
) -> Any:
    """Initialize persistent agent pool for collection tasks"""
    try:
        # Import here to avoid circular dependencies
        from app.services.persistent_agents.tenant_scoped_agent_pool import (
            TenantScopedAgentPool,
        )

        # Validate required identifiers before pool init
        client_id = master_flow.client_account_id
        engagement_id = master_flow.engagement_id

        # Ensure identifiers are non-empty strings to prevent passing "None" or empty IDs
        if not client_id or not engagement_id:
            logger.error("Missing required identifiers for agent pool initialization")
            raise ValueError(
                "client_id and engagement_id are required for agent pool initialization"
            )

        # Convert to safe string representations
        safe_client = str(client_id)
        safe_eng = str(engagement_id)

        # Initialize the tenant pool (returns None but sets up the pool)
        try:
            await TenantScopedAgentPool.initialize_tenant_pool(
                client_id=safe_client,
                engagement_id=safe_eng,
            )
        except Exception as e:
            msg = "Failed to initialize TenantScopedAgentPool for collection flow"
            # Avoid logging sensitive identifiers directly
            logger.exception("%s", msg)
            raise RuntimeError(msg) from e

        logger.info(
            "🏊 Initialized agent pool for collection flow - client_id=%s engagement_id=%s",
            str(client_id),
            str(engagement_id),
        )

        # Return the TenantScopedAgentPool class itself for agent access
        # The pool has been initialized and agents can be retrieved via get_agent()
        return TenantScopedAgentPool

    except Exception as e:
        logger.error(f"❌ Failed to initialize collection agent pool: {e}")
        raise


def map_collection_phase_name(phase_name: str) -> str:
    """Map collection flow phase names to execution methods"""
    phase_mapping = {
        "platform_detection": "platform_detection",
        "automated_collection": "automated_collection",
        "gap_analysis": "gap_analysis",
        "questionnaire_generation": "questionnaire_generation",
        "manual_collection": "manual_collection",
    }
    return phase_mapping.get(phase_name, phase_name)
