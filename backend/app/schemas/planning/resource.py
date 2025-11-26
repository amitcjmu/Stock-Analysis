"""
Pydantic schemas for Resource Planning.

Provides request/response models for resource pools, allocations, and skills.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ===========================
# Resource Pool Schemas
# ===========================


class ResourcePoolBase(BaseModel):
    """Base schema for resource pools."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    pool_name: str = Field(..., description="Resource pool name")
    description: Optional[str] = Field(None, description="Pool description")
    resource_type: str = Field(
        default="role", description="Resource type (individual/role/team)"
    )
    role_name: str = Field(..., description="Role name (e.g., Cloud Architect, DBA)")
    total_capacity_hours: float = Field(..., description="Total capacity in hours")
    available_capacity_hours: float = Field(
        ..., description="Available capacity in hours"
    )
    allocated_capacity_hours: float = Field(
        default=0.0, description="Allocated capacity in hours"
    )
    hourly_rate: Optional[float] = Field(
        None, description="Hourly rate in specified currency"
    )
    currency: str = Field(default="USD", description="Currency code")
    skills: List[str] = Field(default_factory=list, description="List of skills")
    location: Optional[str] = Field(None, description="Resource location")
    timezone: Optional[str] = Field(None, description="Timezone")
    availability_start_date: Optional[datetime] = Field(
        None, description="Availability start date"
    )
    availability_end_date: Optional[datetime] = Field(
        None, description="Availability end date"
    )
    is_active: bool = Field(default=True, description="Active status")
    utilization_percentage: float = Field(
        default=0.0, description="Utilization percentage"
    )


class ResourcePoolCreate(ResourcePoolBase):
    """Schema for creating a resource pool."""

    pass


class ResourcePoolUpdate(BaseModel):
    """Schema for updating a resource pool."""

    model_config = ConfigDict(from_attributes=True)

    pool_name: Optional[str] = None
    description: Optional[str] = None
    total_capacity_hours: Optional[float] = None
    available_capacity_hours: Optional[float] = None
    allocated_capacity_hours: Optional[float] = None
    hourly_rate: Optional[float] = None
    skills: Optional[List[str]] = None
    location: Optional[str] = None
    timezone: Optional[str] = None
    availability_start_date: Optional[datetime] = None
    availability_end_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    utilization_percentage: Optional[float] = None


