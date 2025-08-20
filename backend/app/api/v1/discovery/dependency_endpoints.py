"""
API endpoints for dependency analysis and management.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.api.v1.endpoints.context.services.user_service import UserService
from app.core.database import get_db
from app.models.client_account import User
from app.schemas.dependency_schemas import (
    DependencyAnalysisResponse,
    DependencyCreate,
    DependencyResponse,
)
from app.services.dependency_analysis_service import DependencyAnalysisService

router = APIRouter()


async def get_user_context(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Extract client_account_id and engagement_id from authenticated user.
    """
    service = UserService(db)
    user_context = await service.get_user_context(current_user)

    if not user_context.client:
        raise HTTPException(
            status_code=400, detail="User not associated with a client account"
        )

    return {
        "client_account_id": user_context.client.id,
        "engagement_id": (
            user_context.engagement.id if user_context.engagement else None
        ),
        "user_id": str(current_user.id),
    }


@router.get("/dependencies/analysis", response_model=DependencyAnalysisResponse)
async def get_dependency_analysis(
    db: AsyncSession = Depends(get_db),
    flow_id: Optional[str] = None,
    user_context: dict = Depends(get_user_context),
):
    """Get comprehensive dependency analysis."""
    try:
        if not user_context["client_account_id"] or not user_context["engagement_id"]:
            raise HTTPException(
                status_code=400, detail="Client account and engagement context required"
            )

        service = DependencyAnalysisService(
            db,
            user_context["client_account_id"],
            user_context["engagement_id"],
            flow_id,
        )
        return await service.get_dependency_analysis()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dependencies/analyze/{analysis_type}")
async def analyze_dependencies(
    analysis_type: str,
    db: AsyncSession = Depends(get_db),
    flow_id: Optional[str] = None,
    user_context: dict = Depends(get_user_context),
):
    """Trigger CrewAI analysis for dependencies."""
    try:
        if not user_context["client_account_id"] or not user_context["engagement_id"]:
            raise HTTPException(
                status_code=400, detail="Client account and engagement context required"
            )

        service = DependencyAnalysisService(
            db,
            user_context["client_account_id"],
            user_context["engagement_id"],
            flow_id,
        )
        return await service.analyze_with_crew(analysis_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dependencies/applications")
async def get_available_applications(
    db: AsyncSession = Depends(get_db), user_context: dict = Depends(get_user_context)
):
    """Get list of available applications."""
    try:
        if not user_context["client_account_id"] or not user_context["engagement_id"]:
            raise HTTPException(
                status_code=400, detail="Client account and engagement context required"
            )

        service = DependencyAnalysisService(
            db, user_context["client_account_id"], user_context["engagement_id"]
        )
        analysis = await service.get_dependency_analysis()
        return analysis["cross_application_mapping"]["available_applications"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dependencies/servers")
async def get_available_servers(
    db: AsyncSession = Depends(get_db), user_context: dict = Depends(get_user_context)
):
    """Get list of available servers."""
    try:
        if not user_context["client_account_id"] or not user_context["engagement_id"]:
            raise HTTPException(
                status_code=400, detail="Client account and engagement context required"
            )

        service = DependencyAnalysisService(
            db, user_context["client_account_id"], user_context["engagement_id"]
        )
        analysis = await service.get_dependency_analysis()
        return analysis["app_server_mapping"]["available_servers"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dependencies", response_model=DependencyResponse)
async def create_dependency(
    dependency: DependencyCreate,
    db: AsyncSession = Depends(get_db),
    user_context: dict = Depends(get_user_context),
):
    """Create a new dependency relationship."""
    try:
        if not user_context["client_account_id"] or not user_context["engagement_id"]:
            raise HTTPException(
                status_code=400, detail="Client account and engagement context required"
            )

        service = DependencyAnalysisService(
            db, user_context["client_account_id"], user_context["engagement_id"]
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
