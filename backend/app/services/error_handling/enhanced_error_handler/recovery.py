"""
Enhanced Error Handler - Error Recovery Logic

Handles error recovery operations, pattern learning, and intelligent recovery
strategies. Integrates with the error recovery system for automatic recovery.

Key Features:
- Automatic error recovery initiation
- Error pattern learning and optimization
- Recovery operation scheduling
- Pattern-based improvement recommendations
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from app.core.logging import get_logger
from app.core.security.cache_encryption import sanitize_for_logging
from app.services.auth.fallback_orchestrator import OperationType
from app.services.monitoring.service_health_manager import ServiceType
from app.services.recovery.error_recovery_system import (
    ErrorRecoverySystem,
    FailureCategory,
    RecoveryType,
    get_error_recovery_system,
)

from .base import ErrorClassification, ErrorContext

logger = get_logger(__name__)


class ErrorRecoveryManager:
    """Manages error recovery operations and pattern learning"""

    def __init__(self, recovery_system: Optional[ErrorRecoverySystem] = None):
        self.recovery_system = recovery_system or get_error_recovery_system()

        # Error pattern learning
        self.error_patterns: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        logger.info("ErrorRecoveryManager initialized with pattern learning")

    async def initiate_recovery(
        self,
        error: Exception,
        classification: ErrorClassification,
        context: ErrorContext,
        operation_func: Any,
        operation_args: Tuple,
        operation_kwargs: Dict[str, Any],
    ) -> bool:
        """Initiate recovery process for recoverable errors"""

        try:
            # Schedule recovery operation
            recovery_id = await self.recovery_system.schedule_recovery_operation(
                operation_func=operation_func,
                operation_args=operation_args,
                operation_kwargs=operation_kwargs,
                recovery_type=classification.recovery_type
                or RecoveryType.IMMEDIATE_RETRY,
                failure_category=classification.failure_category
                or FailureCategory.UNKNOWN,
                priority=classification.recovery_priority,
                operation_type=context.operation_type or OperationType.CACHE_READ,
                service_type=context.service_type or ServiceType.REDIS,
                context_data=sanitize_for_logging(context.context_data),
                max_retry_attempts=classification.max_retry_attempts,
            )

            logger.info(
                f"Recovery initiated for error {context.error_id}: recovery_id={recovery_id}",
                extra={
                    "error_id": context.error_id,
                    "recovery_id": recovery_id,
                    "recovery_type": (
                        classification.recovery_type.value
                        if classification.recovery_type
                        else None
                    ),
                },
            )

            return True

        except Exception as recovery_error:
            logger.error(
                f"Failed to initiate recovery for error {context.error_id}: {recovery_error}",
                extra={"error_id": context.error_id},
            )
            return False

    async def learn_from_error_pattern(
        self,
        error: Exception,
        classification: ErrorClassification,
        context: ErrorContext,
    ):
        """Learn from error patterns for improved classification"""

        try:
            pattern_key = f"{classification.category.value}:{type(error).__name__}"

            pattern_data = {
                "timestamp": context.timestamp.isoformat(),
                "error_type": type(error).__name__,
                "classification": classification.to_dict(),
                "context_summary": {
                    "operation_type": (
                        context.operation_type.value if context.operation_type else None
                    ),
                    "service_type": (
                        context.service_type.value if context.service_type else None
                    ),
                    "system_health": context.system_health,
                },
            }

            self.error_patterns[pattern_key].append(pattern_data)

            # Keep only recent patterns (last 100 per pattern)
            if len(self.error_patterns[pattern_key]) > 100:
                self.error_patterns[pattern_key] = self.error_patterns[pattern_key][
                    -100:
                ]

        except Exception as learning_error:
            logger.warning(f"Failed to learn from error pattern: {learning_error}")

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error pattern statistics"""
        pattern_stats = {}

        for pattern_key, patterns in self.error_patterns.items():
            recent_patterns = [
                p
                for p in patterns
                if datetime.fromisoformat(p["timestamp"])
                > datetime.utcnow() - timedelta(hours=24)
            ]

            pattern_stats[pattern_key] = {
                "total_occurrences": len(patterns),
                "recent_24h": len(recent_patterns),
                "latest_occurrence": patterns[-1]["timestamp"] if patterns else None,
            }

        return {
            "total_patterns_learned": len(self.error_patterns),
            "pattern_statistics": pattern_stats,
        }

    def clear_error_patterns(self) -> int:
        """Clear learned error patterns"""
        count = len(self.error_patterns)
        self.error_patterns.clear()

        logger.info(f"Cleared {count} error patterns from learning cache")
        return count

    def get_recovery_recommendations(
        self, error_category: str, service_type: Optional[str] = None
    ) -> List[str]:
        """Get recovery recommendations based on learned patterns"""
        try:
            recommendations = []

            # Get patterns for this error category
            category_patterns = [
                patterns
                for key, patterns in self.error_patterns.items()
                if key.startswith(error_category)
            ]

            if not category_patterns:
                return []

            # Analyze recent patterns
            recent_cutoff = datetime.utcnow() - timedelta(hours=24)
            recent_failures = []

            for patterns in category_patterns:
                for pattern in patterns:
                    if datetime.fromisoformat(pattern["timestamp"]) > recent_cutoff:
                        recent_failures.append(pattern)

            # Generate recommendations based on patterns
            if len(recent_failures) > 5:
                recommendations.append(
                    f"High frequency of {error_category} errors detected. Consider investigating root cause."
                )

            if service_type:
                service_failures = [
                    f
                    for f in recent_failures
                    if f.get("context_summary", {}).get("service_type") == service_type
                ]
                if len(service_failures) > 3:
                    recommendations.append(
                        f"Multiple {service_type} service failures. Check service health."
                    )

            # Add general recommendations based on category
            if error_category == "database":
                recommendations.extend(
                    [
                        "Check database connection pool health",
                        "Review slow query logs",
                        "Verify database resource utilization",
                    ]
                )
            elif error_category == "cache":
                recommendations.extend(
                    [
                        "Check Redis service health",
                        "Review cache miss rates",
                        "Consider cache warming strategies",
                    ]
                )
            elif error_category == "network":
                recommendations.extend(
                    [
                        "Check network connectivity",
                        "Review DNS resolution",
                        "Verify external service endpoints",
                    ]
                )

            return recommendations

        except Exception as e:
            logger.warning(f"Failed to generate recovery recommendations: {e}")
            return []


# Singleton instance
_error_recovery_manager_instance: Optional[ErrorRecoveryManager] = None


def get_error_recovery_manager() -> ErrorRecoveryManager:
    """Get singleton ErrorRecoveryManager instance"""
    global _error_recovery_manager_instance
    if _error_recovery_manager_instance is None:
        _error_recovery_manager_instance = ErrorRecoveryManager()
    return _error_recovery_manager_instance


# Cleanup function for app shutdown
async def shutdown_error_recovery_manager():
    """Shutdown error recovery manager (call during app shutdown)"""
    global _error_recovery_manager_instance
    if _error_recovery_manager_instance:
        _error_recovery_manager_instance.clear_error_patterns()
        _error_recovery_manager_instance = None
