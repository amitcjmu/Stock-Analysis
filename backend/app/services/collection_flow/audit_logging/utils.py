"""
Utility functions for audit logging and monitoring.

This module contains helper functions for metrics calculation,
phase duration analysis, and other supporting utilities.
"""

import statistics
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection_flow import CollectionFlow
from app.models.security_audit import SecurityAuditLog


async def count_flows(db: AsyncSession, client_account_id: str) -> int:
    """
    Count total flows for a client.

    Args:
        db: Database session
        client_account_id: Client account ID

    Returns:
        Total number of flows
    """
    result = await db.execute(
        select(func.count(CollectionFlow.id)).where(
            CollectionFlow.client_account_id == uuid.UUID(client_account_id)
        )
    )
    return result.scalar() or 0


async def count_flows_by_status(
    db: AsyncSession, client_account_id: str, statuses: List[str]
) -> int:
    """
    Count flows by status for a client.

    Args:
        db: Database session
        client_account_id: Client account ID
        statuses: List of status values to count

    Returns:
        Number of flows with specified statuses
    """
    result = await db.execute(
        select(func.count(CollectionFlow.id)).where(
            and_(
                CollectionFlow.client_account_id == uuid.UUID(client_account_id),
                CollectionFlow.status.in_(statuses),
            )
        )
    )
    return result.scalar() or 0


async def calculate_average_duration(db: AsyncSession, client_account_id: str) -> float:
    """
    Calculate average flow duration in minutes for completed flows.

    Args:
        db: Database session
        client_account_id: Client account ID

    Returns:
        Average duration in minutes
    """
    result = await db.execute(
        select(CollectionFlow).where(
            and_(
                CollectionFlow.client_account_id == uuid.UUID(client_account_id),
                CollectionFlow.completed_at.isnot(None),
            )
        )
    )
    flows = result.scalars().all()

    if not flows:
        return 0.0

    durations = []
    for flow in flows:
        if flow.created_at and flow.completed_at:
            duration = (flow.completed_at - flow.created_at).total_seconds() / 60
            durations.append(duration)

    return statistics.mean(durations) if durations else 0.0


async def calculate_average_quality_score(
    db: AsyncSession, client_account_id: str
) -> float:
    """
    Calculate average quality score for flows.

    Args:
        db: Database session
        client_account_id: Client account ID

    Returns:
        Average quality score
    """
    result = await db.execute(
        select(func.avg(CollectionFlow.collection_quality_score)).where(
            and_(
                CollectionFlow.client_account_id == uuid.UUID(client_account_id),
                CollectionFlow.collection_quality_score.isnot(None),
            )
        )
    )
    return result.scalar() or 0.0


async def calculate_average_confidence_score(
    db: AsyncSession, client_account_id: str
) -> float:
    """
    Calculate average confidence score for flows.

    Args:
        db: Database session
        client_account_id: Client account ID

    Returns:
        Average confidence score
    """
    result = await db.execute(
        select(func.avg(CollectionFlow.confidence_score)).where(
            and_(
                CollectionFlow.client_account_id == uuid.UUID(client_account_id),
                CollectionFlow.confidence_score.isnot(None),
            )
        )
    )
    return result.scalar() or 0.0


async def calculate_event_rate(db: AsyncSession, client_account_id: str) -> float:
    """
    Calculate events per hour for the last hour.

    Args:
        db: Database session
        client_account_id: Client account ID

    Returns:
        Events per hour
    """
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)

    result = await db.execute(
        select(func.count(SecurityAuditLog.id)).where(
            and_(
                SecurityAuditLog.resource_type == "collection_flow",
                SecurityAuditLog.client_account_id == uuid.UUID(client_account_id),
                SecurityAuditLog.performed_at >= one_hour_ago,
            )
        )
    )
    return float(result.scalar() or 0)


async def calculate_error_rate(db: AsyncSession, client_account_id: str) -> float:
    """
    Calculate error rate percentage for the last hour.

    Args:
        db: Database session
        client_account_id: Client account ID

    Returns:
        Error rate as percentage
    """
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)

    # Count total events
    total_result = await db.execute(
        select(func.count(SecurityAuditLog.id)).where(
            and_(
                SecurityAuditLog.resource_type == "collection_flow",
                SecurityAuditLog.client_account_id == uuid.UUID(client_account_id),
                SecurityAuditLog.performed_at >= one_hour_ago,
            )
        )
    )
    total_events = total_result.scalar() or 0

    # Count error events
    error_result = await db.execute(
        select(func.count(SecurityAuditLog.id)).where(
            and_(
                SecurityAuditLog.resource_type == "collection_flow",
                SecurityAuditLog.client_account_id == uuid.UUID(client_account_id),
                SecurityAuditLog.performed_at >= one_hour_ago,
                SecurityAuditLog.status == "failure",
            )
        )
    )
    error_events = error_result.scalar() or 0

    if total_events == 0:
        return 0.0

    return (error_events / total_events) * 100


def calculate_phase_durations(
    phase_transitions: List[Dict[str, Any]],
) -> Dict[str, float]:
    """
    Calculate duration for each phase from master flow phase transitions.

    Per ADR-028: Phase data now comes from master flow's phase_transitions,
    not from collection flow's phase_state (which has been removed).

    Args:
        phase_transitions: List of phase transition dicts from master flow

    Returns:
        Dictionary mapping phase names to durations in minutes
    """
    durations = {}

    for transition in phase_transitions:
        phase_name = transition.get("phase")
        timestamp = transition.get("timestamp")  # Master flow uses 'timestamp'
        completed_at = transition.get("completed_at")

        if phase_name and timestamp:
            try:
                start_dt = datetime.fromisoformat(timestamp)
                if completed_at:
                    end_dt = datetime.fromisoformat(completed_at)
                else:
                    end_dt = datetime.utcnow()

                duration_minutes = (end_dt - start_dt).total_seconds() / 60
                # Sum durations if a phase is re-entered
                durations[phase_name] = durations.get(phase_name, 0) + round(
                    duration_minutes, 2
                )
            except Exception:
                pass

    return durations


def assess_flow_health(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assess the health of a flow based on its metrics.

    Args:
        metrics: Flow performance metrics

    Returns:
        Health assessment results
    """
    if not metrics:
        return {"healthy": False, "reason": "Flow not found"}

    health_issues = []

    # Check if flow is stuck
    if metrics["status"] not in ["completed", "failed", "cancelled"]:
        duration = metrics.get("duration_minutes")
        if duration and duration > 120:  # 2 hours
            health_issues.append("Flow running longer than expected")

    # Check progress
    if metrics["progress_percentage"] < 10 and metrics.get("duration_minutes", 0) > 30:
        health_issues.append("Low progress after extended time")

    # Check quality scores
    if metrics.get("quality_score") and metrics["quality_score"] < 50:
        health_issues.append("Low quality score")

    if metrics.get("confidence_score") and metrics["confidence_score"] < 50:
        health_issues.append("Low confidence score")

    return {
        "healthy": len(health_issues) == 0,
        "issues": health_issues,
        "checked_at": datetime.utcnow().isoformat(),
    }
