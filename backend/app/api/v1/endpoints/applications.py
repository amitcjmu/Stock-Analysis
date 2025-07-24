from typing import Any, Dict

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/applications", response_model=Dict[str, Any])
async def get_applications(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Placeholder for fetching applications.
    In a real implementation, this would fetch all unique applications
    related to the current engagement.
    """
    return {"applications": []}
