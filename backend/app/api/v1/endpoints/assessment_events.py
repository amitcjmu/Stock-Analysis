"""
Assessment Flow Real-time Events API using Server-Sent Events (SSE).
Provides real-time updates during agent execution and flow progress.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List

from app.api.v1.auth.auth_utils import get_current_user
from app.core.database import get_db

# from app.core.context import verify_client_access
# TODO: This function doesn't exist - need to implement proper access verification
from app.repositories.assessment_flow_repository import AssessmentFlowRepository
from app.schemas.assessment_flow import AgentProgressEvent, AssessmentFlowEvent
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assessment-flow", tags=["Assessment Flow Events"])

# In-memory storage for active connections (in production, use Redis or similar)
active_connections: Dict[str, Dict[str, Any]] = {}


@router.get("/{flow_id}/events")
async def stream_assessment_events(
    flow_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    # client_account_id: int = Depends(verify_client_access)
    client_account_id: str = "55f4a7eb-de00-de00-de00-888ed4f8e05d",  # TODO: Get from context properly
):
    """
    Stream real-time assessment flow events using Server-Sent Events.

    - **flow_id**: Assessment flow identifier
    - Returns SSE stream with real-time updates
    """

    # Verify user has access to the flow
    repository = AssessmentFlowRepository(db, client_account_id)
    flow_state = await repository.get_assessment_flow_state(flow_id)

    if not flow_state:
        raise HTTPException(status_code=404, detail="Assessment flow not found")

    connection_id = f"{flow_id}_{current_user.id}_{datetime.utcnow().timestamp()}"

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events for the assessment flow."""
        try:
            # Register this connection
            active_connections[connection_id] = {
                "flow_id": flow_id,
                "user_id": current_user.id,
                "client_account_id": client_account_id,
                "connected_at": datetime.utcnow(),
            }

            logger.info(
                f"SSE connection established: {connection_id} for flow {flow_id}"
            )

            # Send initial connection event
            initial_event = AssessmentFlowEvent(
                flow_id=flow_id,
                event_type="connection_established",
                phase=flow_state.current_phase,
                timestamp=datetime.utcnow(),
                message="Real-time updates connected",
            )
            yield f"data: {initial_event.json()}\n\n"

            # Main event loop
            while True:
                try:
                    # Check if flow still exists and get latest status
                    current_flow_state = await repository.get_assessment_flow_state(
                        flow_id
                    )
                    if not current_flow_state:
                        break

                    # Get flow events (this would be implemented with actual event storage)
                    events = await get_flow_events(flow_id, client_account_id)

                    for event in events:
                        yield f"data: {event.json()}\n\n"

                    # Send periodic heartbeat
                    heartbeat_event = AssessmentFlowEvent(
                        flow_id=flow_id,
                        event_type="heartbeat",
                        phase=current_flow_state.current_phase,
                        timestamp=datetime.utcnow(),
                        data={
                            "status": current_flow_state.status.value,
                            "progress": current_flow_state.progress,
                        },
                    )
                    yield f"data: {heartbeat_event.json()}\n\n"

                    # Wait before next iteration
                    await asyncio.sleep(2)

                except asyncio.CancelledError:
                    logger.info(f"SSE connection cancelled: {connection_id}")
                    break
                except Exception as e:
                    logger.error(f"Error in SSE event generator: {str(e)}")
                    error_event = AssessmentFlowEvent(
                        flow_id=flow_id,
                        event_type="error",
                        phase=flow_state.current_phase,
                        timestamp=datetime.utcnow(),
                        message=f"Event stream error: {str(e)}",
                    )
                    yield f"data: {error_event.json()}\n\n"
                    break

        finally:
            # Clean up connection
            if connection_id in active_connections:
                del active_connections[connection_id]
            logger.info(f"SSE connection closed: {connection_id}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
        },
    )


