"""
Monitoring service and handlers for Collection Flow metrics.

This module provides monitoring services for tracking performance,
health checks, and metrics collection.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.collection_flow import CollectionFlow

from .base import MonitoringMetrics
from .storage import AuditLogStorage
from .utils import (
    assess_flow_health,
    calculate_average_confidence_score,
    calculate_average_duration,
    calculate_average_quality_score,
    calculate_error_rate,
    calculate_event_rate,
    calculate_phase_durations,
    count_flows,
    count_flows_by_status,
)

logger = logging.getLogger(__name__)


class MonitoringService:
    """
    Service for monitoring Collection Flow metrics and performance.

    This service provides:
    - Real-time flow metrics
    - Performance monitoring
    - Health checks
    - Alerting support
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize the Monitoring Service.

        Args:
            db: Database session
            context: Request context
        """
        self.db = db
        self.context = context
        self.client_account_id = str(context.client_account_id)
        self.engagement_id = str(context.engagement_id)
        self.storage = AuditLogStorage(db, context)

    async def get_current_metrics(self) -> MonitoringMetrics:
        """
        Get current monitoring metrics.

        Returns:
            Current monitoring metrics
        """
        try:
            # Get flow statistics
            total_flows = await count_flows(self.db, self.client_account_id)
            active_flows = await count_flows_by_status(
                self.db,
                self.client_account_id,
                [
                    "initialized",
                    "platform_detection",
                    "automated_collection",
                    "gap_analysis",
                    "manual_collection",
                ],
            )
            completed_flows = await count_flows_by_status(
                self.db, self.client_account_id, ["completed"]
            )
            failed_flows = await count_flows_by_status(
                self.db, self.client_account_id, ["failed"]
            )

            # Calculate success rate
            finished_flows = completed_flows + failed_flows
            success_rate = (
                (completed_flows / finished_flows * 100) if finished_flows > 0 else 0
            )

            # Get average duration
            avg_duration = await calculate_average_duration(
                self.db, self.client_account_id
            )

            # Get quality metrics
            quality_avg = await calculate_average_quality_score(
                self.db, self.client_account_id
            )
            confidence_avg = await calculate_average_confidence_score(
                self.db, self.client_account_id
            )

            # Get event rate
            events_per_hour = await calculate_event_rate(
                self.db, self.client_account_id
            )

            # Calculate error rate
            error_rate = await calculate_error_rate(self.db, self.client_account_id)

            return MonitoringMetrics(
                total_flows=total_flows,
                active_flows=active_flows,
                completed_flows=completed_flows,
                failed_flows=failed_flows,
                average_duration_minutes=avg_duration,
                success_rate=round(success_rate, 2),
                quality_score_average=round(quality_avg, 2),
                confidence_score_average=round(confidence_avg, 2),
                events_per_hour=round(events_per_hour, 2),
                error_rate=round(error_rate, 2),
                metadata={
                    "timestamp": datetime.utcnow().isoformat(),
                    "client_account_id": self.client_account_id,
                    "engagement_id": self.engagement_id,
                },
            )

        except Exception as e:
            logger.error(f"Failed to get monitoring metrics: {str(e)}")
            raise

    async def get_flow_performance_metrics(self, flow_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get performance metrics for a specific flow.

        Args:
            flow_id: Collection Flow ID

        Returns:
            Flow performance metrics
        """
        try:
            # Get flow details
            result = await self.db.execute(
                select(CollectionFlow).where(
                    and_(
                        CollectionFlow.flow_id == flow_id,
                        CollectionFlow.client_account_id
                        == uuid.UUID(self.client_account_id),
                    )
                )
            )
            flow = result.scalar_one_or_none()

            if not flow:
                return {}

            # Calculate duration
            duration = None
            if flow.completed_at and flow.created_at:
                duration = (flow.completed_at - flow.created_at).total_seconds() / 60

            # Get phase durations
            phase_durations = calculate_phase_durations(flow.phase_state)

            # Get event count
            event_count = await self.storage.count_flow_events(flow_id)

            return {
                "flow_id": str(flow_id),
                "status": (
                    flow.status.value if hasattr(flow.status, "value") else flow.status
                ),
                "automation_tier": (
                    flow.automation_tier.value
                    if hasattr(flow.automation_tier, "value")
                    else flow.automation_tier
                ),
                "progress_percentage": flow.progress_percentage,
                "quality_score": flow.collection_quality_score,
                "confidence_score": flow.confidence_score,
                "duration_minutes": round(duration, 2) if duration else None,
                "phase_durations": phase_durations,
                "event_count": event_count,
                "created_at": flow.created_at.isoformat() if flow.created_at else None,
                "completed_at": (
                    flow.completed_at.isoformat() if flow.completed_at else None
                ),
            }

        except Exception as e:
            logger.error(f"Failed to get flow performance metrics: {str(e)}")
            return {}

    async def check_flow_health(self, flow_id: uuid.UUID) -> Dict[str, Any]:
        """
        Check health status of a flow.

        Args:
            flow_id: Collection Flow ID

        Returns:
            Health check results
        """
        try:
            metrics = await self.get_flow_performance_metrics(flow_id)

            if not metrics:
                return {"healthy": False, "reason": "Flow not found"}

            # Use utility function for health assessment
            health_result = assess_flow_health(metrics)

            # Check error rate for this specific flow
            error_events = await self.storage.count_error_events(flow_id)
            if error_events > 10:
                health_result["issues"].append(f"High error count: {error_events}")
                health_result["healthy"] = False

            health_result["metrics"] = metrics
            return health_result

        except Exception as e:
            logger.error(f"Failed to check flow health: {str(e)}")
            return {"healthy": False, "reason": f"Health check failed: {str(e)}"}


