"""
API endpoints for dependency analysis and management.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import extract_context_from_request
from app.core.database import get_db
from app.schemas.dependency_schemas import (
    DependencyAnalysisResponse,
    DependencyCreate,
    DependencyResponse,
)
from app.services.dependency_analysis_service import DependencyAnalysisService

router = APIRouter()


@router.get("/dependencies/analysis", response_model=DependencyAnalysisResponse)
async def get_dependency_analysis(
    request: Request, db: AsyncSession = Depends(get_db), flow_id: Optional[str] = None
):
    """Get comprehensive dependency analysis."""
    try:
        # Extract context from request headers
        context = extract_context_from_request(request)

        if not context.client_account_id or not context.engagement_id:
            raise HTTPException(
                status_code=400, detail="Client account and engagement context required"
            )

        service = DependencyAnalysisService(
            db, context.client_account_id, context.engagement_id, flow_id
        )
        return await service.get_dependency_analysis()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dependencies/analyze/{analysis_type}")
async def analyze_dependencies(
    request: Request,
    analysis_type: str,
    db: AsyncSession = Depends(get_db),
    flow_id: Optional[str] = None,
):
    """Trigger CrewAI analysis for dependencies."""
    try:
        # Extract context from request headers
        context = extract_context_from_request(request)

        if not context.client_account_id or not context.engagement_id:
            raise HTTPException(
                status_code=400, detail="Client account and engagement context required"
            )

        service = DependencyAnalysisService(
            db, context.client_account_id, context.engagement_id, flow_id
        )
        return await service.analyze_with_crew(analysis_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dependencies/applications")
async def get_available_applications(
    request: Request, db: AsyncSession = Depends(get_db)
):
    """Get list of available applications."""
    try:
        # Extract context from request headers
        context = extract_context_from_request(request)

        if not context.client_account_id or not context.engagement_id:
            raise HTTPException(
                status_code=400, detail="Client account and engagement context required"
            )

        service = DependencyAnalysisService(
            db, context.client_account_id, context.engagement_id
        )
        analysis = await service.get_dependency_analysis()
        return analysis["cross_application_mapping"]["available_applications"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dependencies/servers")
async def get_available_servers(request: Request, db: AsyncSession = Depends(get_db)):
    """Get list of available servers."""
    try:
        # Extract context from request headers
        context = extract_context_from_request(request)

        if not context.client_account_id or not context.engagement_id:
            raise HTTPException(
                status_code=400, detail="Client account and engagement context required"
            )

        service = DependencyAnalysisService(
            db, context.client_account_id, context.engagement_id
        )
        analysis = await service.get_dependency_analysis()
        return analysis["app_server_mapping"]["available_servers"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dependencies", response_model=DependencyResponse)
async def create_dependency(
    request: Request, dependency: DependencyCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new dependency relationship."""
    try:
        # Extract context from request headers
        context = extract_context_from_request(request)

        if not context.client_account_id or not context.engagement_id:
            raise HTTPException(
                status_code=400, detail="Client account and engagement context required"
            )

        service = DependencyAnalysisService(
            db, context.client_account_id, context.engagement_id
        )
        return await service.create_dependency(
            dependency.source_id,
            dependency.target_id,
            dependency.dependency_type,
            dependency.is_app_to_app,
            dependency.description,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
