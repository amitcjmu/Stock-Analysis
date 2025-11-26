"""
Base class for Resource Allocation Service.

Provides initialization, repository setup, and tenant scoping.
"""

import logging
import uuid

# typing imports used by subclasses

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.repositories.planning_flow_repository import PlanningFlowRepository

logger = logging.getLogger(__name__)

# CrewAI imports with fallback
try:
    from crewai import Task

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    logger.warning("CrewAI not available - resource allocation will fail")

    class Task:
        def __init__(self, **kwargs):
            pass


class BaseResourceAllocationService:
    """
    Base class for resource allocation service.

    Provides common initialization and tenant scoping setup.
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize resource allocation service.

        Args:
            db: Async database session
            context: Request context with tenant scoping
        """
        self.db = db
        self.context = context

        # Convert tenant IDs to UUIDs (never convert to integers)
        client_account_id = context.client_account_id
        if isinstance(client_account_id, str):
            client_account_uuid = uuid.UUID(client_account_id)
        else:
            client_account_uuid = client_account_id

        engagement_id = context.engagement_id
        if isinstance(engagement_id, str):
            engagement_uuid = uuid.UUID(engagement_id)
        else:
            engagement_uuid = engagement_id

        self.client_account_uuid = client_account_uuid
        self.engagement_uuid = engagement_uuid

        # Initialize repository with tenant scoping
        self.planning_repo = PlanningFlowRepository(
            db=db,
            client_account_id=client_account_uuid,
            engagement_id=engagement_uuid,
        )
