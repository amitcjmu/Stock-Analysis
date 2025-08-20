"""
Collection Validation Utilities
Validation and failure logging utilities for collection flows including
data flow validation and failure journal integration.
"""

import logging
from typing import Any, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.security.secure_logging import safe_log_format
from app.services.integration.data_flow_validator import DataFlowValidator
from app.services.integration.failure_journal import log_failure

logger = logging.getLogger(__name__)


async def validate_data_flow(
    db: AsyncSession, engagement_id: UUID, validation_scope: set
) -> Dict[str, Any]:
    """Validate data flow for collection/discovery phases.

    Args:
        db: Database session
        engagement_id: Engagement ID to validate
        validation_scope: Set of phases to validate

    Returns:
        Validation results with phase scores and issues
    """
    try:
        validator = DataFlowValidator()
        validation = await validator.validate_end_to_end_data_flow(
            engagement_id=engagement_id,
            validation_scope=validation_scope,
            session=db,
        )

        return {
            "phase_scores": validation.phase_scores,
            "issues": {
                "total": len(validation.issues),
                "critical": len(
                    [i for i in validation.issues if i.severity.value == "critical"]
                ),
                "warning": len(
                    [i for i in validation.issues if i.severity.value == "warning"]
                ),
                "info": len(
                    [i for i in validation.issues if i.severity.value == "info"]
                ),
            },
            "readiness": {
                "architecture_minimums_present": validation.summary.get(
                    "architecture_minimums_present", False
                ),
                "missing_fields": validation.summary.get("missing_fields", []),
                "readiness_score": validation.summary.get("readiness_score", 0.0),
            },
        }
    except Exception as e:
        logger.warning(safe_log_format("Validator unavailable for readiness: {e}", e=e))
        return {
            "phase_scores": {"collection": 0.0, "discovery": 0.0},
            "issues": {"total": 0, "critical": 0, "warning": 0, "info": 0},
            "readiness": {
                "architecture_minimums_present": False,
                "missing_fields": [],
                "readiness_score": 0.0,
            },
        }


async def log_collection_failure(
    db: AsyncSession,
    context: RequestContext,
    source: str,
    operation: str,
    payload: Dict[str, Any],
    error_message: str,
) -> None:
    """Log a failure to the failure journal.

    Args:
        db: Database session
        context: Request context
        source: Source of the failure
        operation: Operation that failed
        payload: Payload data
        error_message: Error message

    Note:
        This is best-effort and won't raise exceptions
    """
    try:
        await log_failure(
            db,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            source=source,
            operation=operation,
            payload=payload,
            error_message=error_message,
        )
    except Exception as e:
        logger.warning(safe_log_format("Failed to log failure: {e}", e=e))
