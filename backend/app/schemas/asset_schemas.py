"""
Pydantic Schemas for Assets
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.models.asset import AssetStatus, AssetType, SixRStrategy
from pydantic import BaseModel, ConfigDict, Field


class AssetBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    name: str = Field(..., description="The name of the asset.")
    asset_type: AssetType = Field(..., description="The type of the asset.")
    description: Optional[str] = None
    environment: Optional[str] = None
    business_owner: Optional[str] = None
    technical_owner: Optional[str] = None


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    asset_type: Optional[AssetType] = None
    description: Optional[str] = None
    environment: Optional[str] = None
    business_owner: Optional[str] = None
    technical_owner: Optional[str] = None
    custom_attributes: Optional[Dict[str, Any]] = None


class AssetResponse(AssetBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    completeness_score: Optional[float] = None
    quality_score: Optional[float] = None
    six_r_strategy: Optional[SixRStrategy] = None
    status: Optional[AssetStatus] = None
    custom_attributes: Optional[Dict[str, Any]] = None


class PaginatedAssetResponse(BaseModel):
    total: int
    page: int
    page_size: int
    assets: List[AssetResponse]
