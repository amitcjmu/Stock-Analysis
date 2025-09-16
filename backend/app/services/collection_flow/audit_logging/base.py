"""
Base classes, enums, and types for audit logging.

This module contains core types and enumerations used throughout
the audit logging system.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


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
