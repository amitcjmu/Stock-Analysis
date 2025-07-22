"""
Service models for agent service layer data structures.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ServiceCallStatus(str, Enum):
    """Service call status enumeration."""
    SUCCESS = "success"
    ERROR = "error"
    NOT_FOUND = "not_found"
    INVALID = "invalid"
    TIMEOUT = "timeout"


class ErrorType(str, Enum):
    """Error type enumeration."""
    SYSTEM = "system"
    NOT_FOUND = "not_found"
    PERMISSION = "permission"
    VALIDATION = "validation"
    TIMEOUT = "timeout"
    DATABASE = "database"


class PhaseType(str, Enum):
    """Discovery phase type enumeration."""
    DATA_IMPORT = "data_import"
    ATTRIBUTE_MAPPING = "attribute_mapping"
    DATA_CLEANSING = "data_cleansing"
    INVENTORY = "inventory"
    DEPENDENCIES = "dependencies"
    TECH_DEBT = "tech_debt"


class AssetType(str, Enum):
    """Asset type enumeration."""
    SERVER = "server"
    DATABASE = "database"
    APPLICATION = "application"
    NETWORK = "network"
    STORAGE = "storage"
    MIDDLEWARE = "middleware"
    SERVICE = "service"
    INFRASTRUCTURE = "infrastructure"
    SECURITY = "security"
    UNKNOWN = "unknown"


class ValidationLevel(str, Enum):
    """Validation level enumeration."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ServiceResponse(BaseModel):
    """Base service response model."""
    status: ServiceCallStatus
    message: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    error: Optional[str] = None
    error_type: Optional[ErrorType] = None
    guidance: Optional[str] = None


class FlowStatusResponse(ServiceResponse):
    """Flow status response model."""
    flow_exists: bool = False
    flow: Optional[Dict[str, Any]] = None
    active_flows_count: int = 0
    has_incomplete_flows: bool = False


class NavigationGuidanceItem(BaseModel):
    """Navigation guidance item model."""
    action: str
    description: str
    priority: str
    next_url: str


class NavigationGuidanceResponse(ServiceResponse):
    """Navigation guidance response model."""
    flow_id: Optional[str] = None
    current_phase: Optional[str] = None
    guidance: List[NavigationGuidanceItem] = []
    flow_status: Optional[Dict[str, Any]] = None


class PhaseCompletionResponse(ServiceResponse):
    """Phase completion response model."""
    flow_id: Optional[str] = None
    phase: Optional[str] = None
    is_complete: bool = False
    completion_details: Optional[Dict[str, Any]] = None


class FlowListItem(BaseModel):
    """Flow list item model."""
    flow_id: str
    status: str
    current_phase: str
    next_phase: Optional[str] = None
    progress: Optional[float] = None
    is_complete: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PhaseTransitionResponse(ServiceResponse):
    """Phase transition validation response model."""
    flow_id: Optional[str] = None
    from_phase: Optional[str] = None
    to_phase: Optional[str] = None
    transition_allowed: bool = False
    incomplete_prerequisites: List[str] = []
    validation_details: Optional[Dict[str, Any]] = None


class DataAnalysisResult(BaseModel):
    """Data analysis result model."""
    record_count: int
    sample_size: Optional[int] = None
    field_analysis: Dict[str, Any]
    data_quality: Dict[str, Any]


class ImportDataResponse(ServiceResponse):
    """Import data response model."""
    flow_id: Optional[str] = None
    data: List[Dict[str, Any]] = []
    metadata: Optional[Dict[str, Any]] = None
    analysis: Optional[DataAnalysisResult] = None


class MappingStatistics(BaseModel):
    """Mapping statistics model."""
    total_source_fields: int
    mapped_fields: int
    unmapped_fields: int
    mapping_completeness: float


class FieldMappingsResponse(ServiceResponse):
    """Field mappings response model."""
    flow_id: Optional[str] = None
    mappings: Dict[str, Any] = {}
    metadata: Optional[Dict[str, Any]] = None
    analysis: Optional[Dict[str, Any]] = None


class MappingValidationResult(BaseModel):
    """Mapping validation result model."""
    source_field: str
    target_mapping: Any
    issues: List[str] = []


class MappingValidationResponse(ServiceResponse):
    """Mapping validation response model."""
    flow_id: Optional[str] = None
    is_valid: bool = False
    validation_results: List[MappingValidationResult] = []
    summary: Optional[Dict[str, Any]] = None


