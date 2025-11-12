"""
Workflow progress query operations.

Handles read-only operations for workflow progress tracking.
"""

from typing import List

from sqlalchemy.future import select

from app.models.asset import WorkflowProgress
from app.repositories.asset_repository.queries.base import BaseWorkflowProgressQueries


class WorkflowProgressQueries(BaseWorkflowProgressQueries):
    """Query operations for workflow progress."""

    async def get_progress_for_asset(self, asset_id: int) -> List[WorkflowProgress]:
        """Get all workflow progress records for an asset."""
        query = select(WorkflowProgress).where(WorkflowProgress.asset_id == asset_id)
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_progress_by_phase(self, phase: str) -> List[WorkflowProgress]:
        """Get workflow progress for a specific phase."""
        query = select(WorkflowProgress).where(WorkflowProgress.phase == phase)
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_active_workflows(self) -> List[WorkflowProgress]:
        """Get workflows that are currently in progress."""
        query = select(WorkflowProgress).where(WorkflowProgress.status == "in_progress")
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()
