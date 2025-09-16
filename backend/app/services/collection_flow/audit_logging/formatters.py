"""
Log formatting and structured output utilities.

This module provides formatters and utilities for creating
structured audit log outputs and reports.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import AuditEvent, AuditEventType


class AuditLogFormatter:
    """
    Formatter for audit log entries and structured outputs.

    Provides consistent formatting for audit events, compliance reports,
    and monitoring outputs.
    """

    @staticmethod
    def format_event_message(event: AuditEvent) -> str:
        """
        Format an audit event into a readable log message.

        Args:
            event: Audit event to format

        Returns:
            Formatted log message
        """
        message_parts = [
            f"[{event.severity.value.upper()}]",
            event.event_type.value,
            event.description,
        ]

        if event.flow_id:
            message_parts.append(f"(Flow: {event.flow_id})")

        return " ".join(message_parts)

    @staticmethod
    def format_event_details(event: AuditEvent) -> Dict[str, Any]:
        """
        Format event details for structured logging.

        Args:
            event: Audit event to format

        Returns:
            Structured event details
        """
        return {
            "event_id": str(event.timestamp.timestamp()),
            "event_type": event.event_type.value,
            "severity": event.severity.value,
            "flow_id": str(event.flow_id) if event.flow_id else None,
            "user_id": str(event.user_id) if event.user_id else None,
            "timestamp": event.timestamp.isoformat(),
            "description": event.description,
            "details": event.details,
            "metadata": event.metadata,
        }

    @staticmethod
    def format_compliance_summary(
        events_by_type: Dict[str, int],
        events_by_severity: Dict[str, int],
        total_events: int,
        period_start: datetime,
        period_end: datetime,
    ) -> Dict[str, Any]:
        """
        Format compliance report summary section.

        Args:
            events_by_type: Event counts by type
            events_by_severity: Event counts by severity
            total_events: Total event count
            period_start: Report period start
            period_end: Report period end

        Returns:
            Formatted compliance summary
        """
        return {
            "period": {
                "start": period_start.isoformat(),
                "end": period_end.isoformat(),
                "duration_hours": (period_end - period_start).total_seconds() / 3600,
            },
            "totals": {
                "total_events": total_events,
                "events_by_type": events_by_type,
                "events_by_severity": events_by_severity,
            },
            "analysis": {
                "most_common_event": (
                    max(events_by_type.items(), key=lambda x: x[1])[0]
                    if events_by_type
                    else None
                ),
                "highest_severity_count": events_by_severity.get("critical", 0)
                + events_by_severity.get("error", 0),
                "event_rate_per_hour": total_events
                / max((period_end - period_start).total_seconds() / 3600, 1),
            },
        }

    @staticmethod
    def format_security_summary(
        security_events: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Format security events summary.

        Args:
            security_events: List of security events

        Returns:
            Formatted security summary
        """
        if not security_events:
            return {
                "total_security_events": 0,
                "unauthorized_access_attempts": 0,
                "credential_access_events": 0,
                "security_risk_level": "low",
            }

        # Count by event type
        unauthorized_count = len(
            [
                e
                for e in security_events
                if e.get("event_type") == AuditEventType.UNAUTHORIZED_ACCESS.value
            ]
        )
        credential_count = len(
            [
                e
                for e in security_events
                if e.get("event_type") == AuditEventType.CREDENTIAL_ACCESSED.value
            ]
        )

        # Determine risk level
        risk_level = "low"
        if unauthorized_count > 0:
            risk_level = "high"
        elif credential_count > 10 or len(security_events) > 50:
            risk_level = "medium"

        return {
            "total_security_events": len(security_events),
            "unauthorized_access_attempts": unauthorized_count,
            "credential_access_events": credential_count,
            "security_risk_level": risk_level,
            "recent_activity": security_events[:5] if security_events else [],
        }

    @staticmethod
    def format_user_activity_summary(
        user_activities: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Format user activity summary.

        Args:
            user_activities: User activity data

        Returns:
            Formatted user activity summary
        """
        if not user_activities:
            return {
                "total_users": 0,
                "most_active_user": None,
                "activity_distribution": {},
            }

        # Find most active user
        most_active_user = max(
            user_activities.items(), key=lambda x: x[1]["total_actions"]
        )

        # Calculate activity distribution
        activity_levels = {"low": 0, "medium": 0, "high": 0}
        for user_data in user_activities.values():
            total_actions = user_data["total_actions"]
            if total_actions < 10:
                activity_levels["low"] += 1
            elif total_actions < 50:
                activity_levels["medium"] += 1
            else:
                activity_levels["high"] += 1

        return {
            "total_users": len(user_activities),
            "most_active_user": {
                "user_id": most_active_user[0],
                "total_actions": most_active_user[1]["total_actions"],
            },
            "activity_distribution": activity_levels,
            "top_users": sorted(
                [
                    {"user_id": uid, "total_actions": data["total_actions"]}
                    for uid, data in user_activities.items()
                ],
                key=lambda x: x["total_actions"],
                reverse=True,
            )[:5],
        }

    @staticmethod
    def format_monitoring_metrics_summary(
        metrics: Dict[str, Any], include_trends: bool = False
    ) -> Dict[str, Any]:
        """
        Format monitoring metrics for display.

        Args:
            metrics: Raw monitoring metrics
            include_trends: Whether to include trend analysis

        Returns:
            Formatted metrics summary
        """
        summary = {
            "overview": {
                "total_flows": metrics.get("total_flows", 0),
                "active_flows": metrics.get("active_flows", 0),
                "success_rate": f"{metrics.get('success_rate', 0):.1f}%",
                "average_duration": f"{metrics.get('average_duration_minutes', 0):.1f} min",
            },
            "quality": {
                "quality_score": f"{metrics.get('quality_score_average', 0):.1f}%",
                "confidence_score": f"{metrics.get('confidence_score_average', 0):.1f}%",
            },
            "performance": {
                "events_per_hour": metrics.get("events_per_hour", 0),
                "error_rate": f"{metrics.get('error_rate', 0):.1f}%",
            },
        }

        if include_trends:
            # Add trend indicators (placeholder logic)
            summary["trends"] = {
                "flow_creation_trend": "stable",  # Would be calculated from historical data
                "quality_trend": (
                    "improving"
                    if metrics.get("quality_score_average", 0) > 75
                    else "stable"
                ),
                "performance_trend": "stable",
            }

        return summary

    @staticmethod
    def format_alert_message(alert: Dict[str, Any]) -> str:
        """
        Format an alert into a readable message.

        Args:
            alert: Alert data

        Returns:
            Formatted alert message
        """
        severity_prefix = {
            "critical": "🚨 CRITICAL",
            "error": "❌ ERROR",
            "warning": "⚠️  WARNING",
            "info": "ℹ️  INFO",
        }.get(alert.get("severity", "info"), "INFO")

        message = f"{severity_prefix}: {alert.get('message', 'Unknown alert')}"

        if alert.get("flow_id"):
            message += f" (Flow: {alert['flow_id']})"

        return message

    @staticmethod
    def export_to_json(data: Any, pretty: bool = True) -> str:
        """
        Export data to JSON format.

        Args:
            data: Data to export
            pretty: Whether to use pretty formatting

        Returns:
            JSON string
        """
        if pretty:
            return json.dumps(data, indent=2, default=str, ensure_ascii=False)
        return json.dumps(data, default=str, ensure_ascii=False)

    @staticmethod
    def export_to_csv_format(
        events: List[Dict[str, Any]], fields: Optional[List[str]] = None
    ) -> List[List[str]]:
        """
        Export events to CSV-ready format.

        Args:
            events: List of event dictionaries
            fields: Optional list of fields to include

        Returns:
            List of rows (each row is a list of values)
        """
        if not events:
            return []

        # Default fields if not specified
        if not fields:
            fields = [
                "timestamp",
                "event_type",
                "severity",
                "user_id",
                "flow_id",
                "description",
            ]

        # Header row
        rows = [fields]

        # Data rows
        for event in events:
            row = []
            for field in fields:
                value = event.get(field, "")
                # Convert to string and handle None values
                row.append(str(value) if value is not None else "")
            rows.append(row)

        return rows
