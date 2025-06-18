from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from enum import Enum
from app.models.asset import SixRStrategy

class ApplicationType(str, Enum):
    """Application type enumeration for COTS vs Custom distinction."""
    CUSTOM = "custom"           # Custom-built applications (can be rewritten)
    COTS = "cots"              # Commercial Off-The-Shelf (cannot be rewritten, only replaced)
    HYBRID = "hybrid"          # Mix of custom and COTS components



class AnalysisStatus(str, Enum):
    """Analysis status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_INPUT = "requires_input"

class QuestionType(str, Enum):
    """Question input type enumeration."""
    TEXT = "text"
    SELECT = "select"
    MULTISELECT = "multiselect"
    FILE_UPLOAD = "file_upload"
    BOOLEAN = "boolean"
    NUMERIC = "numeric"

# Base Schemas for 6R Parameters
class SixRParameterBase(BaseModel):
    """Base 6R analysis parameters."""
    business_value: float = Field(
        default=5.0,
        ge=1.0,
        le=10.0,
        description="Business value of the application (1-10)"
    )
    technical_complexity: float = Field(
        default=5.0,
        ge=1.0,
        le=10.0,
        description="Technical complexity of migration (1-10)"
    )
    migration_urgency: float = Field(
        default=5.0,
        ge=1.0,
        le=10.0,
        description="Urgency of migration timeline (1-10)"
    )
    compliance_requirements: float = Field(
        default=5.0,
        ge=1.0,
        le=10.0,
        description="Compliance and regulatory requirements (1-10)"
    )
    cost_sensitivity: float = Field(
        default=5.0,
        ge=1.0,
        le=10.0,
        description="Cost sensitivity and budget constraints (1-10)"
    )
    risk_tolerance: float = Field(
        default=5.0,
        ge=1.0,
        le=10.0,
        description="Risk tolerance for migration approach (1-10)"
    )
    innovation_priority: float = Field(
        default=5.0,
        ge=1.0,
        le=10.0,
        description="Priority for innovation and modernization (1-10)"
    )
    application_type: ApplicationType = Field(
        default=ApplicationType.CUSTOM,
        description="Type of application (custom, COTS, hybrid)"
    )

    @field_validator('business_value', 'technical_complexity', 'migration_urgency', 
                    'compliance_requirements', 'cost_sensitivity', 'risk_tolerance', 
                    'innovation_priority')
    @classmethod
    def validate_parameter_range(cls, v: float) -> float:
        """Validate parameter is within valid range."""
        if not isinstance(v, (int, float)):
            raise ValueError('Parameter must be a number')
        if not 1.0 <= v <= 10.0:
            raise ValueError('Parameter must be between 1.0 and 10.0')
        return float(v)

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        },
        use_enum_values=True
    )

class SixRParameters(SixRParameterBase):
    """6R analysis parameters with metadata."""
    parameter_source: str = Field(default="user_input", description="Source of parameters")
    confidence_level: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence in parameters")
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = Field(None, description="User who last updated parameters")

# Qualifying Questions Schemas
class QuestionOption(BaseModel):
    """Option for select/multiselect questions."""
    value: str = Field(..., description="Option value")
    label: str = Field(..., description="Option display label")
    description: Optional[str] = Field(None, description="Option description")

class QualifyingQuestion(BaseModel):
    """Schema for qualifying questions."""
    id: str = Field(..., description="Unique question identifier")
    question: str = Field(..., description="Question text")
    question_type: QuestionType = Field(..., description="Type of question input")
    category: str = Field(..., description="Question category")
    priority: int = Field(default=1, ge=1, le=5, description="Question priority (1-5)")
    required: bool = Field(default=False, description="Whether question is required")
    options: Optional[List[QuestionOption]] = Field(None, description="Options for select questions")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="Validation rules")
    help_text: Optional[str] = Field(None, description="Help text for question")
    depends_on: Optional[str] = Field(None, description="Question dependency")

class QuestionResponse(BaseModel):
    """Schema for question responses."""
    question_id: str = Field(..., description="Question identifier")
    response: Union[str, int, float, bool, List[str]] = Field(..., description="Question response")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Response confidence")
    source: str = Field(default="user", description="Response source")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# 6R Recommendation Schemas
class SixRRecommendationScore(BaseModel):
    """Individual 6R strategy score."""
    strategy: SixRStrategy = Field(..., description="6R strategy")
    score: float = Field(..., ge=0.0, le=100.0, description="Strategy score (0-100)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in score")
    rationale: List[str] = Field(default_factory=list, description="Rationale for score")
    risk_factors: List[str] = Field(default_factory=list, description="Risk factors")
    benefits: List[str] = Field(default_factory=list, description="Strategy benefits")

class SixRRecommendation(BaseModel):
    """6R analysis recommendation."""
    recommended_strategy: SixRStrategy = Field(..., description="Recommended strategy")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence")
    strategy_scores: List[SixRRecommendationScore] = Field(..., description="All strategy scores")
    key_factors: List[str] = Field(default_factory=list, description="Key decision factors")
    assumptions: List[str] = Field(default_factory=list, description="Analysis assumptions")
    next_steps: List[str] = Field(default_factory=list, description="Recommended next steps")
    estimated_effort: Optional[str] = Field(None, description="Estimated effort level")
    estimated_timeline: Optional[str] = Field(None, description="Estimated timeline")
    estimated_cost_impact: Optional[str] = Field(None, description="Estimated cost impact")

# Iteration Tracking Schemas
class IterationChange(BaseModel):
    """Schema for tracking changes between iterations."""
    field_name: str = Field(..., description="Changed field name")
    old_value: Any = Field(..., description="Previous value")
    new_value: Any = Field(..., description="New value")
    change_reason: Optional[str] = Field(None, description="Reason for change")
    impact_assessment: Optional[str] = Field(None, description="Impact of change")

class SixRIteration(BaseModel):
    """Schema for 6R analysis iteration."""
    iteration_number: int = Field(..., ge=1, description="Iteration number")
    parameters: SixRParameters = Field(..., description="Parameters for this iteration")
    question_responses: List[QuestionResponse] = Field(default_factory=list, description="Question responses")
    recommendation: Optional[SixRRecommendation] = Field(None, description="Iteration recommendation")
    changes_from_previous: List[IterationChange] = Field(default_factory=list, description="Changes from previous iteration")
    stakeholder_feedback: Optional[str] = Field(None, description="Stakeholder feedback")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(None, description="User who created iteration")

# Request/Response Schemas
class SixRAnalysisRequest(BaseModel):
    """Request schema for starting 6R analysis."""
    application_ids: List[int] = Field(..., description="Application IDs to analyze")
    initial_parameters: Optional[SixRParameterBase] = Field(None, description="Initial parameter values")
    analysis_name: Optional[str] = Field(None, description="Analysis name")
    description: Optional[str] = Field(None, description="Analysis description")
    priority: int = Field(default=3, ge=1, le=5, description="Analysis priority")
    application_types: Optional[Dict[int, ApplicationType]] = Field(None, description="Application type mapping for each app ID")

class SixRParameterUpdateRequest(BaseModel):
    """Request schema for updating 6R parameters."""
    parameters: SixRParameterBase = Field(..., description="Updated parameters")
    update_reason: Optional[str] = Field(None, description="Reason for update")

class QualifyingQuestionsRequest(BaseModel):
    """Request schema for submitting qualifying question responses."""
    responses: List[QuestionResponse] = Field(..., description="Question responses")
    partial_submission: bool = Field(default=False, description="Whether this is a partial submission")

class IterationRequest(BaseModel):
    """Request schema for creating new iteration."""
    parameter_changes: Optional[SixRParameterBase] = Field(None, description="Parameter changes")
    additional_responses: Optional[List[QuestionResponse]] = Field(None, description="Additional question responses")
    stakeholder_feedback: Optional[str] = Field(None, description="Stakeholder feedback")
    iteration_reason: str = Field(..., description="Reason for new iteration")

# Response Schemas
class SixRAnalysisResponse(BaseModel):
    """Response schema for 6R analysis."""
    analysis_id: int = Field(..., description="Analysis ID")
    status: AnalysisStatus = Field(..., description="Analysis status")
    current_iteration: int = Field(..., description="Current iteration number")
    applications: List[Dict[str, Any]] = Field(..., description="Application details")
    parameters: SixRParameters = Field(..., description="Current parameters")
    qualifying_questions: List[QualifyingQuestion] = Field(default_factory=list, description="Qualifying questions")
    recommendation: Optional[SixRRecommendation] = Field(None, description="Current recommendation")
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Analysis progress")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    created_at: datetime = Field(..., description="Analysis creation time")
    updated_at: datetime = Field(..., description="Last update time")

class SixRAnalysisListResponse(BaseModel):
    """Response schema for listing 6R analyses."""
    analyses: List[SixRAnalysisResponse] = Field(..., description="List of analyses")
    total_count: int = Field(..., description="Total number of analyses")
    page: int = Field(default=1, description="Current page")
    page_size: int = Field(default=20, description="Page size")

class SixRRecommendationResponse(BaseModel):
    """Response schema for 6R recommendation."""
    analysis_id: int = Field(..., description="Analysis ID")
    iteration_number: int = Field(..., description="Iteration number")
    recommendation: SixRRecommendation = Field(..., description="6R recommendation")
    comparison_with_previous: Optional[Dict[str, Any]] = Field(None, description="Comparison with previous iteration")
    confidence_evolution: List[Dict[str, float]] = Field(default_factory=list, description="Confidence evolution over iterations")

# Bulk Analysis Schemas
class BulkAnalysisRequest(BaseModel):
    """Request schema for bulk 6R analysis."""
    application_ids: List[int] = Field(..., description="Application IDs to analyze")
    default_parameters: Optional[SixRParameterBase] = Field(None, description="Default parameters for all applications")
    analysis_name: str = Field(..., description="Bulk analysis name")
    batch_size: int = Field(default=10, ge=1, le=50, description="Batch processing size")
    priority: int = Field(default=3, ge=1, le=5, description="Analysis priority")

class BulkAnalysisResponse(BaseModel):
    """Response schema for bulk analysis."""
    bulk_analysis_id: int = Field(..., description="Bulk analysis ID")
    total_applications: int = Field(..., description="Total applications to analyze")
    completed_applications: int = Field(default=0, description="Completed applications")
    failed_applications: int = Field(default=0, description="Failed applications")
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Overall progress")
    individual_analyses: List[SixRAnalysisResponse] = Field(default_factory=list, description="Individual analysis results")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    status: AnalysisStatus = Field(..., description="Bulk analysis status")

# Error Schemas
class SixRAnalysisError(BaseModel):
    """Error schema for 6R analysis."""
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Error message")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    suggested_actions: List[str] = Field(default_factory=list, description="Suggested actions")
    timestamp: datetime = Field(default_factory=datetime.utcnow) 