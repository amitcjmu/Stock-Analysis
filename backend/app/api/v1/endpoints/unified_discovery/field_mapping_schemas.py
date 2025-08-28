"""
Field Mapping Response Schemas for Unified Discovery

Pydantic models for field mapping API responses.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class FieldMappingItem(BaseModel):
    """Individual field mapping item in response."""

    id: str = Field(..., description="Unique identifier for the mapping")
    source_field: str = Field(..., description="Source field name")
    target_field: str = Field(..., description="Target field name")
    confidence_score: Optional[float] = Field(
        None, description="Confidence score of the mapping suggestion"
    )
    field_type: Optional[str] = Field(None, description="Data type of the field")
    status: str = Field("suggested", description="Approval status of the mapping")
    approved_by: Optional[str] = Field(None, description="ID of approver")
    approved_at: Optional[datetime] = Field(None, description="Timestamp of approval")
    agent_reasoning: Optional[str] = Field(
        None, description="Agent's reasoning for the mapping"
    )
    transformation_rules: Optional[dict] = Field(
        None, description="Transformation rules for the mapping"
    )

    class Config:
        orm_mode = True


class FieldMappingsResponse(BaseModel):
    """Response model for field mappings list."""

    success: bool = Field(True, description="Operation success status")
    flow_id: str = Field(..., description="Associated flow ID")
    field_mappings: List[FieldMappingItem] = Field(
        ..., description="List of field mappings"
    )
    count: int = Field(..., description="Total count of mappings")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "flow_id": "123e4567-e89b-12d3-a456-426614174000",
                "field_mappings": [
                    {
                        "id": "456e7890-e89b-12d3-a456-426614174000",
                        "source_field": "hostname",
                        "target_field": "server_name",
                        "confidence_score": 0.95,
                        "field_type": "string",
                        "status": "approved",
                        "approved_by": "user-123",
                        "approved_at": "2025-08-28T10:00:00Z",
                        "agent_reasoning": "Direct name match with high confidence",
                        "transformation_rules": {"lowercase": True},
                    }
                ],
                "count": 1,
            }
        }


class FieldMappingApprovalResponse(BaseModel):
    """Response model for field mapping approval."""

    success: bool = Field(True, description="Operation success status")
    mapping_id: str = Field(..., description="Approved/rejected mapping ID")
    status: str = Field(..., description="New status of the mapping")
    source_field: str = Field(..., description="Source field name")
    target_field: str = Field(..., description="Target field name")
    approved_by: str = Field(..., description="ID of approver")
    approved_at: datetime = Field(..., description="Timestamp of approval")
    message: str = Field(..., description="Success message")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "mapping_id": "456e7890-e89b-12d3-a456-426614174000",
                "status": "approved",
                "source_field": "hostname",
                "target_field": "server_name",
                "approved_by": "user-123",
                "approved_at": "2025-08-28T10:00:00Z",
                "message": "Field mapping hostname -> server_name has been approved",
            }
        }
