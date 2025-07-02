"""
Admin Routes

API endpoints for administrative context operations.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.context import get_current_context
from ..services.validation_service import ValidationService
from ..models.context_schemas import ValidateContextRequest, ValidateContextResponse

router = APIRouter()


@router.get("/context")
async def get_context(
    context=Depends(get_current_context)
) -> dict:
    """
    Get current request context.
    
    This is primarily for debugging and administrative purposes.
    """
    if not context:
        return {"message": "No context available"}
    
    return {
        "client_account_id": context.client_account_id,
        "engagement_id": context.engagement_id,
        "user_id": context.user_id,
        "flow_id": context.flow_id,
        "request_id": context.request_id
    }


@router.post("/context/validate", response_model=ValidateContextResponse)
async def validate_context(
    request: ValidateContextRequest,
    db: AsyncSession = Depends(get_db)
) -> ValidateContextResponse:
    """
    Validate that the provided context is valid.
    
    This checks:
    - Client exists and is active
    - Engagement exists and belongs to the client
    - User has access to the client (if user_id provided)
    """
    service = ValidationService(db)
    return await service.validate_context(
        request.client_id,
        request.engagement_id,
        request.user_id
    )