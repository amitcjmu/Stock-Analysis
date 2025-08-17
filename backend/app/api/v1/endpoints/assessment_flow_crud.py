"""
Assessment Flow CRUD Operations
Core database operations for assessment flows including verification, context creation,
and phase-specific data retrieval operations.
"""

import logging
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment_flow import AssessmentPhase
from app.repositories.assessment_flow_repository import AssessmentFlowRepository

logger = logging.getLogger(__name__)


async def verify_flow_access(
    flow_id: str, db: AsyncSession, client_account_id: str
) -> bool:
    """Verify user has access to assessment flow.

    Args:
        flow_id: Assessment flow identifier
        db: Database session
        client_account_id: Client account ID for scoping

    Returns:
        True if user has access, False otherwise
    """
    repository = AssessmentFlowRepository(db, client_account_id)
    flow_state = await repository.get_assessment_flow_state(flow_id)
    return flow_state is not None


async def get_assessment_flow_context(
    flow_id: str,
    client_account_id: str,
    engagement_id: str,
    user_id: str,
    db: AsyncSession,
) -> Dict[str, Any]:
    """Create flow context for assessment operations.

    Args:
        flow_id: Assessment flow identifier
        client_account_id: Client account ID
        engagement_id: Engagement identifier
        user_id: User identifier
        db: Database session

    Returns:
        Flow context dictionary with all necessary context data
    """
    # This would integrate with the actual flow context creation
    # For now, return a simple dict
    return {
        "flow_id": flow_id,
        "client_account_id": client_account_id,
        "engagement_id": engagement_id,
        "user_id": user_id,
        "db_session": db,
    }


async def get_phase_specific_data(
    repository: AssessmentFlowRepository, flow_id: str, phase: AssessmentPhase
) -> Dict[str, Any]:
    """Get phase-specific data for status response.

    Args:
        repository: Assessment flow repository instance
        flow_id: Assessment flow identifier
        phase: Current assessment phase

    Returns:
        Phase-specific data dictionary
    """
    # Return relevant data for each phase
    phase_data = {}

    if phase == AssessmentPhase.ARCHITECTURE_MINIMUMS:
        engagement_standards = await repository.get_engagement_standards(
            repository.client_account_id  # This would need the actual engagement_id
        )
        app_overrides = await repository.get_application_overrides(flow_id)
        phase_data = {
            "engagement_standards_count": len(engagement_standards),
            "application_overrides_count": len(app_overrides),
        }

    return phase_data
