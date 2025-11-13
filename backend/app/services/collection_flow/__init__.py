"""
Collection Flow Services Package

This package contains all services related to the Adaptive Data Collection System (ADCS).
It provides core functionality for managing Collection Flows, including state management,
adapter interfaces, tier detection, data transformation, quality scoring, and audit logging.
"""

from .adapters import AdapterRegistry, BaseAdapter, adapter_registry
from .audit_logging import AuditLoggingService, MonitoringService
from .data_transformation import DataNormalizationService, DataTransformationService
from .lifecycle_service import CollectionFlowLifecycleService
from .quality_scoring import ConfidenceAssessmentService, QualityAssessmentService
from .state_management import CollectionFlowStateService
from .tier_detection import TierDetectionService

__all__ = [
    "CollectionFlowStateService",
    "CollectionFlowLifecycleService",
    "BaseAdapter",
    "AdapterRegistry",
    "adapter_registry",
    "TierDetectionService",
    "DataTransformationService",
    "DataNormalizationService",
    "QualityAssessmentService",
    "ConfidenceAssessmentService",
    "AuditLoggingService",
    "MonitoringService",
]
