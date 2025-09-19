"""
Data persistence functions for phase completion and error handling.

Contains functions for persisting phase data, errors, and completion states.
"""

import logging
from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.security.secure_logging import mask_id, safe_log_format
from app.models.discovery_flow import DiscoveryFlow
from app.repositories.discovery_flow_repository.commands.flow_phase_management import (
    FlowPhaseManagementCommands,
)

from .transitions import advance_phase
from .utils import extract_agent_insights, extract_next_phase

logger = logging.getLogger(__name__)


async def persist_if_changed(
    db: AsyncSession, flow: DiscoveryFlow, **flag_updates
) -> bool:
    """
    Utility function to persist flag changes with write-through semantics.

    Args:
        db: Database session
        flow: DiscoveryFlow instance
        **flag_updates: Flag name to value mappings

    Returns:
        True if any changes were persisted
    """
    changes_made = False

    for flag_name, new_value in flag_updates.items():
        if hasattr(flow, flag_name):
            current_value = getattr(flow, flag_name)
            if current_value != new_value:
                setattr(flow, flag_name, new_value)
                changes_made = True
        else:
            logger.warning(
                safe_log_format(
                    "⚠️ Unknown flag in persist_if_changed: {flag}", flag=flag_name
                )
            )

    if changes_made:
        flow.update_progress()
        await db.flush()

        logger.info(
            safe_log_format(
                "✅ Flag changes persisted: flow_id={flow_id}, flags={flags}",
                flow_id=mask_id(str(flow.flow_id)),
                flags=list(flag_updates.keys()),
            )
        )

    return changes_made


async def persist_error_with_classification(
    db: AsyncSession,
    flow: DiscoveryFlow,
    error: Exception,
    phase: str,
    error_code: str,
    recovery_hint: str = "",
    is_retryable: bool = False,
) -> None:
    """
    Persist error information with classification for recovery.

    Args:
        db: Database session
        flow: DiscoveryFlow instance
        error: Exception that occurred
        phase: Phase where error occurred
        error_code: Structured error code
        recovery_hint: Human readable recovery guidance
        is_retryable: Whether error is retryable
    """
    try:
        # Classify error type
        error_type = "unknown"
        if "timeout" in str(error).lower() or "connection" in str(error).lower():
            error_type = "transient_io"
            is_retryable = True
        elif "validation" in str(error).lower() or "invalid" in str(error).lower():
            error_type = "validation"
            is_retryable = False
        elif "permission" in str(error).lower() or "auth" in str(error).lower():
            error_type = "permission"
            is_retryable = False

        # Structure error details
        error_details = {
            "error_code": error_code,
            "error_type": error_type,
            "is_retryable": is_retryable,
            "recovery_hint": recovery_hint,
            "timestamp": datetime.utcnow().isoformat(),
            "exception_type": type(error).__name__,
        }

        # Update flow with error information
        flow.error_message = str(error)[:1000]  # Truncate to avoid DB issues
        flow.error_phase = phase
        flow.error_details = error_details

        await db.flush()

        logger.error(
            safe_log_format(
                "❌ Error persisted: flow_id={flow_id}, phase={phase}, code={code}, retryable={retryable}",
                flow_id=mask_id(str(flow.flow_id)),
                phase=phase,
                code=error_code,
                retryable=is_retryable,
            )
        )

    except Exception as persist_error:
        logger.error(
            safe_log_format(
                "❌ Failed to persist error: flow_id={flow_id}, error={error}",
                flow_id=mask_id(str(flow.flow_id)),
                error=str(persist_error),
            )
        )


async def persist_phase_completion(
    db: AsyncSession,
    context: RequestContext,
    flow_id: str,
    phase_name: str,
    result: Dict[str, Any],
) -> None:
    """
    Persist phase completion and update flow state.

    DEPRECATED: Use advance_phase() directly for new code.
    Maintained for backward compatibility.

    Args:
        db: Database session
        context: Request context
        flow_id: Flow identifier
        phase_name: Name of the completed phase
        result: Execution result from MFO
    """
    try:
        # Get the flow
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == UUID(flow_id),
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
            )
        )
        flow_result = await db.execute(stmt)
        flow = flow_result.scalar_one_or_none()

        if not flow:
            logger.warning(
                safe_log_format(
                    "⚠️ Flow not found for phase completion: flow_id={flow_id}",
                    flow_id=mask_id(str(flow_id)),
                )
            )
            return

        # Use legacy flow phase management for data persistence
        phase_mgmt = FlowPhaseManagementCommands(
            db, context.client_account_id, context.engagement_id
        )

        # Extract phase data and agent insights from the result
        phase_data = result.get("result", {}).get("crew_results", {}) or {}
        agent_insights = extract_agent_insights(result)

        # Call update_phase_completion to persist phase completion
        await phase_mgmt.update_phase_completion(
            flow_id=flow_id,
            phase=phase_name,
            data=phase_data,
            completed=True,
            agent_insights=agent_insights,
        )

        logger.info(
            safe_log_format(
                "✅ Phase completion persisted: flow_id={flow_id}, phase={phase}",
                flow_id=mask_id(str(flow_id)),
                phase=phase_name,
            )
        )

        # Update current_phase to next_phase if provided using new helper
        next_phase = extract_next_phase(result)
        if next_phase:
            transition_result = await advance_phase(
                db=db, flow=flow, target_phase=next_phase
            )

            if not transition_result.success:
                logger.warning(
                    safe_log_format(
                        "⚠️ Phase transition failed: flow_id={flow_id}, warnings={warnings}",
                        flow_id=mask_id(str(flow_id)),
                        warnings=transition_result.warnings,
                    )
                )

    except Exception as persistence_error:
        logger.error(
            safe_log_format(
                "❌ Failed to persist phase completion: flow_id={flow_id}, phase={phase}, error={error}",
                flow_id=mask_id(str(flow_id)),
                phase=phase_name,
                error=str(persistence_error),
            )
        )
        # Don't fail the main execution if persistence fails


async def persist_field_mapping_completion(
    db: AsyncSession,
    context: RequestContext,
    flow_id: str,
    result: Any,
) -> None:
    """
    Persist field mapping phase completion.

    Args:
        db: Database session
        context: Request context
        flow_id: Flow identifier
        result: Phase execution result
    """
    try:
        phase_mgmt = FlowPhaseManagementCommands(
            db, context.client_account_id, context.engagement_id
        )

        # Call update_phase_completion to persist field mapping completion
        await phase_mgmt.update_phase_completion(
            flow_id=flow_id,
            phase="field_mapping",
            data=result.data if hasattr(result, "data") else {},
            completed=True,
            agent_insights=[
                {
                    "type": "completion",
                    "content": "Field mapping phase completed successfully",
                }
            ],
        )

        logger.info(
            safe_log_format(
                "✅ Field mapping completion persisted: flow_id={flow_id}",
                flow_id=mask_id(str(flow_id)),
            )
        )

    except Exception as persistence_error:
        logger.error(
            safe_log_format(
                "❌ Failed to persist field mapping completion: flow_id={flow_id}, error={error}",
                flow_id=mask_id(str(flow_id)),
                error=str(persistence_error),
            )
        )
        # Don't fail the main execution if persistence fails
