"""
Discovery Flow Completion Service
Handles flow completion logic, assessment package generation, and handoff to assessment phase.

This module has been modularized for maintainability:
- base.py: Base class and initialization
- validators.py: Flow completion validation logic
- queries.py: Asset retrieval and filtering
- package_generators.py: Assessment package generation and completion
- helpers.py: Helper functions for 6R strategy, risk assessment, etc.
"""

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.services.discovery_flow_completion_service.base import (
    DiscoveryFlowCompletionServiceBase,
)
from app.services.discovery_flow_completion_service.validators import (
    FlowCompletionValidator,
)
from app.services.discovery_flow_completion_service.queries import (
    AssetQueryManager,
)
from app.services.discovery_flow_completion_service.package_generators import (
    AssessmentPackageGenerator,
)


class DiscoveryFlowCompletionService(DiscoveryFlowCompletionServiceBase):
    """
    Service for handling discovery flow completion and assessment handoff.

    This service orchestrates the various components to provide:
    - Flow completion readiness validation
    - Assessment-ready asset queries
    - Assessment package generation
    - Flow completion and handoff
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize the Discovery Flow Completion Service.

        Args:
            db: Async database session
            context: Request context with tenant scoping
        """
        super().__init__(db, context)

        # Initialize component managers
        self._validator = FlowCompletionValidator(self)
        self._query_manager = AssetQueryManager(self)
        self._package_generator = AssessmentPackageGenerator(self)

    async def validate_flow_completion_readiness(
        self, discovery_flow_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Validate if a discovery flow is ready for completion and assessment handoff.

        Args:
            discovery_flow_id: UUID of the discovery flow

        Returns:
            Dict containing validation results and readiness status
        """
        return await self._validator.validate_flow_completion_readiness(
            discovery_flow_id
        )

    async def get_assessment_ready_assets(
        self, discovery_flow_id: uuid.UUID, filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get assets that are ready for assessment with optional filtering.

        Args:
            discovery_flow_id: UUID of the discovery flow
            filters: Optional filters (migration_ready, asset_type, min_confidence, etc.)

        Returns:
            Dict containing filtered assets and metadata
        """
        return await self._query_manager.get_assessment_ready_assets(
            discovery_flow_id, filters
        )

    async def generate_assessment_package(
        self,
        discovery_flow_id: uuid.UUID,
        selected_asset_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive assessment package for handoff to assessment phase.

        Args:
            discovery_flow_id: UUID of the discovery flow
            selected_asset_ids: Optional list of specific asset IDs to include

        Returns:
            Dict containing complete assessment package
        """
        return await self._package_generator.generate_assessment_package(
            discovery_flow_id, selected_asset_ids
        )

    async def complete_discovery_flow(
        self, discovery_flow_id: uuid.UUID, assessment_package: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Mark discovery flow as complete and prepare for assessment handoff.

        Args:
            discovery_flow_id: UUID of the discovery flow
            assessment_package: Generated assessment package

        Returns:
            Dict containing completion results
        """
        return await self._package_generator.complete_discovery_flow(
            discovery_flow_id, assessment_package
        )


# Preserve backward compatibility - export main service class
__all__ = ["DiscoveryFlowCompletionService"]
