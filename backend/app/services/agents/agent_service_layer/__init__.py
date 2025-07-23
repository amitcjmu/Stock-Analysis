"""
Agent Service Layer Module

Modularized agent service layer providing synchronous access to backend services:
- core/: Main service layer orchestration
- handlers/: Specialized handlers for different domains (flow, data, assets)
- validators/: Service validation and input checking
- metrics/: Performance tracking and monitoring
- models/: Pydantic schemas and data structures
- utils/: Utility functions and helpers
"""

# Main service class (backward compatibility)
from .agent_service_layer import AgentServiceLayer as LegacyAgentServiceLayer
from .agent_service_layer import get_agent_service
from .core.service_layer import AgentServiceLayer
from .handlers.asset_handler import AssetHandler
from .handlers.data_handler import DataHandler
from .handlers.flow_handler import FlowHandler
from .metrics.performance_tracker import PerformanceTracker
from .models.service_models import (AssetType, AssetValidationResponse,
                                    ErrorType, FlowStatusResponse,
                                    HealthStatus, NavigationGuidanceResponse,
                                    PerformanceMetrics, PhaseType,
                                    ServiceCallStatus)
from .utils.service_utils import (build_error_response,
                                  calculate_confidence_score, format_duration,
                                  normalize_asset_type, validate_uuid)
from .validators.service_validator import ServiceValidator

__all__ = [
    # Core components
    "AgentServiceLayer",
    "FlowHandler",
    "DataHandler",
    "AssetHandler",
    "ServiceValidator",
    "PerformanceTracker",
    # Models
    "ServiceCallStatus",
    "ErrorType",
    "PhaseType",
    "AssetType",
    "FlowStatusResponse",
    "NavigationGuidanceResponse",
    "AssetValidationResponse",
    "PerformanceMetrics",
    "HealthStatus",
    # Utilities
    "validate_uuid",
    "normalize_asset_type",
    "calculate_confidence_score",
    "format_duration",
    "build_error_response",
    # Legacy compatibility
    "LegacyAgentServiceLayer",
    "get_agent_service",
]