class ResourcePoolResponse(ResourcePoolBase):
    """Schema for resource pool responses."""

    id: UUID = Field(..., description="Resource pool UUID")
    client_account_id: UUID = Field(..., description="Client account UUID")
    engagement_id: UUID = Field(..., description="Engagement UUID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: Optional[UUID] = Field(None, description="Creator user UUID")
    updated_by: Optional[UUID] = Field(None, description="Last updater user UUID")


# ===========================
# Resource Allocation Schemas
# ===========================


class ResourceAllocationBase(BaseModel):
    """Base schema for resource allocations."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    planning_flow_id: UUID = Field(..., description="Planning flow UUID")
    wave_id: UUID = Field(..., description="Wave UUID")
    resource_pool_id: UUID = Field(..., description="Resource pool UUID")
    allocated_hours: float = Field(..., description="Allocated hours")
    allocation_percentage: Optional[float] = Field(
        None, description="Allocation percentage"
    )
    allocation_start_date: datetime = Field(..., description="Allocation start date")
    allocation_end_date: datetime = Field(..., description="Allocation end date")
    estimated_cost: Optional[float] = Field(None, description="Estimated cost")
    actual_cost: Optional[float] = Field(None, description="Actual cost")
    is_ai_suggested: bool = Field(default=False, description="AI suggested allocation")
    ai_confidence_score: Optional[float] = Field(
        None, description="AI confidence score"
    )
    manual_override: bool = Field(default=False, description="Manual override flag")
    override_reason: Optional[str] = Field(None, description="Override reason")
    status: str = Field(default="planned", description="Allocation status")


class ResourceAllocationCreate(ResourceAllocationBase):
    """Schema for creating a resource allocation."""

    pass


class ResourceAllocationUpdate(BaseModel):
    """Schema for updating a resource allocation."""

    model_config = ConfigDict(from_attributes=True)

    allocated_hours: Optional[float] = None
    allocation_percentage: Optional[float] = None
    allocation_start_date: Optional[datetime] = None
    allocation_end_date: Optional[datetime] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    manual_override: Optional[bool] = None
    override_reason: Optional[str] = None
    status: Optional[str] = None


class ResourceAllocationResponse(ResourceAllocationBase):
    """Schema for resource allocation responses."""

    id: UUID = Field(..., description="Allocation UUID")
    client_account_id: UUID = Field(..., description="Client account UUID")
    engagement_id: UUID = Field(..., description="Engagement UUID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: Optional[UUID] = Field(None, description="Creator user UUID")
    updated_by: Optional[UUID] = Field(None, description="Last updater user UUID")


# ===========================
# Resource Skill Schemas
# ===========================


class ResourceSkillBase(BaseModel):
    """Base schema for resource skills."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    wave_id: UUID = Field(..., description="Wave UUID")
    skill_name: str = Field(..., description="Skill name")
    skill_category: Optional[str] = Field(None, description="Skill category")
    proficiency_level: str = Field(
        default="intermediate", description="Proficiency level"
    )
    required_hours: float = Field(..., description="Required hours")
    available_hours: float = Field(default=0.0, description="Available hours")
    has_gap: bool = Field(default=False, description="Has skill gap")
    gap_severity: str = Field(
        default="low", description="Gap severity (low/medium/high)"
    )
    gap_impact_description: Optional[str] = Field(
        None, description="Gap impact description"
    )
    ai_recommendations: Dict[str, Any] = Field(
        default_factory=dict, description="AI recommendations"
    )


class ResourceSkillCreate(ResourceSkillBase):
    """Schema for creating a resource skill requirement."""

    pass


class ResourceSkillUpdate(BaseModel):
    """Schema for updating a resource skill requirement."""

    model_config = ConfigDict(from_attributes=True)

    required_hours: Optional[float] = None
    available_hours: Optional[float] = None
    has_gap: Optional[bool] = None
    gap_severity: Optional[str] = None
    gap_impact_description: Optional[str] = None
    ai_recommendations: Optional[Dict[str, Any]] = None


class ResourceSkillResponse(ResourceSkillBase):
    """Schema for resource skill responses."""

    id: UUID = Field(..., description="Skill requirement UUID")
    client_account_id: UUID = Field(..., description="Client account UUID")
    engagement_id: UUID = Field(..., description="Engagement UUID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# ===========================
# Aggregated Response Schemas
# ===========================


class TeamAssignment(BaseModel):
    """Schema for team assignment within a resource pool."""

    model_config = ConfigDict(from_attributes=True)

    project: str = Field(..., description="Project name")
    allocation: float = Field(..., description="Allocation percentage")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")


class ResourceTeam(BaseModel):
    """Schema for resource team display (aggregated view)."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Pool ID as string")
    name: str = Field(..., description="Team name")
    size: int = Field(..., description="Team size")
    skills: List[str] = Field(default_factory=list, description="Team skills")
    availability: float = Field(..., description="Availability percentage")
    utilization: float = Field(..., description="Utilization percentage")
    assignments: List[TeamAssignment] = Field(
        default_factory=list, description="Team assignments"
    )


class SkillCoverage(BaseModel):
    """Schema for skill coverage metrics."""

    model_config = ConfigDict(from_attributes=True)

    skill_name: str = Field(..., description="Skill name")
    coverage_percentage: float = Field(..., description="Coverage percentage")


class UpcomingNeed(BaseModel):
    """Schema for upcoming resource needs."""

    model_config = ConfigDict(from_attributes=True)

    skill: str = Field(..., description="Required skill")
    demand: int = Field(..., description="Demand count")
    timeline: str = Field(..., description="Timeline (YYYY-MM-DD)")


class ResourceRecommendation(BaseModel):
    """Schema for resource recommendations."""

    model_config = ConfigDict(from_attributes=True)

    type: str = Field(
        ..., description="Recommendation type (capacity/skills/optimization/planning)"
    )
    description: str = Field(..., description="Recommendation description")
    impact: str = Field(..., description="Impact level (High/Medium/Low)")


class ResourceMetrics(BaseModel):
    """Schema for resource metrics."""

    model_config = ConfigDict(from_attributes=True)

    total_teams: int = Field(..., description="Total teams count")
    total_resources: int = Field(..., description="Total resources count")
    average_utilization: float = Field(
        ..., description="Average utilization percentage"
    )
    skill_coverage: Dict[str, float] = Field(
        default_factory=dict, description="Skill coverage map"
    )


class ResourcePlanningResponse(BaseModel):
    """
    Aggregated response for resource planning data.

    This schema matches the mock data structure currently returned by the API.
    """

    model_config = ConfigDict(from_attributes=True)

    teams: List[ResourceTeam] = Field(
        default_factory=list, description="Resource teams"
    )
    metrics: ResourceMetrics = Field(..., description="Resource metrics")
    recommendations: List[ResourceRecommendation] = Field(
        default_factory=list, description="Recommendations"
    )
    upcoming_needs: List[UpcomingNeed] = Field(
        default_factory=list, description="Upcoming resource needs"
    )
