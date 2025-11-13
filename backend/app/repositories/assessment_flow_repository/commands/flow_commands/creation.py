"""
Flow creation operations.

REPOSITORY LAYER: This file contains ONLY data persistence operations.
Business logic has been moved to AssessmentFlowLifecycleService per 7-layer architecture.
"""

import logging

logger = logging.getLogger(__name__)


async def create_assessment_flow(
    self,
    engagement_id: str,
    selected_application_ids: list,
    created_by: str | None = None,
    collection_flow_id: str | None = None,
    background_tasks: object | None = None,
) -> str:
    """
    DEPRECATED: This method signature is maintained for backward compatibility only.

    All business logic has been moved to AssessmentFlowLifecycleService.
    This method now delegates to the service layer.

    API endpoints should call AssessmentFlowLifecycleService.create_assessment_flow()
    directly instead of going through the repository.

    Args:
        engagement_id: Engagement UUID
        selected_application_ids: Asset IDs to assess
        created_by: User ID who created the flow
        collection_flow_id: Optional collection flow ID
        background_tasks: FastAPI BackgroundTasks for enrichment

    Returns:
        Master flow ID (UUID as string)

    Raises:
        NotImplementedError: This method should not be called directly.
            Use AssessmentFlowLifecycleService instead.
    """
    logger.error(
        "DEPRECATED: create_assessment_flow called on repository. "
        "Business logic has been moved to AssessmentFlowLifecycleService. "
        "Update calling code to use service layer instead."
    )
    raise NotImplementedError(
        "Repository layer no longer contains business logic. "
        "Use app.services.assessment.assessment_flow_lifecycle_service."
        "AssessmentFlowLifecycleService.create_assessment_flow() instead."
    )
