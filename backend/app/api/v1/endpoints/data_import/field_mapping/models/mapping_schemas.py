"""
Pydantic schemas for field mapping operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict


class FieldMappingCreate(BaseModel):
    """Schema for creating field mappings."""

    source_field: str = Field(..., description="Source field name")
    target_field: str = Field(..., description="Target field name")
    transformation_rule: Optional[str] = Field(
        None, description="Optional transformation rule"
    )
    validation_rule: Optional[str] = Field(None, description="Optional validation rule")
    is_required: bool = Field(False, description="Whether mapping is required")
    confidence: float = Field(
        0.7, ge=0.0, le=1.0, description="Mapping confidence score"
    )


class FieldMappingUpdate(BaseModel):
    """Schema for updating field mappings."""

    target_field: Optional[str] = Field(None, description="Updated target field")
    transformation_rule: Optional[str] = Field(
        None, description="Updated transformation rule"
    )
    validation_rule: Optional[str] = Field(None, description="Updated validation rule")
    is_required: Optional[bool] = Field(None, description="Updated required status")
    is_approved: Optional[bool] = Field(None, description="Approval status")


class FieldMappingResponse(BaseModel):
    """Schema for field mapping responses."""

    id: UUID
    source_field: str
    target_field: str
    transformation_rule: Optional[str] = None
    validation_rule: Optional[str] = None
    is_required: bool = False
    is_approved: bool = False
    confidence: float = 0.7
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class FieldMappingSuggestion(BaseModel):
    """Schema for AI-generated field mapping suggestions."""

    source_field: str
    target_field: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    sample_values: List[str] = Field(default_factory=list)
    mapping_type: str = Field(default="ai_generated")
    ai_driven: bool = Field(default=True)
    crew_analysis: Optional[str] = None


class FieldMappingAnalysis(BaseModel):
    """Schema for field mapping analysis results."""

    total_fields: int
    mapped_fields: int
    unmapped_fields: int
    confidence_score: float
    suggestions: List[FieldMappingSuggestion]
    validation_errors: List[str] = Field(default_factory=list)


class CustomFieldCreate(BaseModel):
    """Schema for creating custom target fields."""

    name: str = Field(..., min_length=1, max_length=100)
    data_type: str = Field(..., description="Field data type")
    description: Optional[str] = Field(None, max_length=500)
    is_required: bool = Field(False)
    validation_rules: Optional[Dict[str, Any]] = Field(None)

    @field_validator("name")
    @classmethod
    def validate_field_name(cls, v):
        """Validate field name format."""
        if not v.isidentifier():
            raise ValueError("Field name must be a valid identifier")
        return v


class TargetFieldDefinition(BaseModel):
    """Schema for target field definitions."""

    name: str
    data_type: str
    description: Optional[str] = None
    is_required: bool = False
    validation_rules: Optional[Dict[str, Any]] = None
    category: str = Field(default="custom")

    model_config = ConfigDict(from_attributes=True)


class MappingValidationRequest(BaseModel):
    """Schema for mapping validation requests."""

    mappings: List[FieldMappingCreate]
    sample_data: Optional[List[Dict[str, Any]]] = None


class MappingValidationResponse(BaseModel):
    """Schema for mapping validation responses."""

    is_valid: bool
    validation_errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    validated_mappings: List[FieldMappingResponse] = Field(default_factory=list)


class ApprovalRequest(BaseModel):
    """Schema for mapping approval requests."""

    mapping_ids: List[str]  # Changed to str to support UUIDs
    approved: bool
    approval_note: Optional[str] = None


class LearningApprovalRequest(BaseModel):
    """Schema for field mapping learning approval requests."""

    confidence_adjustment: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Confidence score adjustment after approval"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata about the approval"
    )
    learn_from_approval: bool = Field(
        True, description="Whether to learn from this approval for future mappings"
    )
    approval_note: Optional[str] = Field(
        None, max_length=500, description="Optional note explaining the approval"
    )


class LearningRejectionRequest(BaseModel):
    """Schema for field mapping learning rejection requests."""

    rejection_reason: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Reason for rejecting the mapping",
    )
    alternative_suggestion: Optional[str] = Field(
        None, max_length=255, description="Suggested alternative target field"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata about the rejection"
    )
    learn_from_rejection: bool = Field(
        True, description="Whether to learn from this rejection for future mappings"
    )


class MappingLearningAction(BaseModel):
    """Individual mapping learning action for bulk operations."""

    mapping_id: str = Field(..., description="ID of the field mapping")
    action: str = Field(..., description="Action to take", pattern="^(approve|reject)$")
    confidence_adjustment: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Confidence score adjustment"
    )
    rejection_reason: Optional[str] = Field(
        None, max_length=500, description="Reason for rejection (if action is reject)"
    )
    alternative_suggestion: Optional[str] = Field(
        None, max_length=255, description="Alternative target field suggestion"
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class BulkLearningRequest(BaseModel):
    """Schema for bulk learning from multiple mappings."""

    actions: List[MappingLearningAction] = Field(
        ..., min_length=1, description="List of learning actions to perform"
    )
    learn_globally: bool = Field(
        True,
        description="Whether learning should apply globally for the client account",
    )
    context_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Context metadata for the bulk learning operation"
    )


class LearningResponse(BaseModel):
    """Schema for learning operation responses."""

    mapping_id: str
    action: str
    success: bool
    learned_pattern_id: Optional[str] = None
    confidence_score: Optional[float] = None
    error_message: Optional[str] = None
    patterns_created: int = Field(0, description="Number of new patterns created")
    patterns_updated: int = Field(0, description="Number of existing patterns updated")


class BulkLearningResponse(BaseModel):
    """Schema for bulk learning operation responses."""

    total_actions: int
    successful_actions: int
    failed_actions: int
    results: List[LearningResponse]
    global_patterns_created: int = Field(
        0, description="Global patterns created from this batch"
    )
    global_patterns_updated: int = Field(
        0, description="Global patterns updated from this batch"
    )


class LearnedPatternSummary(BaseModel):
    """Schema for learned pattern summaries."""

    pattern_id: str
    pattern_type: str
    pattern_name: str
    confidence_score: float
    evidence_count: int
    times_referenced: int
    effectiveness_score: Optional[float] = None
    insight_type: Optional[str] = None
    created_at: datetime
    last_used_at: Optional[datetime] = None


class LearnedPatternsResponse(BaseModel):
    """Schema for learned patterns response."""

    total_patterns: int
    patterns: List[LearnedPatternSummary]
    context_type: Optional[str] = None
    engagement_id: Optional[str] = None
