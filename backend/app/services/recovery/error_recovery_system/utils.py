"""
Utility functions for error recovery system.

Provides helper functions for retry calculations, consistency checks, and statistics.
"""

import random
from typing import Any, Dict

from app.core.logging import get_logger
from app.services.auth.fallback_orchestrator import OperationType

from .models import RecoveryOperation, RecoveryType

logger = get_logger(__name__)


def calculate_retry_delay(operation: RecoveryOperation) -> float:
    """Calculate retry delay with exponential backoff and jitter"""
    base_delay = operation.base_delay_seconds
    multiplier = operation.backoff_multiplier
    retry_count = operation.retry_count

    # Exponential backoff
    delay = base_delay * (multiplier**retry_count)

    # Apply maximum delay
    delay = min(delay, operation.max_delay_seconds)

    # Add jitter if enabled
    if operation.jitter_enabled:
        jitter = delay * 0.1 * random.uniform(-1, 1)  # ±10% jitter
        delay += jitter

    return max(delay, 0.1)  # Minimum 100ms delay


def perform_consistency_check(
    operation: RecoveryOperation, result: Any, sample_rate: float = 0.1
) -> bool:
    """Perform consistency check on recovered data"""
    try:
        # Sample-based consistency checking
        if random.random() > sample_rate:
            return True  # Skip this check

        # Basic consistency checks based on operation type
        if operation.operation_type == OperationType.USER_SESSION:
            return check_user_session_consistency(result)
        elif operation.operation_type == OperationType.CACHE_WRITE:
            return check_cache_write_consistency(operation, result)

        return True  # Default to consistent if no specific check

    except Exception as e:
        logger.error(f"Consistency check failed for {operation.operation_id}: {e}")
        return False


def check_user_session_consistency(session_data: Any) -> bool:
    """Check user session data consistency"""
    if not isinstance(session_data, dict):
        return False

    required_fields = ["user_id", "email", "role"]
    for required_field in required_fields:
        if required_field not in session_data:
            logger.warning(f"Missing required field in session data: {required_field}")
            return False

    return True


def check_cache_write_consistency(operation: RecoveryOperation, result: Any) -> bool:
    """Check cache write operation consistency"""
    # For cache writes, we consider it consistent if the operation returned success
    return result is True or (isinstance(result, dict) and result.get("success", False))


def get_recovery_stats_summary(
    recovery_stats: Dict[RecoveryType, Dict[str, int]],
) -> Dict[str, Any]:
    """Get summary statistics for recovery operations"""
    total_attempts = 0
    total_successes = 0
    total_failures = 0

    summary = {}

    for recovery_type, stats in recovery_stats.items():
        attempts = stats.get("attempts", 0)
        successes = stats.get("successes", 0)
        failures = stats.get("failures", 0)

        success_rate = (successes / attempts * 100) if attempts > 0 else 0

        summary[recovery_type.value] = {
            "attempts": attempts,
            "successes": successes,
            "failures": failures,
            "success_rate": round(success_rate, 2),
        }

        total_attempts += attempts
        total_successes += successes
        total_failures += failures

    overall_success_rate = (
        (total_successes / total_attempts * 100) if total_attempts > 0 else 0
    )

    summary["overall"] = {
        "total_attempts": total_attempts,
        "total_successes": total_successes,
        "total_failures": total_failures,
        "overall_success_rate": round(overall_success_rate, 2),
    }

    return summary


def classify_failure_category(error_message: str) -> str:
    """Classify failure based on error message"""
    error_lower = error_message.lower()

    if any(keyword in error_lower for keyword in ["timeout", "connection", "network"]):
        return "transient"
    elif any(
        keyword in error_lower
        for keyword in ["auth", "permission", "forbidden", "unauthorized"]
    ):
        return "authentication"
    elif any(
        keyword in error_lower for keyword in ["memory", "disk", "quota", "limit"]
    ):
        return "resource_exhaustion"
    elif any(keyword in error_lower for keyword in ["corrupt", "invalid", "malformed"]):
        return "data_corruption"
    elif any(keyword in error_lower for keyword in ["service", "unavailable", "down"]):
        return "persistent"
    else:
        return "unknown"


def calculate_queue_health_score(queues: Dict, max_queue_size: int) -> float:
    """Calculate overall health score based on queue utilization"""
    total_items = 0
    total_capacity = 0

    for queue in queues.values():
        total_items += len(queue)
        total_capacity += max_queue_size

    if total_capacity == 0:
        return 100.0

    utilization = total_items / total_capacity

    # Score based on utilization (lower utilization = higher score)
    if utilization <= 0.5:
        return 100.0
    elif utilization <= 0.7:
        return 80.0
    elif utilization <= 0.9:
        return 60.0
    else:
        return 30.0