class CleansingResultsResponse(ServiceResponse):
    """Cleansing results response model."""
    flow_id: Optional[str] = None
    results: Dict[str, Any] = {}
    metadata: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None


class ValidationIssue(BaseModel):
    """Validation issue model."""
    issue_type: str
    message: str
    severity: str
    field: Optional[str] = None
    suggestions: List[str] = []


class AssetItem(BaseModel):
    """Asset item model."""
    id: str
    name: str
    asset_type: str
    asset_subtype: Optional[str] = None
    status: str
    criticality: str = "medium"
    quality_score: float = 0.0
    confidence_score: float = 0.0
    validation_status: str = "pending"
    discovery_method: str = "unknown"
    discovered_at: Optional[str] = None
    last_updated: Optional[str] = None


class DependencyInfo(BaseModel):
    """Dependency information model."""
    asset_id: str
    asset_name: str
    asset_type: str
    depends_on: List[str] = []
    depended_by: List[str] = []
    dependency_count: int = 0
    dependent_count: int = 0


class DependencyAnalysis(BaseModel):
    """Dependency analysis model."""
    total_assets: int
    total_dependencies: int
    orphaned_assets: int
    highly_connected_assets: int
    dependency_density: float


class AssetDependenciesResponse(ServiceResponse):
    """Asset dependencies response model."""
    flow_id: Optional[str] = None
    dependencies: Dict[str, DependencyInfo] = {}
    analysis: Optional[DependencyAnalysis] = None
    insights: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class TechDebtSummary(BaseModel):
    """Technical debt summary model."""
    total_assets: int
    total_debt_items: int
    average_debt_score: float
    high_debt_assets: int
    medium_debt_assets: int
    low_debt_assets: int


class TechDebtAnalysisResponse(ServiceResponse):
    """Technical debt analysis response model."""
    flow_id: Optional[str] = None
    analysis: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class AssetValidationResult(BaseModel):
    """Asset validation result model."""
    required_fields: Dict[str, Any]
    data_quality: Dict[str, Any]
    consistency: Dict[str, Any]


class AssetValidationResponse(ServiceResponse):
    """Asset validation response model."""
    asset_id: Optional[str] = None
    asset_name: Optional[str] = None
    is_valid: bool = False
    validation_results: Optional[AssetValidationResult] = None
    recommendations: List[str] = []
    validation_score: float = 0.0


class RelationshipItem(BaseModel):
    """Relationship item model."""
    id: str
    name: str
    type: str
    relationship_type: str = "unknown"


class AssetRelationships(BaseModel):
    """Asset relationships model."""
    depends_on: List[RelationshipItem] = []
    dependents: List[RelationshipItem] = []
    related: List[RelationshipItem] = []


class AssetRelationshipsResponse(ServiceResponse):
    """Asset relationships response model."""
    asset_id: Optional[str] = None
    asset_name: Optional[str] = None
    asset_type: Optional[str] = None
    relationships: Optional[AssetRelationships] = None
    total_relationships: int = 0
    relationship_summary: Optional[Dict[str, int]] = None


class PerformanceOverview(BaseModel):
    """Performance overview model."""
    calls_made: int
    errors: int
    error_rate: float
    avg_response_time: float
    calls_per_second: float
    uptime_seconds: float


class PerformanceMetrics(BaseModel):
    """Performance metrics model."""
    overview: PerformanceOverview
    context: Dict[str, Any]
    recent_performance: Dict[str, Any]
    method_statistics: Dict[str, Any]
    slow_methods: List[Dict[str, Any]]
    error_analysis: Dict[str, Any]
    last_error: Optional[Dict[str, Any]] = None
    hourly_trends: List[Dict[str, Any]] = []


class HealthIndicator(BaseModel):
    """Health indicator model."""
    value: float
    recent_value: Optional[float] = None
    status: str
    threshold: Optional[float] = None


class HealthStatus(BaseModel):
    """Health status model."""
    status: str
    message: str
    indicators: Dict[str, HealthIndicator]
    recommendations: List[str] = []


class ServiceValidationResult(BaseModel):
    """Service validation result model."""
    is_valid: bool
    issues: List[str] = []
    recommendations: List[str] = []
    param_validations: Optional[Dict[str, Any]] = None
    field_validations: Optional[Dict[str, Any]] = None