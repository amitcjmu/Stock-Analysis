"""
Assessment Flow Request Pydantic schemas.

This module contains all request schemas for assessment flow API endpoints.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.models.assessment_flow import AssessmentPhase
from .base import ApplicationAssetGroup, EnrichmentStatus, ReadinessSummary


class AssessmentFlowCreateRequest(BaseModel):
    """Request schema for creating a new assessment flow."""

    # Accept both old and new formats for backward compatibility
    selected_application_ids: Optional[List[str]] = Field(
        None,
        min_length=1,
        max_length=100,
        description=(
            "DEPRECATED: Use selected_asset_ids instead. "
            "Kept for backward compatibility."
        ),
    )

    # NEW: Proper semantic fields
    selected_asset_ids: List[UUID] = Field(
        default_factory=list,
        description="Asset UUIDs selected for assessment (proper semantic field)",
    )

    selected_canonical_application_ids: Optional[List[UUID]] = Field(
        default_factory=list,
        description="Canonical application UUIDs (resolved from assets)",
    )

    application_asset_groups: Optional[List[ApplicationAssetGroup]] = Field(
        default_factory=list, description="Application-asset groupings with metadata"
    )

    enrichment_status: Optional[EnrichmentStatus] = Field(
        None, description="Enrichment table population status"
    )

    readiness_summary: Optional[ReadinessSummary] = Field(
        None, description="Assessment readiness summary"
    )

    @field_validator("selected_application_ids")
    @classmethod
    def validate_application_ids(cls, v):
        """Validate application IDs format (backward compatibility only)."""
        if v is not None:
            for app_id in v:
                if not app_id or not isinstance(app_id, str):
                    raise ValueError("Application IDs must be non-empty strings")
        return v

    @field_validator("selected_asset_ids")
    @classmethod
    def validate_asset_ids(cls, v):
        """Validate asset IDs are valid UUIDs."""
        if v and len(v) > 100:
            raise ValueError("Maximum 100 assets can be selected for assessment")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "selected_asset_ids": ["c4ed088f-6658-405b-b011-8ce50c065ddf"],
                "selected_canonical_application_ids": [
                    "05459507-86cb-41f9-9c2d-2a9f4a50445a"
                ],
                "application_asset_groups": [
                    {
                        "canonical_application_id": (
                            "05459507-86cb-41f9-9c2d-2a9f4a50445a"
                        ),
                        "canonical_application_name": "CRM System",
                        "asset_ids": ["c4ed088f-6658-405b-b011-8ce50c065ddf"],
                        "asset_count": 1,
                        "asset_types": ["server"],
                        "readiness_summary": {"ready": 1, "not_ready": 0},
                    }
                ],
                "enrichment_status": {
                    "compliance_flags": 0,
                    "licenses": 0,
                    "vulnerabilities": 0,
                    "resilience": 0,
                    "dependencies": 0,
                    "product_links": 0,
                    "field_conflicts": 0,
                },
                "readiness_summary": {
                    "total_assets": 1,
                    "ready": 1,
                    "not_ready": 0,
                    "in_progress": 0,
                    "avg_completeness_score": 0.85,
                },
            }
        }
    )


class ResumeFlowRequest(BaseModel):
    """Request schema for resuming assessment flow."""

    user_input: Dict[str, Any] = Field(..., description="User input for current phase")
    save_progress: bool = Field(default=True, description="Whether to save progress")


class NavigateToPhaseRequest(BaseModel):
    """Request schema for navigating to specific phase."""

    target_phase: AssessmentPhase = Field(
        ..., description="Target phase to navigate to"
    )
    force_navigation: bool = Field(
        default=False, description="Force navigation even if prerequisites not met"
    )


class AssessmentFinalization(BaseModel):
    """Schema for finalizing assessment."""

    apps_to_finalize: List[str] = Field(
        ..., description="Application IDs to mark as ready for planning"
    )
    finalization_notes: Optional[str] = Field(
        None, description="Notes about finalization"
    )
    export_to_planning: bool = Field(
        default=True, description="Whether to export to Planning Flow"
    )
