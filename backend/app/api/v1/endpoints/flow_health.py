"""
Flow Health Monitoring API Endpoints
Provides endpoints for monitoring flow health, retry metrics, and recovery options
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.database import get_db
from app.models.client_account import User
from app.services.crewai_flows.handlers.enhanced_error_handler import \
    enhanced_error_handler
from app.services.crewai_flows.monitoring.flow_health_monitor import \
    flow_health_monitor
from app.services.crewai_flows.persistence.checkpoint_manager import \
    checkpoint_manager
from app.services.crewai_flows.utils.retry_utils import retry_metrics

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/flows/{flow_id}/health")
async def get_flow_health(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get health status for a specific flow

    Returns:
        - Current health status
        - Phase execution times
        - Error history
        - Recovery options
    """
    try:
        # Get flow health from monitor
        health_data = flow_health_monitor.get_flow_health(flow_id)

        if not health_data:
            # Try to analyze flow from database
            from sqlalchemy import select

            from app.models.discovery_flow import DiscoveryFlow

            result = await db.execute(
                select(DiscoveryFlow).where(
                    DiscoveryFlow.flow_id == flow_id,
                    DiscoveryFlow.client_account_id == current_user.client_account_id,
                )
            )
            flow = result.scalar_one_or_none()

            if not flow:
                raise HTTPException(status_code=404, detail="Flow not found")

            # Calculate basic health metrics
            now = datetime.utcnow()
            duration = (now - flow.created_at).total_seconds() / 60  # minutes

            health_data = {
                "flow_id": flow_id,
                "status": flow.status,
                "health_status": "unknown",
                "duration_minutes": duration,
                "current_phase": flow.current_phase,
                "progress": flow.progress_percentage,
            }

        # Add retry metrics for this flow
        flow_retry_metrics = {
            k: v for k, v in retry_metrics.retry_counts.items() if flow_id in k
        }

        # Add checkpoint info
        checkpoints = await checkpoint_manager.list_checkpoints(flow_id)

        # Get error summary from enhanced error handler
        error_summary = enhanced_error_handler.get_error_summary()
        flow_errors = [
            e
            for e in error_summary.get("recent_errors", [])
            if e.get("flow_id") == flow_id
        ]

        return {
            "flow_id": flow_id,
            "health": health_data,
            "retry_metrics": flow_retry_metrics,
            "checkpoints": checkpoints,
            "errors": flow_errors,
            "recovery_options": _get_recovery_options(health_data),
        }

    except Exception as e:
        logger.error(f"Error getting flow health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/overview")