@router.get("/{flow_id}/events/agent-progress")
async def stream_agent_progress_events(
    flow_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    # client_account_id: int = Depends(verify_client_access)
    client_account_id: str = "55f4a7eb-de00-de00-de00-888ed4f8e05d",  # TODO: Get from context properly
):
    """
    Stream real-time agent progress events.

    - **flow_id**: Assessment flow identifier
    - Returns SSE stream with agent execution progress
    """

    # Verify user has access to the flow
    repository = AssessmentFlowRepository(db, client_account_id)
    flow_state = await repository.get_assessment_flow_state(flow_id)

    if not flow_state:
        raise HTTPException(status_code=404, detail="Assessment flow not found")

    connection_id = f"agent_{flow_id}_{current_user.id}_{datetime.utcnow().timestamp()}"

    async def agent_event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events for agent progress."""
        try:
            # Register this connection
            active_connections[connection_id] = {
                "flow_id": flow_id,
                "user_id": current_user.id,
                "client_account_id": client_account_id,
                "connection_type": "agent_progress",
                "connected_at": datetime.utcnow(),
            }

            logger.info(f"Agent progress SSE connection established: {connection_id}")

            # Send initial connection event
            initial_event = AgentProgressEvent(
                flow_id=flow_id,
                agent_name="system",
                task_name="connection",
                progress_percentage=0.0,
                status="connected",
                timestamp=datetime.utcnow(),
                details={"message": "Agent progress monitoring connected"},
            )
            yield f"data: {initial_event.json()}\n\n"

            # Main event loop for agent progress
            while True:
                try:
                    # Get agent progress events
                    agent_events = await get_agent_progress_events(
                        flow_id, client_account_id
                    )

                    for event in agent_events:
                        yield f"data: {event.json()}\n\n"

                    # Wait before next iteration
                    await asyncio.sleep(1)  # More frequent updates for agent progress

                except asyncio.CancelledError:
                    logger.info(
                        f"Agent progress SSE connection cancelled: {connection_id}"
                    )
                    break
                except Exception as e:
                    logger.error(f"Error in agent progress event generator: {str(e)}")
                    break

        finally:
            # Clean up connection
            if connection_id in active_connections:
                del active_connections[connection_id]
            logger.info(f"Agent progress SSE connection closed: {connection_id}")

    return StreamingResponse(
        agent_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/events/active-connections")
async def get_active_connections(
    current_user=Depends(get_current_user),
    # client_account_id: int = Depends(verify_client_access)
    client_account_id: str = "55f4a7eb-de00-de00-de00-888ed4f8e05d",  # TODO: Get from context properly
):
    """
    Get information about active SSE connections (admin endpoint).

    - Returns list of active connections for monitoring
    """
    # Filter connections for the current client account
    client_connections = {
        conn_id: conn_info
        for conn_id, conn_info in active_connections.items()
        if conn_info.get("client_account_id") == client_account_id
    }

    return {
        "active_connections": len(client_connections),
        "connections": [
            {
                "connection_id": conn_id,
                "flow_id": conn_info["flow_id"],
                "user_id": conn_info["user_id"],
                "connection_type": conn_info.get("connection_type", "standard"),
                "connected_at": conn_info["connected_at"].isoformat(),
                "duration_seconds": (
                    datetime.utcnow() - conn_info["connected_at"]
                ).total_seconds(),
            }
            for conn_id, conn_info in client_connections.items()
        ],
    }


# Event broadcasting functions (would integrate with actual event system)


async def broadcast_flow_event(
    flow_id: str,
    event_type: str,
    phase: str,
    data: Dict[str, Any] = None,
    message: str = None,
):
    """
    Broadcast an event to all connected clients for a flow.
    In production, this would use a message queue or event system.
    """
    AssessmentFlowEvent(
        flow_id=flow_id,
        event_type=event_type,
        phase=phase,
        timestamp=datetime.utcnow(),
        data=data or {},
        message=message,
    )

    # Store event for retrieval by SSE connections
    # In production, this would be stored in Redis or a database
    logger.info(f"Broadcasting event {event_type} for flow {flow_id}: {message}")


async def broadcast_agent_progress(
    flow_id: str,
    agent_name: str,
    task_name: str,
    progress_percentage: float,
    status: str,
    details: Dict[str, Any] = None,
):
    """
    Broadcast agent progress to all connected clients.
    """
    AgentProgressEvent(
        flow_id=flow_id,
        agent_name=agent_name,
        task_name=task_name,
        progress_percentage=progress_percentage,
        status=status,
        timestamp=datetime.utcnow(),
        details=details,
    )

    # Store event for retrieval by SSE connections
    logger.info(
        f"Broadcasting agent progress for {agent_name} in flow {flow_id}: {progress_percentage}%"
    )


# Helper functions for retrieving events


async def get_flow_events(
    flow_id: str, client_account_id: str
) -> List[AssessmentFlowEvent]:
    """
    Get recent events for a flow.
    In production, this would query an event store.
    """
    # Mock implementation - return empty list for now
    # In actual implementation, this would:
    # 1. Query event store for recent events
    # 2. Filter by flow_id and client_account_id
    # 3. Return events that haven't been sent yet
    return []


async def get_agent_progress_events(
    flow_id: str, client_account_id: str
) -> List[AgentProgressEvent]:
    """
    Get recent agent progress events for a flow.
    In production, this would query an agent monitoring system.
    """
    # Mock implementation - return empty list for now
    # In actual implementation, this would:
    # 1. Query agent monitoring system
    # 2. Get progress updates for active agents
    # 3. Return progress events that haven't been sent yet
    return []


# Integration hooks for the assessment flow service


def notify_phase_started(flow_id: str, phase: str):
    """Notify that a new phase has started."""
    asyncio.create_task(
        broadcast_flow_event(
            flow_id=flow_id,
            event_type="phase_started",
            phase=phase,
            message=f"Started {phase} phase",
        )
    )


def notify_phase_completed(flow_id: str, phase: str, results: Dict[str, Any]):
    """Notify that a phase has completed."""
    asyncio.create_task(
        broadcast_flow_event(
            flow_id=flow_id,
            event_type="phase_completed",
            phase=phase,
            data=results,
            message=f"Completed {phase} phase",
        )
    )


def notify_user_input_required(
    flow_id: str, phase: str, input_requirements: Dict[str, Any]
):
    """Notify that user input is required."""
    asyncio.create_task(
        broadcast_flow_event(
            flow_id=flow_id,
            event_type="user_input_required",
            phase=phase,
            data=input_requirements,
            message=f"User input required for {phase} phase",
        )
    )


def notify_agent_progress(
    flow_id: str,
    agent_name: str,
    task_name: str,
    progress: float,
    status: str,
    details: Dict[str, Any] = None,
):
    """Notify agent progress update."""
    asyncio.create_task(
        broadcast_agent_progress(
            flow_id=flow_id,
            agent_name=agent_name,
            task_name=task_name,
            progress_percentage=progress,
            status=status,
            details=details,
        )
    )
