"""
Discovery Flow Completion Service - Base Module
Handles base class initialization and dependencies.
"""

import logging
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.repositories.asset_repository import AssetRepository
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class DiscoveryFlowCompletionServiceBase:
    """Base class for Discovery Flow Completion Service"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize the Discovery Flow Completion Service.

        Args:
            db: Async database session
            context: Request context with tenant scoping
        """
        self.db = db
        self.context = context
        self.discovery_repo = DiscoveryFlowRepository(
            db, str(context.client_account_id), str(context.engagement_id)
        )
        self.asset_repo = AssetRepository(db, str(context.client_account_id))
