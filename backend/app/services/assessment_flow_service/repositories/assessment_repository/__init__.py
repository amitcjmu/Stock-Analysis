"""
Assessment repository for data access operations.

This module provides a unified AssessmentRepository class that combines
query and command operations for assessment-related data access.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext

from .commands import AssessmentRepositoryCommands
from .queries import AssessmentRepositoryQueries


class AssessmentRepository(AssessmentRepositoryQueries, AssessmentRepositoryCommands):
    """
    Repository for assessment-related data operations.

    This class combines query and command operations through multiple inheritance,
    providing a unified interface for all assessment repository operations while
    keeping the implementation modular and maintainable.

    Query operations (read-only):
    - get_flow_by_id: Get discovery flow by ID
    - get_flow_assets: Get assets for a flow with optional filtering
    - get_assessment_ready_assets: Get assets ready for assessment
    - get_asset_by_id: Get asset by ID
    - get_flow_statistics: Get statistical summary for a flow
    - get_assets_by_criteria: Get assets matching specific criteria
    - search_assets: Search assets by name or type

    Command operations (write):
    - update_flow_completion_status: Update flow completion status
    - update_asset_assessment_data: Update asset with assessment data
    - bulk_update_assets: Bulk update multiple assets
    - delete_assessment_data: Delete assessment data for a flow
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize the assessment repository.

        Args:
            db: AsyncSession for database operations
            context: RequestContext with tenant scoping information
        """
        # Initialize both parent classes
        AssessmentRepositoryQueries.__init__(self, db, context)
        AssessmentRepositoryCommands.__init__(self, db, context)


# Preserve backward compatibility - export all classes
__all__ = [
    "AssessmentRepository",
    "AssessmentRepositoryQueries",
    "AssessmentRepositoryCommands",
]
