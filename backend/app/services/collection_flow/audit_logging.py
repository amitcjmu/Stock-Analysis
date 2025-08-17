"""
Audit Logging and Monitoring Services for Collection Flow

This module provides comprehensive audit logging and monitoring capabilities
for the Collection Flow system, tracking all activities, changes, and events.
"""

import logging
import statistics
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.collection_flow import CollectionFlow
from app.models.security_audit import SecurityAuditLog

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Types of audit events"""

    # Flow lifecycle events
    FLOW_CREATED = "flow.created"
    FLOW_STARTED = "flow.started"
    FLOW_COMPLETED = "flow.completed"
    FLOW_FAILED = "flow.failed"
    FLOW_CANCELLED = "flow.cancelled"

    # Phase transition events
    PHASE_STARTED = "phase.started"
    PHASE_COMPLETED = "phase.completed"
    PHASE_FAILED = "phase.failed"

    # Data collection events
    COLLECTION_STARTED = "collection.started"
    COLLECTION_COMPLETED = "collection.completed"
    COLLECTION_FAILED = "collection.failed"
    DATA_TRANSFORMED = "data.transformed"
    DATA_VALIDATED = "data.validated"

    # Quality and assessment events
    QUALITY_ASSESSED = "quality.assessed"
    CONFIDENCE_ASSESSED = "confidence.assessed"
    GAP_IDENTIFIED = "gap.identified"
    GAP_RESOLVED = "gap.resolved"

    # Security events
    CREDENTIAL_ACCESSED = "credential.accessed"
    CREDENTIAL_VALIDATED = "credential.validated"
    UNAUTHORIZED_ACCESS = "security.unauthorized"

    # Configuration events
    CONFIG_CHANGED = "config.changed"
    ADAPTER_REGISTERED = "adapter.registered"
    ADAPTER_FAILED = "adapter.failed"

    # User action events
    USER_ACTION = "user.action"
    MANUAL_OVERRIDE = "user.override"
    DATA_EXPORT = "data.export"


class AuditSeverity(str, Enum):
    """Severity levels for audit events"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event data structure"""

    event_type: AuditEventType
    severity: AuditSeverity
    flow_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    description: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MonitoringMetrics:
    """Collection Flow monitoring metrics"""

    total_flows: int = 0
    active_flows: int = 0
    completed_flows: int = 0
    failed_flows: int = 0
    average_duration_minutes: float = 0.0
    success_rate: float = 0.0
    quality_score_average: float = 0.0
    confidence_score_average: float = 0.0
    events_per_hour: float = 0.0
    error_rate: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


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
        self.client_account_id = str(context.client_account_id)
        self.engagement_id = str(context.engagement_id)

    async def log_event(self, event: AuditEvent) -> None:
        """
        Log an audit event.

        Args:
            event: Audit event to log
        """
        try:
            # Prepare audit log entry
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
            # Get all audit events in date range
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

            # Categorize events
            events_by_type = {}
            events_by_severity = {}
            user_activities = {}

            for log in audit_logs:
                # By type
                event_type = log.action
                if event_type not in events_by_type:
                    events_by_type[event_type] = 0
                events_by_type[event_type] += 1

                # By severity
                severity = log.details.get("severity", "info")
                if severity not in events_by_severity:
                    events_by_severity[severity] = 0
                events_by_severity[severity] += 1

                # By user
                user_id = str(log.user_id)
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
            security_events = [
                log
                for log in audit_logs
                if log.action
                in [
                    AuditEventType.CREDENTIAL_ACCESSED.value,
                    AuditEventType.CREDENTIAL_VALIDATED.value,
                    AuditEventType.UNAUTHORIZED_ACCESS.value,
                ]
            ]

            report = {
                "report_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
                "summary": {
                    "total_events": len(audit_logs),
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
                            if e.action == AuditEventType.UNAUTHORIZED_ACCESS.value
                        ]
                    ),
                    "credential_access_events": len(
                        [
                            e
                            for e in security_events
                            if e.action == AuditEventType.CREDENTIAL_ACCESSED.value
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
                        "timestamp": log.performed_at.isoformat(),
                        "event_type": log.action,
                        "user_id": str(log.user_id),
                        "description": log.details.get("description", ""),
                        "severity": log.details.get("severity", "info"),
                        "ip_address": log.ip_address,
                    }
                    for log in audit_logs
                ]

            return report

        except Exception as e:
            logger.error(f"Failed to generate compliance report: {str(e)}")
            raise


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

    async def get_current_metrics(self) -> MonitoringMetrics:
        """
        Get current monitoring metrics.

        Returns:
            Current monitoring metrics
        """
        try:
            # Get flow statistics
            total_flows = await self._count_flows()
            active_flows = await self._count_flows_by_status(
                [
                    "initialized",
                    "platform_detection",
                    "automated_collection",
                    "gap_analysis",
                    "manual_collection",
                ]
            )
            completed_flows = await self._count_flows_by_status(["completed"])
            failed_flows = await self._count_flows_by_status(["failed"])

            # Calculate success rate
            finished_flows = completed_flows + failed_flows
            success_rate = (
                (completed_flows / finished_flows * 100) if finished_flows > 0 else 0
            )

            # Get average duration
            avg_duration = await self._calculate_average_duration()

            # Get quality metrics
            quality_avg = await self._calculate_average_quality_score()
            confidence_avg = await self._calculate_average_confidence_score()

            # Get event rate
            events_per_hour = await self._calculate_event_rate()

            # Calculate error rate
            error_rate = await self._calculate_error_rate()

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
            phase_durations = self._calculate_phase_durations(flow.phase_state)

            # Get event count
            event_count = await self._count_flow_events(flow_id)

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

            health_issues = []

            # Check if flow is stuck
            if metrics["status"] not in ["completed", "failed", "cancelled"]:
                duration = metrics.get("duration_minutes")
                if duration and duration > 120:  # 2 hours
                    health_issues.append("Flow running longer than expected")

            # Check progress
            if (
                metrics["progress_percentage"] < 10
                and metrics.get("duration_minutes", 0) > 30
            ):
                health_issues.append("Low progress after extended time")

            # Check quality scores
            if metrics.get("quality_score") and metrics["quality_score"] < 50:
                health_issues.append("Low quality score")

            if metrics.get("confidence_score") and metrics["confidence_score"] < 50:
                health_issues.append("Low confidence score")

            # Check error rate
            error_events = await self._count_error_events(flow_id)
            if error_events > 10:
                health_issues.append(f"High error count: {error_events}")

            return {
                "healthy": len(health_issues) == 0,
                "issues": health_issues,
                "metrics": metrics,
                "checked_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to check flow health: {str(e)}")
            return {"healthy": False, "reason": f"Health check failed: {str(e)}"}

    async def _count_flows(self) -> int:
        """Count total flows."""
        result = await self.db.execute(
            select(func.count(CollectionFlow.id)).where(
                CollectionFlow.client_account_id == uuid.UUID(self.client_account_id)
            )
        )
        return result.scalar() or 0

    async def _count_flows_by_status(self, statuses: List[str]) -> int:
        """Count flows by status."""
        result = await self.db.execute(
            select(func.count(CollectionFlow.id)).where(
                and_(
                    CollectionFlow.client_account_id
                    == uuid.UUID(self.client_account_id),
                    CollectionFlow.status.in_(statuses),
                )
            )
        )
        return result.scalar() or 0

    async def _calculate_average_duration(self) -> float:
        """Calculate average flow duration in minutes."""
        result = await self.db.execute(
            select(CollectionFlow).where(
                and_(
                    CollectionFlow.client_account_id
                    == uuid.UUID(self.client_account_id),
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

    async def _calculate_average_quality_score(self) -> float:
        """Calculate average quality score."""
        result = await self.db.execute(
            select(func.avg(CollectionFlow.collection_quality_score)).where(
                and_(
                    CollectionFlow.client_account_id
                    == uuid.UUID(self.client_account_id),
                    CollectionFlow.collection_quality_score.isnot(None),
                )
            )
        )
        return result.scalar() or 0.0

    async def _calculate_average_confidence_score(self) -> float:
        """Calculate average confidence score."""
        result = await self.db.execute(
            select(func.avg(CollectionFlow.confidence_score)).where(
                and_(
                    CollectionFlow.client_account_id
                    == uuid.UUID(self.client_account_id),
                    CollectionFlow.confidence_score.isnot(None),
                )
            )
        )
        return result.scalar() or 0.0

    async def _calculate_event_rate(self) -> float:
        """Calculate events per hour."""
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)

        result = await self.db.execute(
            select(func.count(SecurityAuditLog.id)).where(
                and_(
                    SecurityAuditLog.resource_type == "collection_flow",
                    SecurityAuditLog.client_account_id
                    == uuid.UUID(self.client_account_id),
                    SecurityAuditLog.performed_at >= one_hour_ago,
                )
            )
        )
        return float(result.scalar() or 0)

    async def _calculate_error_rate(self) -> float:
        """Calculate error rate percentage."""
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)

        # Count total events
        total_result = await self.db.execute(
            select(func.count(SecurityAuditLog.id)).where(
                and_(
                    SecurityAuditLog.resource_type == "collection_flow",
                    SecurityAuditLog.client_account_id
                    == uuid.UUID(self.client_account_id),
                    SecurityAuditLog.performed_at >= one_hour_ago,
                )
            )
        )
        total_events = total_result.scalar() or 0

        # Count error events
        error_result = await self.db.execute(
            select(func.count(SecurityAuditLog.id)).where(
                and_(
                    SecurityAuditLog.resource_type == "collection_flow",
                    SecurityAuditLog.client_account_id
                    == uuid.UUID(self.client_account_id),
                    SecurityAuditLog.performed_at >= one_hour_ago,
                    SecurityAuditLog.status == "failure",
                )
            )
        )
        error_events = error_result.scalar() or 0

        if total_events == 0:
            return 0.0

        return (error_events / total_events) * 100

    async def _count_flow_events(self, flow_id: uuid.UUID) -> int:
        """Count events for a specific flow."""
        result = await self.db.execute(
            select(func.count(SecurityAuditLog.id)).where(
                and_(
                    SecurityAuditLog.resource_id == str(flow_id),
                    SecurityAuditLog.resource_type == "collection_flow",
                )
            )
        )
        return result.scalar() or 0

    async def _count_error_events(self, flow_id: uuid.UUID) -> int:
        """Count error events for a specific flow."""
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

    def _calculate_phase_durations(
        self, phase_state: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate duration for each phase."""
        durations = {}

        phase_history = phase_state.get("phase_history", [])
        for phase in phase_history:
            phase_name = phase.get("phase")
            started_at = phase.get("started_at")
            completed_at = phase.get("completed_at")

            if phase_name and started_at:
                try:
                    start_dt = datetime.fromisoformat(started_at)
                    if completed_at:
                        end_dt = datetime.fromisoformat(completed_at)
                    else:
                        end_dt = datetime.utcnow()

                    duration_minutes = (end_dt - start_dt).total_seconds() / 60
                    durations[phase_name] = round(duration_minutes, 2)
                except Exception:
                    pass

        return durations
