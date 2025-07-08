"""
Pydantic schemas for field mapping operations.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from uuid import UUID


class FieldMappingCreate(BaseModel):
    """Schema for creating field mappings."""
    source_field: str = Field(..., description="Source field name")
    target_field: str = Field(..., description="Target field name") 
    transformation_rule: Optional[str] = Field(None, description="Optional transformation rule")
    validation_rule: Optional[str] = Field(None, description="Optional validation rule")
    is_required: bool = Field(False, description="Whether mapping is required")
    confidence: float = Field(0.7, ge=0.0, le=1.0, description="Mapping confidence score")


class FieldMappingUpdate(BaseModel):
    """Schema for updating field mappings."""
    target_field: Optional[str] = Field(None, description="Updated target field")
    transformation_rule: Optional[str] = Field(None, description="Updated transformation rule")
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
    
    class Config:
        from_attributes = True


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
    
    @validator('name')
    def validate_field_name(cls, v):
        """Validate field name format."""
        if not v.isidentifier():
            raise ValueError('Field name must be a valid identifier')
        return v


class TargetFieldDefinition(BaseModel):
    """Schema for target field definitions."""
    name: str
    data_type: str
    description: Optional[str] = None
    is_required: bool = False
    validation_rules: Optional[Dict[str, Any]] = None
    category: str = Field(default="custom")
    
    class Config:
        from_attributes = True


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
    mapping_ids: List[int]
    approved: bool
    approval_note: Optional[str] = None