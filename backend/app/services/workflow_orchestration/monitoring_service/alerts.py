"""
Alert Management Module
Team C1 - Task C1.6

Handles alert definitions, evaluation, management, and acknowledgment.
"""

import uuid
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from app.core.logging import get_logger

from .models import Alert, AlertDefinition
from .types import AlertSeverity

logger = get_logger(__name__)


class AlertManager:
    """Manages alert definitions and active alerts"""

    def __init__(self):
        self.alert_definitions: Dict[str, AlertDefinition] = {}
        self.active_alerts: Dict[str, Alert] = {}

        # Configuration
        self.alert_evaluation_interval_ms = 10000  # 10 seconds

        # Initialize default alerts
        self._initialize_default_alerts()

    def _initialize_default_alerts(self):
        """Initialize default alert definitions"""
        default_alerts = [
            {
                "name": "Workflow Timeout",
                "description": "Workflow execution time exceeds threshold",
                "condition": "execution_time_ms > threshold",
                "threshold": 7200000,  # 2 hours
                "severity": "warning",
            },
            {
                "name": "High Error Rate",
                "description": "Error rate exceeds acceptable threshold",
                "condition": "error_rate > threshold",
                "threshold": 0.1,  # 10%
                "severity": "error",
            },
            {
                "name": "Low Quality Score",
                "description": "Quality score below minimum threshold",
                "condition": "quality_score < threshold",
                "threshold": 0.7,  # 70%
                "severity": "warning",
            },
            {
                "name": "Resource Utilization High",
                "description": "Resource utilization exceeds threshold",
                "condition": "resource_utilization > threshold",
                "threshold": 0.9,  # 90%
                "severity": "warning",
            },
            {
                "name": "Workflow Failed",
                "description": "Workflow execution failed",
                "condition": "status == 'failed'",
                "threshold": 1,
                "severity": "critical",
            },
        ]

        for alert_data in default_alerts:
            alert_id = f"default-{alert_data['name'].lower().replace(' ', '-')}"
            alert_def = AlertDefinition(
                alert_id=alert_id,
                name=alert_data["name"],
                description=alert_data["description"],
                severity=AlertSeverity(alert_data["severity"]),
                condition=alert_data["condition"],
                threshold=alert_data["threshold"],
                evaluation_window_ms=60000,  # 1 minute
                cooldown_ms=300000,  # 5 minutes
                enabled=True,
                notification_channels=[],
                metadata={"default": True},
            )
            self.alert_definitions[alert_id] = alert_def

    async def create_custom_alert(
        self,
        name: str,
        description: str,
        condition: str,
        threshold: Union[int, float],
        severity: str = "warning",
        evaluation_window_ms: int = 60000,
        workflow_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Create a custom alert definition

        Args:
            name: Alert name
            description: Alert description
            condition: Alert condition expression
            threshold: Alert threshold value
            severity: Alert severity level
            evaluation_window_ms: Evaluation window in milliseconds
            workflow_id: Associated workflow ID (optional)
            user_id: User creating the alert

        Returns:
            Alert definition ID
        """
        try:
            alert_def_id = f"custom-alert-{uuid.uuid4()}"

            alert_definition = AlertDefinition(
                alert_id=alert_def_id,
                name=name,
                description=description,
                severity=AlertSeverity(severity),
                condition=condition,
                threshold=threshold,
                evaluation_window_ms=evaluation_window_ms,
                cooldown_ms=300000,  # 5 minutes default
                enabled=True,
                notification_channels=[],
                metadata={
                    "created_by": user_id,
                    "created_at": datetime.utcnow().isoformat(),
                    "workflow_id": workflow_id,
                    "custom": True,
                },
            )

            # Add to alert definitions
            self.alert_definitions[alert_def_id] = alert_definition

            logger.info(f"✅ Custom alert created: {alert_def_id}")
            return alert_def_id

        except Exception as e:
            logger.error(f"❌ Failed to create custom alert: {e}")
            raise

    async def get_active_alerts(
        self,
        workflow_id: Optional[str] = None,
        severity_filter: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get active alerts with optional filtering

        Args:
            workflow_id: Filter by workflow ID
            severity_filter: Filter by severity level
            limit: Maximum number of alerts to return

        Returns:
            List of active alerts
        """
        try:
            # Filter alerts
            filtered_alerts = list(self.active_alerts.values())

            if workflow_id:
                filtered_alerts = [
                    alert
                    for alert in filtered_alerts
                    if alert.workflow_id == workflow_id
                ]

            if severity_filter:
                filtered_alerts = [
                    alert
                    for alert in filtered_alerts
                    if alert.severity.value == severity_filter
                ]

            # Sort by severity and time
            severity_order = {
                AlertSeverity.CRITICAL: 4,
                AlertSeverity.ERROR: 3,
                AlertSeverity.WARNING: 2,
                AlertSeverity.INFO: 1,
            }

            filtered_alerts.sort(
                key=lambda a: (severity_order[a.severity], a.triggered_at), reverse=True
            )

            # Limit results
            limited_alerts = filtered_alerts[:limit]

            return [asdict(alert) for alert in limited_alerts]

        except Exception as e:
            logger.error(f"❌ Failed to get active alerts: {e}")
            raise

    async def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str,
        notes: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Acknowledge an active alert

        Args:
            alert_id: ID of the alert to acknowledge
            acknowledged_by: User acknowledging the alert
            notes: Optional acknowledgment notes
            user_id: User ID for auditing

        Returns:
            Acknowledgment result
        """
        try:
            alert = self.active_alerts.get(alert_id)
            if not alert:
                raise ValueError(f"Alert not found: {alert_id}")

            # Add acknowledgment
            acknowledgment = {
                "acknowledged_by": acknowledged_by,
                "acknowledged_at": datetime.utcnow().isoformat(),
                "notes": notes,
                "user_id": user_id,
            }

            alert.acknowledgments.append(acknowledgment)

            logger.info(f"✅ Alert acknowledged: {alert_id} by {acknowledged_by}")

            return {
                "alert_id": alert_id,
                "acknowledged": True,
                "acknowledged_by": acknowledged_by,
                "acknowledged_at": acknowledgment["acknowledged_at"],
                "notes": notes,
            }

        except Exception as e:
            logger.error(f"❌ Failed to acknowledge alert: {e}")
            raise

    async def evaluate_alert_condition(self, alert_def: AlertDefinition) -> bool:
        """
        Evaluate an alert condition

        Args:
            alert_def: Alert definition to evaluate

        Returns:
            True if alert should be triggered
        """
        # This would implement real alert condition evaluation
        # For now, simplified placeholder
        return False

    async def check_alert_resolutions(self):
        """Check if any alerts should be resolved"""
        # Would implement alert resolution checking
        pass

    def get_relevant_alerts(self, workflow_id: Optional[str]) -> List[Alert]:
        """Get relevant alerts for workflow or all alerts"""
        if workflow_id:
            return [
                alert
                for alert in self.active_alerts.values()
                if alert.workflow_id == workflow_id
            ]
        return list(self.active_alerts.values())

    async def cleanup_resolved_alerts(self):
        """Clean up resolved alerts"""
        resolved_alerts = [
            alert_id
            for alert_id, alert in self.active_alerts.items()
            if alert.resolved_at
            and (datetime.utcnow() - alert.resolved_at).total_seconds() > 3600  # 1 hour
        ]
        for alert_id in resolved_alerts:
            del self.active_alerts[alert_id]
