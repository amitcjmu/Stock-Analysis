"""
Log storage and persistence layer for audit logging.

This module handles the database operations for storing and retrieving
audit logs and security events.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.security_audit import SecurityAuditLog

from .base import AuditEvent, AuditEventType, AuditSeverity

logger = logging.getLogger(__name__)


class AuditLogStorage:
    """
    Storage service for audit logs and security events.

    Handles database persistence, retrieval, and querying of audit logs
    with proper tenant scoping and security considerations.
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize the Storage Service.

        Args:
            db: Database session
            context: Request context for tenant scoping
        """
        self.db = db
        self.context = context
        self.client_account_id = str(context.client_account_id)
        self.engagement_id = str(context.engagement_id)

    async def store_audit_event(self, event: AuditEvent) -> bool:
        """
        Store an audit event in the database.

        Args:
            event: Audit event to store

        Returns:
            True if stored successfully, False otherwise
        """
        try:
            # Prepare audit log entry with proper tenant scoping
            audit_log = SecurityAuditLog(
                id=uuid.uuid4(),
                client_account_id=uuid.UUID(self.client_account_id),
                engagement_id=uuid.UUID(self.engagement_id),
                user_id=event.user_id or uuid.UUID(str(self.context.user_id)),
                action=event.event_type.value,
                resource_type="collection_flow",
                resource_id=str(event.flow_id) if event.flow_id else None,
                details={
                    "description": event.description,
                    "severity": event.severity.value,
                    "event_details": event.details,
                    "metadata": event.metadata,
                },
                ip_address=self.context.ip_address or "system",
                user_agent=self.context.user_agent or "collection-flow-service",
                status=(
                    "success" if event.severity != AuditSeverity.ERROR else "failure"
                ),
                performed_at=event.timestamp,
            )

            self.db.add(audit_log)
            await self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to store audit event: {str(e)}")
            return False

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
        try:
            query = select(SecurityAuditLog).where(
                and_(
                    SecurityAuditLog.resource_id == str(flow_id),
                    SecurityAuditLog.resource_type == "collection_flow",
                    SecurityAuditLog.client_account_id
                    == uuid.UUID(self.client_account_id),
                )
            )

            if start_date:
                query = query.where(SecurityAuditLog.performed_at >= start_date)
            if end_date:
                query = query.where(SecurityAuditLog.performed_at <= end_date)
            if event_types:
                event_type_values = [et.value for et in event_types]
                query = query.where(SecurityAuditLog.action.in_(event_type_values))

            query = query.order_by(SecurityAuditLog.performed_at.desc())

            result = await self.db.execute(query)
            audit_logs = result.scalars().all()

            return [
                {
                    "id": str(log.id),
                    "timestamp": log.performed_at.isoformat(),
                    "event_type": log.action,
                    "user_id": str(log.user_id),
                    "description": log.details.get("description", ""),
                    "severity": log.details.get("severity", "info"),
                    "details": log.details.get("event_details", {}),
                    "metadata": log.details.get("metadata", {}),
                }
                for log in audit_logs
            ]

        except Exception as e:
            logger.error(f"Failed to retrieve audit trail: {str(e)}")
            return []

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
        try:
            security_event_types = [
                AuditEventType.CREDENTIAL_ACCESSED.value,
                AuditEventType.CREDENTIAL_VALIDATED.value,
                AuditEventType.UNAUTHORIZED_ACCESS.value,
            ]

            query = select(SecurityAuditLog).where(
                and_(
                    SecurityAuditLog.action.in_(security_event_types),
                    SecurityAuditLog.client_account_id
                    == uuid.UUID(self.client_account_id),
                )
            )

            if start_date:
                query = query.where(SecurityAuditLog.performed_at >= start_date)
            if end_date:
                query = query.where(SecurityAuditLog.performed_at <= end_date)

            result = await self.db.execute(query)
            audit_logs = result.scalars().all()

            events = []
            for log in audit_logs:
                severity = log.details.get("severity", "info")
                if severity_filter and AuditSeverity(severity) not in severity_filter:
                    continue

                events.append(
                    {
                        "id": str(log.id),
                        "timestamp": log.performed_at.isoformat(),
                        "event_type": log.action,
                        "user_id": str(log.user_id),
                        "flow_id": log.resource_id,
                        "description": log.details.get("description", ""),
                        "severity": severity,
                        "ip_address": log.ip_address,
                        "details": log.details.get("event_details", {}),
                    }
                )

            return events

        except Exception as e:
            logger.error(f"Failed to retrieve security events: {str(e)}")
            return []

    async def count_events_by_type(
        self, event_types: List[str], start_date: datetime, end_date: datetime
    ) -> Dict[str, int]:
        """
        Count events by type within a date range.

        Args:
            event_types: List of event type values
            start_date: Start date for query
            end_date: End date for query

        Returns:
            Dictionary mapping event types to counts
        """
        try:
            query = (
                select(SecurityAuditLog.action, func.count(SecurityAuditLog.id))
                .where(
                    and_(
                        SecurityAuditLog.action.in_(event_types),
                        SecurityAuditLog.client_account_id
                        == uuid.UUID(self.client_account_id),
                        SecurityAuditLog.performed_at >= start_date,
                        SecurityAuditLog.performed_at <= end_date,
                    )
                )
                .group_by(SecurityAuditLog.action)
            )

            result = await self.db.execute(query)
            return dict(result.all())

        except Exception as e:
            logger.error(f"Failed to count events by type: {str(e)}")
            return {}

    async def count_events_by_severity(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, int]:
        """
        Count events by severity within a date range.

        Args:
            start_date: Start date for query
            end_date: End date for query

        Returns:
            Dictionary mapping severity levels to counts
        """
        try:
            # Since severity is stored in details JSON, we need a different approach
            query = select(SecurityAuditLog).where(
                and_(
                    SecurityAuditLog.resource_type == "collection_flow",
                    SecurityAuditLog.client_account_id
                    == uuid.UUID(self.client_account_id),
                    SecurityAuditLog.performed_at >= start_date,
                    SecurityAuditLog.performed_at <= end_date,
                )
            )

            result = await self.db.execute(query)
            audit_logs = result.scalars().all()

            severity_counts = {}
            for log in audit_logs:
                severity = log.details.get("severity", "info")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1

            return severity_counts

        except Exception as e:
            logger.error(f"Failed to count events by severity: {str(e)}")
            return {}

    async def count_flow_events(self, flow_id: uuid.UUID) -> int:
        """
        Count events for a specific flow.

        Args:
            flow_id: Collection Flow ID

        Returns:
            Number of events for the flow
        """
        try:
            result = await self.db.execute(
                select(func.count(SecurityAuditLog.id)).where(
                    and_(
                        SecurityAuditLog.resource_id == str(flow_id),
                        SecurityAuditLog.resource_type == "collection_flow",
                    )
                )
            )
            return result.scalar() or 0

        except Exception as e:
            logger.error(f"Failed to count flow events: {str(e)}")
            return 0

    async def count_error_events(self, flow_id: uuid.UUID) -> int:
        """
        Count error events for a specific flow.

        Args:
            flow_id: Collection Flow ID

        Returns:
            Number of error events for the flow
        """
        try:
            result = await self.db.execute(
                select(func.count(SecurityAuditLog.id)).where(
                    and_(
                        SecurityAuditLog.resource_id == str(flow_id),
                        SecurityAuditLog.resource_type == "collection_flow",
                        SecurityAuditLog.status == "failure",
                    )
                )
            )
            return result.scalar() or 0

        except Exception as e:
            logger.error(f"Failed to count error events: {str(e)}")
            return 0
