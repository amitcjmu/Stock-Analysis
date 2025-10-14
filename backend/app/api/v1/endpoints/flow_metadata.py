"""
Flow metadata endpoints
Provides authoritative phase information for frontend per ADR-027
"""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.flow_configs.phase_aliases import normalize_phase_name
from app.services.flow_type_registry_helpers import (
    get_all_flow_configs,
    get_flow_config,
)

router = APIRouter(prefix="/flow-metadata")


class PhaseDetail(BaseModel):
    """Phase detail information"""

    name: str
    display_name: str
    description: str
    order: int
    estimated_duration_minutes: int
    can_pause: bool
    can_skip: bool
    ui_route: str
    ui_short_name: str | None = None  # Compact name for sidebar navigation (ADR-027)
    icon: str | None = None
    help_text: str | None = None


class FlowPhasesResponse(BaseModel):
    """Flow phases response"""

    flow_type: str
    display_name: str
    version: str
    phases: List[str]
    phase_details: List[PhaseDetail]
    phase_count: int
    estimated_total_duration_minutes: int


class PhaseNormalizationRequest(BaseModel):
    """Phase normalization request"""

    flow_type: str
    phase: str


class PhaseNormalizationResponse(BaseModel):
    """Phase normalization response"""

    flow_type: str
    input_phase: str
    canonical_phase: str


@router.get("/phases", response_model=Dict[str, FlowPhasesResponse])
async def get_all_flow_phases() -> Dict[str, Any]:
    """
    Get authoritative phase sequences for all flow types

    Frontend SHOULD use this endpoint instead of hardcoding phases.
    Ensures backend/frontend stay synchronized.

    Returns:
        Dictionary of flow types to their phase information
    """
    result = {}

    for config in get_all_flow_configs():
        phases = []
        phase_details = []

        for idx, phase_config in enumerate(config.phases):
            phases.append(phase_config.name)
            phase_details.append(
                PhaseDetail(
                    name=phase_config.name,
                    display_name=phase_config.display_name,
                    description=phase_config.description,
                    order=idx,
                    estimated_duration_minutes=phase_config.metadata.get(
                        "estimated_duration_minutes", 0
                    ),
                    can_pause=phase_config.can_pause,
                    can_skip=phase_config.can_skip,
                    ui_route=phase_config.metadata.get("ui_route", f"/{config.name}"),
                    ui_short_name=phase_config.metadata.get("ui_short_name"),
                    icon=phase_config.metadata.get("icon"),
                    help_text=phase_config.metadata.get("help_text"),
                )
            )

        result[config.name] = FlowPhasesResponse(
            flow_type=config.name,
            display_name=config.display_name,
            version=config.version,
            phases=phases,
            phase_details=phase_details,
            phase_count=len(phases),
            estimated_total_duration_minutes=sum(
                p.estimated_duration_minutes for p in phase_details
            ),
        )

    return result


@router.get("/phases/{flow_type}", response_model=FlowPhasesResponse)
async def get_flow_type_phases(flow_type: str) -> FlowPhasesResponse:
    """
    Get phases for specific flow type

    Args:
        flow_type: Flow type (discovery, collection, assessment, etc.)

    Returns:
        Phase information for the flow type

    Raises:
        404: If flow type not found
    """
    try:
        config = get_flow_config(flow_type)

        phases = []
        phase_details = []

        for idx, phase_config in enumerate(config.phases):
            phases.append(phase_config.name)
            phase_details.append(
                PhaseDetail(
                    name=phase_config.name,
                    display_name=phase_config.display_name,
                    description=phase_config.description,
                    order=idx,
                    estimated_duration_minutes=phase_config.metadata.get(
                        "estimated_duration_minutes", 0
                    ),
                    can_pause=phase_config.can_pause,
                    can_skip=phase_config.can_skip,
                    ui_route=phase_config.metadata.get("ui_route", f"/{config.name}"),
                    ui_short_name=phase_config.metadata.get("ui_short_name"),
                    icon=phase_config.metadata.get("icon"),
                    help_text=phase_config.metadata.get("help_text"),
                )
            )

        return FlowPhasesResponse(
            flow_type=config.name,
            display_name=config.display_name,
            version=config.version,
            phases=phases,
            phase_details=phase_details,
            phase_count=len(phases),
            estimated_total_duration_minutes=sum(
                p.estimated_duration_minutes for p in phase_details
            ),
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/phases/normalize", response_model=PhaseNormalizationResponse)
async def normalize_phase(
    request: PhaseNormalizationRequest,
) -> PhaseNormalizationResponse:
    """
    Normalize a phase name from any variant to canonical name

    Useful for legacy frontend code that uses old phase names.

    Args:
        request: Phase normalization request with flow_type and phase

    Returns:
        Normalized phase name

    Raises:
        400: If phase invalid
    """
    try:
        canonical = normalize_phase_name(request.flow_type, request.phase)
        return PhaseNormalizationResponse(
            flow_type=request.flow_type,
            input_phase=request.phase,
            canonical_phase=canonical,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
