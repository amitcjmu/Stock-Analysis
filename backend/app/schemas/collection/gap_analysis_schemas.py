"""
Schemas for Incremental Gap Analysis (adaptive questionnaire).

Supports weight-based progress tracking and intelligent gap prioritization
per ADR-030.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ProgressMetrics(BaseModel):
    """Progress metrics for gap analysis."""

    total_questions: int = Field(..., description="Total applicable questions")
    answered_questions: int = Field(..., description="Number of answered questions")
    unanswered_questions: int = Field(..., description="Number of unanswered questions")
    total_weight: int = Field(..., description="Sum of all question weights")
    answered_weight: int = Field(..., description="Sum of answered question weights")
    completion_percent: int = Field(..., description="Completion percentage (0-100)")

    class Config:
        json_schema_extra = {
            "example": {
                "total_questions": 10,
                "answered_questions": 7,
                "unanswered_questions": 3,
                "total_weight": 100,
                "answered_weight": 70,
                "completion_percent": 70,
            }
        }


class GapDetail(BaseModel):
    """Individual gap detail."""

    question_id: str = Field(..., description="Question identifier")
    question_text: str = Field(..., description="Question text")
    section: str = Field(..., description="Question section/category")
    weight: int = Field(..., description="Question weight (importance)")
    is_critical: bool = Field(..., description="Whether question is required")
    depends_on: Optional[List[str]] = Field(
        default=None, description="Question IDs this depends on (thorough mode)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "question_id": "app_01_name",
                "question_text": "What is the application name?",
                "section": "Basic Info",
                "weight": 10,
                "is_critical": True,
                "depends_on": None,
            }
        }


class GapAnalysisResponse(BaseModel):
    """Response from gap analysis operation."""

    asset_id: str = Field(..., description="Asset UUID")
    child_flow_id: str = Field(..., description="Child flow UUID")
    analysis_mode: str = Field(..., description="Analysis mode: fast or thorough")
    total_gaps: int = Field(..., description="Total number of gaps found")
    critical_gaps: int = Field(..., description="Number of critical gaps")
    gaps: List[GapDetail] = Field(
        default_factory=list, description="List of gap details"
    )
    progress_metrics: ProgressMetrics = Field(..., description="Progress calculations")

    class Config:
        json_schema_extra = {
            "example": {
                "asset_id": "12345678-1234-1234-1234-123456789012",
                "child_flow_id": "87654321-4321-4321-4321-210987654321",
                "analysis_mode": "fast",
                "total_gaps": 3,
                "critical_gaps": 1,
                "gaps": [
                    {
                        "question_id": "app_01_name",
                        "question_text": "What is the application name?",
                        "section": "Basic Info",
                        "weight": 10,
                        "is_critical": True,
                        "depends_on": None,
                    }
                ],
                "progress_metrics": {
                    "total_questions": 10,
                    "answered_questions": 7,
                    "unanswered_questions": 3,
                    "total_weight": 100,
                    "answered_weight": 70,
                    "completion_percent": 70,
                },
            }
        }
