"""
Base class for Planning Flow Repository.

Provides initialization and multi-tenant scoping for planning flow operations.
"""

import logging
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.planning import PlanningFlow
from app.repositories.context_aware_repository import ContextAwareRepository

logger = logging.getLogger(__name__)


class PlanningFlowRepositoryBase(ContextAwareRepository[PlanningFlow]):
    """
    Base repository for planning flow data access with multi-tenant scoping.

    Follows existing patterns from CollectionFlowRepository and AssessmentFlowRepository.
    All operations are automatically scoped by client_account_id and engagement_id.
    """

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: Optional[uuid.UUID] = None,
        engagement_id: Optional[uuid.UUID] = None,
    ):
        """
        Initialize planning flow repository with context.

        Args:
            db: Async database session
            client_account_id: Client account UUID for tenant scoping (per migration 115)
            engagement_id: Engagement UUID for project scoping (per migration 115)
        """
        super().__init__(db, PlanningFlow, client_account_id, engagement_id)
        logger.debug(
            f"Initialized PlanningFlowRepository: "
            f"client_account_id={client_account_id}, engagement_id={engagement_id}"
        )
