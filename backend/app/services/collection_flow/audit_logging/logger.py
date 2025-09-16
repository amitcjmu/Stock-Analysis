"""
Main audit logging service and service layer for Collection Flow activities.

This module provides the primary service interface for audit logging,
including specialized logging methods for different types of events.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext

from .base import AuditEvent, AuditEventType, AuditSeverity
from .storage import AuditLogStorage

logger = logging.getLogger(__name__)


class AuditLoggingService:
    """
    Service for comprehensive audit logging of Collection Flow activities.

    This service provides:
    - Event logging for all flow activities
    - Security audit trail
    - Performance tracking
    - Error and incident logging
    - Compliance reporting support
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize the Audit Logging Service.

        Args:
            db: Database session
            context: Request context
        """
        self.db = db
        self.context = context
        self.storage = AuditLogStorage(db, context)

    async def log_event(self, event: AuditEvent) -> None:
        """
        Log an audit event.

        Args:
            event: Audit event to log
        """
        try:
            # Store in database
            await self.storage.store_audit_event(event)

            # Also log to application logger
            log_message = f"[{event.severity.value.upper()}] {event.event_type.value}: {event.description}"
            if event.flow_id:
                log_message += f" (Flow: {event.flow_id})"

            if event.severity == AuditSeverity.ERROR:
                logger.error(log_message, extra={"event_details": event.details})
            elif event.severity == AuditSeverity.WARNING:
                logger.warning(log_message, extra={"event_details": event.details})
            else:
                logger.info(log_message, extra={"event_details": event.details})

        except Exception as e:
            logger.error(f"Failed to log audit event: {str(e)}")
            # Don't raise - audit logging should not break the main flow

    async def log_flow_lifecycle_event(
        self,
        flow_id: uuid.UUID,
        event_type: AuditEventType,
        description: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log a flow lifecycle event.

        Args:
            flow_id: Collection Flow ID
            event_type: Type of lifecycle event
            description: Event description
            details: Optional event details
        """
        severity = AuditSeverity.INFO
        if event_type in [AuditEventType.FLOW_FAILED, AuditEventType.FLOW_CANCELLED]:
            severity = AuditSeverity.WARNING

        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            flow_id=flow_id,
            description=description,
            details=details or {},
            metadata={"category": "lifecycle"},
        )

        await self.log_event(event)

    async def log_data_collection_event(
        self,
        flow_id: uuid.UUID,
        platform: str,
        event_type: AuditEventType,
        success: bool,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log a data collection event.

        Args:
            flow_id: Collection Flow ID
            platform: Platform name
            event_type: Type of collection event
            success: Whether operation was successful
            details: Optional event details
        """
        severity = AuditSeverity.INFO if success else AuditSeverity.ERROR

        event_details = {"platform": platform, "success": success, **(details or {})}

        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            flow_id=flow_id,
            description=f"Data collection {event_type.value.split('.')[-1]} for {platform}",
            details=event_details,
            metadata={"category": "data_collection"},
        )

        await self.log_event(event)

    async def log_quality_assessment_event(
        self,
        flow_id: uuid.UUID,
        quality_score: float,
        confidence_score: float,
        issues_found: int,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log a quality assessment event.

        Args:
            flow_id: Collection Flow ID
            quality_score: Overall quality score
            confidence_score: Overall confidence score
            issues_found: Number of quality issues found
            details: Optional assessment details
        """
        severity = AuditSeverity.INFO
        if quality_score < 60 or confidence_score < 60:
            severity = AuditSeverity.WARNING

        event_details = {
            "quality_score": quality_score,
            "confidence_score": confidence_score,
            "issues_found": issues_found,
            **(details or {}),
        }

        event = AuditEvent(
            event_type=AuditEventType.QUALITY_ASSESSED,
            severity=severity,
            flow_id=flow_id,
            description=(
                f"Quality assessment completed (Score: {quality_score:.1f}%, "
                f"Confidence: {confidence_score:.1f}%)"
            ),
            details=event_details,
            metadata={"category": "quality_assessment"},
        )

        await self.log_event(event)

    async def log_security_event(
        self,
        event_type: AuditEventType,
        description: str,
        flow_id: Optional[uuid.UUID] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log a security-related event.

        Args:
            event_type: Type of security event
            description: Event description
            flow_id: Optional Collection Flow ID
            details: Optional event details
        """
        severity = AuditSeverity.WARNING
        if event_type == AuditEventType.UNAUTHORIZED_ACCESS:
            severity = AuditSeverity.CRITICAL

        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            flow_id=flow_id,
            description=description,
            details=details or {},
            metadata={"category": "security"},
        )

        await self.log_event(event)

    async def log_user_action(
        self, flow_id: uuid.UUID, action: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a user action.

        Args:
            flow_id: Collection Flow ID
            action: Action performed
            details: Optional action details
        """
        event = AuditEvent(
            event_type=AuditEventType.USER_ACTION,
            severity=AuditSeverity.INFO,
            flow_id=flow_id,
            description=f"User action: {action}",
            details=details or {},
            metadata={"category": "user_action"},
        )

        await self.log_event(event)

    async def get_flow_audit_trail(
        self,
        flow_id: uuid.UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[AuditEventType]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get audit trail for a specific flow.

        Args:
            flow_id: Collection Flow ID
            start_date: Optional start date filter
            end_date: Optional end date filter
            event_types: Optional list of event types to filter

        Returns:
            List of audit events
        """
        return await self.storage.get_flow_audit_trail(
            flow_id, start_date, end_date, event_types
        )

    async def get_security_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        severity_filter: Optional[List[AuditSeverity]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get security-related audit events.

        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            severity_filter: Optional severity filter

        Returns:
            List of security events
        """
        return await self.storage.get_security_events(
            start_date, end_date, severity_filter
        )

    async def generate_compliance_report(
        self, start_date: datetime, end_date: datetime, include_sensitive: bool = False
    ) -> Dict[str, Any]:
        """
        Generate compliance report for audit purposes.

        Args:
            start_date: Report start date
            end_date: Report end date
            include_sensitive: Whether to include sensitive information

        Returns:
            Compliance report data
        """
        try:
            # Get audit trail data from storage
            all_events = await self.storage.get_flow_audit_trail(
                flow_id=None,  # Get all flows
                start_date=start_date,
                end_date=end_date,
            )

            # Categorize events
            events_by_type = {}
            events_by_severity = {}
            user_activities = {}

            for event in all_events:
                # By type
                event_type = event["event_type"]
                events_by_type[event_type] = events_by_type.get(event_type, 0) + 1

                # By severity
                severity = event["severity"]
                events_by_severity[severity] = events_by_severity.get(severity, 0) + 1

                # By user
                user_id = event["user_id"]
                if user_id not in user_activities:
                    user_activities[user_id] = {
                        "total_actions": 0,
                        "actions_by_type": {},
                    }
                user_activities[user_id]["total_actions"] += 1

                if event_type not in user_activities[user_id]["actions_by_type"]:
                    user_activities[user_id]["actions_by_type"][event_type] = 0
                user_activities[user_id]["actions_by_type"][event_type] += 1

            # Security events summary
            security_events = await self.get_security_events(start_date, end_date)

            report = {
                "report_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
                "summary": {
                    "total_events": len(all_events),
                    "events_by_type": events_by_type,
                    "events_by_severity": events_by_severity,
                    "unique_users": len(user_activities),
                    "security_events": len(security_events),
                },
                "user_activities": user_activities,
                "security_summary": {
                    "total_security_events": len(security_events),
                    "unauthorized_access_attempts": len(
                        [
                            e
                            for e in security_events
                            if e["event_type"]
                            == AuditEventType.UNAUTHORIZED_ACCESS.value
                        ]
                    ),
                    "credential_access_events": len(
                        [
                            e
                            for e in security_events
                            if e["event_type"]
                            == AuditEventType.CREDENTIAL_ACCESSED.value
                        ]
                    ),
                },
                "generated_at": datetime.utcnow().isoformat(),
                "generated_by": str(self.context.user_id),
            }

            # Include detailed events if requested
            if include_sensitive:
                report["detailed_events"] = [
                    {
                        "timestamp": event["timestamp"],
                        "event_type": event["event_type"],
                        "user_id": event["user_id"],
                        "description": event["description"],
                        "severity": event["severity"],
                    }
                    for event in all_events
                ]

            return report

        except Exception as e:
            logger.error(f"Failed to generate compliance report: {str(e)}")
            raise
