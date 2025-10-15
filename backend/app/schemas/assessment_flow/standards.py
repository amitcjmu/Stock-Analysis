"""
Architecture Standards Pydantic schemas.

This module contains schemas for managing architecture standards,
templates, and application-specific overrides.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ArchitectureStandardCreate(BaseModel):
    """Schema for creating architecture standards."""

    standard_type: str = Field(
        ..., description="Type of standard (e.g., cloud_provider, framework)"
    )
    domain: Optional[str] = Field(
        None, description="Domain area (e.g., infrastructure, application)"
    )
    standard_definition: Dict[str, Any] = Field(
        ..., description="The actual standard definition"
    )
    enforcement_level: str = Field(
        default="recommended", description="Enforcement level"
    )
    is_template: bool = Field(
        default=False, description="Whether this is a reusable template"
    )
    customizable_fields: List[str] = Field(
        default=[], description="Fields that can be customized"
    )


class ArchitectureStandardResponse(BaseModel):
    """Response schema for architecture standards."""

    id: str
    standard_type: str
    domain: Optional[str]
    standard_definition: Dict[str, Any]
    enforcement_level: str
    is_template: bool
    customizable_fields: List[str]
    created_by: str
    created_at: datetime
    updated_at: datetime


class ArchitectureStandardUpdate(BaseModel):
    """Schema for updating architecture standards."""

    standard_definition: Optional[Dict[str, Any]] = None
    enforcement_level: Optional[str] = None
    customizable_fields: Optional[List[str]] = None


class ApplicationOverrideCreate(BaseModel):
    """Schema for creating application overrides."""

    application_id: str = Field(..., description="Application ID for override")
    standard_id: str = Field(..., description="Standard ID being overridden")
    override_data: Dict[str, Any] = Field(..., description="Override values")
    override_reason: Optional[str] = Field(
        None, description="Justification for override"
    )
    requires_approval: bool = Field(
        default=False, description="Whether override requires approval"
    )


class ApplicationOverrideResponse(BaseModel):
    """Response schema for application overrides."""

    id: str
    application_id: str
    standard_id: str
    override_data: Dict[str, Any]
    override_reason: Optional[str]
    requires_approval: bool
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    approval_comments: Optional[str]
    created_by: str
    created_at: datetime
    updated_at: datetime


class ArchitectureStandardsUpdateRequest(BaseModel):
    """Request schema for updating architecture standards and overrides."""

    engagement_standards: Optional[List[ArchitectureStandardCreate]] = Field(
        None, description="Engagement-level standards"
    )
    application_overrides: Optional[List[ApplicationOverrideCreate]] = Field(
        None, description="Application-specific overrides"
    )
