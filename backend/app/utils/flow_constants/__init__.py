"""
Flow constants module for standardized flow management.
Provides flow status enums, phase definitions, error types, and performance thresholds.
"""

from .flow_configuration import (
    DEFAULT_FLOW_CONFIGS,
    FlowConfiguration,
    PhaseConfiguration,
    get_flow_configuration,
    get_phase_configuration,
    merge_flow_configurations,
    validate_flow_configuration,
)
from .flow_errors import (
    FLOW_ERROR_MESSAGES,
    FlowError,
    FlowErrorCode,
    FlowErrorSeverity,
    FlowErrorType,
    create_flow_error,
    get_error_message,
    get_error_severity,
    is_critical_error,
    is_recoverable_error,
)
from .flow_states import (
    FlowPhase,
    FlowPriority,
    FlowState,
    FlowStatus,
    FlowType,
    PhaseStatus,
    can_transition_to,
    get_allowed_transitions,
    get_flow_status_message,
    get_next_phase,
    get_previous_phase,
    is_active_status,
    is_error_status,
    is_terminal_status,
)
from .performance_thresholds import (
    PERFORMANCE_THRESHOLDS,
    RETRY_POLICIES,
    TIMEOUT_THRESHOLDS,
    FlowPerformanceMetrics,
    PerformanceThreshold,
    check_performance_threshold,
    get_performance_threshold,
    get_retry_policy,
    get_timeout_threshold,
    is_performance_acceptable,
)

__all__ = [
    # Flow States
    "FlowStatus",
    "FlowPhase",
    "FlowType",
    "FlowPriority",
    "FlowState",
    "PhaseStatus",
    "get_flow_status_message",
    "get_next_phase",
    "get_previous_phase",
    "is_terminal_status",
    "is_error_status",
    "is_active_status",
    "can_transition_to",
    "get_allowed_transitions",
    
    # Flow Errors
    "FlowErrorType",
    "FlowErrorSeverity",
    "FlowError",
    "FlowErrorCode",
    "FLOW_ERROR_MESSAGES",
    "create_flow_error",
    "get_error_message",
    "get_error_severity",
    "is_recoverable_error",
    "is_critical_error",
    
    # Performance Thresholds
    "PerformanceThreshold",
    "FlowPerformanceMetrics",
    "PERFORMANCE_THRESHOLDS",
    "TIMEOUT_THRESHOLDS",
    "RETRY_POLICIES",
    "get_performance_threshold",
    "get_timeout_threshold",
    "get_retry_policy",
    "check_performance_threshold",
    "is_performance_acceptable",
    
    # Flow Configuration
    "FlowConfiguration",
    "PhaseConfiguration",
    "DEFAULT_FLOW_CONFIGS",
    "get_flow_configuration",
    "get_phase_configuration",
    "validate_flow_configuration",
    "merge_flow_configurations"
]