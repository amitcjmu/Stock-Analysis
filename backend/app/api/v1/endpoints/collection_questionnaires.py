"""
Collection Flow Questionnaire Endpoints
Handles questionnaire generation, responses, and submission operations.
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context import get_request_context
from app.core.database import get_db
from app.models import User
from app.schemas.collection_flow import (
    AdaptiveQuestionnaireResponse,
    QuestionnaireSubmissionRequest,
)
from app.api.v1.endpoints import collection_crud

# Import agent questionnaires router
from app.api.v1.endpoints.collection_agent_questionnaires import (
    router as agent_questionnaires_router,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Include agent questionnaires endpoints
router.include_router(agent_questionnaires_router)


@router.get(
    "/flows/{flow_id}/questionnaires",
    response_model=List[AdaptiveQuestionnaireResponse],
)
async def get_adaptive_questionnaires(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> List[AdaptiveQuestionnaireResponse]:
    """Get adaptive questionnaires for manual collection"""
    return await collection_crud.get_adaptive_questionnaires(
        flow_id=flow_id,
        db=db,
        context=context,
    )


@router.get("/flows/{flow_id}/questionnaires/{questionnaire_id}/responses")
async def get_questionnaire_responses(
    flow_id: str,
    questionnaire_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """Get saved questionnaire responses for a specific flow and questionnaire"""
    return await collection_crud.get_questionnaire_responses(
        flow_id=flow_id,
        questionnaire_id=questionnaire_id,
        db=db,
        current_user=current_user,
        context=context,
    )


@router.post("/flows/{flow_id}/questionnaires/{questionnaire_id}/responses")
async def submit_questionnaire_response(
    flow_id: str,
    questionnaire_id: str,
    request_data: QuestionnaireSubmissionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """Submit responses to an adaptive questionnaire"""
    return await collection_crud.submit_questionnaire_response(
        flow_id=flow_id,
        questionnaire_id=questionnaire_id,
        request_data=request_data,
        db=db,
        current_user=current_user,
        context=context,
    )


@router.post("/flows/{flow_id}/questionnaires/{questionnaire_id}/submit")
async def submit_questionnaire_response_legacy(
    flow_id: str,
    questionnaire_id: str,
    request_data: QuestionnaireSubmissionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """LEGACY: Submit responses to an adaptive questionnaire

    This endpoint is provided for backward compatibility.
    New integrations should use /flows/{flow_id}/questionnaires/{questionnaire_id}/responses
    """
    # Forward to the new endpoint implementation
    return await collection_crud.submit_questionnaire_response(
        flow_id=flow_id,
        questionnaire_id=questionnaire_id,
        request_data=request_data,
        db=db,
        current_user=current_user,
        context=context,
    )
