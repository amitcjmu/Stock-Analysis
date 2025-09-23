"""
Collection Flow Questionnaire Query Operations
Questionnaire-specific read operations for collection flows.
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.context import RequestContext
from app.models import User
from app.models.asset import Asset
from app.models.collection_flow import CollectionFlow, AdaptiveQuestionnaire
from app.schemas.collection_flow import (
    AdaptiveQuestionnaireResponse,
)

# Import modular functions
from app.api.v1.endpoints import collection_serializers
from app.api.v1.endpoints.questionnaire_templates import (
    get_bootstrap_questionnaire_template,
)

logger = logging.getLogger(__name__)


async def _get_flow_by_id(
    flow_id: str, db: AsyncSession, context: RequestContext
) -> CollectionFlow:
    """Get and validate collection flow by ID."""
    flow_result = await db.execute(
        select(CollectionFlow).where(
            CollectionFlow.flow_id == UUID(flow_id),
            CollectionFlow.engagement_id == context.engagement_id,
            CollectionFlow.client_account_id == context.client_account_id,
        )
    )
    flow = flow_result.scalar_one_or_none()
    if not flow:
        logger.warning(f"Collection flow not found: {flow_id}")
        raise HTTPException(status_code=404, detail="Collection flow not found")
    return flow


async def _get_existing_questionnaires(
    flow: CollectionFlow, db: AsyncSession
) -> List[AdaptiveQuestionnaireResponse]:
    """Get existing questionnaires from database."""
    questionnaires_result = await db.execute(
        select(AdaptiveQuestionnaire)
        .where(AdaptiveQuestionnaire.collection_flow_id == flow.id)
        .order_by(AdaptiveQuestionnaire.created_at.desc())
    )
    questionnaires = questionnaires_result.scalars().all()

    if questionnaires:
        logger.info(f"Found {len(questionnaires)} questionnaires in database")
        return [
            collection_serializers.build_questionnaire_response(q)
            for q in questionnaires
        ]
    return []


async def _get_existing_assets(
    db: AsyncSession, context: RequestContext
) -> List[Asset]:
    """Get existing assets for engagement."""
    assets_result = await db.execute(
        select(Asset)
        .where(Asset.engagement_id == context.engagement_id)
        .where(Asset.client_account_id == context.client_account_id)
        .order_by(Asset.created_at.desc())
    )
    return list(assets_result.scalars().all())


def _get_selected_application_info(
    flow: CollectionFlow, existing_assets: List[Asset]
) -> tuple[Optional[str], Optional[str]]:
    """Extract selected application info from flow config."""
    selected_application_name: Optional[str] = None
    selected_application_id: Optional[str] = None

    if flow.collection_config and flow.collection_config.get(
        "selected_application_ids"
    ):
        selected_app_ids = flow.collection_config.get("selected_application_ids", [])
        if selected_app_ids:
            selected_application_id = selected_app_ids[0]

            for asset in existing_assets:
                if str(asset.id) == str(selected_application_id):
                    selected_application_name = str(
                        asset.name or asset.application_name or ""
                    )
                    logger.info(
                        f"Pre-populating questionnaire with application: "
                        f"{selected_application_name} (ID: {selected_application_id})"
                    )
                    break
            else:
                logger.warning(
                    f"Selected application {selected_application_id} not found in asset inventory"
                )

    return selected_application_name, selected_application_id


async def get_adaptive_questionnaires(
    flow_id: str,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> List[AdaptiveQuestionnaireResponse]:
    """Get adaptive questionnaires for a collection flow."""
    try:
        # Get and validate flow
        flow = await _get_flow_by_id(flow_id, db, context)

        # Try existing questionnaires first
        existing_questionnaires = await _get_existing_questionnaires(flow, db)
        if existing_questionnaires:
            return existing_questionnaires

        # Check if flow is completed
        if flow.status == "completed":
            logger.info(f"Flow {flow_id} is completed. Returning empty list.")
            return []

        # Get existing assets needed for both agent and bootstrap generation
        existing_assets = await _get_existing_assets(db, context)

        # Check agent generation feature flag
        from app.core.feature_flags import is_feature_enabled

        use_agent = is_feature_enabled("collection.gaps.v2_agent_questionnaires", True)

        if use_agent:
            logger.info(f"Agent generation enabled for flow {flow_id}")
            try:
                # Try agent generation with timeout
                agent_questionnaires = await asyncio.wait_for(
                    _generate_agent_questionnaires(
                        flow_id, flow, existing_assets, context
                    ),
                    timeout=30.0,  # 30 second timeout
                )
                if agent_questionnaires:
                    logger.info(f"Agent generation successful for flow {flow_id}")
                    return agent_questionnaires
                else:
                    logger.warning(
                        f"Agent generation returned empty for flow {flow_id}, falling back to bootstrap"
                    )
            except asyncio.TimeoutError:
                logger.warning(
                    f"Agent generation timed out for flow {flow_id}, falling back to bootstrap"
                )
            except Exception as e:
                logger.error(
                    f"Agent generation failed for flow {flow_id}: {e}, falling back to bootstrap"
                )

            # Fall through to bootstrap generation

        # Generate bootstrap questionnaire
        logger.info(f"Generating bootstrap questionnaire for flow {flow_id}")
        selected_app_name, selected_app_id = _get_selected_application_info(
            flow, existing_assets
        )

        collection_scope = "engagement"
        if flow.collection_config:
            collection_scope = flow.collection_config.get("scope", "engagement")

        bootstrap_template = get_bootstrap_questionnaire_template(
            flow_id=flow_id,
            selected_application_id=selected_app_id,
            selected_application_name=selected_app_name,
            existing_assets=existing_assets,
            scope=collection_scope,
        )

        bootstrap_questionnaire = AdaptiveQuestionnaireResponse(
            id=bootstrap_template["id"],
            collection_flow_id=bootstrap_template["flow_id"],
            title=f"{bootstrap_template['title']} (Bootstrap)",
            description=f"{bootstrap_template['description']} - Generated using bootstrap template",
            target_gaps=[
                "application_selection",
                "basic_info",
                "technical_details",
                "infrastructure",
                "compliance",
            ],
            questions=[
                _convert_template_field_to_question(field, selected_app_name)
                for field in bootstrap_template["form_fields"]
            ],
            validation_rules=bootstrap_template["validation_rules"],
            completion_status="pending",
            responses_collected={},
            created_at=datetime.fromisoformat(
                bootstrap_template["created_at"].replace("Z", "+00:00")
            ),
            completed_at=None,
        )

        logger.info("Returning bootstrap questionnaire")
        return [bootstrap_questionnaire]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting adaptive questionnaires for flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _convert_template_field_to_question(
    field: dict, selected_application_name: Optional[str] = None
) -> dict:
    """Convert a template field to a questionnaire question format.

    Args:
        field: Field from questionnaire template
        selected_application_name: Name of pre-selected application

    Returns:
        Question dictionary
    """
    question = {
        "field_id": field["field_id"],
        "question_text": field["question_text"],
        "field_type": field["field_type"],
        "required": field["required"],
        "category": field["category"],
        "options": field.get("options", []),
        "help_text": field.get("help_text", ""),
        "multiple": field.get("multiple", False),
        "metadata": field.get("metadata", {}),
    }

    # Pre-fill values if available
    if field["field_id"] == "application_name" and selected_application_name:
        question["default_value"] = selected_application_name
    elif field["field_id"] == "asset_name" and selected_application_name:
        question["default_value"] = selected_application_name

    # Handle default values for asset selector
    if field.get("default_value"):
        question["default_value"] = field["default_value"]

    return question


async def _generate_agent_questionnaires(
    flow_id: str,
    flow: CollectionFlow,
    existing_assets: List[Asset],
    context: RequestContext,
) -> List[AdaptiveQuestionnaireResponse]:
    """Generate questionnaires using AI agent with hybrid fallback."""
    try:
        from app.services.ai_analysis.questionnaire_generator import (
            QuestionnaireService,
            QuestionnaireProcessor,
        )
        from app.services.ai_analysis.questionnaire_generator.agents import (
            QuestionnaireAgentManager,
        )
        from app.services.ai_analysis.questionnaire_generator.tasks import (
            QuestionnaireTaskManager,
        )

        # Initialize questionnaire generation service
        agent_manager = QuestionnaireAgentManager()
        agents = agent_manager.create_agents()

        # Create task inputs for questionnaire generation
        task_inputs = {
            "gap_analysis": (
                flow.persistence_data.get("gap_analysis", {})
                if flow.persistence_data
                else {}
            ),
            "business_context": flow.collection_config or {},
            "collection_flow_id": flow_id,
            "stakeholder_context": {},
            "automation_tier": "tier_2",
        }

        task_manager = QuestionnaireTaskManager(agents)
        tasks = task_manager.create_tasks(task_inputs)

        processor = QuestionnaireProcessor(
            agents=agents, tasks=tasks, name="questionnaire_generation"
        )
        service = QuestionnaireService(processor)

        # Prepare data gaps context
        data_gaps = [
            {"gap_type": "application_selection", "priority": "critical"},
            {"gap_type": "basic_info", "priority": "high"},
            {"gap_type": "technical_details", "priority": "medium"},
            {"gap_type": "infrastructure", "priority": "medium"},
            {"gap_type": "compliance", "priority": "low"},
        ]

        # Generate questionnaires
        questionnaires_data = await service.generate_questionnaires(
            data_gaps=data_gaps,
            business_context={"flow_id": flow_id, "scope": "engagement"},
            automation_tier="tier_2",
            collection_flow_id=flow_id,
        )

        # Convert to response format
        result = []
        for idx, q_data in enumerate(questionnaires_data):
            questionnaire = AdaptiveQuestionnaireResponse(
                id=q_data.get("id", f"agent-generated-{idx}"),
                collection_flow_id=flow_id,
                title=f"{q_data.get('title', 'AI-Generated Questionnaire')} (Agent)",
                description=(
                    f"{q_data.get('description', 'Generated by AI agent')} - "
                    "Created using AI questionnaire agent"
                ),
                target_gaps=[
                    "application_selection",
                    "basic_info",
                    "technical_details",
                ],
                questions=q_data.get("questions", []),
                validation_rules=q_data.get("validation_rules", {}),
                completion_status="pending",
                responses_collected={},
                created_at=datetime.now(),
                completed_at=None,
            )
            result.append(questionnaire)

        logger.info(f"Generated {len(result)} questionnaires using AI agent")
        return result

    except ImportError as e:
        logger.warning(f"Questionnaire generation service not available: {e}")
        return []
    except Exception as e:
        logger.error(f"Failed to generate questionnaires with agent: {e}")
        return []
