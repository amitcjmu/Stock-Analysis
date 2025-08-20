"""
Agent Communication Events API using Server-Sent Events (SSE).

Provides real-time updates for all flow types through HTTP/2 SSE,
connecting the Agent-UI Bridge to frontend clients.
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.services.agent_ui_bridge import agent_ui_bridge
from app.services.crewai_flows.persistence.postgres_store import PostgresFlowStateStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/flows")


async def _check_flow_exists_and_permissions(flow_id, context, store):
    """Check if flow exists and user has access permissions."""
    flow_state = await store.get_flow_state(flow_id)

    if not flow_state:
        raise HTTPException(status_code=404, detail=f"Flow {flow_id} not found")

    # Verify tenant access
    if hasattr(flow_state, "client_account_id"):
        if str(flow_state.client_account_id) != str(context.client_account_id):
            raise HTTPException(status_code=403, detail="Access denied to this flow")

    return flow_state


def _prepare_flow_update_data(flow_id, current_state, insights, current_version):
    """Prepare flow update data for SSE event."""
    return {
        "flow_id": flow_id,
        "status": (
            current_state.flow_status
            if hasattr(current_state, "flow_status")
            else "unknown"
        ),
        "current_phase": (
            current_state.current_phase
            if hasattr(current_state, "current_phase")
            else None
        ),
        "progress": (
            current_state.progress_percentage
            if hasattr(current_state, "progress_percentage")
            else 0
        ),
        "agent_insights": insights,
        "timestamp": datetime.utcnow().isoformat(),
        "version": current_version,
    }


def _add_agent_decision_to_update(update_data, current_state):
    """Add latest agent decision to update data if available."""
    if hasattr(current_state, "agent_decisions") and current_state.agent_decisions:
        latest_decision = current_state.agent_decisions[-1]
        update_data["agent_decision"] = latest_decision


async def _process_flow_state_update(flow_id, store, last_version):
    """Process flow state update and return update data if changed."""
    current_state = await store.get_flow_state(flow_id)

    if not current_state:
        logger.warning(f"Flow {flow_id} no longer exists")
        return {
            "event": "flow_deleted",
            "data": json.dumps({"flow_id": flow_id}),
            "id": str(last_version + 1),
        }, None

    # Check for state changes
    current_version = (
        current_state.version if hasattr(current_state, "version") else last_version + 1
    )

    if current_version > last_version:
        # Get agent insights from agent-ui-bridge
        insights = agent_ui_bridge.get_flow_insights(flow_id)

        # Prepare update data
        update_data = _prepare_flow_update_data(
            flow_id, current_state, insights, current_version
        )

        # Check for agent decisions
        _add_agent_decision_to_update(update_data, current_state)

        # Send flow update event
        return {
            "event": "flow_update",
            "data": json.dumps(update_data),
            "id": str(current_version),
        }, current_version

    return None, last_version


def _process_agent_messages(flow_id, last_version):
    """Process and return agent messages as SSE events."""
    messages = []
    agent_messages = agent_ui_bridge.get_pending_messages(
        flow_id, since_version=last_version
    )

    for message in agent_messages:
        messages.append(
            {
                "event": message.get("type", "agent_message"),
                "data": json.dumps(message),
                "id": str(message.get("id", last_version + 1)),
            }
        )

    return messages


def _create_error_event(flow_id, last_version):
    """Create error event for SSE stream."""
    return {
        "event": "error",
        "data": json.dumps(
            {
                "error": "Stream error limit exceeded",
                "flow_id": flow_id,
            }
        ),
        "id": str(last_version + 1),
    }


def _prepare_status_response_data(flow_id, flow_state, insights):
    """Prepare response data for flow status endpoint."""
    response_data = {
        "flow_id": flow_id,
        "status": (
            flow_state.flow_status if hasattr(flow_state, "flow_status") else "unknown"
        ),
        "current_phase": (
            flow_state.current_phase if hasattr(flow_state, "current_phase") else None
        ),
        "progress": (
            flow_state.progress_percentage
            if hasattr(flow_state, "progress_percentage")
            else 0
        ),
        "agent_insights": insights,
        "updated_at": (
            flow_state.updated_at.isoformat()
            if hasattr(flow_state, "updated_at")
            else datetime.utcnow().isoformat()
        ),
        "version": flow_state.version if hasattr(flow_state, "version") else 1,
    }

    # Check for agent decisions
    if hasattr(flow_state, "agent_decisions") and flow_state.agent_decisions:
        response_data["latest_agent_decision"] = flow_state.agent_decisions[-1]

    return response_data


def _generate_etag(response_data):
    """Generate ETag from response data."""
    state_json = json.dumps(response_data, sort_keys=True, default=str)
    return f'"{hashlib.sha256(state_json.encode()).hexdigest()[:32]}"'


def _set_status_response_headers(response, etag, response_data):
    """Set response headers for status endpoint."""
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "no-cache, must-revalidate"
    response.headers["X-Flow-Version"] = str(response_data.get("version", 1))


@router.get("/{flow_id}/events")
async def flow_events(
    flow_id: str,
    request: Request,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
):
    """
    Stream real-time flow events using Server-Sent Events (SSE).

    This endpoint:
    - Works with all flow types (discovery, assessment, planning, etc.)
    - Provides real-time agent insights and decisions
    - Automatically reconnects on connection loss
    - Falls back gracefully when client doesn't support SSE

    Args:
        flow_id: Flow identifier
        request: FastAPI request object
        context: Request context with tenant information
        db: Database session

    Returns:
        EventSourceResponse with real-time flow updates
    """

    # Verify flow exists and user has access
    store = PostgresFlowStateStore(db, context)
    await _check_flow_exists_and_permissions(flow_id, context, store)

    async def event_generator() -> AsyncGenerator[Dict[str, Any], None]:
        """Generate SSE events for the flow"""
        last_version = 0
        error_count = 0
        max_errors = 3

        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info(f"Client disconnected from flow {flow_id}")
                    break

                try:
                    # Track if we yielded any events in this iteration
                    yielded_any = False

                    # Process flow state update
                    update_event, new_version = await _process_flow_state_update(
                        flow_id, store, last_version
                    )

                    if update_event:
                        yield update_event
                        yielded_any = True
                        if new_version is None:  # Flow was deleted
                            break
                        if new_version is not None and new_version > last_version:
                            last_version = new_version
                            error_count = 0  # Reset error count on success

                    # Process agent messages
                    agent_message_events = _process_agent_messages(
                        flow_id, last_version
                    )
                    for message_event in agent_message_events:
                        yield message_event
                        yielded_any = True

                    # If no events were yielded, add a small sleep to prevent busy-looping
                    if not yielded_any:
                        await asyncio.sleep(0.5)

                except Exception as e:
                    logger.error(f"Error in SSE stream for flow {flow_id}: {e}")
                    error_count += 1

                    if error_count >= max_errors:
                        logger.error(
                            f"Too many errors in SSE stream for flow {flow_id}, closing connection"
                        )
                        yield _create_error_event(flow_id, last_version)
                        break

                    # Wait longer on errors
                    await asyncio.sleep(5)
                    continue

                # Normal polling interval
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            logger.info(f"SSE stream cancelled for flow {flow_id}")
        finally:
            logger.info(f"SSE stream closed for flow {flow_id}")

    # Return SSE response
    return EventSourceResponse(event_generator())


@router.get("/{flow_id}/status")
async def get_flow_status_with_etag(
    flow_id: str,
    response: Response,
    if_none_match: Optional[str] = Header(None),
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
):
    """
    Get flow status with ETag support for efficient polling.

    This endpoint:
    - Returns 304 Not Modified if content hasn't changed
    - Includes ETag header for caching
    - Provides fallback when SSE is not available

    Args:
        flow_id: Flow identifier
        response: FastAPI response object
        if_none_match: If-None-Match header value
        context: Request context
        db: Database session

    Returns:
        Flow status or 304 if unchanged
    """

    # Get flow state
    store = PostgresFlowStateStore(db, context)
    flow_state = await _check_flow_exists_and_permissions(flow_id, context, store)

    # Get agent insights
    insights = agent_ui_bridge.get_flow_insights(flow_id)

    # Prepare response data
    response_data = _prepare_status_response_data(flow_id, flow_state, insights)

    # Generate ETag from response data - using SHA-256 for security
    etag = _generate_etag(response_data)

    # Check if content has changed
    if if_none_match == etag:
        response.status_code = 304  # Not Modified
        return None

    # Set response headers
    _set_status_response_headers(response, etag, response_data)

    return response_data


@router.post("/{flow_id}/events/subscribe")
async def subscribe_to_flow_events(
    flow_id: str,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
):
    """
    Subscribe to flow events (for WebSocket fallback or testing).

    This creates a subscription that can be polled or used
    for alternative real-time mechanisms.

    Args:
        flow_id: Flow identifier
        context: Request context
        db: Database session

    Returns:
        Subscription details
    """

    # Verify flow exists
    store = PostgresFlowStateStore(db, context)
    await _check_flow_exists_and_permissions(flow_id, context, store)

    # Create subscription in agent-ui-bridge
    subscription_id = agent_ui_bridge.create_subscription(
        flow_id=flow_id,
        client_id=context.user_id,
        client_account_id=context.client_account_id,
    )

    return {
        "subscription_id": subscription_id,
        "flow_id": flow_id,
        "created_at": datetime.utcnow().isoformat(),
        "polling_endpoint": f"/api/v1/flows/{flow_id}/status",
        "sse_endpoint": f"/api/v1/flows/{flow_id}/events",
    }


@router.delete("/{flow_id}/events/subscribe/{subscription_id}")
async def unsubscribe_from_flow_events(
    flow_id: str,
    subscription_id: str,
    context: RequestContext = Depends(get_current_context),
):
    """
    Unsubscribe from flow events.

    Args:
        flow_id: Flow identifier
        subscription_id: Subscription identifier
        context: Request context

    Returns:
        Unsubscribe confirmation
    """

    # Remove subscription
    success = agent_ui_bridge.remove_subscription(subscription_id)

    if not success:
        raise HTTPException(status_code=404, detail="Subscription not found")

    return {
        "subscription_id": subscription_id,
        "flow_id": flow_id,
        "unsubscribed_at": datetime.utcnow().isoformat(),
    }
