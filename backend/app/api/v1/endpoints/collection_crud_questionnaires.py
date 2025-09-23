"""
Collection Flow Questionnaire Query Operations
Questionnaire-specific read operations for collection flows.
"""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.context import RequestContext
from app.models import User
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


async def get_adaptive_questionnaires(
    flow_id: str,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> List[AdaptiveQuestionnaireResponse]:
    """Get adaptive questionnaires for a collection flow.

    Args:
        flow_id: Collection flow ID
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        List of adaptive questionnaires

    Raises:
        HTTPException: If flow not found or unauthorized
    """
    try:
        # First verify the flow exists and user has access
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

        # Try to get questionnaires from database first
        questionnaires_result = await db.execute(
            select(AdaptiveQuestionnaire)
            .where(AdaptiveQuestionnaire.collection_flow_id == flow.id)
            .order_by(AdaptiveQuestionnaire.created_at.desc())
        )
        questionnaires = questionnaires_result.scalars().all()

        # If we have database questionnaires, serialize and return them
        if questionnaires:
            logger.info(
                f"Found {len(questionnaires)} questionnaires in database for flow {flow_id}"
            )
            return [
                collection_serializers.build_questionnaire_response(q)
                for q in questionnaires
            ]

        # Check master flow for generated questionnaires
        if flow.master_flow_id:
            try:
                # Note: get_questionnaires method not available in current MasterFlowOrchestrator
                # This is a placeholder for future implementation
                # from app.services.master_flow_orchestrator import MasterFlowOrchestrator
                # orchestrator = MasterFlowOrchestrator(db, context)
                # master_flow_questionnaires = await orchestrator.get_questionnaires(str(flow.master_flow_id))
                master_flow_questionnaires: List[AdaptiveQuestionnaireResponse] = []

                if master_flow_questionnaires:
                    logger.info(
                        f"Found {len(master_flow_questionnaires)} questionnaires from master flow"
                    )
                    return master_flow_questionnaires

            except Exception as mfo_error:
                logger.warning(
                    f"Failed to get questionnaires from master flow: {mfo_error}"
                )

        # Check if flow is already completed - if so, don't generate bootstrap
        if flow.status == "completed":
            logger.info(
                f"Flow {flow_id} is already completed. Returning empty questionnaire list."
            )
            return []

        # Check if we should use agent generation or bootstrap
        from app.core.feature_flags import is_feature_enabled

        use_agent = is_feature_enabled("collection.gaps.v2_agent_questionnaires", True)

        if use_agent:
            logger.info(
                f"No questionnaires found for flow {flow_id}, agent generation is enabled"
            )
            # Return empty list to trigger frontend polling
            # Frontend should call the generate endpoint
            return []

        # Fallback to bootstrap questionnaire if agent generation is disabled
        logger.info(
            f"No questionnaires found for flow {flow_id}, generating asset-aware bootstrap questionnaire"
        )

        # Fetch ALL existing assets from the database for this engagement
        # This implements the asset-agnostic collection approach from Phase 2
        from app.models.asset import Asset

        assets_result = await db.execute(
            select(Asset)
            .where(Asset.engagement_id == context.engagement_id)
            .where(Asset.client_account_id == context.client_account_id)
            .order_by(Asset.created_at.desc())
        )
        existing_assets = assets_result.scalars().all()

        logger.info(
            f"Found {len(existing_assets)} existing assets in the database for engagement {context.engagement_id}"
        )

        # Extract selected application info from flow config if already selected
        selected_application_name: Optional[str] = None
        selected_application_id = None

        if flow.collection_config and flow.collection_config.get(
            "selected_application_ids"
        ):
            selected_app_ids = flow.collection_config.get(
                "selected_application_ids", []
            )
            if selected_app_ids:
                selected_application_id = selected_app_ids[0]  # Use first selected app

                # Find the selected asset from our existing assets
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

        # Determine collection scope from flow config
        collection_scope = "engagement"  # Default scope
        if flow.collection_config:
            collection_scope = flow.collection_config.get("scope", "engagement")

        # Get bootstrap questionnaire template with asset list
        bootstrap_template = get_bootstrap_questionnaire_template(
            flow_id=flow_id,
            selected_application_id=selected_application_id,
            selected_application_name=selected_application_name,
            existing_assets=existing_assets,  # Pass the assets list
            scope=collection_scope,  # Pass the collection scope
        )

        # Convert template to AdaptiveQuestionnaireResponse
        bootstrap_questionnaire = AdaptiveQuestionnaireResponse(
            id=bootstrap_template["id"],
            collection_flow_id=bootstrap_template["flow_id"],
            title=bootstrap_template["title"],
            description=bootstrap_template["description"],
            target_gaps=[
                "application_selection",
                "basic_info",
                "technical_details",
                "infrastructure",
                "compliance",
            ],
            questions=[
                _convert_template_field_to_question(field, selected_application_name)
                for field in bootstrap_template["form_fields"]
            ],
            validation_rules=bootstrap_template["validation_rules"],
            completion_status="pending",  # Fixed: String instead of dict
            responses_collected={},  # Fixed: Dict instead of int
            created_at=datetime.fromisoformat(
                bootstrap_template["created_at"].replace("Z", "+00:00")
            ),
            completed_at=None,  # Template returns None, keep it None
        )

        logger.info(
            "Returning bootstrap questionnaire to enable in-form application selection"
        )
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
