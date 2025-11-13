"""
Agent-related operations for questionnaire generation.
Functions for setting up and executing AI agents for questionnaire generation.
"""

import logging
from typing import Any, List

from app.core.context import RequestContext
from app.models.asset import Asset
from app.schemas.collection_flow import AdaptiveQuestionnaireResponse

from .utils import _analyze_selected_assets

logger = logging.getLogger(__name__)


async def _setup_persistent_agent(
    context: RequestContext, flow_id: str
) -> tuple[Any, dict]:
    """Setup persistent agent and prepare inputs."""
    try:
        from app.services.persistent_agents.tenant_scoped_agent_pool import (
            TenantScopedAgentPool,
        )

        logger.info(
            f"Attempting to use persistent questionnaire agent for flow {flow_id}"
        )
        logger.info(
            f"Context: client_account_id={context.client_account_id}, engagement_id={context.engagement_id}"
        )

        # Get the persistent questionnaire agent for this tenant
        questionnaire_agent = await TenantScopedAgentPool.get_agent(
            context=context, agent_type="questionnaire_generator"
        )

        if not questionnaire_agent:
            logger.error(f"Failed to get questionnaire agent for flow {flow_id}")
            raise Exception("Questionnaire agent not available")

        logger.info(f"Successfully obtained questionnaire agent for flow {flow_id}")
        return questionnaire_agent, {}

    except Exception as e:
        logger.error(
            f"Error setting up persistent agent for flow {flow_id}: {e}", exc_info=True
        )
        logger.error(f"Setup error type: {type(e).__name__}")
        logger.error(f"Setup error details: {str(e)}")
        raise


async def _execute_questionnaire_tool(
    questionnaire_agent: Any, agent_inputs: dict, flow_id: str
) -> Any:
    """Execute questionnaire agent using proper CrewAI workflow.

    IMPORTANT: This method should let the agent decide how to use its tools,
    not bypass the agent by calling tool methods directly. The agent uses its
    LLM to make intelligent decisions about question generation.
    """
    logger.info(
        "🤖 Executing questionnaire agent via CrewAI (agent will decide tool usage)"
    )

    # Let the agent process the inputs using its role, goal, and backstory
    # The agent will decide whether and how to use the questionnaire_generation tool
    result = await questionnaire_agent.process(agent_inputs)

    logger.info(f"🔍 Agent process returned type: {type(result)}")
    if isinstance(result, dict):
        logger.info(f"🔍 Agent process returned keys: {list(result.keys())}")
    logger.info(f"🔍 Agent process result: {result}")

    # Parse result if it's a string (agent might return JSON string)
    if isinstance(result, str):
        import json

        try:
            parsed_result = json.loads(result)
            logger.info("✅ Successfully parsed agent response from JSON string")
            return parsed_result
        except json.JSONDecodeError:
            logger.warning(
                "⚠️ Agent returned non-JSON string, wrapping in success response"
            )
            # If agent returns plain text, wrap it as a success message
            return {"status": "success", "message": result, "questionnaires": []}

    return result


async def _process_agent_results(
    agent_result: Any, flow_id: str
) -> List[AdaptiveQuestionnaireResponse]:
    """Process agent results to extract questionnaires."""
    if not isinstance(agent_result, dict):
        logger.warning(f"Agent returned non-dict result: {type(agent_result)}")
        raise Exception("Agent returned unexpected result type")

    # Check for success result structure
    if agent_result.get("status") == "success":
        from .utils import _extract_questionnaire_data

        return _extract_questionnaire_data(agent_result, flow_id)
    elif agent_result.get("status") == "error":
        error_msg = agent_result.get("error", "Unknown agent error")
        logger.warning(f"Agent execution error: {error_msg}")
        raise Exception(f"Agent execution failed: {error_msg}")
    else:
        logger.warning(
            f"Agent returned unexpected status: {agent_result.get('status')}"
        )
        raise Exception(
            f"Agent returned unexpected status: {agent_result.get('status')}"
        )


