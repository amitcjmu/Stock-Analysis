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
from app.models.collection_flow import CollectionFlow
from app.models.collection_questionnaire_response import CollectionQuestionnaireResponse


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

        # Check for required attributes (normalized field names)
        # Business criticality is essential for 6R assessment
        has_business_criticality = any(
            qid in collected_question_ids
            for qid in ["business_criticality", "business_criticality_score"]
        )

        # Environment/deployment info - accept architecture_pattern or availability as proxies
        # These provide sufficient technical context for assessment
        has_environment_or_technical_detail = any(
            qid in collected_question_ids
            for qid in [
                "environment",
                "deployment_environment",
                "hosting_environment",
                "architecture_pattern",  # Proxy: indicates deployment sophistication
                "availability_requirements",  # Proxy: indicates environment needs
            ]
        )

        logger.info(
            f"Assessment readiness check - business_criticality: {has_business_criticality}, "
            f"technical_detail: {has_environment_or_technical_detail}, total responses: {len(collected_question_ids)}"
        )

        # Set assessment_ready if all required attributes are present
        if has_business_criticality and has_environment_or_technical_detail:
            if not flow.assessment_ready:
                flow.assessment_ready = True
                flow.updated_at = datetime.utcnow()
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
