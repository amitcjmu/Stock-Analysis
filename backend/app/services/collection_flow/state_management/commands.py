"""
Command operations for Collection Flow State Management
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.collection_flow import (
    AutomationTier,
    CollectionFlow,
    CollectionFlowStatus,
)

from .base import CollectionPhase, CollectionPhaseUtils

logger = logging.getLogger(__name__)


# Note: _set_current_phase() helper removed per ADR-028
# Phase tracking now uses master flow as single source of truth


class CollectionFlowCommandService:
    """Command service for Collection Flow operations"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize the Collection Flow Command Service.

        Args:
            db: Database session
            context: Request context with tenant information
        """
        self.db = db
        self.context = context
        self.client_account_id = str(context.client_account_id)
        self.engagement_id = str(context.engagement_id)

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

        Per ADR-028: Uses master flow for phase tracking, not local phase_state.

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
        try:
            from app.models.crewai_flow_state_extensions import (
                CrewAIFlowStateExtensions,
            )

            # MFO Two-Table Pattern: flow_id MUST equal master_flow_id
            # This aligns Collection Flow with Discovery/Assessment patterns
            # See Issue #1136 for details
            if not master_flow_id:
                raise ValueError(
                    "master_flow_id is required for collection flow initialization. "
                    "Create master flow first via MFO."
                )

            # ADR-028: Initialize phase in master flow
            master_flow_result = await self.db.execute(
                select(CrewAIFlowStateExtensions).where(
                    CrewAIFlowStateExtensions.flow_id == master_flow_id
                )
            )
            master_flow = master_flow_result.scalar_one_or_none()

            if not master_flow:
                raise ValueError(
                    f"Master flow {master_flow_id} not found. "
                    "Violates ADR-006 (MFO is single source of truth)."
                )

            # Add initial phase transition to master flow (single source of truth)
            master_flow.add_phase_transition(
                phase=CollectionPhase.GAP_ANALYSIS.value,
                status="active",
                metadata={
                    "started_directly": True,
                    "reason": "Default collection flow starts at gap analysis phase (v4 plan)",
                    "skip_platform_detection": True,
                    "skip_automated_collection": True,
                },
            )

            # Create the collection flow (no phase_state per ADR-028)
            # flow_id = master_flow_id per MFO Two-Table Pattern
            collection_flow = CollectionFlow(
                # id will auto-generate (different value, that's OK)
                flow_id=master_flow_id,  # ✅ SAME as master_flow_id
                master_flow_id=master_flow_id,  # ✅ SAME as flow_id
                flow_name=flow_name,
                client_account_id=uuid.UUID(self.client_account_id),
                engagement_id=uuid.UUID(self.engagement_id),
                user_id=uuid.UUID(str(self.context.user_id)),
                automation_tier=automation_tier,
                status=CollectionFlowStatus.INITIALIZED,  # Per ADR-012: lifecycle state
                current_phase=CollectionPhase.GAP_ANALYSIS.value,
                # phase_state removed per ADR-028 - master flow is source of truth
                collection_config=collection_config or {},
                flow_metadata=metadata or {},
                discovery_flow_id=discovery_flow_id,
            )

            self.db.add(collection_flow)
            await self.db.commit()
            await self.db.refresh(collection_flow)

            logger.info(
                f"Initialized Collection Flow {master_flow_id} with tier {automation_tier} "
                f"(master flow: {master_flow_id})"
            )
            return collection_flow

        except Exception as e:
            logger.error(f"Failed to initialize Collection Flow: {str(e)}")
            await self.db.rollback()
            raise

    async def transition_phase(
        self,
        flow_id: uuid.UUID,
        new_phase: CollectionPhase,
        phase_metadata: Optional[Dict[str, Any]] = None,
    ) -> CollectionFlow:
        """
        Transition Collection Flow to a new phase.

        Per ADR-028 and Bug #648: Uses master flow as single source of truth
        for phase tracking. Eliminates duplicated phase_state tracking.

        Args:
            flow_id: Flow ID
            new_phase: New phase to transition to
            phase_metadata: Optional metadata for the phase

        Returns:
            Updated CollectionFlow instance
        """
        try:
            from app.models.crewai_flow_state_extensions import (
                CrewAIFlowStateExtensions,
            )

            # Get the collection flow
            result = await self.db.execute(
                select(CollectionFlow).where(
                    CollectionFlow.flow_id == flow_id,
                    CollectionFlow.client_account_id
                    == uuid.UUID(self.client_account_id),
                )
            )
            collection_flow = result.scalar_one_or_none()

            if not collection_flow:
                raise ValueError(f"Collection Flow {flow_id} not found")

            # Get master flow (ADR-006: single source of truth)
            if not collection_flow.master_flow_id:
                raise ValueError(
                    f"Collection Flow {flow_id} missing master_flow_id. "
                    "Violates ADR-006."
                )

            master_flow_result = await self.db.execute(
                select(CrewAIFlowStateExtensions).where(
                    CrewAIFlowStateExtensions.flow_id == collection_flow.master_flow_id
                )
            )
            master_flow = master_flow_result.scalar_one_or_none()

            if not master_flow:
                raise ValueError(
                    f"Master flow {collection_flow.master_flow_id} not found. "
                    "Violates ADR-006."
                )

            # Validate phase transition
            if not CollectionPhaseUtils.is_valid_transition(
                collection_flow.current_phase, new_phase.value
            ):
                raise ValueError(
                    f"Invalid phase transition from {collection_flow.current_phase} to {new_phase.value}"
                )

            # ADR-028: Complete previous phase in master flow
            if master_flow.phase_transitions:
                # Create mutable copy to notify SQLAlchemy of changes
                transitions = list(master_flow.phase_transitions)
                last_transition = transitions[-1]
                if last_transition.get("status") == "active":
                    last_transition["status"] = "completed"
                    last_transition["completed_at"] = datetime.utcnow().isoformat()
                # Re-assign to notify SQLAlchemy of JSONB mutation
                master_flow.phase_transitions = transitions

            # ADR-028: Add new phase transition to master flow (single source of truth)
            master_flow.add_phase_transition(
                phase=new_phase.value, status="active", metadata=phase_metadata or {}
            )

            # Synchronize current_phase column for query performance
            collection_flow.current_phase = new_phase.value

            # Per ADR-012: Set status based on lifecycle, not phase
            # Determine status based on whether phase requires user input or is complete
            if new_phase == CollectionPhase.FINALIZATION:
                collection_flow.status = CollectionFlowStatus.COMPLETED.value
            elif new_phase == CollectionPhase.INITIALIZATION:
                collection_flow.status = CollectionFlowStatus.INITIALIZED.value
            elif new_phase in [
                CollectionPhase.ASSET_SELECTION,
                CollectionPhase.MANUAL_COLLECTION,
            ]:
                collection_flow.status = (
                    CollectionFlowStatus.PAUSED.value
                )  # Requires user input
            else:
                # GAP_ANALYSIS, QUESTIONNAIRE_GENERATION, DATA_VALIDATION
                collection_flow.status = CollectionFlowStatus.RUNNING.value

            collection_flow.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(collection_flow)

            logger.info(
                f"Transitioned Collection Flow {flow_id} to phase {new_phase.value} "
                f"(master flow: {collection_flow.master_flow_id})"
            )
            return collection_flow

        except Exception as e:
            logger.error(
                f"Failed to transition phase for Collection Flow {flow_id}: {str(e)}"
            )
            await self.db.rollback()
            raise

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
        try:
            # Get the collection flow
            result = await self.db.execute(
                select(CollectionFlow).where(
                    CollectionFlow.flow_id == flow_id,
                    CollectionFlow.client_account_id
                    == uuid.UUID(self.client_account_id),
                )
            )
            collection_flow = result.scalar_one_or_none()

            if not collection_flow:
                raise ValueError(f"Collection Flow {flow_id} not found")

            # Update progress and scores
            collection_flow.progress_percentage = min(
                100.0, max(0.0, progress_percentage)
            )

            if quality_score is not None:
                collection_flow.collection_quality_score = quality_score

            if confidence_score is not None:
                collection_flow.confidence_score = confidence_score

            # Update metadata
            if metadata_updates:
                metadata = collection_flow.metadata or {}
                metadata.update(metadata_updates)
                collection_flow.metadata = metadata

            collection_flow.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(collection_flow)

            logger.info(
                f"Updated progress for Collection Flow {flow_id}: {progress_percentage}%"
            )
            return collection_flow

        except Exception as e:
            logger.error(
                f"Failed to update progress for Collection Flow {flow_id}: {str(e)}"
            )
            await self.db.rollback()
            raise

    async def fail_flow(
        self,
        flow_id: uuid.UUID,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None,
    ) -> CollectionFlow:
        """
        Mark Collection Flow as failed.

        Per ADR-028: Records error in master flow, not local phase_state.

        Args:
            flow_id: Flow ID
            error_message: Error message
            error_details: Optional error details

        Returns:
            Updated CollectionFlow instance
        """
        try:
            from app.models.crewai_flow_state_extensions import (
                CrewAIFlowStateExtensions,
            )

            # Get the collection flow
            result = await self.db.execute(
                select(CollectionFlow).where(
                    CollectionFlow.flow_id == flow_id,
                    CollectionFlow.client_account_id
                    == uuid.UUID(self.client_account_id),
                )
            )
            collection_flow = result.scalar_one_or_none()

            if not collection_flow:
                raise ValueError(f"Collection Flow {flow_id} not found")

            # Update flow status
            collection_flow.status = CollectionFlowStatus.FAILED
            collection_flow.error_message = error_message
            collection_flow.error_details = error_details or {}
            collection_flow.updated_at = datetime.utcnow()

            # ADR-028: Record error in master flow
            if collection_flow.master_flow_id:
                master_flow_result = await self.db.execute(
                    select(CrewAIFlowStateExtensions).where(
                        CrewAIFlowStateExtensions.flow_id
                        == collection_flow.master_flow_id
                    )
                )
                master_flow = master_flow_result.scalar_one_or_none()

                if master_flow:
                    # Mark current phase as failed in master flow
                    if master_flow.phase_transitions:
                        # Create mutable copy to notify SQLAlchemy of changes
                        transitions = list(master_flow.phase_transitions)
                        last_transition = transitions[-1]
                        if last_transition.get("status") == "active":
                            last_transition["status"] = "failed"
                            last_transition["completed_at"] = (
                                datetime.utcnow().isoformat()
                            )
                            last_transition["error"] = error_message
                        # Re-assign to notify SQLAlchemy of JSONB mutation
                        master_flow.phase_transitions = transitions

                    # Add error to master flow's error history
                    master_flow.add_error(
                        phase=collection_flow.current_phase or "unknown",
                        error=error_message,
                        details=error_details,
                    )

            await self.db.commit()
            await self.db.refresh(collection_flow)

            logger.error(f"Collection Flow {flow_id} failed: {error_message}")
            return collection_flow

        except Exception as e:
            logger.error(
                f"Failed to mark Collection Flow {flow_id} as failed: {str(e)}"
            )
            await self.db.rollback()
            raise
