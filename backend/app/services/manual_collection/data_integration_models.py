"""
Data Integration Models

Models and enums for data integration service.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID


class DataSource(str, Enum):
    """Types of data sources"""

    AUTOMATED_DISCOVERY = "automated_discovery"
    MANUAL_COLLECTION = "manual_collection"
    BULK_UPLOAD = "bulk_upload"
    API_INTEGRATION = "api_integration"
    USER_INPUT = "user_input"


class ConflictResolutionStrategy(str, Enum):
    """Strategies for resolving data conflicts"""

    PREFER_MANUAL = "prefer_manual"
    PREFER_AUTOMATED = "prefer_automated"
    PREFER_NEWEST = "prefer_newest"
    PREFER_HIGHEST_CONFIDENCE = "prefer_highest_confidence"
    REQUIRE_USER_REVIEW = "require_user_review"


class DataQualityLevel(str, Enum):
    """Data quality assessment levels"""

    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class DataPoint:
    """Individual data point with metadata"""

    attribute_name: str
    value: Any
    source: DataSource
    confidence_score: float
    timestamp: datetime
    collection_method: str
    validation_status: str
    metadata: Dict[str, Any]


@dataclass
class DataConflict:
    """Conflict between data points"""

    attribute_name: str
    conflicting_values: List[DataPoint]
    resolution_strategy: ConflictResolutionStrategy
    resolved_value: Optional[DataPoint] = None
    requires_review: bool = False


@dataclass
class IntegratedDataset:
    """Complete integrated dataset for an application"""

    application_id: UUID
    data_points: List[DataPoint]
    conflicts: List[DataConflict]
    completeness_score: float
    quality_level: DataQualityLevel
    critical_attributes_coverage: float
    confidence_score: float
    sixr_readiness_score: float
    created_at: datetime
    last_updated: datetime


@dataclass
class DataSourceSummary:
    """Summary of data from a specific source"""

    source: DataSource
    total_attributes: int
    coverage_percentage: float
    average_confidence: float
    collection_timestamp: datetime
    method_details: Dict[str, Any]


@dataclass
class IntegrationReport:
    """Report of data integration process"""

    application_id: UUID
    sources_integrated: List[DataSourceSummary]
    total_conflicts: int
    resolved_conflicts: int
    pending_conflicts: int
    data_quality_level: DataQualityLevel
    completeness_score: float
    recommendations: List[str]
    next_actions: List[str]
    integration_timestamp: datetime
