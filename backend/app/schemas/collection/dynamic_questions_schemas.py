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
    asset_type: str = Field(..., description="Application, Server, Database, etc.")
    include_answered: bool = Field(
        default=False, description="Include already-answered questions"
    )
    refresh_agent_analysis: bool = Field(
        default=False, description="Run agent pruning (30s timeout)"
    )


class DynamicQuestionsResponse(BaseModel):
    """Response with filtered questions."""

    questions: List[QuestionDetail]
    agent_status: str = Field(..., description="not_requested, completed, fallback")
    fallback_used: bool
    total_questions: int = Field(..., description="Count of returned questions")


class DependencyChangeRequest(BaseModel):
    """Request to handle a dependency change."""

    changed_asset_id: UUID
    changed_field: str
    old_value: Any
    new_value: Any


class DependencyChangeResponse(BaseModel):
    """Response from dependency change handling."""

    reopened_question_ids: List[str]
    reason: str
    affected_assets: List[UUID] = Field(default_factory=list)
