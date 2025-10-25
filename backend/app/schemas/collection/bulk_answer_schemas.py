"""
Pydantic schemas for Collection Bulk Answer operations.
"""

from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AnswerInput(BaseModel):
    """Single answer to apply to multiple assets."""

    question_id: str = Field(..., description="Question identifier")
    answer_value: str = Field(..., description="Answer value to apply")


class BulkAnswerPreviewRequest(BaseModel):
    """Request to preview bulk answer operation."""

    child_flow_id: UUID = Field(..., description="Collection child flow UUID")
    asset_ids: List[UUID] = Field(..., description="List of asset UUIDs to update")
    question_ids: List[str] = Field(..., description="List of question IDs to answer")


class ConflictDetail(BaseModel):
    """Details about an answer conflict."""

    question_id: str
    existing_answers: Dict[str, List[UUID]] = Field(
        ..., description="Map of answer values to asset IDs"
    )
    conflict_count: int


class BulkAnswerPreviewResponse(BaseModel):
    """Response from bulk answer preview."""

    total_assets: int
    total_questions: int
    potential_conflicts: int
    conflicts: List[ConflictDetail]


class ConflictResolutionStrategy(str, Enum):
    """Valid conflict resolution strategies."""

    OVERWRITE = "overwrite"
    SKIP = "skip"
    MERGE = "merge"


class BulkAnswerSubmitRequest(BaseModel):
    """Request to submit bulk answers."""

    child_flow_id: UUID = Field(..., description="Collection child flow UUID")
    asset_ids: List[UUID] = Field(..., description="List of asset UUIDs to update")
    answers: List[AnswerInput] = Field(..., description="Answers to apply")
    conflict_resolution_strategy: ConflictResolutionStrategy = Field(
        default=ConflictResolutionStrategy.OVERWRITE,
        description="How to handle conflicts: overwrite, skip, merge",
    )
    # Alias for backward compatibility with tests
    conflict_strategy: Optional[ConflictResolutionStrategy] = Field(
        None,
        description="Alias for conflict_resolution_strategy",
    )

    def __init__(self, **data):
        # If conflict_strategy is provided but not conflict_resolution_strategy, use it
        if "conflict_strategy" in data and "conflict_resolution_strategy" not in data:
            data["conflict_resolution_strategy"] = data["conflict_strategy"]
        super().__init__(**data)


class ChunkError(BaseModel):
    """Error details for a failed chunk."""

    chunk_index: int
    asset_ids: List[str]
    error: str
    error_code: str


class BulkAnswerSubmitResponse(BaseModel):
    """Response from bulk answer submission."""

    success: bool
    total_assets: int = Field(..., description="Total number of assets in request")
    assets_updated: int = Field(
        ..., description="Number of assets successfully updated"
    )
    successful_assets: Optional[int] = Field(
        None, description="Alias for assets_updated (backward compatibility)"
    )
    questions_answered: int
    conflict_strategy: Optional[str] = Field(
        None, description="Conflict resolution strategy used"
    )
    updated_questionnaire_ids: List[UUID]
    failed_chunks: Optional[List[ChunkError]] = Field(default_factory=list)

    def __init__(self, **data):
        # Auto-populate successful_assets from assets_updated if not provided
        if "successful_assets" not in data and "assets_updated" in data:
            data["successful_assets"] = data["assets_updated"]
        super().__init__(**data)
