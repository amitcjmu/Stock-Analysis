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
    """Execute questionnaire generation tool or fallback to generic process."""
    logger.info("Executing persistent questionnaire agent with tools")
    questionnaire_tool = None
    for tool in questionnaire_agent.tools:
        if hasattr(tool, "name") and "questionnaire_generation" in tool.name.lower():
            questionnaire_tool = tool
            break

    if questionnaire_tool:
        # Execute questionnaire generation tool directly
        # Build data_gaps from the gap_analysis data
        gap_analysis = agent_inputs.get("gap_analysis", {})
        data_gaps = {
            "missing_critical_fields": gap_analysis.get("missing_critical_fields", {}),
            "unmapped_attributes": gap_analysis.get("unmapped_attributes", {}),
            "data_quality_issues": gap_analysis.get("data_quality_issues", {}),
            "assets_with_gaps": gap_analysis.get("assets_with_gaps", []),
        }
        result = await questionnaire_tool._arun(
            data_gaps=data_gaps,
            business_context=agent_inputs["business_context"],
        )
        logger.info(f"Tool returned type: {type(result)}, value: {result}")
        # Ensure result is a dict
        if isinstance(result, str):
            # Try to parse as JSON if it's a string
            import json

            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                # If not JSON, wrap in a dict
                result = {"status": "success", "message": result, "questionnaires": []}
        return result
    else:
        logger.warning(
            f"No questionnaire generation tool found on agent for flow {flow_id}, using generic process"
        )
        result = await questionnaire_agent.process(agent_inputs)
        logger.info(f"Agent process returned type: {type(result)}, value: {result}")
        # Ensure result is a dict
        if isinstance(result, str):
            # Try to parse as JSON if it's a string
            import json

            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                # If not JSON, wrap in a dict
                result = {"status": "success", "message": result, "questionnaires": []}
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
    flow_id: str, existing_assets: List[Asset], context: RequestContext
) -> List[AdaptiveQuestionnaireResponse]:
    """
    Generate questionnaires using persistent agent with fallback to service.

    Args:
        flow_id: Collection flow ID
        existing_assets: List of available assets
        context: Request context with tenant information

    Returns:
        List of generated questionnaires

    Raises:
        Exception: If both agent and service generation fail
    """
    try:
        logger.info(
            f"Starting agent questionnaire generation for flow {flow_id} with {len(existing_assets)} assets"
        )

        # Analyze selected assets for gaps and context
        selected_assets, asset_analysis = _analyze_selected_assets(existing_assets)

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
