"""
Pydantic schemas for two-phase gap analysis API.

These schemas define request/response models for:
- Phase 1: Programmatic gap scanning
- Phase 2: AI-enhanced gap analysis
- Gap resolution and updates
"""

from typing import Any, List, Optional
from pydantic import BaseModel, Field, validator


# ============================================================================
# Phase 1: Programmatic Gap Scan Schemas
# ============================================================================


class ScanGapsRequest(BaseModel):
    """Request body for programmatic gap scan (Phase 1)."""

    selected_asset_ids: List[str] = Field(
        ..., description="UUIDs of assets to scan for gaps", min_length=1
    )

    class Config:
        json_schema_extra = {
            "example": {
                "selected_asset_ids": [
                    "11111111-1111-1111-1111-111111111111",
                    "22222222-2222-2222-2222-222222222222",
                ]
            }
        }


class DataGap(BaseModel):
    """Individual data gap identified by scanner or enhanced by AI."""

    asset_id: str = Field(..., description="UUID of asset with gap")
    asset_name: str = Field(..., description="Human-readable asset name")
    field_name: str = Field(..., description="Critical attribute name")
    gap_type: str = Field(
        ..., description="Type of gap (missing_field, incomplete_data, etc.)"
    )
    gap_category: str = Field(
        ..., description="Category (infrastructure, application, business, etc.)"
    )
    priority: int = Field(..., description="Priority 1-4 (1=critical)")
    current_value: Optional[Any] = Field(
        None, description="Current value if partially populated"
    )
    suggested_resolution: str = Field(..., description="How to resolve this gap")
    confidence_score: Optional[float] = Field(
        None, description="AI confidence 0.0-1.0, null if no AI"
    )
    ai_suggestions: Optional[List[str]] = Field(
        None, description="AI suggestions array"
    )

    @validator("priority")
    def validate_priority(cls, v):
        if v not in [1, 2, 3, 4]:
            raise ValueError("Priority must be 1-4")
        return v

    @validator("confidence_score")
    def validate_confidence_score(cls, v):
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "asset_id": "11111111-1111-1111-1111-111111111111",
                "asset_name": "App-001",
                "field_name": "technology_stack",
                "gap_type": "missing_field",
                "gap_category": "application",
                "priority": 1,
                "current_value": None,
                "suggested_resolution": "Manual collection required",
                "confidence_score": None,
                "ai_suggestions": None,
            }
        }


class GapScanSummary(BaseModel):
    """Summary statistics for gap scan."""

    total_gaps: int = Field(..., description="Total gaps identified")
    assets_analyzed: int = Field(..., description="Number of assets scanned")
    critical_gaps: int = Field(..., description="Number of priority 1 gaps")
    execution_time_ms: int = Field(
        ..., description="Scan execution time in milliseconds"
    )
    gaps_persisted: int = Field(..., description="Number of gaps persisted to database")


class ScanGapsResponse(BaseModel):
    """Response from programmatic gap scan."""

    gaps: List[DataGap] = Field(..., description="List of identified gaps")
    summary: GapScanSummary = Field(..., description="Scan summary statistics")
    status: str = Field(
        ..., description="SCAN_COMPLETE, SCAN_FAILED, SCAN_COMPLETE_NO_ASSETS"
    )
    error: Optional[str] = Field(
        None, description="Error message if status=SCAN_FAILED"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "gaps": [
                    {
                        "asset_id": "11111111-1111-1111-1111-111111111111",
                        "asset_name": "App-001",
                        "field_name": "technology_stack",
                        "gap_type": "missing_field",
                        "gap_category": "application",
                        "priority": 1,
                        "current_value": None,
                        "suggested_resolution": "Manual collection required",
                        "confidence_score": None,
                    }
                ],
                "summary": {
                    "total_gaps": 16,
                    "assets_analyzed": 2,
                    "critical_gaps": 5,
                    "execution_time_ms": 234,
                    "gaps_persisted": 16,
                },
                "status": "SCAN_COMPLETE",
            }
        }


# ============================================================================
# Phase 2: AI-Enhanced Analysis Schemas
# ============================================================================


