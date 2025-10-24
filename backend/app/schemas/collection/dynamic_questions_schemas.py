"""
Pydantic schemas for Dynamic Question Engine operations.
"""

from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class QuestionDetail(BaseModel):
    """Details of a single question."""

    question_id: str
    question_text: str
    question_type: str = Field(..., description="dropdown, multi_select, text")
    answer_options: Optional[List[str]] = None
    section: Optional[str] = None
    weight: int = Field(default=40)
    is_required: bool = Field(default=False)
    display_order: Optional[int] = None


class DynamicQuestionsRequest(BaseModel):
    """Request to get filtered questions for an asset."""

    child_flow_id: UUID = Field(..., description="Collection child flow UUID")
    asset_id: UUID = Field(..., description="Asset UUID")
    asset_type: Optional[str] = Field(
        None, description="Application, Server, Database, etc."
    )
    include_answered: bool = Field(
        default=False, description="Include already-answered questions"
    )
    refresh_agent_analysis: bool = Field(
        default=False, description="Run agent pruning (30s timeout)"
    )


class DynamicQuestionsResponse(BaseModel):
    """Response with filtered questions."""

    asset_type: Optional[str] = Field(None, description="Asset type")
    questions: List[QuestionDetail]
    total_questions: int = Field(..., description="Count of returned questions")
    agent_status: str = Field(..., description="not_requested, completed, fallback")
    fallback_used: Optional[bool] = Field(
        False, description="Whether fallback was used"
    )
    include_answered: Optional[bool] = Field(
        None, description="Echo of request parameter"
    )


class DependencyChangeRequest(BaseModel):
    """Request to handle a dependency change."""

    child_flow_id: UUID = Field(..., description="Collection child flow UUID")
    asset_id: UUID = Field(..., description="Asset UUID that changed")
    changed_field: str = Field(..., description="Field that changed")
    new_value: Any = Field(..., description="New value of the field")
    old_value: Optional[Any] = Field(None, description="Previous value (optional)")

    # Alias for backward compatibility
    @property
    def changed_asset_id(self) -> UUID:
        """Alias for asset_id."""
        return self.asset_id


class DependencyChangeResponse(BaseModel):
    """Response from dependency change handling."""

    changed_field: str = Field(..., description="Field that changed")
    old_value: Optional[Any] = Field(None, description="Previous value")
    new_value: Any = Field(..., description="New value")
    reopened_question_ids: List[str] = Field(
        default_factory=list, description="Questions reopened due to change"
    )
    reason: Optional[str] = Field(None, description="Reason for reopening")
    affected_assets: List[UUID] = Field(
        default_factory=list, description="Other assets affected"
    )
