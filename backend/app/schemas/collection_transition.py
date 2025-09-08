"""
Collection to Assessment Transition Schemas

Pydantic schemas for collection flow to assessment flow transition endpoints.
All field names use snake_case to match backend standards.
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


class ReadinessResult(BaseModel):
    """Readiness validation result schema"""

    is_ready: bool
    confidence: float
    reason: str
    missing_requirements: List[str]
    thresholds_used: Dict[str, float]
    recommended_actions: Optional[List[str]] = None

    model_config = ConfigDict(
        from_attributes=True
    )  # Required for SQLAlchemy integration


class TransitionResponse(BaseModel):
    """Assessment transition response schema"""

    status: str
    assessment_flow_id: str  # snake_case
    collection_flow_id: str  # snake_case
    message: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )  # Required for SQLAlchemy integration


class TransitionResult(BaseModel):
    """Internal transition result schema"""

    assessment_flow_id: UUID
    assessment_flow: Any  # AssessmentFlow model instance
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
