"""
Pydantic schemas for asset conflict resolution.

Per Issue #910: Support for 'create_both_with_dependency' resolution action
that allows users to keep both conflicting assets and link them to a shared parent.

CC: Request/response models for conflict resolution endpoints
"""

from typing import Optional, Literal, Dict
from pydantic import BaseModel, Field
from uuid import UUID


class AssetConflictDetail(BaseModel):
    """Conflict detail for UI display"""

    conflict_id: UUID
    conflict_type: str  # hostname, ip_address, or name
    conflict_key: str  # The conflicting value
    existing_asset: Dict  # Serialized asset for comparison
    new_asset: Dict  # Proposed new asset data


class DependencySelection(BaseModel):
    """
    Represents a user's selection of a parent asset and dependency type
    when choosing to create both conflicting assets with a shared dependency.
    """

    parent_asset_id: UUID = Field(..., description="UUID of parent application asset")
    parent_asset_name: str = Field(
        ..., description="Display name of parent application"
    )
    dependency_type: Literal["hosting", "infrastructure", "server"] = Field(
        ..., description="Type of dependency relationship"
    )
    confidence_score: float = Field(
        default=1.0,
        description="Confidence score (1.0 for manual user-created dependencies)",
    )


class AssetConflictResolutionRequest(BaseModel):
    """
    Represents a single conflict resolution decision made by the user.
    """

    conflict_id: str = Field(..., description="Unique identifier for the conflict")
    resolution_action: Literal[
        "keep_existing", "replace_with_new", "merge", "create_both_with_dependency"
    ] = Field(..., description="Resolution action chosen by the user")
    merge_field_selections: Optional[dict[str, str]] = Field(
        default=None,
        description="Field-level selections for merge action (field_name -> 'existing' | 'new')",
    )
    dependency_selection: Optional[DependencySelection] = Field(
        default=None,
        description="Parent asset and dependency type (required for create_both_with_dependency)",
    )
    # Asset data from the conflict
    existing_asset_id: Optional[UUID] = Field(
        default=None, description="ID of existing asset in conflict"
    )
    existing_asset_data: Optional[dict] = Field(
        default=None, description="Data of existing asset"
    )
    new_asset_data: Optional[dict] = Field(
        default=None, description="Data of new asset to be created"
    )


class BulkConflictResolutionRequest(BaseModel):
    """
    Represents a bulk resolution request for multiple conflicts.
    """

    resolutions: list[AssetConflictResolutionRequest] = Field(
        ..., description="List of conflict resolutions to process"
    )
    client_account_id: UUID = Field(
        ..., description="Client account ID for multi-tenant isolation"
    )
    engagement_id: UUID = Field(
        ..., description="Engagement ID for multi-tenant isolation"
    )
    flow_id: UUID = Field(
        ..., description="Flow ID that triggered the conflict resolution"
    )


class ConflictResolutionResponse(BaseModel):
    """
    Response after processing conflict resolutions.
    """

    resolved_count: int = Field(
        ..., description="Number of conflicts successfully resolved"
    )
    total_requested: int = Field(
        ..., description="Total number of conflicts in the request"
    )
    created_assets: list[UUID] = Field(
        default_factory=list, description="UUIDs of newly created assets"
    )
    created_dependencies: list[UUID] = Field(
        default_factory=list,
        description="UUIDs of newly created dependency relationships",
    )
    errors: list[str] = Field(
        default_factory=list, description="Error messages for any failed resolutions"
    )
