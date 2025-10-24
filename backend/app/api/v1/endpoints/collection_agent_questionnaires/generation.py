"""
Collection Agent Questionnaire Generation
Agent-driven questionnaire generation logic with fallback handling.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, List, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException

from app.core.context import RequestContext
from app.core.database import get_db
from app.models.collection_flow import CollectionFlow, AdaptiveQuestionnaire
from app.services.persistent_agents import TenantScopedAgentPool

from .helpers import build_agent_context, mark_generation_failed
from .bootstrap import get_bootstrap_questionnaire

logger = logging.getLogger(__name__)


async def generate_questionnaire_with_agent(
    flow_id: int,
    flow_uuid: UUID,
    context: RequestContext,
    selected_asset_ids: Optional[list[str]] = None,
) -> None:
    """
    Background task to generate questionnaire using persistent agent.

    Args:
        flow_id: Internal flow ID
        flow_uuid: Flow UUID for external reference
        context: Request context with tenant information
        selected_asset_ids: Optional list of selected asset IDs
    """
    try:
        async with AsyncSession(get_db()) as db:
            # Gather context for generating questionnaire
            agent_context = await build_agent_context(
                db=db,
                flow_id=flow_id,
                context=context,
                selected_asset_ids=selected_asset_ids,
            )

            # Get persistent questionnaire generator agent
            logger.info(
                f"Getting TenantScopedAgentPool questionnaire_generator for flow {flow_uuid}"
            )

            try:
                # Get persistent agent for questionnaire generation
                agent = await TenantScopedAgentPool.get_agent(
                    context=context, agent_type="questionnaire_generator"
                )

                logger.info(
                    f"Successfully obtained questionnaire_generator agent for flow {flow_uuid}"
                )

                # Prepare agent input data
                gaps_data = _prepare_gaps_data(agent_context)
                agent_input = _prepare_agent_input(
                    gaps_data, agent_context, flow_uuid, selected_asset_ids
                )

                # Execute questionnaire generation through persistent agent
                logger.info(
                    f"Executing questionnaire generation with persistent agent for flow {flow_uuid}"
                )

                # Execute agent generation
                result = await _execute_agent_generation(
                    agent, gaps_data, agent_input, agent_context, flow_uuid
                )

            except Exception as agent_error:
                logger.error(
                    f"Failed to use persistent agent for questionnaire generation: {agent_error}"
                )
                # Fallback to bootstrap questionnaire
                logger.info(
                    f"Using bootstrap questionnaire as fallback for flow {flow_uuid}"
                )
                questionnaire_data = get_bootstrap_questionnaire(agent_context)
                result = {"questionnaire": questionnaire_data}

            # Save results to database
            await _save_questionnaire_results(db, result, flow_id, flow_uuid, context)

    except Exception as e:
        logger.error(f"Agent questionnaire generation failed: {e}")
        try:
            async with AsyncSession(get_db()) as db:
                await mark_generation_failed(db, flow_id, context)
        except Exception:
            pass


def _prepare_gaps_data(agent_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Prepare gaps data from agent context for agent input."""
    gaps_data = []
    for asset in agent_context.get("assets", []):
        if asset.get("gaps"):
            for gap in asset["gaps"]:
                gaps_data.append(
                    {
                        "asset_id": asset["id"],
                        "asset_name": asset["name"],
                        "gap": gap,
                        "priority": "high",
                        "category": "data_collection",
                    }
                )

    # If no specific gaps, create generic ones
    if not gaps_data:
        gaps_data = [
            {
                "gap": "Asset selection required",
                "priority": "critical",
                "category": "asset_selection",
            },
            {
                "gap": "Basic information incomplete",
                "priority": "high",
                "category": "basic_info",
            },
        ]

    return gaps_data


def _prepare_agent_input(
    gaps_data: List[Dict[str, Any]],
    agent_context: Dict[str, Any],
    flow_uuid: UUID,
    selected_asset_ids: Optional[List[str]],
) -> Dict[str, Any]:
    """Prepare context for agent execution."""
    return {
        "data_gaps": gaps_data,
        "business_context": {
            "flow_id": str(flow_uuid),
            "scope": agent_context.get("scope", "engagement"),
            "selected_assets": selected_asset_ids or [],
            "existing_assets": agent_context.get("assets", []),
        },
        "collection_flow_id": str(flow_uuid),
        "automation_tier": "tier_2",
    }


