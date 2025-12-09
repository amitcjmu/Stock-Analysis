"""
Discovery Flow Cleanup Service - Base Module
⚠️ LEGACY COMPATIBILITY LAYER - MIGRATING TO V2 ARCHITECTURE

Base class with core initialization and imports for discovery flow cleanup.
"""

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class DiscoveryFlowCleanupServiceBase:
    """
    Base class for discovery flow cleanup service
    Handles initialization and common state
    """

    def __init__(
        self,
        db_session: Optional[AsyncSession] = None,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
    ):
        self.db = db_session
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
