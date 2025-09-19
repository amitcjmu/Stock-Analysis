"""
Phase transition logic and state management.

Contains the core logic for atomic phase transitions with state machine validation.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.security.secure_logging import mask_id, safe_log_format
from app.models.discovery_flow import DiscoveryFlow

from .base import PHASE_FLAG_MAP, PhaseTransitionResult, is_valid_transition

logger = logging.getLogger(__name__)


async def advance_phase(  # noqa: C901
    db: AsyncSession,
    flow: DiscoveryFlow,
    target_phase: str,
    *,
    set_status: Optional[str] = None,
    extra_updates: Optional[dict] = None,
) -> PhaseTransitionResult:
    """
    Authoritative helper for atomic phase transitions with state machine validation.

    This is the single source of truth for all phase transitions.
    ALL direct phase updates should use this helper.

    Args:
        db: Database session (will create its own transaction for atomicity)
        flow: DiscoveryFlow instance (will be locked with SELECT FOR UPDATE)
        target_phase: Phase to transition to
        set_status: Optional status to set on child flow
        extra_updates: Optional additional field updates

    Returns:
        PhaseTransitionResult with success status and metadata
    """
    result = PhaseTransitionResult(
        success=False, was_idempotent=False, prior_phase=flow.current_phase, warnings=[]
    )

    try:
        # Lock the row for atomic update
        async with db.begin():
            # Re-fetch with FOR UPDATE lock
            stmt = (
                select(DiscoveryFlow)
                .where(
                    and_(
                        DiscoveryFlow.flow_id == flow.flow_id,
                        DiscoveryFlow.client_account_id == flow.client_account_id,
                        DiscoveryFlow.engagement_id == flow.engagement_id,
                    )
                )
                .with_for_update()
            )
            locked_result = await db.execute(stmt)
            locked_flow = locked_result.scalar_one_or_none()

            if not locked_flow:
                result.add_warning(f"Flow {flow.flow_id} not found for locking")
                return result

            # Check for idempotency
            if locked_flow.current_phase == target_phase:
                result.was_idempotent = True
                result.success = True
                result.add_warning(f"Phase {target_phase} already current, no-op")

                # Even if idempotent, check if flow is complete and update status/completed_at
                if locked_flow.is_complete():
                    if locked_flow.status != "completed":
                        locked_flow.status = "completed"
                        result.add_warning(
                            "Updated status to completed during idempotent check"
                        )
                    if locked_flow.completed_at is None:
                        locked_flow.completed_at = datetime.utcnow()
                        result.add_warning("Set completed_at during idempotent check")
                    await db.flush()

                return result

            # Validate transition using state machine
            if not is_valid_transition(locked_flow.current_phase, target_phase):
                result.add_warning(
                    f"Invalid transition from {locked_flow.current_phase} to {target_phase}"
                )
                return result

            # Mark prior phase as completed if mapping exists
            prior_phase = locked_flow.current_phase
            if prior_phase and prior_phase in PHASE_FLAG_MAP:
                flag_name = PHASE_FLAG_MAP[prior_phase]
                setattr(locked_flow, flag_name, True)

                # Update phases_completed list
                phases_completed = locked_flow.phases_completed or []
                if prior_phase not in phases_completed:
                    phases_completed.append(prior_phase)
                    locked_flow.phases_completed = phases_completed

            # Set new current phase
            locked_flow.current_phase = target_phase

            # Set status if provided
            if set_status:
                locked_flow.status = set_status

            # Apply extra updates
            if extra_updates:
                for field, value in extra_updates.items():
                    if hasattr(locked_flow, field):
                        setattr(locked_flow, field, value)
                    else:
                        result.add_warning(f"Unknown field '{field}' in extra_updates")

            # Update progress percentage
            locked_flow.update_progress()

            # Check for completion
            if locked_flow.is_complete():
                locked_flow.status = "completed"
                locked_flow.completed_at = datetime.utcnow()

            await db.flush()
            result.success = True
            result.prior_phase = prior_phase

            logger.info(
                safe_log_format(
                    "✅ Phase transition completed: flow_id={flow_id}, {prior} → {target}",
                    flow_id=mask_id(str(flow.flow_id)),
                    prior=prior_phase or "None",
                    target=target_phase,
                )
            )

    except Exception as e:
        result.add_warning(f"Phase transition failed: {str(e)}")
        logger.error(
            safe_log_format(
                "❌ Phase transition failed: flow_id={flow_id}, error={error}",
                flow_id=mask_id(str(flow.flow_id)),
                error=str(e),
            )
        )

    return result


async def advance_flow_phase(
    db: AsyncSession,
    context: RequestContext,
    flow_id: str,
    from_phase: str,
    to_phase: str,
) -> None:
    """
    Advance the flow to the next phase.

    DEPRECATED: Use advance_phase() directly for new code.
    Maintained for backward compatibility.

    Args:
        db: Database session
        context: Request context
        flow_id: Flow identifier
        from_phase: Current phase name
        to_phase: Next phase name
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
                    "⚠️ Flow not found for phase advance: flow_id={flow_id}",
                    flow_id=mask_id(str(flow_id)),
                )
            )
            return

        # Use new atomic helper
        transition_result = await advance_phase(db=db, flow=flow, target_phase=to_phase)

        if transition_result.success:
            logger.info(
                safe_log_format(
                    "✅ Flow phase advanced: flow_id={flow_id}, from={from_phase} to={to_phase}",
                    flow_id=mask_id(str(flow_id)),
                    from_phase=from_phase,
                    to_phase=to_phase,
                )
            )
        else:
            logger.warning(
                safe_log_format(
                    "⚠️ Flow phase advance failed: flow_id={flow_id}, warnings={warnings}",
                    flow_id=mask_id(str(flow_id)),
                    warnings=transition_result.warnings,
                )
            )

    except Exception as phase_update_error:
        logger.error(
            safe_log_format(
                "❌ Failed to advance flow phase: flow_id={flow_id}, error={error}",
                flow_id=mask_id(str(flow_id)),
                error=str(phase_update_error),
            )
        )
        # Don't fail the main execution if phase update fails
