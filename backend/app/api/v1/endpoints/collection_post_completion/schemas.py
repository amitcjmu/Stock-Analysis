"""
Pydantic schemas for Collection Post-Completion endpoints.

Request and response models for resolving unmapped assets to canonical applications
after collection flow completion.
"""

from typing import Optional
from pydantic import BaseModel, Field


class LinkAssetRequest(BaseModel):
    """Request model for linking asset to canonical application"""

    asset_id: str = Field(..., description="UUID of the asset to link")
    canonical_application_id: str = Field(
        ..., description="UUID of the canonical application to map to"
    )
    deduplication_method: Optional[str] = Field(
        "user_manual",
        description="Method used for mapping (user_manual, fuzzy_match, etc.)",
    )
    match_confidence: Optional[float] = Field(
        1.0, description="Confidence score for the mapping (0.0-1.0)", ge=0.0, le=1.0
    )


class UnmappedAssetResponse(BaseModel):
    """Response model for unmapped asset details"""

    collection_app_id: str = Field(
        ..., description="UUID of the collection_flow_application record"
    )
    asset_id: str = Field(..., description="UUID of the asset")
    asset_name: str = Field(..., description="Name of the asset")
    asset_type: str = Field(..., description="Type of asset (server, database, etc.)")
    application_name: str = Field(
        ..., description="Original application name from collection"
    )


class LinkAssetResponse(BaseModel):
    """Response model for successful asset-to-application link"""

    success: bool = Field(..., description="Whether the operation succeeded")
    collection_app_id: str = Field(
        ..., description="UUID of the updated collection_flow_application"
    )
    asset_id: str = Field(..., description="UUID of the linked asset")
    canonical_application_id: str = Field(
        ..., description="UUID of the canonical application"
    )
    canonical_name: str = Field(..., description="Name of the canonical application")
    deduplication_method: str = Field(..., description="Method used for deduplication")
    match_confidence: float = Field(..., description="Confidence score (0.0-1.0)")
