"""
Audit data models and enums.

Defines the core data structures for audit logging.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class AuditLevel(Enum):
    """Audit logging levels"""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditCategory(Enum):
    """Audit event categories"""

    FLOW_LIFECYCLE = "flow_lifecycle"
    FLOW_EXECUTION = "flow_execution"
    USER_ACTION = "user_action"
    SYSTEM_EVENT = "system_event"
    SECURITY_EVENT = "security_event"
    COMPLIANCE_EVENT = "compliance_event"
    PERFORMANCE_EVENT = "performance_event"
    ERROR_EVENT = "error_event"
    AGENT_DECISION = "agent_decision"  # Agent decision audit events


@dataclass
class AuditEvent:
    """Audit event data structure"""

    event_id: str
    timestamp: datetime
    category: AuditCategory
    level: AuditLevel
    flow_id: str
    operation: str
    user_id: Optional[str] = None
    client_account_id: Optional[str] = None
    engagement_id: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    details: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
