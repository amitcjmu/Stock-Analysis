"""
Data Validation Schemas for Unified Discovery

Request and response models for data validation and profiling endpoints.

Related: ADR-038, Issue #1204, Issue #1210
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ==============================================================================
# Data Profile Response Models
# ==============================================================================


class QualityScores(BaseModel):
    """Quality scores for a data profile."""

    completeness: float = Field(..., description="Percentage of non-null values")
    consistency: float = Field(..., description="Data type consistency score")
    constraint_compliance: float = Field(
        ..., description="Schema constraint compliance score"
    )
    overall: float = Field(..., description="Overall quality score")


class DataProfileSummary(BaseModel):
    """Summary statistics for a data profile."""

    total_records: int
    total_fields: int
    quality_scores: QualityScores


class DataIssue(BaseModel):
    """A data quality issue detected during profiling."""

    severity: Literal["critical", "warning", "info"]
    field: str
    issue: str
    schema_limit: Optional[int] = None
    max_found: Optional[int] = None
    exceeds_by: Optional[int] = None
    affected_count: Optional[int] = None
    delimiter: Optional[str] = None
    null_percentage: Optional[float] = None
    samples: Optional[List[Dict[str, Any]]] = None
    recommendations: Optional[List[str]] = None
    recommendation: Optional[str] = None  # Single recommendation for multi-value


class DataProfileIssues(BaseModel):
    """Categorized data issues."""

    critical: List[DataIssue] = Field(default_factory=list)
    warnings: List[DataIssue] = Field(default_factory=list)
    info: List[DataIssue] = Field(default_factory=list)


class FieldProfile(BaseModel):
    """Profile for a single field."""

    min_length: int = 0
    max_length: int = 0
    avg_length: float = 0
    null_count: int = 0
    null_percentage: float = 0
    unique_count: int = 0
    unique_capped: bool = False
    total_records: int = 0
    non_null_records: int = 0


class DataProfileResponse(BaseModel):
    """Response model for data profile endpoint."""

    generated_at: datetime
    summary: DataProfileSummary
    issues: DataProfileIssues
    field_profiles: Dict[str, FieldProfile]
    user_action_required: bool
    blocking_issues: int


class DataProfileWrapper(BaseModel):
    """Wrapper response for data profile endpoint."""

    success: bool
    flow_id: str
    data_profile: Optional[DataProfileResponse] = None
    error: Optional[str] = None
    message: Optional[str] = None


# ==============================================================================
# Decision Request/Response Models
# ==============================================================================


class FieldDecision(BaseModel):
    """User decision for handling a data issue on a specific field."""

    field_name: str = Field(..., description="Name of the field to apply decision to")
    action: Literal["split", "truncate", "skip", "keep", "first_value"] = Field(
        ...,
        description="Action to take: split=create separate records, "
        "truncate=cut to limit, skip=exclude record, "
        "keep=store as-is, first_value=use first value before delimiter",
    )
    custom_delimiter: Optional[str] = Field(
        None,
        description="Custom delimiter for split action (overrides detected delimiter)",
    )


class DataProfileDecisionsRequest(BaseModel):
    """Request model for submitting data profile decisions."""

    decisions: List[FieldDecision] = Field(
        ..., description="List of decisions for each field with issues"
    )
    proceed_with_warnings: bool = Field(
        False, description="Whether to proceed despite unresolved warnings"
    )


class DataProfileDecisionsResponse(BaseModel):
    """Response model for data profile decisions submission."""

    success: bool
    flow_id: str
    decisions_applied: int
    message: str
    next_phase: Optional[str] = None
    warnings: Optional[List[str]] = None


# ==============================================================================
# Multi-Value Detection Models
# ==============================================================================


class MultiValueSample(BaseModel):
    """Sample of a multi-valued field value."""

    record_index: int
    value: str
    delimiter: str
    item_count: int


class MultiValueFieldResult(BaseModel):
    """Result of multi-value detection for a field."""

    field: str
    is_multi_valued: bool
    affected_count: int
    delimiter: Optional[str] = None
    samples: List[MultiValueSample] = Field(default_factory=list)
    recommendation: str


class MultiValueDetectionResponse(BaseModel):
    """Response for multi-value detection endpoint."""

    success: bool
    flow_id: str
    results: List[MultiValueFieldResult]


# ==============================================================================
# Length Violation Models
# ==============================================================================


class LengthViolationSample(BaseModel):
    """Sample of a length violation."""

    record_index: int
    value_length: int
    preview: str


class LengthViolationResult(BaseModel):
    """Result of length violation check for a field."""

    severity: Literal["critical"] = "critical"
    field: str
    issue: str
    schema_limit: int
    max_found: int
    exceeds_by: int
    affected_count: int
    samples: List[LengthViolationSample] = Field(default_factory=list)
    recommendations: List[str]


class LengthValidationResponse(BaseModel):
    """Response for length validation endpoint."""

    success: bool
    flow_id: str
    violations: List[LengthViolationResult]
    total_violations: int
