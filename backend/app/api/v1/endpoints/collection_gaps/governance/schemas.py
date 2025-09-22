"""
Pydantic schemas for governance API endpoints.

Defines request and response models for governance requirements and migration exceptions.
"""

from typing import Optional

from pydantic import BaseModel, Field


class GovernanceRequirementRequest(BaseModel):
    """Request model for creating governance requirements (approval requests)."""

    entity_type: str = Field(
        ...,
        description="Type of entity requiring approval",
        example="migration_exception",
        min_length=1,
        max_length=100,
    )
    entity_id: Optional[str] = Field(
        None,
        description="ID of entity requiring approval",
        example="123e4567-e89b-12d3-a456-426614174000",
    )
    notes: Optional[str] = Field(
        None,
        description="Optional notes for the approval request",
        example="High-risk exception requiring executive approval",
        max_length=1000,
    )


class GovernanceRequirementResponse(BaseModel):
    """Response model for governance requirements."""

    id: str = Field(
        ...,
        description="Approval request ID",
        example="123e4567-e89b-12d3-a456-426614174000",
    )
    entity_type: str = Field(
        ..., description="Type of entity", example="migration_exception"
    )
    entity_id: Optional[str] = Field(
        None, description="Entity ID", example="123e4567-e89b-12d3-a456-426614174001"
    )
    status: str = Field(..., description="Approval status", example="PENDING")
    notes: Optional[str] = Field(None, description="Request notes")
    requested_at: str = Field(
        ..., description="Request timestamp", example="2025-01-15T10:30:00Z"
    )
    decided_at: Optional[str] = Field(
        None, description="Decision timestamp", example="2025-01-16T14:20:00Z"
    )
    approver_id: Optional[str] = Field(None, description="Approver user ID")


class MigrationExceptionRequest(BaseModel):
    """Request model for creating migration exceptions."""

    exception_type: str = Field(
        ...,
        description="Type of migration exception",
        example="custom_approach",
        min_length=1,
        max_length=100,
    )
    rationale: str = Field(
        ...,
        description="Business/technical justification for the exception",
        example=(
            "Legacy system requires specialized migration approach "
            "due to proprietary protocols"
        ),
        min_length=10,
        max_length=2000,
    )
    risk_level: str = Field(
        ...,
        description="Risk level assessment",
        example="high",
        pattern="^(low|medium|high|critical)$",
    )
    application_id: Optional[str] = Field(
        None,
        description="Application ID if exception is application-specific",
        example="123e4567-e89b-12d3-a456-426614174000",
    )
    asset_id: Optional[str] = Field(
        None,
        description="Asset ID if exception is asset-specific",
        example="123e4567-e89b-12d3-a456-426614174001",
    )


class MigrationExceptionResponse(BaseModel):
    """Response model for migration exceptions."""

    id: str = Field(
        ...,
        description="Exception ID",
        example="123e4567-e89b-12d3-a456-426614174000",
    )
    exception_type: str = Field(
        ..., description="Exception type", example="custom_approach"
    )
    rationale: str = Field(..., description="Exception rationale")
    risk_level: str = Field(..., description="Risk level", example="high")
    status: str = Field(..., description="Exception status", example="OPEN")
    application_id: Optional[str] = Field(None, description="Application ID")
    asset_id: Optional[str] = Field(None, description="Asset ID")
    approval_request_id: Optional[str] = Field(
        None, description="Linked approval request"
    )
    created_at: str = Field(
        ..., description="Creation timestamp", example="2025-01-15T10:30:00Z"
    )
