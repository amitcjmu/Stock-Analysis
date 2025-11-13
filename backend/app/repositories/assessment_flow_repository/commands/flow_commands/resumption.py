"""
Flow resumption operations.

REPOSITORY LAYER: This file contains ONLY data persistence operations.
Business logic has been moved to AssessmentFlowLifecycleService per 7-layer architecture.
"""

import logging

logger = logging.getLogger(__name__)


async def resume_flow(self, flow_id: str, user_input: dict) -> dict:
    """
    DEPRECATED: This method signature is maintained for backward compatibility only.

    All business logic (phase normalization, progression, validation) has been moved
    to AssessmentFlowLifecycleService per 7-layer architecture.

    API endpoints should call AssessmentFlowLifecycleService.resume_flow()
    directly instead of going through the repository.

    Args:
        flow_id: Master or child flow ID
        user_input: User-provided input for resumption

    Returns:
        Dict with flow transition details

    Raises:
        NotImplementedError: This method should not be called directly.
            Use AssessmentFlowLifecycleService instead.
    """
    logger.error(
        "DEPRECATED: resume_flow called on repository. "
        "Business logic has been moved to AssessmentFlowLifecycleService. "
        "Update calling code to use service layer instead."
    )
    raise NotImplementedError(
        "Repository layer no longer contains business logic. "
        "Use app.services.assessment.assessment_flow_lifecycle_service."
        "AssessmentFlowLifecycleService.resume_flow() instead."
    )