class AnalyzeGapsRequest(BaseModel):
    """Request body for AI-enhanced gap analysis (Phase 2)."""

    gaps: Optional[List[DataGap]] = Field(
        None,
        description=(
            "Gaps from programmatic scan. "
            "If None or empty, will load heuristic gaps from CollectionDataGap table."
        ),
    )
    selected_asset_ids: List[str] = Field(..., description="Asset UUIDs for context")

    @validator("gaps", pre=True, always=True)
    def normalize_gaps(cls, v):
        """Normalize empty list to None for consistent handling."""
        if v is not None and len(v) == 0:
            return None
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "gaps": [
                    {
                        "asset_id": "11111111-1111-1111-1111-111111111111",
                        "asset_name": "App-001",
                        "field_name": "technology_stack",
                        "gap_type": "missing_field",
                        "gap_category": "application",
                        "priority": 1,
                        "current_value": None,
                        "suggested_resolution": "Manual collection required",
                    }
                ],
                "selected_asset_ids": ["11111111-1111-1111-1111-111111111111"],
            }
        }


class AnalysisSummary(BaseModel):
    """Summary statistics for AI analysis."""

    total_gaps: int = Field(..., description="Total gaps received")
    enhanced_gaps: int = Field(..., description="Gaps enhanced with AI")
    execution_time_ms: int = Field(..., description="Total execution time")
    agent_duration_ms: int = Field(..., description="Agent processing time")


class AnalyzeGapsResponse(BaseModel):
    """Response from AI-enhanced gap analysis."""

    enhanced_gaps: List[DataGap] = Field(
        ..., description="AI-enhanced gaps with confidence scores"
    )
    summary: AnalysisSummary = Field(..., description="Analysis summary")
    status: str = Field(..., description="AI_ANALYSIS_COMPLETE, AI_ANALYSIS_FAILED")
    error: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        json_schema_extra = {
            "example": {
                "enhanced_gaps": [
                    {
                        "asset_id": "11111111-1111-1111-1111-111111111111",
                        "asset_name": "App-001",
                        "field_name": "technology_stack",
                        "gap_type": "missing_field",
                        "gap_category": "application",
                        "priority": 1,
                        "current_value": None,
                        "suggested_resolution": "Check deployment artifacts for framework detection",
                        "confidence_score": 0.85,
                        "ai_suggestions": [
                            "Check package.json for Node.js stack",
                            "Review pom.xml for Java stack",
                        ],
                    }
                ],
                "summary": {
                    "total_gaps": 16,
                    "enhanced_gaps": 12,
                    "execution_time_ms": 14500,
                    "agent_duration_ms": 13200,
                },
                "status": "AI_ANALYSIS_COMPLETE",
            }
        }


# ============================================================================
# Gap Update Schemas
# ============================================================================


class GapUpdate(BaseModel):
    """Individual gap update."""

    gap_id: str = Field(..., description="UUID of gap to update")
    field_name: str = Field(..., description="Field name for validation")
    resolved_value: Optional[str] = Field(None, description="User-entered or AI value")
    resolution_status: str = Field(..., description="pending, resolved")
    resolution_method: Optional[str] = Field(
        None, description="manual_entry, ai_suggestion, hybrid"
    )

    @validator("resolution_status")
    def validate_resolution_status(cls, v):
        allowed_statuses = ["pending", "resolved", "skipped", "unresolved"]
        if v not in allowed_statuses:
            raise ValueError(
                f"Resolution status must be one of: {', '.join(allowed_statuses)}"
            )
        return v

    @validator("resolution_method")
    def validate_resolution_method(cls, v):
        if v is not None and v not in ["manual_entry", "ai_suggestion", "hybrid"]:
            raise ValueError(
                "Resolution method must be manual_entry, ai_suggestion, or hybrid"
            )
        return v


class UpdateGapsRequest(BaseModel):
    """Request body for updating/resolving gaps."""

    updates: List[GapUpdate] = Field(
        ..., description="List of gap updates", min_length=1
    )

    class Config:
        json_schema_extra = {
            "example": {
                "updates": [
                    {
                        "gap_id": "33333333-3333-3333-3333-333333333333",
                        "field_name": "technology_stack",
                        "resolved_value": "Node.js, Express, PostgreSQL",
                        "resolution_status": "resolved",
                        "resolution_method": "manual_entry",
                    }
                ]
            }
        }


class UpdateGapsResponse(BaseModel):
    """Response from gap update operation."""

    updated_gaps: int = Field(..., description="Number of gaps updated")
    gaps_resolved: int = Field(..., description="Number of gaps marked resolved")
    remaining_gaps: int = Field(..., description="Number of pending gaps remaining")

    class Config:
        json_schema_extra = {
            "example": {"updated_gaps": 1, "gaps_resolved": 1, "remaining_gaps": 15}
        }
