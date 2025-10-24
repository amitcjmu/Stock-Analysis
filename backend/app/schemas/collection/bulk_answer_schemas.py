"""
Pydantic schemas for Collection Bulk Answer operations.
"""

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


class BulkAnswerSubmitRequest(BaseModel):
    """Request to submit bulk answers."""

    child_flow_id: UUID = Field(..., description="Collection child flow UUID")
    asset_ids: List[UUID] = Field(..., description="List of asset UUIDs to update")
    answers: List[AnswerInput] = Field(..., description="Answers to apply")
    conflict_resolution_strategy: str = Field(
        default="overwrite",
        description="How to handle conflicts: overwrite, skip, merge",
    )


class ChunkError(BaseModel):
    """Error details for a failed chunk."""

    chunk_index: int
    asset_ids: List[str]
    error: str
    error_code: str


class BulkAnswerSubmitResponse(BaseModel):
    """Response from bulk answer submission."""

    success: bool
    assets_updated: int
    questions_answered: int
    updated_questionnaire_ids: List[UUID]
    failed_chunks: Optional[List[ChunkError]] = Field(default_factory=list)
