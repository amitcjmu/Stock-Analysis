"""
Pydantic schemas for agentic critical attributes operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CriticalAttribute(BaseModel):
    """Schema for a critical attribute identified by AI agents."""

    name: str = Field(..., description="Attribute name")
    importance: float = Field(..., ge=0.0, le=1.0, description="Importance score")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="AI confidence in this attribute"
    )
    reasoning: str = Field(..., description="AI reasoning for why this is critical")
    migration_impact: str = Field(..., description="Impact on migration")
    data_type: str = Field(..., description="Expected data type")
    sample_values: List[str] = Field(
        default_factory=list, description="Sample values from data"
    )
    mapping_suggestions: List[str] = Field(
        default_factory=list, description="Suggested target fields"
    )
    validation_rules: Optional[List[str]] = Field(
        None, description="Suggested validation rules"
    )
    agent_source: str = Field(..., description="Which agent identified this attribute")


class AttributeSuggestion(BaseModel):
    """Schema for AI-generated attribute suggestions."""

    source_field: str
    suggested_target: str
    importance_score: float = Field(ge=0.0, le=1.0)
    confidence_score: float = Field(ge=0.0, le=1.0)
    reasoning: str
    crew_analysis: Optional[str] = None
    migration_priority: int = Field(ge=1, le=10, default=5)


class AnalysisStatistics(BaseModel):
    """Schema for analysis statistics."""

    total_attributes: int
    critical_count: int
    high_importance_count: int
    medium_importance_count: int
    low_importance_count: int
    mapped_count: int
    unmapped_count: int
    average_confidence: float
    analysis_duration_seconds: float
    agent_execution_time: Optional[float] = None


class AttributeAnalysisRequest(BaseModel):
    """Schema for requesting attribute analysis."""

    import_id: Optional[str] = None
    use_latest_import: bool = Field(default=True)
    force_reanalysis: bool = Field(default=False)
    include_crew_analysis: bool = Field(default=True)
    analysis_depth: str = Field(
        default="comprehensive", pattern="^(quick|standard|comprehensive)$"
    )


class AttributeAnalysisResponse(BaseModel):
    """Schema for attribute analysis results."""

    success: bool
    analysis_id: str
    attributes: List[CriticalAttribute]
    suggestions: List[AttributeSuggestion]
    statistics: AnalysisStatistics
    execution_mode: str = Field(description="'crew_ai', 'fallback', or 'cached'")
    cache_hit: bool = Field(default=False)
    timestamp: datetime
    context: Dict[str, Any] = Field(default_factory=dict)


class AgentFeedback(BaseModel):
    """Schema for user feedback on agent analysis."""

    analysis_id: str
    attribute_name: str
    feedback_type: str = Field(
        pattern="^(correct|incorrect|partially_correct|missing)$"
    )
    user_correction: Optional[str] = None
    importance_adjustment: Optional[float] = Field(None, ge=0.0, le=1.0)
    notes: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CrewExecutionRequest(BaseModel):
    """Schema for requesting CrewAI execution."""

    import_id: str
    analysis_type: str = Field(
        default="field_mapping",
        pattern="^(field_mapping|critical_attributes|full_analysis)$",
    )
    background_execution: bool = Field(default=True)
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")
    parameters: Optional[Dict[str, Any]] = None


class CrewExecutionResponse(BaseModel):
    """Schema for CrewAI execution results."""

    success: bool
    execution_id: str
    status: str = Field(pattern="^(queued|running|completed|failed)$")
    message: str
    results: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None
    agent_outputs: Optional[Dict[str, Any]] = None
    error_details: Optional[str] = None


class LearningPatternUpdate(BaseModel):
    """Schema for updating learning patterns based on feedback."""

    pattern_type: str
    source_pattern: str
    target_suggestion: str
    success_feedback: bool
    confidence_adjustment: float
    context_metadata: Optional[Dict[str, Any]] = None


class BackgroundTaskStatus(BaseModel):
    """Schema for background task status."""

    task_id: str
    status: str = Field(pattern="^(pending|running|completed|failed)$")
    progress: float = Field(ge=0.0, le=1.0, default=0.0)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result_summary: Optional[Dict[str, Any]] = None


class AttributeValidationResult(BaseModel):
    """Schema for attribute validation results."""

    attribute_name: str
    is_valid: bool
    validation_errors: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    data_quality_score: float = Field(ge=0.0, le=1.0)
    completeness_score: float = Field(ge=0.0, le=1.0)
