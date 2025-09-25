"""
Agent-related operations for questionnaire generation.
Functions for setting up and executing AI agents for questionnaire generation.
"""

import logging
from datetime import datetime, timezone
from typing import Any, List
from uuid import UUID

from app.core.context import RequestContext
from app.models.asset import Asset
from app.schemas.collection_flow import AdaptiveQuestionnaireResponse

from .utils import _analyze_selected_assets

logger = logging.getLogger(__name__)


async def _setup_persistent_agent(
    context: RequestContext, flow_id: str
) -> tuple[Any, dict]:
    """Setup persistent agent and prepare inputs."""
    from app.services.persistent_agents.tenant_scoped_agent_pool import (
        TenantScopedAgentPool,
    )

    logger.info(f"Attempting to use persistent questionnaire agent for flow {flow_id}")

    # Get the persistent questionnaire agent for this tenant
    questionnaire_agent = await TenantScopedAgentPool.get_agent(
        context=context, agent_type="questionnaire_generator"
    )

    return questionnaire_agent, {}


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
        return await questionnaire_tool._arun(
            data_gaps=agent_inputs["gap_analysis"]["data_gaps"],
            business_context=agent_inputs["business_context"],
        )
    else:
        logger.warning(
            f"No questionnaire generation tool found on agent for flow {flow_id}, using generic process"
        )
        return await questionnaire_agent.process(agent_inputs)


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


async def _fallback_service_generation(
    flow_id: str, selected_assets: List[Asset], context: RequestContext
) -> List[AdaptiveQuestionnaireResponse]:
    """Fallback to service-based questionnaire generation when agent fails."""
    try:
        logger.info(f"Using fallback service generation for flow {flow_id}")
        from app.services.ai_analysis.questionnaire_generator.service import (
            QuestionnaireGeneratorService,
        )

        # Initialize the service
        service = QuestionnaireGeneratorService()

        # Analyze selected assets
        _, asset_analysis = _analyze_selected_assets(selected_assets)

        # Build service inputs
        service_inputs = {
            "flow_id": flow_id,
            "assets": [
                {
                    "id": str(asset.id),
                    "name": asset.name,
                    "asset_type": asset.asset_type,
                    "business_criticality": asset.business_criticality,
                    "custom_attributes": asset.custom_attributes or {},
                }
                for asset in selected_assets
            ],
            "gap_analysis": asset_analysis,
            "business_context": {
                "engagement_id": context.engagement_id,
                "client_account_id": context.client_account_id,
            },
        }

        # Generate questionnaires using service
        logger.info("Generating questionnaires using service")
        questionnaires_result = await service.generate_questionnaires(service_inputs)

        if (
            not questionnaires_result
            or questionnaires_result.get("status") != "success"
        ):
            logger.warning("Service generation failed or returned no results")
            raise Exception("Service generation failed")

        # Extract questionnaires from service result
        questionnaires_data = questionnaires_result.get("questionnaires", [])
        if not questionnaires_data:
            logger.warning("Service returned no questionnaires")
            raise Exception("No questionnaires generated by service")

        # Convert to AdaptiveQuestionnaireResponse format
        questionnaires = []
        for idx, q_data in enumerate(questionnaires_data):
            questionnaire = AdaptiveQuestionnaireResponse(
                id=str(UUID(int=hash(f"{flow_id}-{idx}") & 0x7FFFFFFF)),
                title=q_data.get("title", f"Service Generated Questionnaire {idx + 1}"),
                description=q_data.get(
                    "description", "Generated using fallback service"
                ),
                template_name="service_generated",
                template_type="detailed",
                version="2.0",
                applicable_tiers=["tier_1", "tier_2", "tier_3", "tier_4"],
                questions=q_data.get("questions", []),
                completion_status="pending",
                responses_collected={},
                is_active=True,
                is_template=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            questionnaires.append(questionnaire)

        logger.info(f"Service generated {len(questionnaires)} questionnaires")
        return questionnaires

    except Exception as e:
        logger.error(f"Fallback service generation failed for flow {flow_id}: {e}")
        raise


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
            questionnaire_agent, base_inputs = await _setup_persistent_agent(
                context, flow_id
            )

            # Build comprehensive inputs for agent
            agent_inputs = {
                **base_inputs,
                "flow_id": flow_id,
                "assets": [
                    {
                        "id": str(asset.id),
                        "name": asset.name,
                        "asset_type": asset.asset_type,
                        "business_criticality": asset.business_criticality,
                        "custom_attributes": asset.custom_attributes or {},
                    }
                    for asset in selected_assets
                ],
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
            logger.warning(
                f"Persistent agent generation failed for flow {flow_id}: {agent_error}"
            )
            logger.info("Falling back to service generation")

            # Fallback to service generation
            return await _fallback_service_generation(flow_id, selected_assets, context)

    except Exception as e:
        logger.error(
            f"All questionnaire generation methods failed for flow {flow_id}: {e}"
        )
        raise