async def get_health_overview(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get overall health metrics for all flows

    Returns:
        - Total flows monitored
        - Flows by health status
        - Retry statistics
        - Error trends
    """
    try:
        # Get all health metrics
        all_metrics = flow_health_monitor.get_all_health_metrics()

        # Get retry statistics
        retry_stats = retry_metrics.get_summary()

        # Get error summary
        error_summary = enhanced_error_handler.get_error_summary()

        # Calculate health breakdown
        health_breakdown = {
            "healthy": 0,
            "warning": 0,
            "critical": 0,
            "hanging": 0,
            "failed": 0,
        }

        for flow_metrics in all_metrics.get("flows", {}).values():
            status = (
                flow_metrics.get("status", {}).value
                if hasattr(flow_metrics.get("status", {}), "value")
                else str(flow_metrics.get("status", "unknown"))
            )
            if status in health_breakdown:
                health_breakdown[status] += 1

        return {
            "overview": {
                "total_monitored_flows": all_metrics.get("monitored_flows", 0),
                "hanging_flows": all_metrics.get("hanging_flows", 0),
                "critical_flows": all_metrics.get("critical_flows", 0),
                "failed_flows": all_metrics.get("failed_flows", 0),
            },
            "health_breakdown": health_breakdown,
            "retry_statistics": retry_stats,
            "error_trends": {
                "total_errors": error_summary.get("total_errors", 0),
                "errors_by_phase": error_summary.get("errors_by_phase", {}),
                "recovery_success_rate": error_summary.get("recovery_success_rate", 0),
            },
            "monitoring_active": flow_health_monitor._monitoring_task is not None
            and not flow_health_monitor._monitoring_task.done(),
        }

    except Exception as e:
        logger.error(f"Error getting health overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flows/{flow_id}/recover")
async def recover_flow(
    flow_id: str,
    recovery_action: str = Query(
        ..., description="Recovery action: restart, complete, fail, checkpoint_restore"
    ),
    checkpoint_id: Optional[str] = Query(
        None, description="Checkpoint ID for restore action"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Initiate recovery action for a flow

    Args:
        flow_id: The flow to recover
        recovery_action: Type of recovery (restart, complete, fail, checkpoint_restore)
        checkpoint_id: Optional checkpoint ID for restore

    Returns:
        Recovery result
    """
    try:
        # Validate flow ownership
        from sqlalchemy import select

        from app.models.discovery_flow import DiscoveryFlow

        result = await db.execute(
            select(DiscoveryFlow).where(
                DiscoveryFlow.flow_id == flow_id,
                DiscoveryFlow.client_account_id == current_user.client_account_id,
            )
        )
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail="Flow not found")

        # Handle checkpoint restore
        if recovery_action == "checkpoint_restore":
            if not checkpoint_id:
                # Get latest checkpoint
                latest = await checkpoint_manager.get_latest_checkpoint(flow_id)
                if not latest:
                    raise HTTPException(
                        status_code=400, detail="No checkpoints available for restore"
                    )
                checkpoint_id = latest.get("checkpoint_id")

            # Restore from checkpoint
            restored_data = await checkpoint_manager.restore_checkpoint(checkpoint_id)
            if not restored_data:
                raise HTTPException(
                    status_code=400, detail="Failed to restore checkpoint"
                )

            # Update flow state with restored data
            # This would need to be integrated with the flow execution
            return {
                "success": True,
                "action": "checkpoint_restore",
                "checkpoint_id": checkpoint_id,
                "restored_phase": restored_data.get("phase"),
                "message": "Checkpoint restored. Flow can be resumed from this state.",
            }

        # Use flow health monitor for other recovery actions
        result = await flow_health_monitor.force_recover_flow(flow_id, recovery_action)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recovering flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/start")
async def start_monitoring(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Start flow health monitoring

    Returns:
        Monitoring status
    """
    try:
        # Check if user is admin
        if not current_user.is_platform_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        await flow_health_monitor.start_monitoring()

        return {
            "status": "started",
            "monitoring_interval": flow_health_monitor.monitoring_interval,
            "message": "Flow health monitoring started successfully",
        }

    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/stop")
async def stop_monitoring(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Stop flow health monitoring

    Returns:
        Monitoring status
    """
    try:
        # Check if user is admin
        if not current_user.is_platform_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        await flow_health_monitor.stop_monitoring()

        return {
            "status": "stopped",
            "message": "Flow health monitoring stopped successfully",
        }

    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/flows/{flow_id}/checkpoints")
async def get_flow_checkpoints(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """
    Get all checkpoints for a flow

    Returns:
        List of checkpoint summaries
    """
    try:
        # Validate flow ownership
        from sqlalchemy import select

        from app.models.discovery_flow import DiscoveryFlow

        result = await db.execute(
            select(DiscoveryFlow).where(
                DiscoveryFlow.flow_id == flow_id,
                DiscoveryFlow.client_account_id == current_user.client_account_id,
            )
        )
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail="Flow not found")

        # Get checkpoints
        checkpoints = await checkpoint_manager.list_checkpoints(flow_id)

        return checkpoints

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting checkpoints: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_recovery_options(health_data: Dict[str, Any]) -> List[str]:
    """Determine available recovery options based on health data"""
    options = []

    status = health_data.get("status", "")
    health_status = health_data.get("health_status", "")

    if status in ["failed", "error"]:
        options.extend(["restart", "checkpoint_restore", "manual_intervention"])
    elif health_status in ["hanging", "critical"]:
        options.extend(["restart", "complete", "fail", "checkpoint_restore"])
    elif status == "processing" and health_status == "warning":
        options.extend(["monitor", "checkpoint_restore"])
    else:
        options.append("monitor")

    return options
