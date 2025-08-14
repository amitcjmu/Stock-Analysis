"""
Base Child Flow Service
Abstract base class for child flow services
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext


class BaseChildFlowService(ABC):
    """Abstract base class for child flow services"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context

    @abstractmethod
    async def get_child_status(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get child flow status

        Args:
            flow_id: Flow identifier

        Returns:
            Child flow status dictionary or None
        """
        pass

    @abstractmethod
    async def get_by_master_flow_id(self, flow_id: str) -> Optional[Any]:
        """
        Get child flow by master flow ID

        Args:
            flow_id: Master flow identifier

        Returns:
            Child flow entity or None
        """
        pass