class AlertHandler:
    """
    Handler for monitoring alerts and notifications.

    This class provides methods for evaluating alert conditions
    and triggering notifications based on monitoring metrics.
    """

    def __init__(self, monitoring_service: MonitoringService):
        """
        Initialize the Alert Handler.

        Args:
            monitoring_service: MonitoringService instance
        """
        self.monitoring_service = monitoring_service

    async def check_alert_conditions(self) -> List[Dict[str, Any]]:
        """
        Check for alert conditions based on current metrics.

        Returns:
            List of active alerts
        """
        alerts = []

        try:
            metrics = await self.monitoring_service.get_current_metrics()

            # High error rate alert
            if metrics.error_rate > 20:  # 20% error rate
                alerts.append(
                    {
                        "type": "high_error_rate",
                        "severity": "critical",
                        "message": f"Error rate is {metrics.error_rate:.1f}%",
                        "value": metrics.error_rate,
                        "threshold": 20,
                    }
                )

            # Low success rate alert
            if metrics.success_rate < 80 and metrics.total_flows > 5:
                alerts.append(
                    {
                        "type": "low_success_rate",
                        "severity": "warning",
                        "message": f"Success rate is {metrics.success_rate:.1f}%",
                        "value": metrics.success_rate,
                        "threshold": 80,
                    }
                )

            # High average duration alert
            if metrics.average_duration_minutes > 180:  # 3 hours
                alerts.append(
                    {
                        "type": "high_duration",
                        "severity": "warning",
                        "message": f"Average duration is {metrics.average_duration_minutes:.1f} minutes",
                        "value": metrics.average_duration_minutes,
                        "threshold": 180,
                    }
                )

            # Low quality score alert
            if metrics.quality_score_average < 70 and metrics.completed_flows > 0:
                alerts.append(
                    {
                        "type": "low_quality",
                        "severity": "warning",
                        "message": f"Average quality score is {metrics.quality_score_average:.1f}%",
                        "value": metrics.quality_score_average,
                        "threshold": 70,
                    }
                )

        except Exception as e:
            logger.error(f"Failed to check alert conditions: {str(e)}")
            alerts.append(
                {
                    "type": "monitoring_error",
                    "severity": "error",
                    "message": f"Failed to check alerts: {str(e)}",
                }
            )

        return alerts

    async def evaluate_flow_alerts(self, flow_id: uuid.UUID) -> List[Dict[str, Any]]:
        """
        Evaluate alert conditions for a specific flow.

        Args:
            flow_id: Collection Flow ID

        Returns:
            List of flow-specific alerts
        """
        alerts = []

        try:
            health = await self.monitoring_service.check_flow_health(flow_id)

            if not health["healthy"]:
                for issue in health.get("issues", []):
                    alerts.append(
                        {
                            "type": "flow_health",
                            "severity": "warning",
                            "message": f"Flow health issue: {issue}",
                            "flow_id": str(flow_id),
                            "issue": issue,
                        }
                    )

        except Exception as e:
            logger.error(f"Failed to evaluate flow alerts: {str(e)}")
            alerts.append(
                {
                    "type": "flow_alert_error",
                    "severity": "error",
                    "message": f"Failed to evaluate flow alerts: {str(e)}",
                    "flow_id": str(flow_id),
                }
            )

        return alerts
