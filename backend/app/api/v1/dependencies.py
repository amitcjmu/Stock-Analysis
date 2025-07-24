"""
Shared dependencies for API endpoints.
"""

from app.core.database import get_db
from app.services.crewai_flow_service import CrewAIFlowService
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession


def get_crewai_flow_service(db: AsyncSession = Depends(get_db)) -> CrewAIFlowService:
    """
    Dependency injector for CrewAIFlowService.
    Ensures the service is instantiated once per request with a valid DB session.
    """
    return CrewAIFlowService(db)
