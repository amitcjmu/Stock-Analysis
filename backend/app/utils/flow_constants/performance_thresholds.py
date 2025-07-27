"""
Performance thresholds and monitoring constants for flow management.
Provides performance metrics, timeout thresholds, and retry policies.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class PerformanceThreshold(str, Enum):
    """Performance threshold categories."""

    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class FlowPerformanceMetrics:
    """Performance metrics for flow operations."""

    execution_time_seconds: float
    memory_usage_mb: float
    cpu_usage_percent: float
    network_requests: int
    database_queries: int
    error_rate_percent: float

    def get_overall_performance(self) -> PerformanceThreshold:
        """Calculate overall performance threshold."""
        # Simple scoring based on multiple factors
        score = 0

        # Execution time scoring (0-25 points)
        if self.execution_time_seconds < 30:
            score += 25
        elif self.execution_time_seconds < 60:
            score += 20
        elif self.execution_time_seconds < 120:
            score += 15
        elif self.execution_time_seconds < 300:
            score += 10
        else:
            score += 0

        # Memory usage scoring (0-25 points)
        if self.memory_usage_mb < 100:
            score += 25
        elif self.memory_usage_mb < 500:
            score += 20
        elif self.memory_usage_mb < 1000:
            score += 15
        elif self.memory_usage_mb < 2000:
            score += 10
        else:
            score += 0

        # CPU usage scoring (0-25 points)
        if self.cpu_usage_percent < 20:
            score += 25
        elif self.cpu_usage_percent < 40:
            score += 20
        elif self.cpu_usage_percent < 60:
            score += 15
        elif self.cpu_usage_percent < 80:
            score += 10
        else:
            score += 0

        # Error rate scoring (0-25 points)
        if self.error_rate_percent < 1:
            score += 25
        elif self.error_rate_percent < 5:
            score += 20
        elif self.error_rate_percent < 10:
            score += 15
        elif self.error_rate_percent < 20:
            score += 10
        else:
            score += 0

        # Convert score to threshold
        if score >= 90:
            return PerformanceThreshold.EXCELLENT
        elif score >= 75:
            return PerformanceThreshold.GOOD
        elif score >= 60:
            return PerformanceThreshold.ACCEPTABLE
        elif score >= 40:
            return PerformanceThreshold.POOR
        else:
            return PerformanceThreshold.CRITICAL


# Performance thresholds by flow type and phase
PERFORMANCE_THRESHOLDS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "discovery": {
        "initialization": {
            "max_execution_time": 30,
            "max_memory_usage": 100,
            "max_cpu_usage": 50,
            "max_error_rate": 2,
        },
        "data_import": {
            "max_execution_time": 300,
            "max_memory_usage": 1000,
            "max_cpu_usage": 80,
            "max_error_rate": 5,
        },
        "data_validation": {
            "max_execution_time": 120,
            "max_memory_usage": 500,
            "max_cpu_usage": 60,
            "max_error_rate": 3,
        },
        "field_mapping": {
            "max_execution_time": 180,
            "max_memory_usage": 300,
            "max_cpu_usage": 70,
            "max_error_rate": 5,
        },
        "data_cleansing": {
            "max_execution_time": 600,
            "max_memory_usage": 1500,
            "max_cpu_usage": 90,
            "max_error_rate": 10,
        },
        "asset_inventory": {
            # No timeout restrictions for agentic classification activities
            "max_execution_time": None,  # Unlimited time for asset classification
            "max_memory_usage": 800,
            "max_cpu_usage": 70,
            "max_error_rate": 3,
        },
        "dependency_analysis": {
            "max_execution_time": 900,
            "max_memory_usage": 2000,
            "max_cpu_usage": 95,
            "max_error_rate": 5,
        },
        "tech_debt_analysis": {
            "max_execution_time": 600,
            "max_memory_usage": 1000,
            "max_cpu_usage": 80,
            "max_error_rate": 8,
        },
    },
    "assessment": {
        "initialization": {
            "max_execution_time": 20,
            "max_memory_usage": 50,
            "max_cpu_usage": 30,
            "max_error_rate": 1,
        },
        "assessment": {
            "max_execution_time": 1800,
            "max_memory_usage": 2500,
            "max_cpu_usage": 95,
            "max_error_rate": 5,
        },
        "tech_debt_analysis": {
            "max_execution_time": 600,
            "max_memory_usage": 1000,
            "max_cpu_usage": 80,
            "max_error_rate": 8,
        },
    },
}

# Timeout thresholds for different operations
TIMEOUT_THRESHOLDS: Dict[str, Dict[str, int]] = {
    "database_operations": {
        "simple_query": 5,
        "complex_query": 30,
        "transaction": 60,
        "bulk_insert": 300,
        "migration": 1800,
    },
    "file_operations": {
        "small_file_upload": 30,
        "large_file_upload": 300,
        "file_processing": 600,
        "file_validation": 120,
    },
    "external_services": {
        "api_call": 30,
        "llm_request": 120,
        "webhook_call": 60,
        "health_check": 10,
    },
    "agent_operations": {
        "agent_initialization": 60,
        "task_execution": 600,
        "crew_collaboration": 1800,
        "agent_communication": 30,
    },
    "flow_operations": {
        "phase_initialization": 30,
        "phase_execution": 3600,
        "phase_cleanup": 120,
        "flow_completion": 60,
    },
}

# Retry policies for different error types
RETRY_POLICIES: Dict[str, Dict[str, Any]] = {
    "network_errors": {
        "max_retries": 3,
        "base_delay": 1,
        "max_delay": 60,
        "backoff_factor": 2,
        "exponential_backoff": True,
    },
    "timeout_errors": {
        "max_retries": 2,
        "base_delay": 5,
        "max_delay": 120,
        "backoff_factor": 3,
        "exponential_backoff": True,
    },
    "rate_limit_errors": {
        "max_retries": 5,
        "base_delay": 10,
        "max_delay": 300,
        "backoff_factor": 2,
        "exponential_backoff": True,
    },
    "temporary_errors": {
        "max_retries": 3,
        "base_delay": 2,
        "max_delay": 30,
        "backoff_factor": 2,
        "exponential_backoff": True,
    },
    "agent_errors": {
        "max_retries": 2,
        "base_delay": 5,
        "max_delay": 60,
        "backoff_factor": 2,
        "exponential_backoff": True,
    },
    "system_errors": {
        "max_retries": 1,
        "base_delay": 10,
        "max_delay": 60,
        "backoff_factor": 1,
        "exponential_backoff": False,
    },
}

# Resource usage thresholds
RESOURCE_THRESHOLDS: Dict[str, Dict[str, Any]] = {
    "memory": {
        "warning_threshold": 1000,  # MB
        "critical_threshold": 2000,  # MB
        "max_threshold": 4000,  # MB
    },
    "cpu": {
        "warning_threshold": 70,  # %
        "critical_threshold": 90,  # %
        "max_threshold": 95,  # %
    },
    "disk": {
        "warning_threshold": 5000,  # MB
        "critical_threshold": 10000,  # MB
        "max_threshold": 20000,  # MB
    },
    "network": {
        "warning_threshold": 100,  # requests/minute
        "critical_threshold": 500,  # requests/minute
        "max_threshold": 1000,  # requests/minute
    },
}


# Helper functions
def get_performance_threshold(flow_type: str, phase: str) -> Dict[str, Any]:
    """Get performance threshold for specific flow type and phase."""
    flow_thresholds = PERFORMANCE_THRESHOLDS.get(flow_type, {})
    return flow_thresholds.get(
        phase,
        {
            "max_execution_time": 300,
            "max_memory_usage": 500,
            "max_cpu_usage": 70,
            "max_error_rate": 5,
        },
    )


def get_timeout_threshold(operation_category: str, operation_type: str) -> int:
    """Get timeout threshold for specific operation."""
    category_timeouts = TIMEOUT_THRESHOLDS.get(operation_category, {})
    return category_timeouts.get(operation_type, 300)  # Default 5 minutes


def get_retry_policy(error_type: str) -> Dict[str, Any]:
    """Get retry policy for specific error type."""
    return RETRY_POLICIES.get(
        error_type,
        {
            "max_retries": 3,
            "base_delay": 1,
            "max_delay": 60,
            "backoff_factor": 2,
            "exponential_backoff": True,
        },
    )


def check_performance_threshold(
    metrics: FlowPerformanceMetrics, flow_type: str, phase: str
) -> bool:
    """Check if performance metrics meet threshold requirements."""
    thresholds = get_performance_threshold(flow_type, phase)

    # Check each metric against threshold
    if metrics.execution_time_seconds > thresholds.get("max_execution_time", 300):
        return False

    if metrics.memory_usage_mb > thresholds.get("max_memory_usage", 500):
        return False

    if metrics.cpu_usage_percent > thresholds.get("max_cpu_usage", 70):
        return False

    if metrics.error_rate_percent > thresholds.get("max_error_rate", 5):
        return False

    return True


def is_performance_acceptable(metrics: FlowPerformanceMetrics) -> bool:
    """Check if performance metrics are acceptable."""
    performance_level = metrics.get_overall_performance()
    return performance_level in {
        PerformanceThreshold.EXCELLENT,
        PerformanceThreshold.GOOD,
        PerformanceThreshold.ACCEPTABLE,
    }


def get_resource_threshold(resource_type: str, threshold_level: str) -> Optional[int]:
    """Get resource threshold for specific resource type and level."""
    resource_thresholds = RESOURCE_THRESHOLDS.get(resource_type, {})
    return resource_thresholds.get(threshold_level)


def calculate_backoff_delay(
    retry_count: int,
    base_delay: int,
    max_delay: int,
    backoff_factor: int,
    exponential: bool = True,
) -> int:
    """Calculate backoff delay for retry attempts."""
    if exponential:
        delay = base_delay * (backoff_factor**retry_count)
    else:
        delay = base_delay * backoff_factor * retry_count

    return min(delay, max_delay)


def should_retry(error_type: str, retry_count: int) -> bool:
    """Check if operation should be retried based on error type and count."""
    policy = get_retry_policy(error_type)
    return retry_count < policy.get("max_retries", 3)


def get_next_retry_delay(error_type: str, retry_count: int) -> int:
    """Get delay for next retry attempt."""
    policy = get_retry_policy(error_type)

    return calculate_backoff_delay(
        retry_count=retry_count,
        base_delay=policy.get("base_delay", 1),
        max_delay=policy.get("max_delay", 60),
        backoff_factor=policy.get("backoff_factor", 2),
        exponential=policy.get("exponential_backoff", True),
    )


def get_performance_recommendations(metrics: FlowPerformanceMetrics) -> Dict[str, str]:
    """Get performance improvement recommendations based on metrics."""
    recommendations = {}

    if metrics.execution_time_seconds > 300:
        recommendations["execution_time"] = (
            "Consider optimizing algorithms or adding parallel processing"
        )

    if metrics.memory_usage_mb > 1000:
        recommendations["memory"] = (
            "Consider implementing memory optimization or data streaming"
        )

    if metrics.cpu_usage_percent > 80:
        recommendations["cpu"] = (
            "Consider load balancing or reducing computational complexity"
        )

    if metrics.error_rate_percent > 5:
        recommendations["error_rate"] = (
            "Review error handling and implement better validation"
        )

    if metrics.database_queries > 100:
        recommendations["database"] = (
            "Consider query optimization or caching strategies"
        )

    return recommendations
