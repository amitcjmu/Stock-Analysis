"""
Pydantic schemas for asset conflict resolution API.

CC: Request/response models for conflict resolution endpoints
"""

from pydantic import BaseModel
from typing import Dict, List, Literal, Optional
from uuid import UUID


class AssetConflictDetail(BaseModel):
    """Conflict detail for UI display"""

    conflict_id: UUID
    conflict_type: str  # hostname, ip_address, or name
    conflict_key: str  # The conflicting value
    existing_asset: Dict  # Serialized asset for comparison
    new_asset: Dict  # Proposed new asset data


class AssetConflictResolutionRequest(BaseModel):
    """Single conflict resolution request"""

    conflict_id: UUID
    resolution_action: Literal["keep_existing", "replace_with_new", "merge"]
    merge_field_selections: Optional[Dict[str, Literal["existing", "new"]]] = None
    # Example: {"os_version": "new", "memory_gb": "existing", "cpu_cores": "new"}


class BulkConflictResolutionRequest(BaseModel):
    """Bulk resolution request for multiple conflicts"""

    resolutions: List[AssetConflictResolutionRequest]


class ConflictResolutionResponse(BaseModel):
    """Response after resolving conflicts"""

    resolved_count: int
    total_requested: int
    errors: Optional[List[str]] = None
