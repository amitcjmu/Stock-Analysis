"""
Assessment Readiness Validation
Functions for checking if collection is ready for assessment transition.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.asset import Asset
from app.models.collection_flow import CollectionFlow
from app.models.collection_questionnaire_response import CollectionQuestionnaireResponse
from app.services.flow_configs.collection_flow_config import get_collection_flow_config


async def check_and_set_assessment_ready(
    flow: CollectionFlow,
    form_responses: Dict[str, Any],
    db: AsyncSession,
    context: RequestContext,
    logger: logging.Logger,
) -> None:
    """
    Check if collection has all required attributes and set assessment_ready=true if complete.

    Required attributes for assessment readiness:
    - business_criticality (or business_criticality_score)
    - environment (or deployment_environment)
    """
    try:
        # Get all responses for this flow to check if required attributes are filled
        responses_result = await db.execute(
            select(CollectionQuestionnaireResponse).where(
                CollectionQuestionnaireResponse.collection_flow_id == flow.id,
                CollectionQuestionnaireResponse.validation_status == "valid",
            )
        )
        all_responses = responses_result.scalars().all()

        # Build a set of all collected question IDs from database
        collected_question_ids = {r.question_id for r in all_responses}

        # CRITICAL: Include freshly submitted form_responses to ensure assessment_ready
        # can flip to True in the same request, even if validation_status is still "pending"
        if form_responses:
            freshly_submitted_ids = set(form_responses.keys())
            collected_question_ids.update(freshly_submitted_ids)
            logger.info(
                f"Added {len(freshly_submitted_ids)} freshly submitted question IDs to assessment check"
            )

        # Get configurable assessment readiness requirements from flow config
        # Updated per Qodo review to decouple logic from code
        flow_config = get_collection_flow_config()
        readiness_requirements = flow_config.default_configuration.get(
            "assessment_readiness_requirements",
            {
                # Fallback to defaults if config not available
                "business_criticality_questions": [
                    "business_criticality",
                    "business_criticality_score",
                ],
                "environment_questions": [
                    "environment",
                    "deployment_environment",
                    "hosting_environment",
                    "architecture_pattern",
                    "availability_requirements",
                ],
            },
        )

        # Check for required attributes using configurable question IDs
        # Business criticality is essential for 6R assessment
        has_business_criticality_from_questionnaire = any(
            qid in collected_question_ids
            for qid in readiness_requirements["business_criticality_questions"]
        )

        # Environment/deployment info - accept architecture_pattern or availability as proxies
        # These provide sufficient technical context for assessment
        has_environment_from_questionnaire = any(
            qid in collected_question_ids
            for qid in readiness_requirements["environment_questions"]
        )

        # CRITICAL FIX: Also check if these fields exist in asset data
        # Gap analysis doesn't create gaps for fields that already exist, so we must
        # check both questionnaire responses AND asset fields for assessment readiness
        selected_asset_ids = (flow.flow_metadata or {}).get("selected_asset_ids", [])
        has_business_criticality_from_assets = False
        has_environment_from_assets = False

        if selected_asset_ids:
            # Load assets to check if they have the required fields
            assets_result = await db.execute(
                select(Asset).where(
                    Asset.id.in_(selected_asset_ids),
                    Asset.client_account_id == context.client_account_id,
                    Asset.engagement_id == context.engagement_id,
                )
            )
            assets = list(assets_result.scalars().all())

            # Check if ANY asset has business_criticality
            for asset in assets:
                # Check criticality field or custom_attributes.business_criticality
                if asset.criticality:
                    has_business_criticality_from_assets = True
                elif asset.custom_attributes and asset.custom_attributes.get(
                    "business_criticality"
                ):
                    has_business_criticality_from_assets = True

                # Check environment field or custom_attributes.environment
                if asset.environment:
                    has_environment_from_assets = True
                elif asset.custom_attributes and asset.custom_attributes.get(
                    "environment"
                ):
                    has_environment_from_assets = True

                # Early exit if both found
                if has_business_criticality_from_assets and has_environment_from_assets:
                    break

        # Combine checks: field is satisfied if it exists in EITHER questionnaire OR asset fields
        has_business_criticality = (
            has_business_criticality_from_questionnaire
            or has_business_criticality_from_assets
        )
        has_environment_or_technical_detail = (
            has_environment_from_questionnaire or has_environment_from_assets
        )

        logger.info(
            f"Assessment readiness check - "
            f"business_criticality: {has_business_criticality} "
            f"(questionnaire: {has_business_criticality_from_questionnaire}, "
            f"assets: {has_business_criticality_from_assets}), "
            f"environment: {has_environment_or_technical_detail} "
            f"(questionnaire: {has_environment_from_questionnaire}, "
            f"assets: {has_environment_from_assets}), "
            f"total responses: {len(collected_question_ids)}"
        )

        # Set assessment_ready if all required attributes are present
        if has_business_criticality and has_environment_or_technical_detail:
            if not flow.assessment_ready:
                flow.assessment_ready = True
                flow.updated_at = datetime.utcnow()
                logger.info(
                    f"🔍 BUG#668: Setting assessment_ready=True for flow {flow.flow_id} via assessment_validation"
                )
                logger.info(
                    f"✅ Collection flow {flow.flow_id} is now ready for assessment! "
                    f"All required attributes collected."
                )
        else:
            missing = []
            if not has_business_criticality:
                missing.append("business_criticality")
            if not has_environment_or_technical_detail:
                missing.append("environment/technical_detail")
            logger.info(
                f"⚠️ Collection flow {flow.flow_id} not yet ready for assessment. "
                f"Missing: {', '.join(missing)}"
            )

    except Exception as e:
        logger.error(
            f"Error checking assessment readiness for flow {flow.flow_id}: {e}"
        )
        # Don't fail the entire submission if this check fails
        pass