async def _execute_agent_generation(
    agent: Any,
    gaps_data: List[Dict[str, Any]],
    agent_input: Dict[str, Any],
    agent_context: Dict[str, Any],
    flow_uuid: UUID,
) -> Dict[str, Any]:
    """Execute questionnaire generation using agent tools."""
    # Use agent tools for questionnaire generation
    questionnaire_tool = None
    for tool in agent.tools:
        if hasattr(tool, "name") and "questionnaire_generation" in tool.name.lower():
            questionnaire_tool = tool
            break

    if questionnaire_tool:
        # Execute questionnaire generation tool
        agent_result = await questionnaire_tool._arun(
            data_gaps=gaps_data,
            business_context=agent_input["business_context"],
        )

        # Process agent result
        if isinstance(agent_result, dict) and agent_result.get("questionnaire"):
            questionnaire_data = agent_result["questionnaire"]
            logger.info(
                f"Agent generated questionnaire successfully for flow {flow_uuid}"
            )
        else:
            # Fallback to asset-aware bootstrap
            logger.warning(
                f"Agent returned invalid result for flow {flow_uuid}, using bootstrap"
            )
            questionnaire_data = get_bootstrap_questionnaire(agent_context)
    else:
        logger.warning(
            f"No questionnaire generation tool found on agent for flow {flow_uuid}, using bootstrap"
        )
        questionnaire_data = get_bootstrap_questionnaire(agent_context)

    return {"questionnaire": questionnaire_data}


async def _save_questionnaire_results(
    db: AsyncSession,
    result: Dict[str, Any],
    flow_id: int,
    flow_uuid: UUID,
    context: RequestContext,
) -> None:
    """Save questionnaire results to database."""
    if result and result.get("questionnaire"):
        # Save questionnaire to database
        questionnaire_data = result["questionnaire"]

        questionnaire = AdaptiveQuestionnaire(
            collection_flow_id=flow_id,  # flow_id param = PK (router.py passes flow.id)
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            title=questionnaire_data.get("title", "Adaptive Questionnaire"),
            description=questionnaire_data.get("description", ""),
            questions=questionnaire_data.get("questions", []),
            target_gaps=questionnaire_data.get("target_gaps", []),
            validation_rules=questionnaire_data.get("validation_rules", {}),
            completion_status="pending",
            metadata={
                "agent_generated": True,
                "generation_method": "TenantScopedAgentPool",
                "agent_type": "questionnaire_generator",
                "requires_asset_selection": result.get(
                    "requires_asset_selection", False
                ),
                "generation_time": datetime.utcnow().isoformat(),
            },
        )

        db.add(questionnaire)

        # Bug #668 Debug: Log questionnaire creation details
        logger.info(
            f"🔍 BUG#668: Created questionnaire {questionnaire.id} for flow {flow_id} - "
            f"completion_status={questionnaire.completion_status}, "
            f"target_gaps_count={len(questionnaire.target_gaps)}, "
            f"question_count={len(questionnaire.questions)}"
        )

        # Update flow metadata with tenant scoping
        flow_result = await db.execute(
            select(CollectionFlow).where(
                and_(
                    CollectionFlow.id == flow_id,
                    CollectionFlow.client_account_id == context.client_account_id,
                    CollectionFlow.engagement_id == context.engagement_id,
                )
            )
        )
        flow = flow_result.scalar_one_or_none()

        if not flow:
            logger.error(
                f"Flow not found: flow_id={flow_id}, tenant={context.client_account_id}, "
                f"engagement={context.engagement_id}"
            )
            raise HTTPException(
                status_code=404, detail=f"Flow not found with id {flow_id}"
            )

        if not flow.flow_metadata:
            flow.flow_metadata = {}
        flow.flow_metadata["questionnaire_generating"] = False
        flow.flow_metadata["questionnaire_ready"] = True
        flow.flow_metadata["agent_questionnaire_id"] = str(questionnaire.id)

        # Bug #668 Debug: Log flow state before commit
        logger.info(
            f"🔍 BUG#668: Flow {flow.flow_id} state before commit - "
            f"assessment_ready={flow.assessment_ready}, "
            f"current_phase={flow.current_phase}, "
            f"status={flow.status}"
        )

        await db.commit()

        # Bug #668 Debug: Log flow state after commit
        await db.refresh(flow)
        await db.refresh(questionnaire)
        logger.info(
            f"🔍 BUG#668: After commit - flow.assessment_ready={flow.assessment_ready}, "
            f"questionnaire.completion_status={questionnaire.completion_status}"
        )

        logger.info(
            f"TenantScopedAgentPool questionnaire generated successfully for flow {flow_uuid}"
        )

    else:
        logger.warning(f"Agent returned no questionnaire for flow {flow_uuid}")
        await mark_generation_failed(db, flow_id, context)
