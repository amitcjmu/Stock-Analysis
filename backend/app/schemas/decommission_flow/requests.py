"""
Decommission Flow Request Pydantic schemas.

This module contains all request schemas for decommission flow API endpoints.
Per ADR-027: Phases match FlowTypeConfig (decommission_planning, data_migration, system_shutdown).
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict


class DecommissionFlowCreateRequest(BaseModel):
    """Request schema for creating a new decommission flow."""

    selected_system_ids: List[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Asset UUIDs selected for decommission (1-100 systems)",
    )

    flow_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional name for the decommission flow",
    )

    decommission_strategy: Dict[str, Any] = Field(
        default_factory=lambda: {
            "priority": "cost_savings",
            "execution_mode": "phased",
            "rollback_enabled": True,
        },
        description="Strategy configuration for decommission execution",
    )

    @field_validator("selected_system_ids")
    @classmethod
    def validate_system_ids(cls, v):
        """Validate system IDs format."""
        if not v:
            raise ValueError("At least one system ID is required")

        for system_id in v:
            if not system_id or not isinstance(system_id, str):
                raise ValueError("System IDs must be non-empty strings")
            # Validate UUID format
            try:
                UUID(system_id)
            except (ValueError, AttributeError):
                raise ValueError(f"Invalid UUID format for system ID: {system_id}")

        return v

    @field_validator("decommission_strategy")
    @classmethod
    def validate_strategy(cls, v):
        """Validate decommission strategy configuration."""
        valid_priorities = ["cost_savings", "risk_reduction", "compliance"]
        valid_modes = ["immediate", "scheduled", "phased"]

        if "priority" in v and v["priority"] not in valid_priorities:
            raise ValueError(
                f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"
            )

        if "execution_mode" in v and v["execution_mode"] not in valid_modes:
            raise ValueError(
                f"Invalid execution_mode. Must be one of: {', '.join(valid_modes)}"
            )

        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "selected_system_ids": [
                    "550e8400-e29b-41d4-a716-446655440000",
                    "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                ],
                "flow_name": "Q1 2025 Legacy System Retirement",
                "decommission_strategy": {
                    "priority": "cost_savings",
                    "execution_mode": "phased",
                    "rollback_enabled": True,
                    "stakeholder_approvals": ["IT Manager", "Security Officer"],
                },
            }
        }
    )


class ResumeFlowRequest(BaseModel):
    """Request schema for resuming paused decommission flow."""

    phase: Optional[str] = Field(
        None,
        description="Optional phase to resume from (defaults to current phase)",
    )

    user_input: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional user input for resuming execution",
    )

    @field_validator("phase")
    @classmethod
    def validate_phase(cls, v):
        """Validate phase name matches FlowTypeConfig (ADR-027)."""
        if v is not None:
            valid_phases = [
                "decommission_planning",
                "data_migration",
                "system_shutdown",
            ]
            if v not in valid_phases:
                raise ValueError(
                    f"Invalid phase. Must be one of: {', '.join(valid_phases)}"
                )
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "phase": "data_migration",
                "user_input": {
                    "approved_by": "admin@example.com",
                    "approval_notes": "Proceed with data archival",
                },
            }
        }
    )
