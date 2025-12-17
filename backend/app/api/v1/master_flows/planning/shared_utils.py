"""
Shared utilities for planning flow endpoints.

Consolidates common logic for:
- UUID parsing and validation
- Date parsing with strict ISO 8601 validation
- Background task execution with lifecycle management

Per Qodo Bot security review:
- Proper task lifecycle management (no orphaned asyncio.create_task)
- Strict date parsing to prevent timezone manipulation
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import HTTPException

from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal

# Planning services removed - planning flow functionality disabled
# from app.services.planning import execute_wave_planning_for_flow

logger = logging.getLogger(__name__)

# Track active background tasks for proper lifecycle management
_active_planning_tasks: Dict[str, asyncio.Task] = {}


def parse_uuid(value: Any, field_name: str = "UUID") -> UUID:
    """Parse and validate a single UUID value.

    Args:
        value: String or UUID to parse
        field_name: Name for error messages

    Returns:
        Validated UUID

    Raises:
        HTTPException: If UUID format is invalid
    """
    if isinstance(value, UUID):
        return value
    if not value:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} is required",
        )
    try:
        return UUID(str(value))
    except (ValueError, TypeError) as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {field_name} format: {str(e)}",
        )


def parse_tenant_uuids(
    client_account_id: Any,
    engagement_id: Any,
    planning_flow_id: Optional[Any] = None,
) -> tuple:
    """Parse and validate tenant UUIDs from context.

    Args:
        client_account_id: Client account ID (string or UUID)
        engagement_id: Engagement ID (string or UUID)
        planning_flow_id: Optional planning flow ID (string or UUID)

    Returns:
        Tuple of (client_account_uuid, engagement_uuid) or
        (planning_flow_uuid, client_account_uuid, engagement_uuid) if planning_flow_id provided

    Raises:
        HTTPException: If any UUID format is invalid
    """
    client_account_uuid = parse_uuid(client_account_id, "client_account_id")
    engagement_uuid = parse_uuid(engagement_id, "engagement_id")

    if planning_flow_id is not None:
        planning_flow_uuid = parse_uuid(planning_flow_id, "planning_flow_id")
        return planning_flow_uuid, client_account_uuid, engagement_uuid

    return client_account_uuid, engagement_uuid


def parse_migration_date(date_str: Optional[str]) -> datetime:
    """Parse migration start date with strict ISO 8601 validation.

    Per Qodo Bot security review: Enforces strict ISO 8601 format with
    timezone to prevent timezone-naive inputs causing date shifts.

    Supported formats:
    - YYYY-MM-DD (date only, assumes UTC)
    - YYYY-MM-DDTHH:MM:SS (no TZ, rejected)
    - YYYY-MM-DDTHH:MM:SSZ (UTC)
    - YYYY-MM-DDTHH:MM:SS+00:00 (explicit TZ)

    Args:
        date_str: ISO format date string

    Returns:
        Timezone-aware datetime (always UTC)

    Raises:
        ValueError: If format is invalid or timezone-naive with time
    """
    if not date_str:
        return datetime.now(timezone.utc)

    # Date-only format (YYYY-MM-DD) - safe to assume UTC
    if len(date_str) == 10 and "-" in date_str:
        try:
            parsed = datetime.strptime(date_str, "%Y-%m-%d")
            return parsed.replace(tzinfo=timezone.utc)
        except ValueError as e:
            raise ValueError(f"Invalid date format '{date_str}': {e}")

    # Full timestamp - must have timezone
    if "T" in date_str:
        # Normalize Z to +00:00
        normalized = date_str.replace("Z", "+00:00")

        # Check for timezone indicator (+ or - after time portion)
        # Valid: 2025-01-01T12:00:00+00:00, 2025-01-01T12:00:00-05:00
        # Invalid: 2025-01-01T12:00:00 (no timezone)
        time_part = normalized.split("T")[1] if "T" in normalized else ""
        has_timezone = "+" in time_part or (
            "-" in time_part and time_part.count("-") > 0
        )

        if not has_timezone and len(normalized) > 19:
            # Has microseconds but no timezone
            has_timezone = "+" in normalized[19:] or "-" in normalized[19:]

        if not has_timezone and normalized == date_str:
            # No Z and no explicit timezone - reject as ambiguous
            raise ValueError(
                f"Timezone-naive datetime '{date_str}' is ambiguous. "
                f"Use UTC (Z suffix) or explicit timezone (+HH:MM)"
            )

        try:
            parsed = datetime.fromisoformat(normalized)
            if parsed.tzinfo is None:
                # fromisoformat didn't get a timezone - reject
                raise ValueError(
                    f"Timezone-naive datetime '{date_str}' is ambiguous. "
                    f"Use UTC (Z suffix) or explicit timezone (+HH:MM)"
                )
            return parsed
        except ValueError as e:
            raise ValueError(f"Invalid ISO 8601 format '{date_str}': {e}")

    raise ValueError(
        f"Unrecognized date format '{date_str}'. "
        f"Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ"
    )


def parse_migration_date_safe(
    date_str: Optional[str],
    fallback_to_now: bool = True,
) -> datetime:
    """Parse migration date with fallback behavior.

    Unlike parse_migration_date(), this logs warnings instead of raising
    for invalid formats, falling back to current time.

    Args:
        date_str: ISO format date string
        fallback_to_now: If True, return current time on parse failure

    Returns:
        Parsed datetime or current time on failure
    """
    if not date_str:
        logger.info("No migration_start_date provided, using current date")
        return datetime.now(timezone.utc)

    try:
        result = parse_migration_date(date_str)
        logger.info(f"Using user-provided migration start date: {result}")
        return result
    except ValueError as e:
        if fallback_to_now:
            logger.warning(f"{e}, using current date")
            return datetime.now(timezone.utc)
        raise


async def run_wave_planning_background(
    planning_flow_id: UUID,
    context: RequestContext,
    planning_config: Dict[str, Any],
) -> None:
    """Background task to execute wave planning with proper lifecycle management.

    DISABLED: Planning flow functionality has been removed.

    Per Qodo Bot security review: Implements proper task tracking and cleanup
    to prevent orphaned tasks on worker shutdown.

    Args:
        planning_flow_id: Planning flow UUID
        context: Request context with tenant info
        planning_config: Wave planning configuration
    """
    task_key = str(planning_flow_id)
    bg_db = None

    try:
        bg_db = AsyncSessionLocal()
        logger.warning(
            f"[Background] Wave planning disabled - planning flow functionality removed"
        )

        # Planning services removed - return error result
        logger.warning(
            f"[Background] Wave planning not available for {planning_flow_id} - "
            f"planning flow functionality has been removed"
        )

    except asyncio.CancelledError:
        logger.warning(
            f"[Background] Wave planning cancelled for {planning_flow_id} "
            f"(worker shutdown)"
        )
        raise  # Re-raise to properly handle cancellation

    except Exception as e:
        logger.error(
            f"[Background] Wave planning error for {planning_flow_id}: {e}",
            exc_info=True,
        )

    finally:
        if bg_db:
            await bg_db.close()
        # Cleanup task tracking
        _active_planning_tasks.pop(task_key, None)


def schedule_wave_planning_task(
    planning_flow_id: UUID,
    context: RequestContext,
    planning_config: Dict[str, Any],
) -> asyncio.Task:
    """Schedule wave planning background task with lifecycle tracking.

    Creates an asyncio task with proper naming and tracking for graceful
    shutdown handling.

    Args:
        planning_flow_id: Planning flow UUID
        context: Request context with tenant info
        planning_config: Wave planning configuration

    Returns:
        The scheduled asyncio.Task (for optional monitoring)
    """
    task_key = str(planning_flow_id)

    # Cancel any existing task for this flow (prevents duplicates)
    existing_task = _active_planning_tasks.get(task_key)
    if existing_task and not existing_task.done():
        logger.warning(f"Cancelling existing wave planning task for {planning_flow_id}")
        existing_task.cancel()

    # Create new task with name for debugging
    task = asyncio.create_task(
        run_wave_planning_background(
            planning_flow_id=planning_flow_id,
            context=context,
            planning_config=planning_config,
        ),
        name=f"wave_planning_{planning_flow_id}",
    )

    # Track active task
    _active_planning_tasks[task_key] = task

    logger.info(f"Scheduled background wave planning task for flow: {planning_flow_id}")

    return task


async def cancel_all_planning_tasks() -> int:
    """Cancel all active planning tasks (for graceful shutdown).

    Returns:
        Number of tasks cancelled
    """
    cancelled = 0
    for task_key, task in list(_active_planning_tasks.items()):
        if not task.done():
            task.cancel()
            cancelled += 1
            logger.info(f"Cancelled planning task: {task_key}")

    _active_planning_tasks.clear()
    return cancelled
