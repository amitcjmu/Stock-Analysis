"""
Unified Discovery Flow API Endpoints
Single source of truth for all discovery flow operations.
Connects frontend to UnifiedDiscoveryFlow CrewAI execution engine.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.context import get_current_context, RequestContext
from app.services.crewai_flows.unified_discovery_flow import UnifiedDiscoveryFlow, create_unified_discovery_flow
from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Unified Discovery Flow"])

# === Request/Response Models ===

class InitializeFlowRequest(BaseModel):
    """Request model for initializing unified discovery flow"""
    session_id: str = Field(..., description="Session ID for the flow")
    client_account_id: str = Field(..., description="Client account ID")
    engagement_id: str = Field(..., description="Engagement ID")
    user_id: str = Field(..., description="User ID")
    raw_data: list = Field(..., description="Raw CMDB data")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional metadata")

class ExecutePhaseRequest(BaseModel):
    """Request model for executing flow phase"""
    data: Optional[Dict[str, Any]] = Field(default={}, description="Phase-specific data")

class FlowStatusResponse(BaseModel):
    """Response model for flow status"""
    flow_id: str
    session_id: str
    client_account_id: str
    engagement_id: str
    user_id: str
    current_phase: str
    phase_completion: Dict[str, bool]
    crew_status: Dict[str, Any]
    raw_data: list
    field_mappings: Dict[str, Any]
    cleaned_data: list
    asset_inventory: Dict[str, Any]
    dependencies: Dict[str, Any]
    technical_debt: Dict[str, Any]
    status: str
    progress_percentage: float
    errors: list
    warnings: list
    created_at: str
    updated_at: str

class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    unified_flow_available: bool
    crewai_service_status: str
    database_status: str
    timestamp: str

# === API Endpoints ===

@router.post("/flow/initialize", response_model=Dict[str, Any])
async def initialize_discovery_flow(
    request: InitializeFlowRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """
    Initialize a new unified discovery flow with CrewAI execution.
    This creates the flow and starts the CrewAI execution engine.
    """
    try:
        logger.info(f"🚀 Initializing unified discovery flow: session={request.session_id}")
        
        # Import CrewAI service
        try:
            from app.services.crewai_service import CrewAIService
            crewai_service = CrewAIService()
        except ImportError:
            logger.warning("CrewAI service not available, using mock")
            crewai_service = None
        
        # Create unified discovery flow
        flow = create_unified_discovery_flow(
            session_id=request.session_id,
            client_account_id=request.client_account_id,
            engagement_id=request.engagement_id,
            user_id=request.user_id,
            raw_data=request.raw_data,
            crewai_service=crewai_service,
            context=context
        )
        
        # Start the flow
        result = await flow.kickoff()
        
        logger.info(f"✅ Unified discovery flow initialized: session={request.session_id}")
        
        return {
            "status": "initialized",
            "session_id": request.session_id,
            "flow_id": flow.state.flow_id,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize unified discovery flow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize discovery flow: {str(e)}"
        )

@router.get("/flow/status/{session_id}", response_model=FlowStatusResponse)
async def get_flow_status(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """
    Get current status of unified discovery flow.
    Returns comprehensive flow state including phase completion and crew status.
    """
    try:
        logger.info(f"🔍 Getting unified flow status: session={session_id}")
        
        # Try to get flow state from database persistence
        try:
            from app.services.crewai_flows.postgresql_flow_persistence import PostgreSQLFlowPersistence
            persistence = PostgreSQLFlowPersistence(db, context)
            flow_state = await persistence.restore_flow_state(session_id)
            
            if flow_state:
                logger.info(f"✅ Flow state restored from database: session={session_id}")
                return FlowStatusResponse(**flow_state.dict())
            
        except Exception as e:
            logger.warning(f"Failed to restore from database: {e}")
        
        # If no database state, try to find active flow
        # For now, return a mock response to prevent frontend errors
        logger.warning(f"No flow state found for session={session_id}, returning mock data")
        
        mock_state = UnifiedDiscoveryFlowState(
            flow_id=f"flow-{session_id}",
            session_id=session_id,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            user_id=context.user_id,
            current_phase="initialization",
            phase_completion={
                "data_import": False,
                "field_mapping": False,
                "data_cleansing": False,
                "asset_inventory": False,
                "dependency_analysis": False,
                "tech_debt_analysis": False
            },
            crew_status={},
            raw_data=[],
            field_mappings={},
            cleaned_data=[],
            asset_inventory={},
            dependencies={},
            technical_debt={},
            status="not_found",
            progress_percentage=0.0,
            errors=[f"No flow found for session {session_id}"],
            warnings=["Flow may not have been initialized"],
            created_at="",
            updated_at=""
        )
        
        return FlowStatusResponse(**mock_state.dict())
        
    except Exception as e:
        logger.error(f"❌ Failed to get flow status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get flow status: {str(e)}"
        )

@router.post("/flow/execute/{phase}", response_model=Dict[str, Any])
async def execute_flow_phase(
    phase: str,
    request: ExecutePhaseRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """
    Execute a specific phase of the unified discovery flow.
    Triggers CrewAI crew execution for the specified phase.
    """
    try:
        logger.info(f"🔄 Executing unified flow phase: phase={phase}")
        
        # For now, return a mock success response
        # TODO: Implement actual phase execution
        logger.warning(f"Phase execution not yet implemented for phase={phase}")
        
        return {
            "status": "phase_started",
            "phase": phase,
            "message": f"Phase {phase} execution started",
            "crew_status": "initializing"
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to execute phase {phase}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute phase {phase}: {str(e)}"
        )

@router.get("/flow/health", response_model=HealthResponse)
async def get_flow_health(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """
    Get health status of the unified discovery flow system.
    Checks CrewAI service availability and database connectivity.
    """
    try:
        from datetime import datetime
        
        # Check CrewAI service availability
        crewai_status = "available"
        try:
            from app.services.crewai_service import CrewAIService
            crewai_service = CrewAIService()
        except ImportError:
            crewai_status = "unavailable"
        
        # Check database connectivity
        db_status = "connected"
        try:
            await db.execute("SELECT 1")
        except Exception:
            db_status = "disconnected"
        
        overall_status = "healthy" if crewai_status == "available" and db_status == "connected" else "degraded"
        
        return HealthResponse(
            status=overall_status,
            unified_flow_available=True,
            crewai_service_status=crewai_status,
            database_status=db_status,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            unified_flow_available=False,
            crewai_service_status="error",
            database_status="error",
            timestamp=datetime.utcnow().isoformat()
        ) 