"""
Pydantic schemas for Unified Import Orchestrator operations.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class FieldMappingSuggestion(BaseModel):
    """Suggested mapping for a CSV column."""

    csv_column: str
    suggested_field: Optional[str]
    confidence: float = Field(..., ge=0.0, le=1.0)
    suggestions: List[Dict[str, Any]]


class ImportAnalysisResponse(BaseModel):
    """Response from import file analysis."""

    file_name: str
    total_rows: int
    detected_columns: List[str]
    suggested_mappings: List[FieldMappingSuggestion]
    unmapped_columns: List[str]
    validation_warnings: List[str]
    import_batch_id: UUID


class ConfirmedMapping(BaseModel):
    """User-confirmed field mapping."""

    csv_column: str
    database_field: str


class ImportExecutionRequest(BaseModel):
    """Request to execute import."""

    child_flow_id: UUID = Field(..., description="Collection child flow UUID")
    import_batch_id: UUID = Field(..., description="Batch ID from analysis step")
    confirmed_mappings: Dict[str, str] = Field(
        ..., description="Map of CSV column -> database field"
    )
    import_type: str = Field(..., description="application, server, database")
    overwrite_existing: bool = Field(
        default=False, description="Overwrite existing data"
    )
    gap_recalculation_mode: str = Field(default="fast", description="fast or thorough")


class ImportTaskResponse(BaseModel):
    """Response with background task status."""

    id: UUID = Field(..., description="Task ID for polling")
    status: str = Field(..., description="pending, running, completed, failed")
    progress_percent: int = Field(..., ge=0, le=100)
    current_stage: str


class ImportTaskStatusRequest(BaseModel):
    """Request to check import task status."""

    task_id: UUID


class ImportTaskDetailResponse(BaseModel):
    """Detailed task status response."""

    id: UUID
    status: str
    progress_percent: int
    current_stage: str
    rows_processed: int
    total_rows: Optional[int]
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
