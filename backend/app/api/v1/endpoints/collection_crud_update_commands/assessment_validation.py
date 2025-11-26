"""
Assessment Readiness Validation
Functions for checking if collection is ready for assessment transition.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.context import RequestContext
from app.models.asset import Asset
from app.models.collection_flow import CollectionFlow
from app.models.collection_questionnaire_response import CollectionQuestionnaireResponse
from app.services.flow_configs.collection_flow_config import get_collection_flow_config


async def check_and_set_assessment_ready(  # noqa: C901
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

        # CRITICAL FIX: Check if ALL selected assets have completed questionnaires
        # Bug: Previously only checked if required fields exist, not if all assets have questionnaires
        selected_asset_ids = (flow.flow_metadata or {}).get("selected_asset_ids", [])
        all_questionnaires_completed = await _check_all_questionnaires_completed(
            flow, selected_asset_ids, db, logger
        )

        logger.info(
            f"Assessment readiness check - "
            f"business_criticality: {has_business_criticality} "
            f"(questionnaire: {has_business_criticality_from_questionnaire}, "
            f"assets: {has_business_criticality_from_assets}), "
            f"environment: {has_environment_or_technical_detail} "
            f"(questionnaire: {has_environment_from_questionnaire}, "
            f"assets: {has_environment_from_assets}), "
            f"total responses: {len(collected_question_ids)}, "
            f"all_questionnaires_completed: {all_questionnaires_completed}"
        )

        # Set assessment_ready if all required attributes are present AND all questionnaires completed
        if (
            has_business_criticality
            and has_environment_or_technical_detail
            and all_questionnaires_completed
        ):
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

                # CC FIX: Also update asset-level assessment_readiness for all selected assets
                # This ensures the "Start New Assessment" modal shows assets as ready
                if selected_asset_ids:
                    asset_uuids = [
                        UUID(aid) if isinstance(aid, str) else aid
                        for aid in selected_asset_ids
                    ]
                    await db.execute(
                        update(Asset)
                        .where(
                            Asset.id.in_(asset_uuids),
                            Asset.client_account_id == context.client_account_id,
                            Asset.engagement_id == context.engagement_id,
                        )
                        .values(
                            assessment_readiness="ready",
                            sixr_ready="ready",
                        )
                    )
                    logger.info(
                        f"✅ CC FIX: Updated {len(asset_uuids)} asset(s) to assessment_readiness='ready' "
                        f"(flow {flow.flow_id} assessment_ready=True)"
                    )
        else:
            missing = []
            if not has_business_criticality:
                missing.append("business_criticality")
            if not has_environment_or_technical_detail:
                missing.append("environment/technical_detail")
            if not all_questionnaires_completed:
                missing.append("incomplete questionnaires")
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


async def _check_all_questionnaires_completed(
    flow: CollectionFlow,
    selected_asset_ids: List[str],
    db: AsyncSession,
    logger: logging.Logger,
) -> bool:
    """
    Check if ALL selected assets are ready for assessment.

    Per ADR-037: Assets are ready for assessment if:
    1. They have a completed questionnaire, OR
    2. They have no questionnaire at all (IntelligentGapScanner found no TRUE gaps,
       meaning the asset already has complete data in existing sources)

    Returns True only if:
    1. There are selected assets
    2. Every selected asset either has a completed questionnaire OR has no questionnaire
       (assets with pending/ready/failed questionnaires are NOT ready)

    Returns False if any asset has an incomplete questionnaire (pending/ready/failed).
    """
    if not selected_asset_ids:
        logger.warning(
            f"⚠️ No selected_asset_ids found in flow metadata for flow {flow.flow_id}. "
            "Cannot verify all questionnaires completed."
        )
        return False

    # Import here to avoid circular dependency
    from app.models.collection_flow.adaptive_questionnaire_model import (
        AdaptiveQuestionnaire,
    )

    # Get ALL questionnaires for this flow (not just completed)
    all_questionnaires_result = await db.execute(
        select(AdaptiveQuestionnaire).where(
            AdaptiveQuestionnaire.collection_flow_id == flow.id,
        )
    )
    all_questionnaires = list(all_questionnaires_result.scalars().all())

    # Categorize assets by questionnaire status
    assets_with_completed_questionnaires = set()
    assets_with_incomplete_questionnaires = (
        set()
    )  # pending or ready (awaiting user input)
    assets_with_no_gaps_failures = (
        set()
    )  # "failed" but due to no TRUE gaps (asset complete)

    for questionnaire in all_questionnaires:
        # CC FIX: Check asset_id column FIRST (primary source), then fallback to target_gaps
        # The asset_id column is set during questionnaire creation and is the authoritative source
        # target_gaps may be empty in ADR-037 per-section generation flow
        asset_ids_for_questionnaire = set()

        # Primary: Check the questionnaire's asset_id column directly
        if questionnaire.asset_id:
            asset_ids_for_questionnaire.add(str(questionnaire.asset_id))

        # Fallback: Check questions for asset_id (legacy questionnaires stored it there)
        # Each question may have target_gaps array with asset_id
        if questionnaire.questions:
            for question in questionnaire.questions:
                if isinstance(question, dict):
                    question_gaps = question.get("target_gaps", [])
                    for gap in question_gaps:
                        if isinstance(gap, dict) and gap.get("asset_id"):
                            asset_ids_for_questionnaire.add(str(gap["asset_id"]))

        # Categorize based on completion status
        if questionnaire.completion_status == "completed":
            assets_with_completed_questionnaires.update(asset_ids_for_questionnaire)
        elif questionnaire.completion_status == "failed":
            # CC FIX: Distinguish between "no gaps" failures vs actual failures
            # "No questionnaires could be generated" = IntelligentGapScanner found no TRUE gaps
            # This means the asset already has complete data and is READY for assessment
            description = questionnaire.description or ""
            questions_count = (
                len(questionnaire.questions) if questionnaire.questions else 0
            )

            if (
                "No questionnaires could be generated" in description
                or "no TRUE gaps" in description.lower()
                or (questions_count == 0 and "generation failed" in description.lower())
            ):
                # Asset has complete data - treat as ready for assessment
                assets_with_no_gaps_failures.update(asset_ids_for_questionnaire)
                logger.debug(
                    f"Asset(s) {asset_ids_for_questionnaire} marked as ready "
                    f"(questionnaire failed due to no TRUE gaps)"
                )
            else:
                # Genuine failure - blocks assessment
                assets_with_incomplete_questionnaires.update(
                    asset_ids_for_questionnaire
                )
        else:
            # pending or ready - awaiting user input, blocks assessment
            assets_with_incomplete_questionnaires.update(asset_ids_for_questionnaire)

    # Convert selected_asset_ids to strings for comparison
    selected_asset_ids_set = {str(aid) for aid in selected_asset_ids}

    # CC FIX (ADR-037): Check for incomplete questionnaires instead of missing ones
    # Assets WITHOUT questionnaires are considered ready (IntelligentGapScanner found no TRUE gaps)
    # Assets WITH "no gaps" failures are also considered ready (same reason - complete data)
    # Only assets WITH pending/ready questionnaires or genuine failures should block assessment

    # Assets that are ready for assessment:
    # - Completed questionnaires
    # - "Failed" questionnaires due to no TRUE gaps (asset has complete data)
    assets_ready_for_assessment = (
        assets_with_completed_questionnaires | assets_with_no_gaps_failures
    )

    # Remove ready assets from incomplete set (in case same asset has multiple questionnaires)
    assets_blocking_assessment = (
        assets_with_incomplete_questionnaires - assets_ready_for_assessment
    )

    # Only check for blocking assets that are in the selected set
    blocking_selected_assets = assets_blocking_assessment & selected_asset_ids_set

    if blocking_selected_assets:
        # Some selected assets have questionnaires that aren't completed
        logger.info(
            f"⚠️ Not all questionnaires completed for flow {flow.flow_id}. "
            f"{len(selected_asset_ids_set)} selected assets, "
            f"{len(assets_with_completed_questionnaires)} with completed questionnaires, "
            f"{len(assets_with_no_gaps_failures)} with no TRUE gaps (ready), "
            f"{len(blocking_selected_assets)} with incomplete questionnaires blocking assessment"
        )
        return False

    # Count assets in different states for logging
    assets_with_questionnaires = (
        assets_with_completed_questionnaires
        | assets_with_incomplete_questionnaires
        | assets_with_no_gaps_failures
    )
    assets_without_questionnaires = selected_asset_ids_set - assets_with_questionnaires

    logger.info(
        f"✅ All selected assets ready for assessment in flow {flow.flow_id}: "
        f"{len(assets_with_completed_questionnaires)} completed questionnaires, "
        f"{len(assets_with_no_gaps_failures)} had no TRUE gaps (failed=complete), "
        f"{len(assets_without_questionnaires)} had no questionnaire at all (complete data)"
    )
    return True
