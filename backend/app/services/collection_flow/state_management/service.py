"""
Main Collection Flow State Management Service

This service manages the lifecycle and state transitions of Collection Flows,
combining all the modularized components for backward compatibility.
"""

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.collection_flow import (
    AutomationTier,
    CollectionFlow,
    CollectionFlowStatus,
)

from .base import CollectionPhase
from .commands import CollectionFlowCommandService
from .completion import CollectionFlowCompletionService
from .queries import CollectionFlowQueryService


class CollectionFlowStateService:
    """
    Service for managing Collection Flow state and lifecycle.

    This service handles:
    - Flow initialization and setup
    - Phase transitions and validation
    - State updates and persistence
    - Flow completion and finalization
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize the Collection Flow State Service.

        Args:
            db: Database session
            context: Request context with tenant information
        """
        self.db = db
        self.context = context
        self.client_account_id = str(context.client_account_id)
        self.engagement_id = str(context.engagement_id)

        # Initialize component services
        self._commands = CollectionFlowCommandService(db, context)
        self._completion = CollectionFlowCompletionService(db, context)
        self._queries = CollectionFlowQueryService(db, context)

    async def initialize_flow(
        self,
        flow_name: str,
        automation_tier: AutomationTier,
        master_flow_id: Optional[uuid.UUID] = None,
        discovery_flow_id: Optional[uuid.UUID] = None,
        collection_config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CollectionFlow:
        """
        Initialize a new Collection Flow.

        Args:
            flow_name: Name of the collection flow
            automation_tier: Automation tier (tier_1, tier_2, tier_3, tier_4)
            master_flow_id: Optional master flow ID
            discovery_flow_id: Optional discovery flow ID
            collection_config: Optional collection configuration
            metadata: Optional metadata

        Returns:
            Created CollectionFlow instance
        """
        return await self._commands.initialize_flow(
            flow_name=flow_name,
            automation_tier=automation_tier,
            master_flow_id=master_flow_id,
            discovery_flow_id=discovery_flow_id,
            collection_config=collection_config,
            metadata=metadata,
        )

    async def transition_phase(
        self,
        flow_id: uuid.UUID,
        new_phase: CollectionPhase,
        phase_metadata: Optional[Dict[str, Any]] = None,
    ) -> CollectionFlow:
        """
        Transition Collection Flow to a new phase.

        Args:
            flow_id: Flow ID
            new_phase: New phase to transition to
            phase_metadata: Optional metadata for the phase

        Returns:
            Updated CollectionFlow instance
        """
        return await self._commands.transition_phase(
            flow_id=flow_id, new_phase=new_phase, phase_metadata=phase_metadata
        )

    async def update_progress(
        self,
        flow_id: uuid.UUID,
        progress_percentage: float,
        quality_score: Optional[float] = None,
        confidence_score: Optional[float] = None,
        metadata_updates: Optional[Dict[str, Any]] = None,
    ) -> CollectionFlow:
        """
        Update Collection Flow progress and scores.

        Args:
            flow_id: Flow ID
            progress_percentage: Progress percentage (0-100)
            quality_score: Optional quality score
            confidence_score: Optional confidence score
            metadata_updates: Optional metadata updates

        Returns:
            Updated CollectionFlow instance
        """
        return await self._commands.update_progress(
            flow_id=flow_id,
            progress_percentage=progress_percentage,
            quality_score=quality_score,
            confidence_score=confidence_score,
            metadata_updates=metadata_updates,
        )

    async def fail_flow(
        self,
        flow_id: uuid.UUID,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None,
    ) -> CollectionFlow:
        """
        Mark Collection Flow as failed.

        Args:
            flow_id: Flow ID
            error_message: Error message
            error_details: Optional error details

        Returns:
            Updated CollectionFlow instance
        """
        return await self._commands.fail_flow(
            flow_id=flow_id, error_message=error_message, error_details=error_details
        )

    async def complete_flow(
        self,
        flow_id: uuid.UUID,
        final_quality_score: float,
        final_confidence_score: float,
        completion_metadata: Optional[Dict[str, Any]] = None,
    ) -> CollectionFlow:
        """
        Mark Collection Flow as completed.

        Args:
            flow_id: Flow ID
            final_quality_score: Final quality score
            final_confidence_score: Final confidence score
            completion_metadata: Optional completion metadata

        Returns:
            Updated CollectionFlow instance
        """
        return await self._completion.complete_flow(
            flow_id=flow_id,
            final_quality_score=final_quality_score,
            final_confidence_score=final_confidence_score,
            completion_metadata=completion_metadata,
        )

    async def get_flow_by_id(self, flow_id: uuid.UUID) -> Optional[CollectionFlow]:
        """
        Get Collection Flow by ID.

        Args:
            flow_id: Flow ID

        Returns:
            CollectionFlow instance or None
        """
        return await self._queries.get_flow_by_id(flow_id)

    async def get_flows_by_status(
        self, status: CollectionFlowStatus, limit: int = 100
    ) -> List[CollectionFlow]:
        """
        Get Collection Flows by status.

        Args:
            status: Flow status
            limit: Maximum number of flows to return

        Returns:
            List of CollectionFlow instances
        """
        return await self._queries.get_flows_by_status(status, limit)
