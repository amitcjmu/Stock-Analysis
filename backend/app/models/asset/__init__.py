"""
CMDB Asset models for multi-tenant asset management.

This module maintains backward compatibility by exporting all original classes
and enums from the modularized structure.
"""

# Import from modularized structure
from .mixins import AssetPropertiesMixin, AssetBusinessLogicMixin
from .enums import (
    AssetType,
    AssetStatus,
    SixRStrategy,
    WaveStatus,
    WorkflowStage,
    AnalysisStatus,
    ComplexityLevel,
    CriticalityLevel,
    DiscoveryMethod,
    AssessmentReadiness,
    ApplicationType,
    Lifecycle,
    HostingModel,
    ServerRole,
    RiskLevel,
    TShirtSize,
    VirtualizationType,
)
from .models import Asset
from .relationships import (
    AssetDependency,
    WorkflowProgress,
    CMDBSixRAnalysis,
    MigrationWave,
)
from .specialized import AssetEOLAssessment, AssetContact
from .base import (
    SQLALCHEMY_AVAILABLE,
    SMALL_STRING_LENGTH,
    MEDIUM_STRING_LENGTH,
    LARGE_STRING_LENGTH,
    IP_ADDRESS_LENGTH,
    MAC_ADDRESS_LENGTH,
    DEFAULT_MIGRATION_PRIORITY,
    DEFAULT_STATUS,
    DEFAULT_MIGRATION_STATUS,
    DEFAULT_ASSESSMENT_READINESS,
    DEFAULT_CURRENT_PHASE,
    DEFAULT_SOURCE_PHASE,
    COMPLEXITY_PENALTIES,
    MIN_SCORE,
    MAX_SCORE,
    ASSET_TYPE_PRIORITIES,
)

# Export everything that was available in the original file
__all__ = [
    # Enum classes
    "AssetType",
    "AssetStatus",
    "SixRStrategy",
    "WaveStatus",
    "WorkflowStage",
    "AnalysisStatus",
    "ComplexityLevel",
    "CriticalityLevel",
    "DiscoveryMethod",
    "AssessmentReadiness",
    "ApplicationType",
    "Lifecycle",
    "HostingModel",
    "ServerRole",
    "RiskLevel",
    "TShirtSize",
    "VirtualizationType",
    # Model classes
    "Asset",
    "AssetDependency",
    "WorkflowProgress",
    "CMDBSixRAnalysis",
    "MigrationWave",
    "AssetEOLAssessment",
    "AssetContact",
    # Mixins
    "AssetPropertiesMixin",
    "AssetBusinessLogicMixin",
    # Constants and utilities
    "SQLALCHEMY_AVAILABLE",
    "SMALL_STRING_LENGTH",
    "MEDIUM_STRING_LENGTH",
    "LARGE_STRING_LENGTH",
    "IP_ADDRESS_LENGTH",
    "MAC_ADDRESS_LENGTH",
    "DEFAULT_MIGRATION_PRIORITY",
    "DEFAULT_STATUS",
    "DEFAULT_MIGRATION_STATUS",
    "DEFAULT_ASSESSMENT_READINESS",
    "DEFAULT_CURRENT_PHASE",
    "DEFAULT_SOURCE_PHASE",
    "COMPLEXITY_PENALTIES",
    "MIN_SCORE",
    "MAX_SCORE",
    "ASSET_TYPE_PRIORITIES",
]
