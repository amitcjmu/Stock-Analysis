"""
Request/Response schemas for collection applications API
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator


class CanonicalApplicationRequest(BaseModel):
    """Request model for canonical application operations"""

    application_names: List[str] = Field(
        ...,
        min_items=1,
        max_items=100,
        description="List of application names to process",
    )
    similarity_threshold: Optional[float] = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Similarity threshold for fuzzy matching (0.0-1.0)",
    )
    enable_vector_search: bool = Field(
        default=True,
        description="Enable vector similarity search for semantic matching",
    )
    auto_merge_high_confidence: bool = Field(
        default=True, description="Automatically merge high-confidence matches"
    )

    @validator("application_names")
    def validate_application_names(cls, names):
        """Validate application names"""
        if not names:
            raise ValueError("At least one application name is required")

        for name in names:
            if not name or not name.strip():
                raise ValueError("Application names cannot be empty")
            if len(name.strip()) > 255:
                raise ValueError("Application names cannot exceed 255 characters")

        return [name.strip() for name in names]


class CanonicalApplicationResponse(BaseModel):
    """Response model for canonical application operations"""

    canonical_application: Dict[str, Any]
    name_variant: Optional[Dict[str, Any]]
    is_new_canonical: bool
    is_new_variant: bool
    match_method: str
    similarity_score: float
    confidence_score: float
    requires_verification: bool
    idempotency_key: str


class BulkDeduplicationRequest(BaseModel):
    """Request model for bulk application deduplication"""

    applications: List[str] = Field(
        ...,
        min_items=1,
        max_items=1000,
        description="List of application names to deduplicate",
    )
    collection_flow_id: Optional[str] = Field(
        default=None, description="Optional collection flow ID to link applications"
    )
    similarity_threshold: float = Field(
        default=0.85, ge=0.0, le=1.0, description="Similarity threshold for matching"
    )
    batch_size: int = Field(
        default=50, ge=1, le=100, description="Batch size for processing"
    )


class PotentialDuplicatesResponse(BaseModel):
    """Response model for potential duplicates analysis"""

    duplicates: List[Dict[str, Any]]
    total_count: int
    confidence_distribution: Dict[str, int]
    recommendations: Dict[str, Any]
