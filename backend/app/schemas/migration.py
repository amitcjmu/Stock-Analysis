"""
Pydantic schemas for migration-related API operations.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from app.models.migration import MigrationPhase, MigrationStatus
from pydantic import BaseModel, ConfigDict, Field


class MigrationBase(BaseModel):
    """Base migration schema with common fields."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    source_environment: Optional[str] = None
    target_environment: Optional[str] = None
    migration_strategy: Optional[str] = None


class MigrationCreate(MigrationBase):
    """Schema for creating a new migration."""

    start_date: Optional[datetime] = None
    target_completion_date: Optional[datetime] = None
    settings: Optional[Dict[str, Any]] = None


class MigrationUpdate(BaseModel):
    """Schema for updating a migration."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    source_environment: Optional[str] = None
    target_environment: Optional[str] = None
    migration_strategy: Optional[str] = None
    status: Optional[MigrationStatus] = None
    current_phase: Optional[MigrationPhase] = None
    start_date: Optional[datetime] = None
    target_completion_date: Optional[datetime] = None
    actual_completion_date: Optional[datetime] = None
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    total_assets: Optional[int] = Field(None, ge=0)
    migrated_assets: Optional[int] = Field(None, ge=0)
    ai_recommendations: Optional[Dict[str, Any]] = None
    risk_assessment: Optional[Dict[str, Any]] = None
    cost_estimates: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None


class MigrationListResponse(BaseModel):
    """Schema for migration list response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: MigrationStatus
    current_phase: MigrationPhase
    progress_percentage: int
    total_assets: int
    migrated_assets: int
    created_at: datetime
    target_completion_date: Optional[datetime]


class MigrationResponse(BaseModel):
    """Schema for detailed migration response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str]
    status: MigrationStatus
    current_phase: MigrationPhase
    created_at: datetime
    updated_at: Optional[datetime]
    start_date: Optional[datetime]
    target_completion_date: Optional[datetime]
    actual_completion_date: Optional[datetime]
    source_environment: Optional[str]
    target_environment: Optional[str]
    migration_strategy: Optional[str]
    progress_percentage: int
    total_assets: int
    migrated_assets: int
    ai_recommendations: Optional[Dict[str, Any]]
    risk_assessment: Optional[Dict[str, Any]]
    cost_estimates: Optional[Dict[str, Any]]
    settings: Optional[Dict[str, Any]]


class MigrationProgressResponse(BaseModel):
    """Schema for migration progress response."""

    migration_id: int
    overall_progress: int
    phase_progress: Dict[str, float]
    asset_counts: Dict[str, int]
    current_phase: str
    status: str


class MigrationAIAssessmentResponse(BaseModel):
    """Schema for AI assessment response."""

    message: str
    migration_id: int
    assessment: Dict[str, Any]
