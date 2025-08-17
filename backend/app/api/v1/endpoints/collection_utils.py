"""
Collection Flow Utilities
Helper functions for collection flow operations including time handling,
status determination, progress calculations, and external service interactions.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.security.secure_logging import safe_log_format
from app.models.collection_flow import (
    CollectionFlow,
    CollectionFlowStatus,
    CollectionPhase,
)
from app.services.master_flow_orchestrator import MasterFlowOrchestrator
from app.services.integration.data_flow_validator import DataFlowValidator
from app.services.integration.failure_journal import log_failure

logger = logging.getLogger(__name__)


def ensure_timezone_aware(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware, assuming UTC if naive.

    Args:
        dt: Datetime object that may or may not be timezone-aware

    Returns:
        Timezone-aware datetime object
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def calculate_time_since_creation(created_at: datetime) -> timedelta:
    """Calculate time elapsed since creation with proper timezone handling.

    Args:
        created_at: Creation timestamp

    Returns:
        Timedelta representing elapsed time
    """
    now = datetime.now(timezone.utc)
    created_at_aware = ensure_timezone_aware(created_at)
    return now - created_at_aware


def is_flow_stuck_in_initialization(
    flow: CollectionFlow, timeout_minutes: int = 5
) -> bool:
    """Check if a flow is stuck in INITIALIZED state beyond timeout.

    Args:
        flow: Collection flow to check
        timeout_minutes: Timeout in minutes (default 5)

    Returns:
        True if flow is stuck, False otherwise
    """
    if flow.status != CollectionFlowStatus.INITIALIZED.value:
        return False

    time_since_creation = calculate_time_since_creation(flow.created_at)
    return time_since_creation > timedelta(minutes=timeout_minutes)


def determine_next_phase_status(next_phase: str) -> str:
    """Determine the appropriate flow status based on next phase.

    Args:
        next_phase: The next phase name

    Returns:
        Appropriate collection flow status
    """
    phase_status_mapping = {
        CollectionPhase.PLATFORM_DETECTION.value: CollectionFlowStatus.PLATFORM_DETECTION.value,
        CollectionPhase.GAP_ANALYSIS.value: CollectionFlowStatus.GAP_ANALYSIS.value,
    }

    return phase_status_mapping.get(
        next_phase, CollectionFlowStatus.AUTOMATED_COLLECTION.value
    )


def calculate_progress_percentage(
    milestones_completed: int, total_milestones: int
) -> float:
    """Calculate progress percentage from completed milestones.

    Args:
        milestones_completed: Number of completed milestones
        total_milestones: Total number of milestones

    Returns:
        Progress percentage (0.0 to 100.0)
    """
    if total_milestones <= 0:
        return 0.0
    return min(100.0, (milestones_completed / total_milestones) * 100.0)


async def create_mfo_flow(
    db: AsyncSession,
    context: RequestContext,
    flow_type: str,
    initial_state: Dict[str, Any],
) -> Tuple[str, Dict[str, Any]]:
    """Create a flow through Master Flow Orchestrator.

    Args:
        db: Database session
        context: Request context
        flow_type: Type of flow to create
        initial_state: Initial state for the flow

    Returns:
        Tuple of (master_flow_id, master_flow_data)

    Raises:
        Exception: If flow creation fails
    """
    mfo = MasterFlowOrchestrator(db, context)
    return await mfo.create_flow(flow_type=flow_type, initial_state=initial_state)


async def execute_mfo_phase(
    db: AsyncSession,
    context: RequestContext,
    flow_id: str,
    phase_name: str,
    phase_input: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute a phase through Master Flow Orchestrator.

    Args:
        db: Database session
        context: Request context
        flow_id: Flow ID to execute
        phase_name: Name of phase to execute
        phase_input: Input data for the phase

    Returns:
        Execution result

    Raises:
        Exception: If execution fails
    """
    mfo = MasterFlowOrchestrator(db, context)
    return await mfo.execute_phase(
        flow_id=flow_id, phase_name=phase_name, phase_input=phase_input
    )


async def resume_mfo_flow(
    db: AsyncSession,
    context: RequestContext,
    flow_id: str,
    resume_context: Dict[str, Any],
) -> Dict[str, Any]:
    """Resume a flow through Master Flow Orchestrator.

    Args:
        db: Database session
        context: Request context
        flow_id: Flow ID to resume
        resume_context: Context for resuming the flow

    Returns:
        Resume result

    Raises:
        Exception: If resume fails
    """
    mfo = MasterFlowOrchestrator(db, context)
    return await mfo.resume_flow(flow_id=flow_id, resume_context=resume_context)


async def delete_mfo_flow(
    db: AsyncSession, context: RequestContext, flow_id: str
) -> None:
    """Delete a flow from Master Flow Orchestrator.

    Args:
        db: Database session
        context: Request context
        flow_id: Flow ID to delete

    Note:
        This is best-effort and logs warnings on failure
    """
    try:
        mfo = MasterFlowOrchestrator(db, context)
        await mfo.delete_flow(flow_id)
    except Exception as e:
        logger.warning(
            safe_log_format(
                "MFO deletion failed for flow {flow_id}: {e}", flow_id=flow_id, e=e
            )
        )


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


def format_flow_display_name(
    application_count: int, timestamp: Optional[datetime] = None
) -> str:
    """Format a display name for a collection flow.

    Args:
        application_count: Number of applications in the flow
        timestamp: Optional timestamp (defaults to current time)

    Returns:
        Formatted display name
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    if application_count > 0:
        return f"Collection from Discovery - {application_count} apps"
    else:
        return f"Collection Flow - {timestamp.strftime('%Y-%m-%d %H:%M')}"


def estimate_completion_time(phase: str, application_count: int = 1) -> int:
    """Estimate completion time in seconds for a collection phase.

    Args:
        phase: Collection phase name
        application_count: Number of applications

    Returns:
        Estimated time in seconds
    """
    base_times = {
        CollectionPhase.INITIALIZATION.value: 30,
        CollectionPhase.PLATFORM_DETECTION.value: 60,
        CollectionPhase.GAP_ANALYSIS.value: 120,
        CollectionPhase.AUTOMATED_COLLECTION.value: 300,
    }

    base_time = base_times.get(phase, 60)
    # Scale with application count but with diminishing returns
    scaling_factor = min(application_count * 0.5, 5.0)
    return int(base_time * (1 + scaling_factor))


def safe_format_error(
    error: Exception, default_message: str = "An error occurred"
) -> str:
    """Safely format an error message for logging.

    Args:
        error: Exception to format
        default_message: Default message if formatting fails

    Returns:
        Formatted error message
    """
    try:
        return safe_log_format("Error: {e}", e=error)
    except Exception:
        return default_message


def normalize_uuid(value: Any) -> Optional[UUID]:
    """Normalize a value to UUID, handling strings and None.

    Args:
        value: Value to normalize (UUID, string, or None)

    Returns:
        UUID object or None if conversion fails
    """
    if value is None:
        return None

    if isinstance(value, UUID):
        return value

    try:
        return UUID(str(value))
    except (ValueError, TypeError):
        return None
