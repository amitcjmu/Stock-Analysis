"""
Component and Tech Debt Models
Models for application component identification and technical debt tracking.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .enums import ComponentType, SixRStrategy, TechDebtSeverity


class ApplicationComponent(BaseModel):
    """Flexible component identification beyond 3-tier architecture"""

    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)

    component_name: str = Field(
        ..., min_length=1, max_length=255, description="Name of the component"
    )
    component_type: ComponentType = Field(..., description="Type of component")
    technology_stack: Optional[Dict[str, Any]] = Field(
        default=None, description="Technology details and versions"
    )
    dependencies: Optional[List[str]] = Field(
        default=None, description="Other components this depends on"
    )

    @field_validator("component_name")
    @classmethod
    def validate_component_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Component name cannot be empty")
        return v.strip()


class TechDebtItem(BaseModel):
    """Tech debt analysis item with severity and remediation tracking"""

    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)

    category: str = Field(
        ..., description="Category of tech debt (e.g., 'security', 'performance')"
    )
    severity: TechDebtSeverity = Field(
        ..., description="Severity level of the tech debt"
    )
    description: str = Field(
        ..., min_length=1, description="Description of the tech debt issue"
    )
    remediation_effort_hours: Optional[int] = Field(
        default=None, ge=0, description="Estimated hours to remediate"
    )
    impact_on_migration: Optional[str] = Field(
        default=None, description="How this impacts migration"
    )
    tech_debt_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Quantified score for prioritization",
    )
    detected_by_agent: Optional[str] = Field(
        default=None, description="Which agent detected this debt"
    )
    agent_confidence: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Agent confidence in detection"
    )
    component_id: Optional[UUID] = Field(
        default=None, description="Associated component UUID"
    )


class ComponentTreatment(BaseModel):
    """Component-level 6R treatment with compatibility validation"""

    model_config = ConfigDict(use_enum_values=True, validate_assignment=True)

    component_name: str = Field(..., description="Name of the component")
    component_type: ComponentType = Field(..., description="Type of component")
    recommended_strategy: SixRStrategy = Field(
        ..., description="Recommended 6R strategy"
    )
    rationale: str = Field(..., description="Rationale for the strategy choice")
    compatibility_validated: bool = Field(
        default=False, description="Whether compatibility has been validated"
    )
    compatibility_issues: Optional[List[str]] = Field(
        default=None, description="List of compatibility concerns"
    )