# FALLBACK REMOVED - NO FALLBACKS ALLOWED
# This function was intentionally removed to ensure we only use agent-based generation
# and can properly debug issues without fallback masking the real problems


async def _generate_agent_questionnaires(
    flow_id: str, existing_assets: List[Asset], context: RequestContext, db=None
) -> List[AdaptiveQuestionnaireResponse]:
    """
    Generate questionnaires using persistent agent with Issue #980 gap detection.

    ✅ FIX 0.5 (Issue #980): Integrated database-backed gap analysis.

    Args:
        flow_id: Collection flow ID
        existing_assets: List of available assets
        context: Request context with tenant information
        db: Database session (required for Issue #980 gap detection)

    Returns:
        List of generated questionnaires

    Raises:
        Exception: If both agent and service generation fail
    """
    try:
        logger.info(
            f"Starting agent questionnaire generation for flow {flow_id} with {len(existing_assets)} assets"
        )

        # ✅ FIX 0.5: Analyze selected assets using Issue #980's gap detection
        # Reads from collection_data_gaps table instead of legacy asset inspection
        selected_assets, asset_analysis = await _analyze_selected_assets(
            existing_assets, flow_id, db
        )

        if not selected_assets:
            logger.warning("No assets available for questionnaire generation")
            raise Exception("No assets available for analysis")

        logger.info(
            f"Analyzing {len(selected_assets)} assets with "
            f"{len(asset_analysis.get('assets_with_gaps', []))} assets having gaps"
        )

        # Try persistent agent generation first
        try:
            logger.info(f"Setting up persistent agent for flow {flow_id}")
            questionnaire_agent, base_inputs = await _setup_persistent_agent(
                context, flow_id
            )
            logger.info(f"Successfully set up persistent agent for flow {flow_id}")

            # Build comprehensive inputs for agent
            # Note: selected_assets is a list of dicts from _analyze_selected_assets, not Asset objects

            # CRITICAL FIX: Build asset_names mapping for questionnaire generation
            # Resolves issue where questions showed "Asset df0d34a9" instead of "Admin Dashboard"
            asset_names = {
                asset["asset_id"]: asset["asset_name"]
                for asset in selected_assets
                if asset.get("asset_id") and asset.get("asset_name")
            }
            logger.info(
                f"Built asset_names mapping with {len(asset_names)} entries: {asset_names}"
            )

            agent_inputs = {
                **base_inputs,
                "flow_id": flow_id,
                "assets": selected_assets,  # Already formatted as list of dicts
                "gap_analysis": asset_analysis,
                "business_context": {
                    "engagement_id": context.engagement_id,
                    "client_account_id": context.client_account_id,
                    "total_assets": len(selected_assets),
                    "assets_with_gaps": len(asset_analysis.get("assets_with_gaps", [])),
                    "asset_names": asset_names,  # CRITICAL: Pass asset names for proper display in questions
                    # CRITICAL: Pass assets with OS data for OS-aware questions
                    "existing_assets": selected_assets,
                },
            }

            logger.info(f"Executing persistent agent for flow {flow_id}")
            agent_result = await _execute_questionnaire_tool(
                questionnaire_agent, agent_inputs, flow_id
            )

            # Process agent results
            questionnaires = await _process_agent_results(agent_result, flow_id)

            logger.info(
                f"Agent generated {len(questionnaires)} questionnaires for flow {flow_id}"
            )
            return questionnaires

        except Exception as agent_error:
            # Log with full stack trace for debugging
            logger.error(
                f"Persistent agent generation failed for flow {flow_id}: {agent_error}",
                exc_info=True,
            )
            logger.error(f"Agent error type: {type(agent_error).__name__}")
            logger.error(f"Agent error details: {str(agent_error)}")
            # NO FALLBACK - raise the actual error to fix root cause
            raise agent_error

    except Exception as e:
        logger.error(
            f"All questionnaire generation methods failed for flow {flow_id}: {e}",
            exc_info=True,
        )
        logger.error(f"Final error type: {type(e).__name__}")
        logger.error(f"Final error details: {str(e)}")
        raise
