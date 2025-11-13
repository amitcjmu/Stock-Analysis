"""
Base dependency repository with core initialization.
"""

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import AssetDependency
from app.repositories.context_aware_repository import ContextAwareRepository

logger = logging.getLogger(__name__)


class DependencyRepository(ContextAwareRepository[AssetDependency]):
    """Enhanced dependency repository with application-specific operations."""

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
    ):
        """Initialize dependency repository with context."""
        super().__init__(db, AssetDependency, client_account_id, engagement_id)
        # Override context filtering since AssetDependency doesn't have context fields
        self.has_client_account = False
        self.has_engagement = False
