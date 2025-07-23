"""
Agent Performance API Endpoints
Provides comprehensive agent observability endpoints for individual agent metrics
Part of the Agent Observability Enhancement Phase 3
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_db
from app.core.context import RequestContext, get_request_context
from app.core.logging import get_logger as enhanced_get_logger
from app.services.agent_monitor import agent_monitor
from app.services.agent_performance_aggregation_service import \
    agent_performance_aggregation_service
from app.services.agent_task_history_service import AgentTaskHistoryService

logger = enhanced_get_logger(__name__)

router = APIRouter()


@router.get("/agents/{agent_name}/performance")
async def get_agent_performance(
    agent_name: str,
    days: int = Query(default=7, ge=1, le=90, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> Dict[str, Any]:
    """
    Get comprehensive performance metrics for an individual agent.

    Returns:
    - Performance summary with success rates, durations, and confidence scores
    - Token usage statistics
    - Error patterns analysis
    - Performance trends over time
    """
    try:
        # Get sync session for service compatibility
        from app.core.database import get_db as get_sync_db

        sync_db = next(get_sync_db())
        service = AgentTaskHistoryService(sync_db)

        # Get comprehensive performance summary
        performance_summary = service.get_agent_performance_summary(
            agent_name=agent_name,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            days=days,
        )

        # Check for errors in the service response
        if "error" in performance_summary:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get performance data: {performance_summary['error']}",
            )

        # Get current real-time status from agent monitor
        monitor_status = agent_monitor.get_status_report()
        active_tasks = [
            task
            for task in monitor_status.get("active_task_details", [])
            if task.get("agent", "").lower() == agent_name.lower()
        ]

        # Enhance with current status
        performance_summary["current_status"] = {
            "is_active": len(active_tasks) > 0,
            "active_tasks": active_tasks,
            "last_activity": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"Retrieved performance data for agent {agent_name}",
            extra={
                "agent_name": agent_name,
                "days": days,
                "client_account_id": context.client_account_id,
                "engagement_id": context.engagement_id,
            },
        )

        # Close sync db session
        sync_db.close()

        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "data": performance_summary,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting agent performance: {e}",
            extra={
                "agent_name": agent_name,
                "client_account_id": context.client_account_id,
                "engagement_id": context.engagement_id,
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to get agent performance: {str(e)}"
        )


@router.get("/agents/{agent_name}/history")
async def get_agent_task_history(
    agent_name: str,
    limit: int = Query(
        default=50, ge=1, le=500, description="Maximum number of tasks to return"
    ),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    status_filter: Optional[str] = Query(
        None, description="Filter by task status (completed, failed, timeout)"
    ),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> Dict[str, Any]:
    """
    Get paginated task execution history for an agent.

    Returns detailed task execution records including:
    - Task details and outcomes
    - Execution times and durations
    - Token usage per task
    - Error messages for failed tasks
    """
    try:
        # Get sync session for service compatibility
        from app.core.database import get_db as get_sync_db

        sync_db = next(get_sync_db())
        service = AgentTaskHistoryService(sync_db)

        # Get paginated task history
        task_history = service.get_agent_task_history(
            agent_name=agent_name,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            limit=limit,
            offset=offset,
            status_filter=status_filter,
        )

        if "error" in task_history:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get task history: {task_history['error']}",
            )

        logger.info(
            f"Retrieved task history for agent {agent_name}",
            extra={
                "agent_name": agent_name,
                "limit": limit,
                "offset": offset,
                "status_filter": status_filter,
                "total_tasks": task_history.get("total_tasks", 0),
            },
        )

        # Close sync db session
        sync_db.close()

        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "data": task_history,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting agent task history: {e}",
            extra={"agent_name": agent_name},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to get agent task history: {str(e)}"
        )


@router.get("/agents/{agent_name}/analytics")
async def get_agent_analytics(
    agent_name: str,
    period_days: int = Query(
        default=7, ge=1, le=90, description="Analysis period in days"
    ),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> Dict[str, Any]:
    """
    Get detailed analytics for an agent including:
    - Performance distribution (percentiles)
    - Resource usage analysis
    - Pattern discovery statistics
    - Task complexity analysis
    """
    try:
        # Get sync session for service compatibility
        from app.core.database import get_db as get_sync_db

        sync_db = next(get_sync_db())
        service = AgentTaskHistoryService(sync_db)

        # Get comprehensive analytics
        analytics = service.get_agent_analytics(
            agent_name=agent_name,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            period_days=period_days,
        )

        if "error" in analytics:
            raise HTTPException(
                status_code=500, detail=f"Failed to get analytics: {analytics['error']}"
            )

        # Get aggregated performance trends
        performance_trends = (
            agent_performance_aggregation_service.get_agent_performance_trends(
                agent_name=agent_name,
                client_account_id=context.client_account_id,
                engagement_id=context.engagement_id,
                days=period_days,
            )
        )

        # Combine analytics with trends
        analytics["performance_trends"] = performance_trends

        logger.info(
            f"Retrieved analytics for agent {agent_name}",
            extra={"agent_name": agent_name, "period_days": period_days},
        )

        # Close sync db session
        sync_db.close()

        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "data": analytics,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting agent analytics: {e}",
            extra={"agent_name": agent_name},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to get agent analytics: {str(e)}"
        )


@router.get("/agents/activity-feed")
async def get_agents_activity_feed(
    limit: int = Query(
        default=100, ge=1, le=500, description="Maximum number of activities"
    ),
    agent_filter: Optional[str] = Query(
        None, description="Filter by specific agent name"
    ),
    include_completed: bool = Query(
        default=True, description="Include completed tasks"
    ),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> Dict[str, Any]:
    """
    Get real-time activity feed for all agents or specific agent.

    Returns a chronological feed of agent activities including:
    - Current active tasks
    - Recently completed tasks
    - Task transitions and events
    """
    try:
        # Get current monitoring status
        monitor_status = agent_monitor.get_status_report()

        # Build activity feed from active and completed tasks
        activities = []

        # Add active tasks
        for task in monitor_status.get("active_task_details", []):
            if agent_filter and task.get("agent", "").lower() != agent_filter.lower():
                continue

            activities.append(
                {
                    "id": task.get("task_id"),
                    "type": "task_active",
                    "agent": task.get("agent"),
                    "task": task.get("task"),
                    "status": "active",
                    "started_at": task.get("start_time"),
                    "duration_seconds": task.get("duration", 0),
                    "details": task,
                }
            )

        # Add completed tasks if requested
        if include_completed:
            # Get sync session for service compatibility
            from app.core.database import get_db as get_sync_db

            sync_db = next(get_sync_db())
            service = AgentTaskHistoryService(sync_db)

            # Get recent completed tasks
            recent_tasks = service.get_agent_task_history(
                agent_name=agent_filter or "",  # Empty string gets all agents
                client_account_id=context.client_account_id,
                engagement_id=context.engagement_id,
                limit=limit,
                offset=0,
            )

            if "tasks" in recent_tasks:
                for task in recent_tasks["tasks"]:
                    if (
                        agent_filter
                        and task.get("agent_name", "").lower() != agent_filter.lower()
                    ):
                        continue

                    activities.append(
                        {
                            "id": task.get("id"),
                            "type": "task_completed",
                            "agent": task.get("agent_name"),
                            "task": task.get("task_description"),
                            "status": task.get("status"),
                            "started_at": task.get("started_at"),
                            "completed_at": task.get("completed_at"),
                            "duration_seconds": task.get("duration_seconds"),
                            "success": task.get("success"),
                            "confidence_score": task.get("confidence_score"),
                            "details": task,
                        }
                    )

        # Sort by timestamp (most recent first)
        activities.sort(key=lambda x: x.get("started_at", ""), reverse=True)

        # Limit results
        activities = activities[:limit]

        # Close sync db session if it was opened
        if include_completed and "sync_db" in locals():
            sync_db.close()

        logger.info(
            "Retrieved activity feed",
            extra={
                "limit": limit,
                "agent_filter": agent_filter,
                "activities_count": len(activities),
            },
        )

        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "activities": activities,
                "total_activities": len(activities),
                "monitoring_active": monitor_status.get("monitoring_active", False),
                "filters": {
                    "agent": agent_filter,
                    "include_completed": include_completed,
                    "limit": limit,
                },
            },
        }

    except Exception as e:
        logger.error(f"Error getting activity feed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get activity feed: {str(e)}"
        )


@router.get("/agents/discovered-patterns")
async def get_discovered_patterns(
    agent_name: Optional[str] = Query(None, description="Filter by agent name"),
    pattern_type: Optional[str] = Query(None, description="Filter by pattern type"),
    min_confidence: float = Query(
        default=0.0, ge=0.0, le=1.0, description="Minimum confidence score"
    ),
    limit: int = Query(
        default=100, ge=1, le=500, description="Maximum patterns to return"
    ),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> Dict[str, Any]:
    """
    Get patterns discovered by agents during task execution.

    Returns discovered patterns with:
    - Pattern details and metadata
    - Confidence scores
    - Discovery timestamps
    - Agent attribution
    """
    try:
        # Get sync session for service compatibility
        from app.core.database import get_db as get_sync_db

        sync_db = next(get_sync_db())
        service = AgentTaskHistoryService(sync_db)

        # Get discovered patterns
        patterns = service.get_discovered_patterns(
            agent_name=agent_name,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            pattern_type=pattern_type,
            min_confidence=min_confidence,
        )

        # Limit results
        patterns = patterns[:limit]

        logger.info(
            "Retrieved discovered patterns",
            extra={
                "agent_name": agent_name,
                "pattern_type": pattern_type,
                "min_confidence": min_confidence,
                "patterns_count": len(patterns),
            },
        )

        # Close sync db session
        sync_db.close()

        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "patterns": patterns,
                "total_patterns": len(patterns),
                "filters": {
                    "agent_name": agent_name,
                    "pattern_type": pattern_type,
                    "min_confidence": min_confidence,
                },
            },
        }

    except Exception as e:
        logger.error(f"Error getting discovered patterns: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get discovered patterns: {str(e)}"
        )


@router.get("/agents/summary")
async def get_all_agents_summary(
    days: int = Query(default=7, ge=1, le=90, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> Dict[str, Any]:
    """
    Get performance summary for all agents in the current context.

    Returns aggregated metrics for all agents including:
    - Total tasks and success rates
    - Average durations
    - Resource usage
    - Ranking by activity
    """
    try:
        # Get summary for all agents
        summaries = agent_performance_aggregation_service.get_all_agents_summary(
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            days=days,
        )

        # Get current active agents from monitor
        monitor_status = agent_monitor.get_status_report()
        active_agents = set(
            task.get("agent", "")
            for task in monitor_status.get("active_task_details", [])
        )

        # Enhance summaries with current status
        for summary in summaries:
            summary["is_active"] = summary["agent_name"] in active_agents

        logger.info(
            "Retrieved summary for all agents",
            extra={"days": days, "agent_count": len(summaries)},
        )

        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "period_days": days,
                "agents": summaries,
                "total_agents": len(summaries),
                "active_agents": len(active_agents),
            },
        }

    except Exception as e:
        logger.error(f"Error getting all agents summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get agents summary: {str(e)}"
        )


@router.post("/agents/performance/aggregate")
async def trigger_performance_aggregation(
    target_date: Optional[str] = Query(
        None, description="Target date (YYYY-MM-DD) to aggregate, defaults to yesterday"
    ),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> Dict[str, Any]:
    """
    Manually trigger performance aggregation for a specific date.

    This endpoint allows manual triggering of the daily aggregation process
    for debugging or backfilling purposes.
    """
    try:
        # Parse target date
        if target_date:
            try:
                target = datetime.strptime(target_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
                )
        else:
            target = date.today() - timedelta(days=1)

        # Trigger aggregation
        agent_performance_aggregation_service.manual_trigger_aggregation(target)

        logger.info(
            f"Triggered performance aggregation for {target}",
            extra={"target_date": target.isoformat(), "triggered_by": context.user_id},
        )

        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Performance aggregation triggered for {target.isoformat()}",
            "target_date": target.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering aggregation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to trigger aggregation: {str(e)}"
        )
