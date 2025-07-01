"""
Discovery flow management route handlers.
Thin controllers that delegate to service layer.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.context import get_current_context, RequestContext
from ..services.discovery_orchestrator import DiscoveryOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/flow", tags=["discovery-flow"])


class InitializeDiscoveryRequest(BaseModel):
    """Request model for flow initialization."""
    execution_mode: str = Field(default="hybrid", pattern="^(crewai|database|hybrid)$")
    raw_data: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    data_import_id: Optional[str] = None


class DiscoveryFlowResponse(BaseModel):
    """Response model for discovery flow operations."""
    flow_id: str
    client_account_id: str
    engagement_id: str
    user_id: str
    status: str
    current_phase: str
    progress_percentage: float
    phases: Dict[str, bool]
    crewai_status: str
    database_status: str
    agent_insights: List[Dict[str, Any]]
    created_at: str
    updated_at: str


class FlowExecutionRequest(BaseModel):
    """Request model for flow execution."""
    flow_id: str
    execution_mode: str = Field(default="hybrid", pattern="^(crewai|database|hybrid)$")
    phase: Optional[str] = None


def get_discovery_orchestrator(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> DiscoveryOrchestrator:
    """Dependency injection for discovery orchestrator."""
    return DiscoveryOrchestrator(db, context)


@router.post("/initialize", response_model=DiscoveryFlowResponse)
async def initialize_discovery_flow(
    request: InitializeDiscoveryRequest,
    orchestrator: DiscoveryOrchestrator = Depends(get_discovery_orchestrator)
):
    """
    Initialize discovery flow with hybrid CrewAI + PostgreSQL architecture.
    Single entry point that coordinates both execution engine and management layer.
    """
    try:
        result = await orchestrator.initialize_discovery_flow(
            execution_mode=request.execution_mode,
            raw_data=request.raw_data,
            metadata=request.metadata,
            data_import_id=request.data_import_id
        )
        
        return DiscoveryFlowResponse(**result)
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize discovery flow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize discovery flow: {str(e)}"
        )


@router.get("/status/{flow_id}", response_model=DiscoveryFlowResponse)
async def get_discovery_flow_status(
    flow_id: str,
    orchestrator: DiscoveryOrchestrator = Depends(get_discovery_orchestrator)
):
    """Get unified discovery flow status from both CrewAI and PostgreSQL layers."""
    try:
        result = await orchestrator.get_discovery_flow_status(flow_id)
        
        # Ensure all required fields are present for the response model
        if "flow_id" not in result:
            result["flow_id"] = flow_id
        
        # Set defaults for missing fields
        defaults = {
            "client_account_id": "",
            "engagement_id": "",
            "user_id": "",
            "status": "unknown",
            "current_phase": "unknown",
            "progress_percentage": 0.0,
            "phases": {},
            "crewai_status": "unknown",
            "database_status": "unknown",
            "agent_insights": [],
            "created_at": "",
            "updated_at": ""
        }
        
        for key, default_value in defaults.items():
            if key not in result:
                result[key] = default_value
        
        return DiscoveryFlowResponse(**result)
        
    except Exception as e:
        logger.error(f"❌ Failed to get flow status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get flow status: {str(e)}"
        )


@router.post("/execute", response_model=Dict[str, Any])
async def execute_discovery_flow(
    request: FlowExecutionRequest,
    orchestrator: DiscoveryOrchestrator = Depends(get_discovery_orchestrator)
):
    """Execute discovery flow with specified execution mode."""
    try:
        result = await orchestrator.execute_discovery_flow(
            flow_id=request.flow_id,
            execution_mode=request.execution_mode,
            phase=request.phase
        )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to execute discovery flow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute discovery flow: {str(e)}"
        )


@router.get("/active", response_model=Dict[str, Any])
async def get_active_discovery_flows(
    limit: int = 50,
    include_completed: bool = False,
    orchestrator: DiscoveryOrchestrator = Depends(get_discovery_orchestrator)
):
    """Get list of active discovery flows for the current context."""
    try:
        result = await orchestrator.get_active_discovery_flows(
            limit=limit,
            include_completed=include_completed
        )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to get active flows: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active flows: {str(e)}"
        )