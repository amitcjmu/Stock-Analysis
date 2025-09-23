"""
Collection Agent Questionnaire Generation
Agent-driven questionnaire generation logic with fallback handling.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.context import RequestContext
from app.core.database import get_db
from app.models.collection_flow import CollectionFlow, AdaptiveQuestionnaire
from app.services.ai_analysis.questionnaire_generator import (
    AdaptiveQuestionnaireGenerator,
)

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

            # Initialize the adaptive questionnaire generator
            logger.info(
                f"Initializing AdaptiveQuestionnaireGenerator for flow {flow_uuid}"
            )
            questionnaire_generator = AdaptiveQuestionnaireGenerator()

            # Prepare gaps data from context
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

            # Generate questionnaires using the AI service
            logger.info(f"Generating adaptive questionnaires for flow {flow_uuid}")

            try:
                questionnaires = await questionnaire_generator.generate_questionnaires(
                    data_gaps=gaps_data,
                    business_context={
                        "flow_id": str(flow_uuid),
                        "scope": agent_context.get("scope", "engagement"),
                        "selected_assets": selected_asset_ids or [],
                        "existing_assets": agent_context.get("assets", []),
                    },
                    collection_flow_id=str(flow_uuid),
                )

                # Process the generated questionnaires
                if questionnaires and len(questionnaires) > 0:
                    questionnaire_data = questionnaires[0]  # Use first questionnaire
                else:
                    # Fallback to asset-aware bootstrap
                    questionnaire_data = get_bootstrap_questionnaire(agent_context)

                result = {"questionnaire": questionnaire_data}

            except Exception as e:
                logger.error(f"Failed to generate questionnaire: {e}")
                result = None

            if result and result.get("questionnaire"):
                # Save questionnaire to database
                questionnaire_data = result["questionnaire"]

                questionnaire = AdaptiveQuestionnaire(
                    collection_flow_id=flow_id,
                    title=questionnaire_data.get("title", "Adaptive Questionnaire"),
                    description=questionnaire_data.get("description", ""),
                    questions=questionnaire_data.get("questions", []),
                    target_gaps=questionnaire_data.get("target_gaps", []),
                    validation_rules=questionnaire_data.get("validation_rules", {}),
                    completion_status="pending",
                    metadata={
                        "agent_generated": True,
                        "requires_asset_selection": result.get(
                            "requires_asset_selection", False
                        ),
                        "generation_time": datetime.utcnow().isoformat(),
                    },
                )

                db.add(questionnaire)

                # Update flow metadata
                flow_result = await db.execute(
                    select(CollectionFlow).where(CollectionFlow.id == flow_id)
                )
                flow = flow_result.scalar_one()

                if not flow.flow_metadata:
                    flow.flow_metadata = {}
                flow.flow_metadata["questionnaire_generating"] = False
                flow.flow_metadata["questionnaire_ready"] = True
                flow.flow_metadata["agent_questionnaire_id"] = str(questionnaire.id)

                await db.commit()

                logger.info(f"Agent questionnaire generated for flow {flow_uuid}")

            else:
                logger.warning(f"Agent returned no questionnaire for flow {flow_uuid}")
                await mark_generation_failed(db, flow_id)

    except Exception as e:
        logger.error(f"Agent questionnaire generation failed: {e}")
        try:
            async with AsyncSession(get_db()) as db:
                await mark_generation_failed(db, flow_id)
        except Exception:
            pass
