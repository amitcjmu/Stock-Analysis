"""
Assessment Flow Base Pydantic schemas - Core data models.

This module contains the foundational data models used across
assessment flow operations (October 2025 refactor).
"""

from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class ApplicationAssetGroup(BaseModel):
    """
    Application group with its associated assets.

    Represents the canonical application grouping of assets for assessment purposes.
    Supports both mapped applications (with canonical_application_id) and unmapped
    assets (canonical_application_id = None).
    """

    canonical_application_id: Optional[UUID] = Field(
        None, description="Canonical application ID (None if unmapped asset)"
    )
    canonical_application_name: str = Field(
        ..., description="Application name (falls back to asset name if unmapped)"
    )
    asset_ids: List[UUID] = Field(
        default_factory=list, description="List of asset UUIDs in this group"
    )
    asset_count: int = Field(0, ge=0, description="Number of assets in this group")
    asset_types: List[str] = Field(
        default_factory=list,
        description="Distinct asset types (server, database, network_device, etc.)",
    )
    readiness_summary: Dict[str, float] = Field(
        default_factory=dict,
        description=(
            "Readiness breakdown with avg_completeness_score: "
            "{ready: 2, not_ready: 1, in_progress: 0, avg_completeness_score: 0.75}"
        ),
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "canonical_application_id": "05459507-86cb-41f9-9c2d-2a9f4a50445a",
                "canonical_application_name": "CRM System",
                "asset_ids": ["c4ed088f-6658-405b-b011-8ce50c065ddf"],
                "asset_count": 3,
                "asset_types": ["server", "database", "network_device"],
                "readiness_summary": {
                    "ready": 2,
                    "not_ready": 1,
                    "in_progress": 0,
                    "avg_completeness_score": 0.75,
                },
            }
        }
    )


class EnrichmentStatus(BaseModel):
    """
    Summary of enrichment table population.

    Tracks how many assets have been enriched with data from various
    enrichment tables (compliance, licenses, vulnerabilities, etc.).
    """

    compliance_flags: int = Field(0, ge=0, description="Assets with compliance data")
    licenses: int = Field(0, ge=0, description="Assets with license data")
    vulnerabilities: int = Field(0, ge=0, description="Assets with vulnerability data")
    resilience: int = Field(0, ge=0, description="Assets with resilience data")
    dependencies: int = Field(0, ge=0, description="Assets with dependency data")
    product_links: int = Field(0, ge=0, description="Assets with product catalog links")
    field_conflicts: int = Field(0, ge=0, description="Assets with field conflicts")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "compliance_flags": 2,
                "licenses": 0,
                "vulnerabilities": 3,
                "resilience": 1,
                "dependencies": 4,
                "product_links": 0,
                "field_conflicts": 0,
            }
        }
    )


class ReadinessSummary(BaseModel):
    """
    Assessment readiness summary.

    Aggregates readiness metrics across all selected assets to provide
    a high-level view of assessment preparedness.
    """

    total_assets: int = Field(0, ge=0, description="Total number of assets")
    ready: int = Field(0, ge=0, description="Assets ready for assessment")
    not_ready: int = Field(0, ge=0, description="Assets not ready")
    in_progress: int = Field(0, ge=0, description="Assets in progress")
    avg_completeness_score: float = Field(
        0.0, ge=0.0, le=1.0, description="Average completeness score (0.0-1.0)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_assets": 5,
                "ready": 2,
                "not_ready": 3,
                "in_progress": 0,
                "avg_completeness_score": 0.64,
            }
        }
    )


class AssessmentApplicationInfo(BaseModel):
    """Schema for basic application information in assessment flows."""

    id: str
    name: str
    type: Optional[str] = None
    environment: Optional[str] = None
    business_criticality: Optional[str] = None
    technology_stack: List[str] = Field(default_factory=list)
    complexity_score: Optional[float] = None
    readiness_score: Optional[float] = None
    discovery_completed_at: Optional[str] = (
        None  # Changed from datetime for JSON serialization
    )
