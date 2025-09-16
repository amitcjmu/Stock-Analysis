"""
Enhanced Error Handler - Base Classes and Data Structures

Core data structures, enums, and base classes for the enhanced error handling system.
Provides the foundational types used throughout the error handling framework.

Key Components:
- Error severity levels and categories
- User audience definitions
- Error context data structures
- Error classification and response models
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from app.services.auth.fallback_orchestrator import OperationType
from app.services.monitoring.service_health_manager import ServiceType
from app.services.recovery.error_recovery_system import (
    FailureCategory,
    RecoveryPriority,
    RecoveryType,
)


class ErrorSeverity(str, Enum):
    """Error severity levels"""

    LOW = "low"  # Minor issues, non-blocking
    MEDIUM = "medium"  # Degraded functionality
    HIGH = "high"  # Significant functionality loss
    CRITICAL = "critical"  # System or security critical


class ErrorCategory(str, Enum):
    """Error categories for classification"""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    NETWORK = "network"
    DATABASE = "database"
    CACHE = "cache"
    SERVICE_UNAVAILABLE = "service_unavailable"
    RATE_LIMITING = "rate_limiting"
    CONFIGURATION = "configuration"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class UserAudience(str, Enum):
    """Target audience for error messages"""

    END_USER = "end_user"  # Regular application users
    ADMIN_USER = "admin_user"  # Administrative users
    DEVELOPER = "developer"  # Developers and support staff
    SYSTEM = "system"  # System-to-system communication


@dataclass
class ErrorContext:
    """Context information for error handling"""

    error_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation_type: Optional[OperationType] = None
    service_type: Optional[ServiceType] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None

    # Sanitized context data (no sensitive information)
    context_data: Dict[str, Any] = field(default_factory=dict)

    # System state at time of error
    system_health: Optional[str] = None
    active_fallbacks: List[str] = field(default_factory=list)

    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ErrorClassification:
    """Classification result for an error"""

    category: ErrorCategory
    severity: ErrorSeverity
    is_recoverable: bool
    recovery_type: Optional[RecoveryType] = None
    failure_category: Optional[FailureCategory] = None
    confidence: float = 1.0  # Confidence in classification (0.0-1.0)

    # Service implications
    affected_services: Set[ServiceType] = field(default_factory=set)
    fallback_recommended: bool = False

    # Recovery recommendations
    recovery_priority: RecoveryPriority = RecoveryPriority.NORMAL
    max_retry_attempts: int = 3

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "is_recoverable": self.is_recoverable,
            "recovery_type": self.recovery_type.value if self.recovery_type else None,
            "failure_category": (
                self.failure_category.value if self.failure_category else None
            ),
            "confidence": self.confidence,
            "affected_services": [s.value for s in self.affected_services],
            "fallback_recommended": self.fallback_recommended,
            "recovery_priority": self.recovery_priority.value,
            "max_retry_attempts": self.max_retry_attempts,
        }


@dataclass
class ErrorResponse:
    """Structured error response"""

    # User-facing information
    error_code: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    recovery_suggestions: List[str] = field(default_factory=list)

    # System information
    error_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    category: ErrorCategory = ErrorCategory.UNKNOWN

    # Developer information (only in development)
    debug_info: Optional[Dict[str, Any]] = None

    # Recovery information
    recovery_initiated: bool = False
    fallback_active: bool = False
    estimated_recovery_time: Optional[int] = None  # seconds

    def to_dict(self, audience: UserAudience = UserAudience.END_USER) -> Dict[str, Any]:
        """Convert to dictionary based on target audience"""
        response = {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "recovery_suggestions": self.recovery_suggestions,
            "error_id": self.error_id,
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity.value,
            "category": self.category.value,
        }

        # Add system information for admin and developer audiences
        if audience in [UserAudience.ADMIN_USER, UserAudience.DEVELOPER]:
            response.update(
                {
                    "recovery_initiated": self.recovery_initiated,
                    "fallback_active": self.fallback_active,
                    "estimated_recovery_time": self.estimated_recovery_time,
                }
            )

        # Add debug information for developers
        if audience == UserAudience.DEVELOPER and self.debug_info:
            response["debug_info"] = self.debug_info

        return response
