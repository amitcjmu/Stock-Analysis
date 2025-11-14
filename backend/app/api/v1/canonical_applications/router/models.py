"""
Pydantic models for canonical applications API endpoints.

Request and response schemas for asset mapping and application queries.
"""

from typing import Optional

from pydantic import BaseModel, Field


class MapAssetRequest(BaseModel):
    """Request to map an asset to a canonical application"""

    asset_id: str = Field(..., description="Asset UUID to map")
    canonical_application_id: str = Field(..., description="Canonical application UUID")
    collection_flow_id: Optional[str] = Field(
        None, description="Optional collection flow ID for traceability"
    )


class MapAssetResponse(BaseModel):
    """Response after mapping asset"""

    success: bool
    message: str
    mapping_id: str  # UUID of created CollectionFlowApplication record
