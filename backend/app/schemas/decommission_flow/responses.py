"""
Decommission Flow Response Pydantic schemas.

This module contains all response schemas for decommission flow API endpoints.
Per ADR-027: Phase names match FlowTypeConfig exactly.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


class DecommissionFlowResponse(BaseModel):
    """Response schema for decommission flow operations."""

    flow_id: str = Field(..., description="Decommission flow UUID")
    status: str = Field(..., description="Flow operational status")
    current_phase: str = Field(..., description="Current phase (per FlowTypeConfig)")
    next_phase: Optional[str] = Field(
        None, description="Next phase in progression (per FlowTypeConfig)"
    )
    selected_systems: List[str] = Field(
        ..., description="UUIDs of systems selected for decommission"
    )
    message: str = Field(..., description="Status or operation message")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "flow_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "initialized",
                "current_phase": "decommission_planning",
                "next_phase": "data_migration",
                "selected_systems": [
                    "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                    "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                ],
                "message": "Decommission flow initialized for 2 systems",
            }
        }
    )


class DecommissionFlowStatusResponse(BaseModel):
    """Detailed status response for decommission flow."""

    flow_id: str = Field(..., description="Decommission flow UUID")
    master_flow_id: str = Field(..., description="Master flow UUID (MFO)")
    status: str = Field(..., description="Flow operational status")
    current_phase: str = Field(..., description="Current phase (per FlowTypeConfig)")
    system_count: int = Field(..., description="Number of systems being decommissioned")

    # Phase progress (ADR-027: names match FlowTypeConfig)
    phase_progress: Dict[str, str] = Field(
        ...,
        description="Status of each phase (pending/in_progress/completed/failed)",
    )

    # Aggregated metrics
    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Decommission metrics (systems_decommissioned, savings, compliance)",
    )

    # Runtime state
    runtime_state: Dict[str, Any] = Field(
        default_factory=dict,
        description="Current runtime execution state",
    )

    # Timestamps
    created_at: datetime = Field(..., description="Flow creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    # Optional completion indicators
    decommission_complete: bool = Field(
        default=False, description="Whether decommission is complete"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "flow_id": "550e8400-e29b-41d4-a716-446655440000",
                "master_flow_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "decommission_planning",
                "current_phase": "decommission_planning",
                "system_count": 2,
                "phase_progress": {
                    "decommission_planning": "in_progress",
                    "data_migration": "pending",
                    "system_shutdown": "pending",
                },
                "metrics": {
                    "systems_decommissioned": 0,
                    "estimated_savings": 120000.00,
                    "compliance_score": 85.5,
                },
                "runtime_state": {
                    "current_agent": "dependency_analyzer",
                    "pending_approvals": [],
                    "warnings": [],
                },
                "created_at": "2025-01-05T10:30:00Z",
                "updated_at": "2025-01-05T11:45:00Z",
                "decommission_complete": False,
            }
        }
    )


class DecommissionSystemInfo(BaseModel):
    """Information about a system in decommission flow."""

    system_id: str = Field(..., description="Asset UUID")
    system_name: str = Field(..., description="System/asset name")
    system_type: Optional[str] = Field(
        None, description="System type (server, application, etc.)"
    )
    six_r_strategy: Optional[str] = Field(
        None, description="6R strategy if from assessment (Retire, etc.)"
    )
    decommission_status: str = Field(
        ..., description="Status for this system (pending/in_progress/completed/failed)"
    )
    estimated_annual_savings: Optional[float] = Field(
        None, description="Estimated annual cost savings"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "system_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                "system_name": "Legacy Billing System",
                "system_type": "application",
                "six_r_strategy": "Retire",
                "decommission_status": "pending",
                "estimated_annual_savings": 60000.00,
            }
        }
    )
