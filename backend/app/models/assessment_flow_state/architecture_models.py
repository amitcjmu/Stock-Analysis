"""
Architecture Standards and Override Models
Models for engagement-level architecture requirements and application-specific overrides.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .enums import OverrideType


class ArchitectureRequirement(BaseModel):
    """Engagement-level architecture requirement definition"""

    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)

    requirement_type: str = Field(
        ...,
        description="Type of requirement (e.g., 'java_versions', 'security_standards')",
    )
    description: str = Field(
        ..., description="Human-readable description of the requirement"
    )
    mandatory: bool = Field(
        default=True, description="Whether this requirement is mandatory or optional"
    )
    supported_versions: Optional[Dict[str, str]] = Field(
        default=None, description="Supported technology versions"
    )
    requirement_details: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional requirement specifications"
    )
    created_by: Optional[str] = Field(
        default=None, description="Who created this requirement"
    )
    created_at: Optional[datetime] = Field(
        default=None, description="When this requirement was created"
    )
    updated_at: Optional[datetime] = Field(
        default=None, description="When this requirement was last updated"
    )


class ApplicationArchitectureOverride(BaseModel):
    """Application-specific architecture override with rationale"""

    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)

    application_id: UUID = Field(..., description="UUID of the application")
    standard_id: Optional[UUID] = Field(
        default=None, description="UUID of the standard being overridden"
    )
    override_type: OverrideType = Field(..., description="Type of override")
    override_details: Optional[Dict[str, Any]] = Field(
        default=None, description="Details of the override"
    )
    rationale: str = Field(..., description="Business rationale for the override")
    approved_by: Optional[str] = Field(
        default=None, description="Who approved this override"
    )
    created_at: Optional[datetime] = Field(
        default=None, description="When this override was created"
    )
