"""
Pydantic Schemas for Assets
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.asset import (
    AssetType,
    SixRStrategy,
    ApplicationType,
    Lifecycle,
    HostingModel,
    ServerRole,
    RiskLevel,
    TShirtSize,
)


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
    status: Optional[str] = (
        None  # Allow any string value (database has legacy values like 'active', 'not_ready', etc.)
    )
    custom_attributes: Optional[Dict[str, Any]] = None

    # CMDB Enhancement Fields (Issue #833)
    business_unit: Optional[str] = None
    vendor: Optional[str] = None
    application_type: Optional[ApplicationType] = None
    lifecycle: Optional[Lifecycle] = None
    hosting_model: Optional[HostingModel] = None
    server_role: Optional[ServerRole] = None
    security_zone: Optional[str] = None
    database_type: Optional[str] = None
    database_version: Optional[str] = None
    database_size_gb: Optional[float] = None
    cpu_utilization_percent_max: Optional[float] = None
    memory_utilization_percent_max: Optional[float] = None
    storage_free_gb: Optional[float] = None
    storage_used_gb: Optional[float] = None
    tech_debt_flags: Optional[str] = None
    pii_flag: Optional[bool] = None
    application_data_classification: Optional[str] = None
    has_saas_replacement: Optional[bool] = None
    risk_level: Optional[RiskLevel] = None
    tshirt_size: Optional[TShirtSize] = None
    proposed_treatmentplan_rationale: Optional[str] = None
    annual_cost_estimate: Optional[float] = None
    backup_policy: Optional[str] = None
    asset_tags: Optional[List[str]] = None

    # Child table relationships (Issue #833)
    contacts: Optional[List[Dict[str, Any]]] = []
    eol_assessments: Optional[List[Dict[str, Any]]] = []


class PaginatedAssetResponse(BaseModel):
    total: int
    page: int
    page_size: int
    assets: List[AssetResponse]


# Issue #911: AI Grid Editing Schemas


class AssetFieldUpdateRequest(BaseModel):
    """Request schema for updating a single asset field."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    value: Any = Field(
        ..., description="New value for the field (type varies by field)"
    )
    updated_by: Optional[UUID] = Field(
        None,
        description="User ID who made the update (optional, can come from auth context)",
    )


class AssetFieldUpdateResponse(BaseModel):
    """Response schema for single field update."""

    model_config = ConfigDict(from_attributes=True)

    asset_id: UUID
    field_name: str
    old_value: Any
    new_value: Any
    updated_at: datetime
    updated_by: Optional[UUID] = None


class BulkAssetFieldUpdate(BaseModel):
    """Single asset field update in bulk operation."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    asset_id: UUID
    field_name: str
    value: Any


class BulkAssetUpdateRequest(BaseModel):
    """Request schema for bulk asset field updates."""

    model_config = ConfigDict(from_attributes=True)

    updates: List[BulkAssetFieldUpdate] = Field(
        ..., description="List of asset field updates to perform"
    )
    updated_by: Optional[UUID] = Field(None, description="User ID who made the updates")


class BulkAssetUpdateResponse(BaseModel):
    """Response schema for bulk asset updates."""

    model_config = ConfigDict(from_attributes=True)

    success_count: int
    failure_count: int
    updated_assets: List[AssetFieldUpdateResponse]
    errors: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of errors for failed updates"
    )


# Issue #912: Soft Delete Schemas


class AssetSoftDeleteResponse(BaseModel):
    """Response schema for soft delete operation."""

    model_config = ConfigDict(from_attributes=True)

    asset_id: UUID
    deleted_at: datetime
    deleted_by: Optional[UUID] = None


class AssetRestoreResponse(BaseModel):
    """Response schema for restore operation."""

    model_config = ConfigDict(from_attributes=True)

    asset_id: UUID
    restored_at: datetime


class BulkSoftDeleteRequest(BaseModel):
    """Request schema for bulk soft delete."""

    model_config = ConfigDict(from_attributes=True)

    asset_ids: List[UUID] = Field(..., description="List of asset IDs to soft delete")
    deleted_by: Optional[UUID] = Field(
        None, description="User ID performing the deletion"
    )


class BulkSoftDeleteResponse(BaseModel):
    """Response schema for bulk soft delete."""

    model_config = ConfigDict(from_attributes=True)

    success_count: int
    failure_count: int
    deleted_assets: List[AssetSoftDeleteResponse]
    errors: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of errors for failed deletions"
    )


class TrashAssetResponse(AssetResponse):
    """Extended asset response for trash view with deletion metadata."""

    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None


class PaginatedTrashResponse(BaseModel):
    """Paginated response for trash view."""

    model_config = ConfigDict(from_attributes=True)

    total: int
    page: int
    page_size: int
    assets: List[TrashAssetResponse]
